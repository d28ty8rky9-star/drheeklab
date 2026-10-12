"""Production batches, one-time consumption and individual photographic inspection."""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import shutil
from uuid import uuid4
from PySide6.QtGui import QImageReader
from .catalog import Catalog, required
from .inventory import Inventory
from .products import Products
from .pricing import integer, number, grams_mg, cents, money, calculate
from .storage import now
from .transactions import transaction
from .journal import record
from .sales import Sales

STATES = {'waiting':'Aguardando', 'printing':'Imprimindo', 'inspection':'Aguardando inspeção', 'completed':'Concluída'}
PRIORITIES = {'high':'Alta', 'normal':'Normal', 'low':'Baixa'}
CHECKS = {
    'decorative': ('surface', 'supports', 'adhesion', 'detail', 'appearance'),
    'functional': ('surface', 'supports', 'adhesion', 'detail', 'dimensions', 'fit', 'strength'),
    'mixed': ('surface', 'supports', 'adhesion', 'detail', 'appearance', 'dimensions', 'fit', 'strength'),
}
CHECK_LABELS = {'surface':'Superfície', 'supports':'Remoção de suportes', 'adhesion':'Camadas e adesão', 'detail':'Detalhes delicados', 'appearance':'Aparência', 'dimensions':'Dimensões', 'fit':'Encaixe e função', 'strength':'Resistência adequada ao uso'}
VIEWS = {'front':'Frente', 'back':'Lateral ou verso', 'detail':'Detalhe crítico'}


def split(total, weights):
    """Integer allocation, largest remainders; sum always equals total."""
    weights = [number(w) for w in weights]
    denominator = sum(weights)
    if not denominator:
        raise ValueError('O rateio deve ter pelo menos um peso positivo.')
    shares = [Decimal(total) * w / denominator for w in weights]
    result = [int(w) for w in shares]
    for index in sorted(range(len(shares)), key=lambda i: shares[i]-result[i], reverse=True)[:total-sum(result)]:
        result[index] += 1
    return result


class Production:
    def __init__(self, storage):
        self.storage, self.db = storage, storage.db
        self.catalog, self.products, self.inventory = Catalog(storage), Products(storage), Inventory(storage)

    def get(self, identifier):
        row = self.db.execute('SELECT * FROM production_orders WHERE id=?', (identifier,)).fetchone()
        if not row: raise ValueError('Ordem de produção não encontrada.')
        return dict(row)

    def entries(self, identifier):
        return [dict(r) for r in self.db.execute('SELECT e.*,v.name AS variant_name,p.name AS product_name,p.id AS product_id FROM production_entries e JOIN variants v ON v.id=e.variant_id JOIN products p ON p.id=v.product_id WHERE op_id=? ORDER BY e.id', (identifier,))]

    def queue(self):
        return [dict(r) for r in self.db.execute("SELECT * FROM production_orders ORDER BY CASE state WHEN 'completed' THEN 1 ELSE 0 END,CASE priority WHEN 'high' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END,position,id")]

    def create(self, printer_id, minutes, entries, responsible, parameters, priority='normal', item_id=None, weights=None, allocation_reason='', parent_id=None):
        responsible = required(responsible, 'Responsável')
        parameters = required(parameters, 'Parâmetros de impressão')
        if priority not in PRIORITIES: raise ValueError('Prioridade inválida.')
        minutes = integer(minutes, 'Tempo previsto', minimum=1)
        if not entries or len(entries)>100: raise ValueError('Adicione de 1 a 100 modelos ao lote.')
        snapshots, rows = [], []
        with transaction(self.db):
            if parent_id: self.get(parent_id)
            for entry in entries:
                variant = self.products.active_variant(entry['variant_id'])
                model = self.products.active_product(variant['product_id'])
                project = self.products.get('project_versions', entry['project_id'])
                if project['archived']: raise ValueError('Restaure a versão do arquivo antes de criar nova OP.')
                if project['product_id'] != model['id']: raise ValueError('Arquivo não pertence ao modelo selecionado.')
                self.products.media_path(project['id'], 'project')
                qty = integer(entry['quantity'], 'Quantidade', minimum=1)
                if qty > 10000: raise ValueError('Máximo de 10.000 peças por modelo.')
                snap = self.catalog.estimate(printer_id, 0, entry['filaments'], entry.get('auxiliary','0'), qty)
                snap['project'] = project
                snap['product'] = model
                snap['variant'] = variant
                snapshots.append(snap)
                rows.append((variant['id'], project['id'], qty, model['category']))
            if sum(r[2] for r in rows)>10000: raise ValueError('Máximo de 10.000 peças por lote.')
            if item_id:
                sales = Sales(self.storage); item = sales.get('order_items', item_id)
                if sales.get('orders', item['order_id'])['state'] != 'approved': raise ValueError('Pedido cancelado não aceita nova produção.')
                mapped = self.db.execute('SELECT variant_id FROM order_fulfillment WHERE item_id=?', (item_id,)).fetchone()
                expected = mapped[0] if mapped else item['variant_id']
                if expected is None and len(rows)==1:
                    expected=rows[0][0]
                    self.db.execute('INSERT INTO order_fulfillment VALUES(?,?)',(item_id,expected))
                    self.storage.audit('pedido:variante de produção',f'order_items:{item_id}',None,{'variant_id':expected},'Variante operacional selecionada na criação da OP; dados comerciais preservados')
                if len(rows)!=1 or rows[0][0]!=expected: raise ValueError('Selecione uma única variante correspondente ao item do pedido.')
            if weights is None:
                weights = [sum(Decimal(f['grams']) for f in snap['filaments']) for snap in snapshots]
            else:
                required(allocation_reason, 'Justificativa do rateio manual')
                if len(weights)!=len(rows): raise ValueError('Informe um peso de rateio por modelo.')
            weights = [str(number(w)) for w in weights]
            machine = cents(str(money(sum(Decimal(snapshots[0]['printer'][k]) for k in ('investment_hour_cents','energy_hour_cents','maintenance_hour_cents')) / 100 * minutes / 60)))
            shares = split(machine, weights)
            for snap, share in zip(snapshots, shares):
                snap['machine_cost'] = str(Decimal(share)/100)
                snap['total_cost'] = str(money(Decimal(snap['material_cost'])+Decimal(snap['auxiliary'])+Decimal(share)/100))
                snap['unit_cost'] = str(money(Decimal(snap['total_cost'])/snap['quantity']))
            planned = {'minutes':minutes, 'weights':weights, 'allocation_reason':allocation_reason, 'machine_cents':machine, 'reference_cents':sum(cents(s['total_cost']) for s in snapshots), 'printer':snapshots[0]['printer']}
            code = Sales(self.storage).code('OP')
            pos = self.db.execute('SELECT COALESCE(MAX(position),0)+1 FROM production_orders').fetchone()[0]
            op = self.db.execute("INSERT INTO production_orders(code,printer_id,item_id,parent_id,created_at,priority,position,state,responsible,parameters,planned) VALUES(?,?,?,?,?,?,?,'waiting',?,?,?)", (code,printer_id,item_id,parent_id,now(),priority,pos,responsible,parameters,json.dumps(planned))).lastrowid
            for values,snap in zip(rows,snapshots):
                self.db.execute('INSERT INTO production_entries(op_id,variant_id,project_id,quantity,category,planned) VALUES(?,?,?,?,?,?)', (op,*values,json.dumps(snap,ensure_ascii=False)))
            self.storage.audit('produção:criar', f'OP:{op}', None, {'order':self.get(op),'entries':snapshots})
        return op

    def reorder(self, identifiers, priority):
        if priority not in PRIORITIES: raise ValueError('Prioridade inválida.')
        with transaction(self.db):
            expected = {r['id'] for r in self.queue() if r['priority']==priority and r['state']!='completed'}
            if len(identifiers)!=len(set(identifiers)) or set(identifiers)!=expected: raise ValueError('Reordene todas as ordens ativas desta prioridade.')
            for pos,identifier in enumerate(identifiers):
                self.db.execute('UPDATE production_orders SET position=? WHERE id=?', (pos,identifier))
            self.storage.audit('produção:fila','queue',None,identifiers,priority)

    def priority(self, identifier, priority):
        if priority not in PRIORITIES: raise ValueError('Prioridade inválida.')
        with transaction(self.db):
            old = self.get(identifier)
            if old['state']=='completed': raise ValueError('Ordem concluída não entra na fila.')
            self.db.execute('UPDATE production_orders SET priority=? WHERE id=?',(priority,identifier))
            self.storage.audit('produção:prioridade',f'OP:{identifier}',old,self.get(identifier))

    def start(self, identifier):
        with transaction(self.db):
            op = self.get(identifier)
            if op['cost_consolidated']: raise ValueError('Custo desta OP já consolidado. Crie uma nova OP de reimpressão.')
            if op['state']!='waiting': raise ValueError('Somente uma ordem aguardando pode ser iniciada.')
            printer = self.catalog.get('printers',op['printer_id'])
            if printer['archived'] or printer['status']!='operational': raise ValueError('Impressora indisponível.')
            if self.db.execute("SELECT 1 FROM production_orders WHERE printer_id=? AND state='printing'",(op['printer_id'],)).fetchone(): raise ValueError('Esta impressora já possui uma ordem imprimindo.')
            self.db.execute("UPDATE production_orders SET state='printing',started_at=? WHERE id=?",(now(),identifier))
            self.storage.audit('produção:iniciar',f'OP:{identifier}',op,self.get(identifier))

    def elapsed_minutes(self, identifier):
        op=self.get(identifier)
        if op['state']!='printing' or not op['started_at']: return 0
        return max(0,int((datetime.now(timezone.utc)-datetime.fromisoformat(op['started_at'])).total_seconds()/60))

    def confirm(self, identifier, minutes, entries, progress='100', reason='', operation_key=None):
        """Confirm real totals once. Progress only supplies editable suggested consumption."""
        minutes = integer(minutes, 'Tempo real confirmado')
        progress = number(progress, 'Progresso', places=2)
        if progress>100: raise ValueError('Progresso deve estar entre 0 e 100%.')
        operation_key = operation_key or str(uuid4())
        with transaction(self.db):
            op=self.get(identifier)
            if op['state']!='printing': raise ValueError('Inicie a impressão antes de confirmar; esta tentativa pode já estar consolidada.')
            self.validate_sources(identifier)
            planned=json.loads(op['planned']); expected=self.entries(identifier)
            if len(entries)!=len(expected): raise ValueError('Confirme cada modelo do lote.')
            if progress<100: required(reason,'Motivo da interrupção/falha')
            machine=cents(str(money(sum(Decimal(planned['printer'][k]) for k in ('investment_hour_cents','energy_hour_cents','maintenance_hour_cents'))/100*minutes/60)))
            shares=split(machine, planned['weights'])
            actuals=[]; spool_totals={}; produced=[]
            for entry, saved, share in zip(entries,expected,shares):
                if entry['entry_id']!=saved['id']: raise ValueError('Modelo de confirmação incorreto.')
                snap=json.loads(saved['planned'])
                failed=integer(entry.get('failed',0),'Peças perdidas')
                if failed>saved['quantity']: raise ValueError('Perdas excedem a quantidade planejada.')
                if failed: required(reason,'Motivo das perdas')
                consumption=entry['consumptions']
                if set(consumption)!={f['id'] for f in snap['filaments']}: raise ValueError('Confirme todos os carretéis deste modelo.')
                fs=[{**f,'grams':consumption[f['id']]} for f in snap['filaments']]
                cost=calculate(planned['printer'],0,fs,entry.get('auxiliary',snap['auxiliary']),saved['quantity'],actual=True)
                ref=cents(cost['total_cost'])+share
                acquired=cost['acquisition_production_cost']
                existing=cents(acquired)+share if acquired is not None else ref
                loss_percent=number(entry.get('loss_percent',str(Decimal(failed)*100/saved['quantity'])),'Percentual de perda')
                if loss_percent>100: raise ValueError('Percentual de perda inválido.')
                actuals.append({'entry_id':saved['id'],'quantity':saved['quantity'],'failed':failed,'produced':saved['quantity']-failed,'machine_cents':share,'reference_cents':ref,'existing_cents':existing,'basis':'acquisition' if acquired is not None else 'reference','loss_cents':int((Decimal(existing)*loss_percent/100).quantize(Decimal('1'),rounding=ROUND_HALF_UP)),'loss_percent':str(loss_percent),'cost':cost})
                produced.append(saved['quantity']-failed)
                for f in cost['filaments']:
                    spool_totals[f['id']]=spool_totals.get(f['id'],0)+grams_mg(f['grams'])
            attempt=self.db.execute('INSERT INTO production_attempts(op_id,created_at,minutes,progress,reason,actual,operation_key) VALUES(?,?,?,?,?,?,?)',(identifier,now(),minutes,str(progress),reason,json.dumps(actuals),operation_key)).lastrowid
            for spool_id, consumed in spool_totals.items():
                spool=self.catalog.get('filaments',spool_id); before=spool['remaining_mg']
                if consumed and (spool['archived'] or spool['state']=='finished'): raise ValueError('Carretel indisponível para confirmar consumo.')
                remaining=None if before is None else before-consumed
                if remaining is not None and remaining<0: raise ValueError('Saldo insuficiente; nenhum consumo foi consolidado.')
                self.db.execute('UPDATE filaments SET remaining_mg=?,state=? WHERE id=?',(remaining,'finished' if remaining==0 else 'open' if consumed else spool['state'],spool_id))
                record(self.storage,'consumption','filament',spool_id,-consumed,before,remaining,f'{op["code"]}, tentativa {attempt}',f'op:{attempt}:filament:{spool_id}')
            before=self.catalog.get('printers',op['printer_id'])['accumulated_minutes']
            self.db.execute('UPDATE printers SET accumulated_minutes=accumulated_minutes+? WHERE id=?',(minutes,op['printer_id']))
            self.storage.audit('produção:tempo confirmado',f'printers:{op["printer_id"]}',before,before+minutes,f'{op["code"]}, tentativa {attempt}')
            for saved,actual in zip(expected,actuals):
                qty=actual['produced']
                if qty:
                    receipt,pieces=self.inventory.receive(saved['variant_id'],qty,f'{op["code"]}, tentativa {attempt}','quarantine','Inspeção formal pendente',f'op:{attempt}:entry:{saved["id"]}',total_cost=str(Decimal(actual['existing_cents'])/100))
                    self.db.execute('UPDATE receipts SET cost_basis=?,cost_snapshot=? WHERE id=?',(actual['basis'],json.dumps(actual),receipt))
                    for piece in pieces: self.db.execute('INSERT INTO production_pieces VALUES(?,?,?)',(piece,saved['id'],attempt))
                if actual['failed']:
                    self.problem(identifier,saved['product_id'],'failure',reason,op['responsible'])
            self.db.execute('UPDATE production_orders SET state=?,started_at=NULL WHERE id=?',('inspection' if sum(produced) else 'waiting',identifier))
            self.storage.audit('produção:consumo confirmado',f'OP:{identifier}',None,{'attempt':attempt,'actual':actuals,'minutes':minutes,'progress':str(progress)},reason)
        return attempt

    def suggested_consumption(self, identifier, progress):
        percent=number(progress,'Progresso')
        if percent>100: raise ValueError('Progresso inválido.')
        return [{f['id']:str((Decimal(f['grams'])*percent/100).quantize(Decimal('.001'))) for f in json.loads(e['planned'])['filaments']} for e in self.entries(identifier)]

    def pieces(self, identifier):
        return [dict(r) for r in self.db.execute('SELECT p.*,e.category,e.variant_id,e.product_id,i.result AS inspection_result FROM pieces p JOIN production_pieces pp ON pp.piece_id=p.id JOIN (SELECT e.*,v.product_id FROM production_entries e JOIN variants v ON v.id=e.variant_id) e ON e.id=pp.entry_id LEFT JOIN inspections i ON i.id=(SELECT MAX(id) FROM inspections WHERE piece_id=p.id AND valid=1) WHERE e.op_id=? ORDER BY p.id',(identifier,))]

    def validate_sources(self, identifier):
        for e in self.entries(identifier):
            snap=json.loads(e['planned'])
            if self.products.active_product(e['product_id'])!=snap['product'] or self.products.active_variant(e['variant_id'])!=snap['variant']:
                raise ValueError('Produto ou variante alterado após a criação. Registre a revalidação da OP antes de liberar as peças.')
            self.products.media_path(e['project_id'],'project')

    def inspect(self, identifier, piece_id, result, checklist, photos, responsible, notes=''):
        if result not in ('approved','notes','rejected'): raise ValueError('Resultado inválido.')
        required(responsible,'Responsável pela inspeção')
        if result in ('notes','rejected'): required(notes,'Observações da inspeção')
        self.validate_sources(identifier)
        op=self.get(identifier); candidates={p['id']:p for p in self.pieces(identifier)}
        if piece_id not in candidates: raise ValueError('Peça não pertence à ordem.')
        piece=candidates[piece_id]
        if piece['state'] not in ('quarantine','available','personal'): raise ValueError('Libere a reserva antes de reinspecionar; peças baixadas/descartadas não podem ser alteradas.')
        if set(checklist)!=set(CHECKS[piece['category']]): raise ValueError('Preencha todo o checklist da categoria.')
        for value in checklist.values():
            if value.get('result') not in ('ok','fail','na'): raise ValueError('Checklist incompleto.')
            if value['result'] in ('na','fail'): required(value.get('reason'),'Justificativa do item não aplicável ou reprovado')
            if value['result']=='fail' and result!='rejected': raise ValueError('Checklist reprovado impede a aprovação.')
        if set(photos)!=set(VIEWS): raise ValueError('Exatamente três vistas são obrigatórias: frente, lateral/verso e detalhe.')
        created=[]; hashes=set()
        try:
            with transaction(self.db):
                inspection=self.db.execute('INSERT INTO inspections(piece_id,revision,created_at,responsible,result,checklist,notes) VALUES(?,?,?,?,?,?,?)',(piece_id,op['revision'],now(),responsible,result,json.dumps(checklist),notes)).lastrowid
                for view,source in photos.items():
                    source=Path(source)
                    if source.suffix.lower() not in ('.png','.jpg','.jpeg') or not source.is_file(): raise ValueError('Selecione fotos PNG ou JPEG válidas.')
                    reader=QImageReader(str(source))
                    if not reader.canRead() or reader.read().isNull(): raise ValueError('A foto não pode ser decodificada.')
                    target=self.storage.home/'Fotos dos Produtos'/('inspection-'+uuid4().hex+source.suffix.lower())
                    created.append(target); shutil.copyfile(source,target)
                    sha=hashlib.sha256(target.read_bytes()).hexdigest()
                    if sha in hashes: raise ValueError('Utilize três fotos distintas das três vistas da peça.')
                    hashes.add(sha)
                    relative=target.relative_to(self.storage.home).as_posix()
                    self.db.execute('INSERT INTO inspection_photos(inspection_id,view,path,sha256) VALUES(?,?,?,?)',(inspection,view,relative,sha))
                self.db.execute('UPDATE inspections SET valid=0 WHERE piece_id=? AND id<>?',(piece_id,inspection))
                state='quarantine'  # Availability begins only after final cost allocation at completion.
                self.db.execute('UPDATE pieces SET state=?,condition=? WHERE id=?',(state,notes or 'Inspeção formal aprovada',piece_id))
                record(self.storage,'review','piece',piece_id,0,piece['state'],state,notes or 'Inspeção formal',f'inspection:{inspection}')
                self.storage.audit('produção:inspeção',f'pieces:{piece_id}',piece,{'inspection':inspection,'result':result,'checklist':checklist},responsible+': '+notes)
                if result=='rejected': self.problem(identifier,piece['product_id'],'inspection',notes,responsible)
                self.db.execute("UPDATE production_orders SET state='inspection' WHERE id=?",(identifier,))
        except Exception:
            for path in created: path.unlink(missing_ok=True)
            raise
        return inspection

    def complete(self, identifier):
        with transaction(self.db):
            self.validate_sources(identifier)
            op=self.get(identifier); pieces=self.pieces(identifier)
            if op['state']!='inspection' or not pieces: raise ValueError('A ordem deve estar aguardando inspeção e ter peças produzidas.')
            if any(p['inspection_result'] is None for p in pieces): raise ValueError('Inspecione individualmente todas as peças antes de concluir.')
            for p in pieces:
                for row in self.db.execute('SELECT ip.* FROM inspection_photos ip JOIN inspections i ON i.id=ip.inspection_id WHERE i.piece_id=? AND i.valid=1',(p['id'],)):
                    self.photo_path(row['id'])
            if not any(p['inspection_result'] in ('approved','notes') for p in pieces): raise ValueError('Nenhuma peça aprovada. Registre reimpressão antes de concluir a produção.')
            # Absorb failed/rejected attempts into approved units, conserving the
            # existing production cost. Rejection is not a second expenditure.
            for entry in self.entries(identifier):
                if op['cost_consolidated']:
                    continue  # Existing cost and issued units are immutable on a return/reinspection.
                total = sum(a['existing_cents'] for row in self.db.execute('SELECT actual FROM production_attempts WHERE op_id=?',(identifier,)) for a in json.loads(row[0]) if a['entry_id']==entry['id'])
                ids = {r[0] for r in self.db.execute('SELECT piece_id FROM production_pieces WHERE entry_id=?',(entry['id'],))}
                approved = [p for p in pieces if p['id'] in ids and p['inspection_result'] in ('approved','notes')]
                if not approved:
                    # Keep rejected stock cost until a later reprint; no invented good unit.
                    continue
                shares = split(total, [1]*len(approved))
                good_costs = {p['id']:c for p,c in zip(approved,shares)}
                for p in pieces:
                    if p['id'] not in ids: continue
                    cost = good_costs.get(p['id'],0)
                    state = 'available' if p['id'] in good_costs else 'quarantine'
                    self.db.execute('UPDATE pieces SET unit_cost_cents=?,state=? WHERE id=?',(cost,state,p['id']))
                    record(self.storage,'review','piece',p['id'],0,p['state'],state,'Consolidação do custo com perdas incluídas',f'op-complete:{identifier}:{op["revision"]}:{p["id"]}',cost)
            if op['cost_consolidated']:
                for p in pieces:
                    if p['state']=='quarantine' and p['inspection_result'] in ('approved','notes'):
                        self.db.execute("UPDATE pieces SET state='available' WHERE id=?",(p['id'],))
                        record(self.storage,'review','piece',p['id'],0,'quarantine','available','Reinspeção aprovada',f'op-reapprove:{identifier}:{op["revision"]}:{p["id"]}:{uuid4().hex}',p['unit_cost_cents'])
            self.db.execute("UPDATE production_orders SET state='completed',cost_consolidated=1 WHERE id=?",(identifier,))
            self.storage.audit('produção:concluir',f'OP:{identifier}',op,self.get(identifier))
        return self.summary(identifier)

    def summary(self, identifier):
        records=self.db.execute('SELECT id,actual FROM production_attempts WHERE op_id=?',(identifier,)).fetchall()
        attempts=[json.loads(r['actual']) for r in records]
        total=sum(a['existing_cents'] for rows in attempts for a in rows)
        reference=sum(a['reference_cents'] for rows in attempts for a in rows)
        failed=sum(a['failed'] for rows in attempts for a in rows)
        parts=self.pieces(identifier); good=sum(p['inspection_result'] in ('approved','notes') for p in parts)
        rejected=sum(p['inspection_result']=='rejected' for p in parts)
        loss=sum(a['loss_cents'] for rows in attempts for a in rows)
        for attempt,rows in zip(records,attempts):
            for a in rows:
                n=self.db.execute("SELECT count(*) FROM production_pieces pp JOIN inspections i ON i.piece_id=pp.piece_id AND i.valid=1 WHERE pp.entry_id=? AND i.result='rejected' AND pp.attempt_id=?",(a['entry_id'],attempt['id'])).fetchone()[0]
                if a['produced']:
                    loss+=int((Decimal(a['existing_cents']-a['loss_cents'])*n/a['produced']).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
        planned=json.loads(self.get(identifier)['planned'])['reference_cents']
        return {'total_cents':total,'reference_cents':reference,'planned_reference_cents':planned,'reference_delta_cents':reference-planned,'loss_included_cents':loss,'planned':sum(e['quantity'] for e in self.entries(identifier)), 'produced':len(parts),'failed':failed,'rejected':rejected,'good':good,'effective_unit':str(money(Decimal(total)/100/good)) if good else None,'attempts':len(attempts)}

    def reprint(self, identifier, responsible, replacements=None):
        op=self.get(identifier); planned=json.loads(op['planned']); entries=[]
        for e in self.entries(identifier):
            snap=json.loads(e['planned'])
            entries.append({'variant_id':e['variant_id'],'project_id':e['project_id'],'quantity':e['quantity'],'filaments':[((replacements or {}).get(f['id'],f['id']),f['grams']) for f in snap['filaments']], 'auxiliary':snap['auxiliary']})
        return self.create(op['printer_id'],planned['minutes'],entries,responsible,op['parameters'],op['priority'],op['item_id'],planned['weights'],planned['allocation_reason'] or 'Rateio copiado da ordem de origem',identifier)

    def revalidate(self, identifier, parameters, reason):
        required(parameters,'Parâmetros');required(reason,'Justificativa da alteração')
        with transaction(self.db):
            op=self.get(identifier); parts=self.pieces(identifier)
            if op['state']=='printing' or any(p['state'] in ('reserved','issued','discarded') for p in parts): raise ValueError('Alteração bloqueada durante impressão ou com peças reservadas/baixadas/descartadas. Libere as reservas ou crie nova OP.')
            self.db.execute('UPDATE production_orders SET parameters=?,revision=revision+1,state=? WHERE id=?',(parameters,'inspection' if parts else 'waiting',identifier))
            for entry in self.entries(identifier):
                snap=json.loads(entry['planned']); variant=self.products.active_variant(entry['variant_id']); model=self.products.active_product(variant['product_id'])
                snap['product']=model; snap['variant']=variant
                self.db.execute('UPDATE production_entries SET category=?,planned=? WHERE id=?',(model['category'],json.dumps(snap),entry['id']))
            for p in parts:
                self.db.execute('UPDATE inspections SET valid=0 WHERE piece_id=?',(p['id'],))
                self.db.execute("UPDATE pieces SET state='quarantine',condition='Revalidação obrigatória' WHERE id=?",(p['id'],))
                record(self.storage,'review','piece',p['id'],0,p['state'],'quarantine',reason,f'revalidate:{identifier}:{op["revision"]+1}:{p["id"]}')
            self.storage.audit('produção:revalidar',f'OP:{identifier}',op,self.get(identifier),reason)

    def problem(self, identifier, product_id, kind, description, responsible):
        required(description,'Descrição do problema');required(responsible,'Responsável')
        if kind not in ('surface','supports','adhesion','detail','failure','inspection'): raise ValueError('Tipo de problema inválido.')
        if product_id not in {e['product_id'] for e in self.entries(identifier)}: raise ValueError('Produto não pertence à ordem.')
        with transaction(self.db):
            pk=self.db.execute('INSERT INTO production_problems(op_id,product_id,created_at,kind,description,responsible) VALUES(?,?,?,?,?,?)',(identifier,product_id,now(),kind,description,responsible)).lastrowid
            self.storage.audit('produção:problema',f'OP:{identifier}',None,{'product_id':product_id,'problem_id':pk,'kind':kind,'description':description},responsible)
        return pk

    def photo_path(self, photo_id):
        row=self.db.execute('SELECT * FROM inspection_photos WHERE id=?',(photo_id,)).fetchone()
        if not row: raise ValueError('Foto de inspeção não encontrada.')
        root=self.storage.home.resolve();relative=Path(row['path']);path=(root/relative).resolve()
        if relative.is_absolute() or len(relative.parts)!=2 or relative.parts[0]!='Fotos dos Produtos' or not path.is_relative_to(root):
            raise ValueError('Referência de foto inválida.')
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError('Foto de inspeção ausente ou alterada. Restaure backup completo.')
        return path

    def problems(self, product_id=None):
        sql='SELECT p.*,o.code FROM production_problems p JOIN production_orders o ON o.id=p.op_id'
        return [dict(r) for r in self.db.execute(sql+(' WHERE p.product_id=?' if product_id else '')+' ORDER BY p.id DESC',(product_id,) if product_id else ())]

    def verify_release(self, piece_id):
        linked=self.db.execute('SELECT e.op_id FROM production_pieces pp JOIN production_entries e ON e.id=pp.entry_id WHERE pp.piece_id=?',(piece_id,)).fetchone()
        if not linked: return  # Documented pre-existing stock keeps Phase 3 provenance.
        self.validate_sources(linked[0])
        if self.get(linked[0])['state']!='completed': raise ValueError('Conclua a OP antes de reservar ou entregar as peças.')
        inspection=self.db.execute('SELECT * FROM inspections WHERE piece_id=? AND valid=1 ORDER BY id DESC LIMIT 1',(piece_id,)).fetchone()
        if not inspection or inspection['result'] not in ('approved','notes'): raise ValueError('Peça exige reinspeção formal antes da entrega.')
        photos=self.db.execute('SELECT id FROM inspection_photos WHERE inspection_id=?',(inspection['id'],)).fetchall()
        if len(photos)!=3: raise ValueError('Evidências fotográficas incompletas.')
        for photo in photos:self.photo_path(photo['id'])
