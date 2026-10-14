"""Financial projections from immutable source events; consumption never pays cash."""
from contextlib import contextmanager
from datetime import date
from decimal import Decimal,ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import shutil
from uuid import uuid4
from PySide6.QtGui import QImageReader
from PySide6.QtPdf import QPdfDocument
from .catalog import Catalog,required,optional_date
from .inventory import Inventory
from .pricing import cents,integer,grams_mg,money
from .journal import record
from .storage import now
from .transactions import transaction

TREATMENTS={'inventory':'Compra para estoque','allocated':'Pagamento de recurso apropriado na produção','capital':'Investimento em equipamento','operating':'Despesa operacional adicional'}
ENTRY_KINDS={'capital_in':'Aporte do proprietário','capital_out':'Retirada do proprietário','opening_in':'Saldo inicial positivo','opening_out':'Saldo inicial negativo'}
STATUS={'pending':'Pendente','partial':'Parcial','paid':'Quitado','overdue':'Atrasado','cancelled':'Cancelado'}


def effective_date(value=None):
    value=optional_date(value or date.today().isoformat())
    if value>date.today().isoformat():raise ValueError('Data efetiva não pode ser futura.')
    return value


def period(start=None,end=None):
    start=optional_date(start) or '0001-01-01';end=optional_date(end) or date.today().isoformat()
    if start>end:raise ValueError('Data inicial deve ser anterior ou igual à final.')
    return start,end


class Finance:
    def __init__(self,storage):self.storage,self.db=storage,storage.db

    @contextmanager
    def event(self):
        files=[]
        try:
            with transaction(self.db):yield files
        except BaseException:
            for path in files:path.unlink(missing_ok=True)
            raise

    def categories(self,archived=False):
        return [dict(r) for r in self.db.execute('SELECT * FROM expense_categories WHERE archived=? ORDER BY id',(int(archived),))]

    def get(self,table,identifier):
        if table not in ('expense_categories','payables','payable_installments','payable_payments','finance_entries','finance_proofs'):raise ValueError('Registro financeiro inválido.')
        row=self.db.execute(f'SELECT * FROM {table} WHERE id=?',(identifier,)).fetchone()
        if not row:raise ValueError('Registro financeiro não encontrado.')
        return dict(row)

    def save_category(self,name,treatment,identifier=None):
        name=required(name,'Categoria')
        if treatment not in TREATMENTS:raise ValueError('Tratamento financeiro inválido.')
        with transaction(self.db):
            before=self.get('expense_categories',identifier) if identifier else None
            if before and before['archived']:raise ValueError('Restaure a categoria antes de editar.')
            if identifier:self.db.execute('UPDATE expense_categories SET name=?,treatment=? WHERE id=?',(name,treatment,identifier))
            else:identifier=self.db.execute('INSERT INTO expense_categories(name,treatment) VALUES(?,?)',(name,treatment)).lastrowid
            self.storage.audit('financeiro:categoria',f'category:{identifier}',before,self.get('expense_categories',identifier),'Contas existentes mantêm classificação histórica')
        return identifier

    def archive_category(self,identifier,archived,reason):
        required(reason,'Justificativa')
        with transaction(self.db):
            before=self.get('expense_categories',identifier)
            self.db.execute('UPDATE expense_categories SET archived=? WHERE id=?',(int(archived),identifier))
            self.storage.audit('financeiro:categoria arquivada',f'category:{identifier}',before,self.get('expense_categories',identifier),reason)

    def create_payable(self,description,category_id,amount,supplier='',incurred_on=None,installments=None,count=1,first_due=None,operation_key=None):
        from .sales import Sales
        description=required(description,'Descrição');amount=cents(amount,'Valor da conta')
        if not amount:raise ValueError('Valor da conta deve ser positivo.')
        incurred_on=effective_date(incurred_on)
        with transaction(self.db):
            category=self.get('expense_categories',category_id)
            if category['archived']:raise ValueError('Categoria arquivada não pode ser utilizada.')
            plan=installments if installments is not None else Sales.split_installments(amount,count,optional_date(first_due))
            values=[(cents(i['amount'],'Parcela'),optional_date(i.get('due_on'))) for i in plan]
            if not values or len(values)>120 or any(a<=0 for a,d in values) or sum(a for a,d in values)!=amount:raise ValueError('Parcelas positivas devem somar o valor da conta; máximo de 120 parcelas.')
            identifier=self.db.execute("INSERT INTO payables(description,category_id,category_snapshot,supplier,amount_cents,incurred_on,created_at,state,operation_key) VALUES(?,?,?,?,?,?,?,'active',?)",(description,category_id,json.dumps(category),str(supplier).strip(),amount,incurred_on,now(),operation_key or uuid4().hex)).lastrowid
            for a,d in values:self.db.execute('INSERT INTO payable_installments(payable_id,amount_cents,due_on) VALUES(?,?,?)',(identifier,a,d))
            self.storage.audit('financeiro:conta a pagar',f'payable:{identifier}',None,{'bill':self.get('payables',identifier),'installments':values})
        return identifier

    def payables(self,as_of=None):
        end=optional_date(as_of) or date.today().isoformat();rows=[]
        for r in self.db.execute('SELECT i.*,p.description,p.supplier,p.category_snapshot,p.state,p.incurred_on FROM payable_installments i JOIN payables p ON p.id=i.payable_id WHERE p.incurred_on<=? ORDER BY COALESCE(i.due_on,\'9999-12-31\'),i.id',(end,)):
            row=dict(r);paid=self.db.execute('SELECT COALESCE(SUM(amount_cents),0) FROM payable_payments WHERE installment_id=? AND paid_on<=?',(row['id'],end)).fetchone()[0]
            cancellation=self.db.execute("SELECT created_at FROM audit WHERE operation='financeiro:conta cancelada' AND record=? ORDER BY id LIMIT 1",(f'payable:{row["payable_id"]}',)).fetchone()
            cancelled=row['state']=='cancelled' and cancellation and cancellation[0][:10]<=end
            row['paid_cents']=paid;row['balance_cents']=0 if cancelled else row['amount_cents']-paid
            row['status']='cancelled' if cancelled else 'paid' if not row['balance_cents'] else 'overdue' if row['due_on'] and row['due_on']<end else 'partial' if paid else 'pending'
            row['category']=json.loads(row['category_snapshot'])['name'];rows.append(row)
        return rows

    def pay(self,installment_id,amount,method='pix',fee='0',paid_on=None,proof=None,operation_key=None):
        from .sales import PAYMENT_METHODS
        amount=cents(amount,'Pagamento');fee=cents(fee,'Taxa');paid_on=effective_date(paid_on)
        if amount<=0 or method not in PAYMENT_METHODS or method=='customer_credit':raise ValueError('Pagamento positivo e meio de pagamento efetivo são obrigatórios.')
        with self.event() as files:
            installment=self.get('payable_installments',installment_id);bill=self.get('payables',installment['payable_id'])
            if bill['state']!='active':raise ValueError('Conta cancelada não recebe pagamentos.')
            if paid_on<bill['incurred_on']:raise ValueError('Pagamento não pode preceder a obrigação.')
            paid=self.db.execute('SELECT COALESCE(SUM(amount_cents),0) FROM payable_payments WHERE installment_id=?',(installment_id,)).fetchone()[0]
            if paid+amount>installment['amount_cents']:raise ValueError('Pagamento excede o saldo da parcela.')
            identifier=self.db.execute('INSERT INTO payable_payments(installment_id,amount_cents,fee_cents,paid_on,method,created_at,operation_key) VALUES(?,?,?,?,?,?,?)',(installment_id,amount,fee,paid_on,method,now(),operation_key or uuid4().hex)).lastrowid
            if proof:self.import_proof(proof,files,payment_id=identifier)
            self.storage.audit('financeiro:pagamento efetivo',f'payable_payment:{identifier}',None,self.get('payable_payments',identifier))
        return identifier

    def cancel_payable(self,identifier,reason):
        required(reason,'Justificativa')
        with transaction(self.db):
            before=self.get('payables',identifier)
            if before['state']!='active':raise ValueError('Conta já cancelada.')
            if self.db.execute('SELECT 1 FROM payable_payments pp JOIN payable_installments i ON i.id=pp.installment_id WHERE i.payable_id=?',(identifier,)).fetchone():raise ValueError('Conta com pagamento preservado não pode ser apagada/cancelada por este fluxo.')
            if self.db.execute('SELECT 1 FROM finance_purchases WHERE payable_id=?',(identifier,)).fetchone():raise ValueError('Compra recebida em estoque não pode ser cancelada sem tratamento físico do material.')
            self.db.execute("UPDATE payables SET state='cancelled',reason=? WHERE id=?",(reason,identifier))
            self.storage.audit('financeiro:conta cancelada',f'payable:{identifier}',before,self.get('payables',identifier),reason)

    def entry(self,kind,amount,description,responsible,occurred_on=None,proof=None,operation_key=None,reversal_of=None):
        if kind not in ENTRY_KINDS:raise ValueError('Tipo de movimentação do proprietário inválido.')
        amount=cents(amount);description=required(description,'Descrição/justificativa');responsible=required(responsible,'Responsável');day=effective_date(occurred_on)
        if not amount:raise ValueError('Valor deve ser positivo.')
        with self.event() as files:
            if reversal_of:
                original=self.get('finance_entries',reversal_of)
                opposite={'capital_in':'capital_out','capital_out':'capital_in','opening_in':'opening_out','opening_out':'opening_in'}
                if kind!=opposite[original['kind']] or amount!=original['amount_cents'] or day<original['occurred_on']:raise ValueError('Estorno deve inverter o valor original, em data igual ou posterior.')
            identifier=self.db.execute('INSERT INTO finance_entries(kind,amount_cents,occurred_on,description,responsible,created_at,reversal_of,operation_key) VALUES(?,?,?,?,?,?,?,?)',(kind,amount,day,description,responsible,now(),reversal_of,operation_key or uuid4().hex)).lastrowid
            if proof:self.import_proof(proof,files,entry_id=identifier)
            self.storage.audit('financeiro:estorno' if reversal_of else 'financeiro:movimento proprietário',f'finance_entry:{identifier}',None,self.get('finance_entries',identifier),description)
        return identifier

    def reverse_entry(self,identifier,reason,responsible,occurred_on=None):
        original=self.get('finance_entries',identifier)
        opposite={'capital_in':'capital_out','capital_out':'capital_in','opening_in':'opening_out','opening_out':'opening_in'}
        return self.entry(opposite[original['kind']],str(Decimal(original['amount_cents'])/100),required(reason,'Motivo do estorno'),responsible,occurred_on,reversal_of=identifier)

    def import_proof(self,source,files,payment_id=None,entry_id=None):
        source=Path(source)
        if not source.is_file():raise ValueError('Comprovante não encontrado.')
        suffix=source.suffix.lower()
        if suffix in ('.png','.jpg','.jpeg'):
            reader=QImageReader(str(source))
            if not reader.canRead() or reader.read().isNull():raise ValueError('Imagem de comprovante inválida.')
        elif suffix=='.pdf':
            doc=QPdfDocument(None)
            if doc.load(str(source))!=QPdfDocument.Error.None_ or doc.pageCount()<1:raise ValueError('PDF de comprovante inválido.')
            doc.close()
        else:raise ValueError('Comprovante deve ser PDF, PNG ou JPEG.')
        target=self.storage.home/'Pedidos e Comprovantes'/('finance-'+uuid4().hex+suffix);files.append(target);shutil.copyfile(source,target)
        identifier=self.db.execute('INSERT INTO finance_proofs(payment_id,entry_id,path,sha256,original_name,created_at) VALUES(?,?,?,?,?,?)',(payment_id,entry_id,target.relative_to(self.storage.home).as_posix(),hashlib.sha256(target.read_bytes()).hexdigest(),source.name,now())).lastrowid
        return identifier

    def proof_path(self,identifier):
        from .sales_documents import owned_path
        row=self.get('finance_proofs',identifier)
        return owned_path(self.storage,row['path'],row['sha256'])

    def purchase_filament(self,data,category_id=1,installments=None,count=1,first_due=None,paid=False,method='pix',proof=None,operation_key=None):
        """Create one spool, obligation and optional cash payment in one transaction."""
        quantity=grams_mg(data.get('initial_grams',''),'Peso comprado')
        if not quantity or data.get('remaining_grams') not in (None,'',data.get('initial_grams')):raise ValueError('Compra nova deve entrar com peso integral conhecido.')
        data={**data,'remaining_grams':data['initial_grams'],'state':'new'}
        with self.event() as files:
            if self.get('expense_categories',category_id)['treatment']!='inventory':raise ValueError('Selecione categoria de compra para estoque.')
            spool=Catalog(self.storage).save_filament(data)
            bill=self.create_payable('Compra de filamento: '+required(data.get('name'),'Nome'),category_id,data.get('purchase','0'),data.get('supplier',''),data.get('purchased_on'),installments,count,first_due,operation_key)
            self.db.execute('INSERT INTO finance_purchases(payable_id,filament_id,quantity_milli,operation_key) VALUES(?,?,?,?)',(bill,spool,quantity,operation_key or uuid4().hex))
            if paid:
                for i in self.db.execute('SELECT * FROM payable_installments WHERE payable_id=?',(bill,)).fetchall():
                    payment=self.pay(i['id'],str(Decimal(i['amount_cents'])/100),method,paid_on=data.get('purchased_on'))
                    if proof and i['id']==self.db.execute('SELECT MIN(id) FROM payable_installments WHERE payable_id=?',(bill,)).fetchone()[0]:self.import_proof(proof,files,payment_id=payment)
            self.storage.audit('financeiro:compra integrada',f'purchase:{bill}',None,{'filament_id':spool,'quantity_milli':quantity,'payable_id':bill})
        return bill,spool

    def purchase_material(self,material_id,quantity,amount,supplier='',count=1,first_due=None,paid=False,method='pix',operation_key=None,category_id=2):
        quantity_milli=grams_mg(quantity,'Quantidade comprada')
        if quantity_milli<=0:raise ValueError('Quantidade comprada deve ser positiva.')
        with transaction(self.db):
            material=Inventory(self.storage).get('materials',material_id)
            if material['archived']:raise ValueError('Material arquivado não aceita compra.')
            category=self.get('expense_categories',category_id)
            if category['archived'] or category['treatment']!='inventory':raise ValueError('Selecione uma categoria ativa de compra para estoque.')
            bill=self.create_payable('Compra: '+material['name'],category['id'],amount,supplier,count=count,first_due=first_due,operation_key=operation_key)
            before=material['balance_milli'];after=before+quantity_milli
            self.db.execute('UPDATE materials SET balance_milli=? WHERE id=?',(after,material_id))
            self.db.execute('INSERT INTO finance_purchases(payable_id,material_id,quantity_milli,operation_key) VALUES(?,?,?,?)',(bill,material_id,quantity_milli,operation_key or uuid4().hex))
            record(self.storage,'purchase','material',material_id,quantity_milli,before,after,'Compra financeira recebida',f'purchase:{bill}',cents(amount))
            if paid:
                for i in self.db.execute('SELECT * FROM payable_installments WHERE payable_id=?',(bill,)).fetchall():self.pay(i['id'],str(Decimal(i['amount_cents'])/100),method)
            self.storage.audit('financeiro:compra integrada',f'purchase:{bill}',None,{'material_id':material_id,'quantity_milli':quantity_milli,'payable_id':bill})
        return bill

    def link_existing_purchase(self,payable_id,filament_id):
        """Identify an existing catalog purchase; never add its stock twice."""
        with transaction(self.db):
            bill=self.get('payables',payable_id);spool=Catalog(self.storage).get('filaments',filament_id)
            if bill['state']!='active' or json.loads(bill['category_snapshot'])['treatment']!='inventory':raise ValueError('Conta deve ser uma compra de estoque ativa.')
            if bill['amount_cents']!=spool['purchase_cents'] or spool['initial_mg'] is None:raise ValueError('Valor/peso da compra deve corresponder ao carretel existente.')
            self.db.execute('INSERT INTO finance_purchases(payable_id,filament_id,quantity_milli,operation_key) VALUES(?,?,?,?)',(payable_id,filament_id,spool['initial_mg'],uuid4().hex))
            self.storage.audit('financeiro:compra existente vinculada',f'purchase:{payable_id}',None,{'filament_id':filament_id},'Saldo preservado; nenhuma entrada física adicional')

    def capture_costs(self):
        """Capture historical issue amounts, including records before schema 6."""
        with transaction(self.db):
            rows=self.db.execute("SELECT m.*,i.id AS item_id,i.snapshot AS item_snapshot,i.description,i.order_id,p.variant_id,r.calculation_id FROM stock_movements m JOIN pieces p ON p.id=m.piece_id JOIN receipts r ON r.id=p.receipt_id JOIN order_items i ON m.operation_key='issue:'||i.reservation_id||':'||m.piece_id WHERE m.kind='issue' AND NOT EXISTS(SELECT 1 FROM financial_costs c WHERE c.movement_id=m.id)").fetchall()
            for r in rows:
                prod=self.db.execute('SELECT o.printer_id FROM production_pieces pp JOIN production_entries e ON e.id=pp.entry_id JOIN production_orders o ON o.id=e.op_id WHERE pp.piece_id=?',(r['piece_id'],)).fetchone()
                calc=self.db.execute('SELECT printer_id FROM calculations WHERE id=?',(r['calculation_id'],)).fetchone() if r['calculation_id'] else None
                printer=prod[0] if prod else calc[0] if calc else None
                product=self.db.execute('SELECT product_id FROM variants WHERE id=?',(r['variant_id'],)).fetchone()[0]
                snapshot={'commercial':json.loads(r['item_snapshot']),'description':r['description'],'cost_basis':'existing_piece','printer_id':printer}
                self.db.execute('INSERT INTO financial_costs(movement_id,item_id,piece_id,printer_id,product_id,cost_cents,occurred_on,snapshot) VALUES(?,?,?,?,?,?,?,?)',(r['id'],r['item_id'],r['piece_id'],printer,product,r['cost_cents'] or 0,r['created_at'][:10],json.dumps(snapshot,ensure_ascii=False)))
                self.storage.audit('financeiro:CPV capturado',f'movement:{r["id"]}',None,snapshot,'Custo histórico da baixa; nenhum consumo ou caixa adicional')
            for r in self.db.execute('SELECT r.*,c.id AS cost_id,c.cost_cents FROM order_returns r JOIN financial_costs c ON c.piece_id=r.piece_id JOIN order_items i ON i.id=c.item_id AND i.order_id=r.order_id WHERE NOT EXISTS(SELECT 1 FROM financial_returns f WHERE f.return_id=r.id)').fetchall():
                self.db.execute('INSERT INTO financial_returns VALUES(?,?,?,?)',(r['id'],r['cost_id'],r['cost_cents'],r['created_at'][:10]))

    def cash_events(self,start=None,end=None):
        start,end=period(start,end);rows=[]
        def add(day,kind,source,description,amount,order_id=None,item_id=None,fee=0,treatment='',method=''):
            if start<=day<=end:rows.append({'date':day,'kind':kind,'source':source,'description':description,'amount_cents':amount,'order_id':order_id,'item_id':item_id,'fee_cents':fee,'treatment':treatment,'method':method})
        for r in self.db.execute("SELECT p.*,o.code FROM payments p JOIN orders o ON o.id=p.order_id WHERE p.kind='cash'"):
            add(r['paid_on'],'sale_payment',f'payment:{r["id"]}',r['code'],r['amount_cents'],r['order_id'],method=r['method'])
            if r['fee_cents']:add(r['paid_on'],'sale_fee',f'payment-fee:{r["id"]}',r['code']+' • taxa',-r['fee_cents'],r['order_id'],method=r['method'])
        for r in self.db.execute('SELECT r.*,c.order_id FROM refunds r JOIN cancellations c ON c.id=r.cancellation_id'):add(r['paid_on'],'refund',f'refund:{r["id"]}',r['reason'],-r['amount_cents'],r['order_id'],method=r['method'])
        for r in self.db.execute('SELECT pp.*,p.description,p.category_snapshot FROM payable_payments pp JOIN payable_installments i ON i.id=pp.installment_id JOIN payables p ON p.id=i.payable_id'):
            category=json.loads(r['category_snapshot'])
            add(r['paid_on'],'payable_payment',f'payable-payment:{r["id"]}',r['description'],-r['amount_cents'],treatment=category['treatment'],method=r['method'])
            if r['fee_cents']:add(r['paid_on'],'payable_fee',f'payable-fee:{r["id"]}',r['description']+' • taxa',-r['fee_cents'],treatment='operating',method=r['method'])
        for r in self.db.execute('SELECT * FROM finance_entries'):add(r['occurred_on'],r['kind'],f'entry:{r["id"]}',r['description'],r['amount_cents']*(1 if r['kind'].endswith('_in') else -1))
        return sorted(rows,key=lambda r:(r['date'],r['source']))

    def receivables(self,as_of=None):
        end=optional_date(as_of) or date.today().isoformat();rows=[]
        for r in self.db.execute('SELECT i.*,o.client_id,o.code,o.created_at,c.created_at AS cancelled_at FROM installments i JOIN orders o ON o.id=i.order_id LEFT JOIN cancellations c ON c.order_id=o.id WHERE substr(o.created_at,1,10)<=?',(end,)):
            row=dict(r);paid=self.db.execute('SELECT COALESCE(SUM(a.amount_cents),0) FROM installment_allocations a JOIN payments p ON p.id=a.payment_id WHERE a.installment_id=? AND p.paid_on<=?',(row['id'],end)).fetchone()[0]
            cancelled=row['cancelled_at'] and row['cancelled_at'][:10]<=end
            row['paid_cents']=paid;row['balance_cents']=0 if cancelled else row['amount_cents']-paid
            row['status']='cancelled' if cancelled else 'paid' if not row['balance_cents'] else 'overdue' if row['due_on'] and row['due_on']<end else 'partial' if paid else 'pending';rows.append(row)
        return rows

    def production_loss_events(self,start,end,product_id=None,printer_id=None,eligible_orders=None):
        events=[]
        for op in self.db.execute('SELECT * FROM production_orders'):
            if printer_id is not None and op['printer_id']!=printer_id:continue
            item=self.db.execute('SELECT order_id FROM order_items WHERE id=?',(op['item_id'],)).fetchone() if op['item_id'] else None
            if eligible_orders is not None and (not item or item[0] not in eligible_orders):continue
            first=self.db.execute("SELECT created_at FROM audit WHERE operation='produção:concluir' AND record=? ORDER BY id LIMIT 1",(f'OP:{op["id"]}',)).fetchone()
            completion=first[0] if first else None
            recipe=self.db.execute('SELECT 1 FROM recipe_orders WHERE op_id=?',(op['id'],)).fetchone()
            if recipe:
                event=self.db.execute('SELECT completed_at FROM production_completions WHERE op_id=?',(op['id'],)).fetchone()
                if not event or event[0][:10]>end:continue
                completion=event[0]
            entries={r['id']:r['product_id'] for r in self.db.execute('SELECT e.id,v.product_id FROM production_entries e JOIN variants v ON v.id=e.variant_id WHERE e.op_id=?',(op['id'],))}
            absorbed={}
            for attempt in self.db.execute('SELECT * FROM production_attempts WHERE op_id=? AND substr(created_at,1,10)<=?',(op['id'],end)):
                for actual in json.loads(attempt['actual']):
                    entry=actual['entry_id'];product=entries[entry]
                    if product_id is not None and product!=product_id:continue
                    loss=actual['loss_cents']
                    recognition=completion[:10] if recipe else attempt['created_at'][:10]
                    if loss and start<=recognition<=end:
                        events.append({'date':recognition,'op':op['code'],'attempt_id':attempt['id'],'entry_id':entry,'product_id':product,'printer_id':op['printer_id'],'kind':'loss','amount_cents':loss,'cash_cents':0})
                    if loss and completion and attempt['created_at']<=completion:
                        approved=self.db.execute("SELECT 1 FROM production_pieces pp JOIN inspections i ON i.id=(SELECT MAX(ii.id) FROM inspections ii WHERE ii.piece_id=pp.piece_id AND ii.created_at<=?) WHERE pp.entry_id=? AND i.result IN('approved','notes') LIMIT 1",(completion,entry)).fetchone()
                        # Approved units absorb all attempts of their model. If a
                        # model has only rejects, only attempts with physical
                        # survivors remain in their frozen quarantined cost.
                        if approved or actual['produced']>0:absorbed[entry]=absorbed.get(entry,0)+loss
            if completion and start<=completion[:10]<=end:
                for entry,amount in absorbed.items():
                    events.append({'date':completion[:10],'op':op['code'],'attempt_id':None,'entry_id':entry,'product_id':entries[entry],'printer_id':op['printer_id'],'kind':'absorption','amount_cents':-amount,'cash_cents':0})
        return events

    def report(self,start=None,end=None,client_id=None,product_id=None,printer_id=None,status=None):
        """Date-filtered events and balances as of end, with explicit cost pending."""
        from .production import split
        start,end=period(start,end)
        if status is not None and status not in STATUS:raise ValueError('Situação financeira inválida.')
        self.capture_costs();receivables=self.receivables(end);sale_rows=[];selected_orders=set();eligible_orders=set()
        full_groups={}
        costs=[dict(r) for r in self.db.execute('SELECT * FROM financial_costs WHERE occurred_on<=?',(end,))]
        returns=[dict(r) for r in self.db.execute('SELECT * FROM financial_returns WHERE occurred_on<=?',(end,))]
        for item in self.db.execute('SELECT i.*,o.client_id,o.code,o.created_at,c.created_at AS cancelled_at FROM order_items i JOIN orders o ON o.id=i.order_id LEFT JOIN cancellations c ON c.order_id=o.id WHERE substr(o.created_at,1,10)<=?',(end,)):
            if client_id is not None and item['client_id']!=client_id:continue
            obligations=[r for r in receivables if r['order_id']==item['order_id']]
            finance_status='cancelled' if item['cancelled_at'] and item['cancelled_at'][:10]<=end else 'paid' if sum(r['balance_cents'] for r in obligations)==0 else 'overdue' if any(r['status']=='overdue' for r in obligations) else 'partial' if any(r['paid_cents'] for r in obligations) else 'pending'
            if status is not None and finance_status!=status:continue
            snap=json.loads(item['snapshot']);model=snap.get('product');variant=snap.get('variant')
            if not model:
                mapping=self.db.execute('SELECT v.product_id FROM order_fulfillment f JOIN variants v ON v.id=f.variant_id WHERE f.item_id=?',(item['id'],)).fetchone()
                model_id=mapping[0] if mapping else None
            else:model_id=model['id']
            if product_id is not None and model_id!=product_id:continue
            eligible_orders.add(item['order_id'])
            item_costs=[c for c in costs if c['item_id']==item['id']]
            groups={}
            for c in item_costs:groups[c['printer_id']]=groups.get(c['printer_id'],0)+1
            missing=max(0,item['quantity']-len(item_costs))
            if missing:groups[None]=groups.get(None,0)+missing
            if not groups:groups[None]=item['quantity']
            full_groups[item['id']]=groups
            reference=(variant or {}).get('suggested_price_cents')
            if reference is None:reference=(model or {}).get('suggested_price_cents')
            discount=max(0,(reference or item['unit_price_cents'])-item['unit_price_cents'])
            for printer,qty in groups.items():
                if printer_id is not None and printer!=printer_id:continue
                selected_orders.add(item['order_id'])
                relevant=[c for c in item_costs if c['printer_id']==printer]
                cpv=sum(c['cost_cents'] for c in relevant if start<=c['occurred_on']<=end)-sum(r['cost_cents'] for r in returns if start<=r['occurred_on']<=end and r['cost_id'] in {c['id'] for c in relevant})
                created=item['created_at'][:10];cancelled=item['cancelled_at'][:10] if item['cancelled_at'] else None
                sign=int(start<=created<=end)-int(cancelled is not None and start<=cancelled<=end)
                sale_rows.append({'order_id':item['order_id'],'order':item['code'],'item_id':item['id'],'client_id':item['client_id'],'product_id':model_id,'printer_id':printer,'description':item['description'],'approved_on':created,'cancelled_on':cancelled,'status':finance_status,'quantity':qty*sign,'sales_cents':item['unit_price_cents']*qty*sign,'discount_cents':discount*qty*sign,'cost_cents':cpv,'pending_quantity':missing if printer is None and finance_status!='cancelled' else 0,'priced_quantity':qty})
        scoped=any(v is not None for v in (client_id,product_id,printer_id,status))
        selected_item_ids={r['item_id'] for r in sale_rows}
        # Cash is a consolidated ledger. Scoped commercial reports identify it
        # explicitly, because purchases/aportes have no client/product ownership.
        cash=self.cash_events(start,end)
        incoming=sum(r['amount_cents'] for r in cash if r['kind']=='sale_payment')
        sale_fees=-sum(r['amount_cents'] for r in cash if r['kind']=='sale_fee')
        refunds=-sum(r['amount_cents'] for r in cash if r['kind']=='refund')
        expenses=-sum(r['amount_cents'] for r in cash if r['kind'] in ('payable_payment','payable_fee'))+sale_fees
        operating=-sum(r['amount_cents'] for r in cash if r['kind']=='payable_fee' or r['kind']=='payable_payment' and r['treatment']=='operating')
        def portion(amount,item_id):
            groups=full_groups[item_id];keys=sorted(groups,key=lambda k:-1 if k is None else k)
            shares=split(amount,[groups[k] for k in keys])
            return sum(share for key,share in zip(keys,shares) if printer_id is None or key==printer_id)
        scoped_fees=0;scoped_incoming=0
        for payment in self.db.execute('SELECT * FROM payments WHERE paid_on BETWEEN ? AND ?',(start,end)):
            if not scoped:scoped_fees+=payment['fee_cents'];continue
            allocations=self.db.execute('SELECT * FROM payment_allocations WHERE payment_id=? ORDER BY id',(payment['id'],)).fetchall()
            shares=split(payment['fee_cents'],[r['amount_cents'] for r in allocations]) if allocations else []
            for allocation,share in zip(allocations,shares):
                if allocation['item_id'] in selected_item_ids:
                    scoped_fees+=portion(share,allocation['item_id'])
                    if payment['kind']=='cash':scoped_incoming+=portion(allocation['amount_cents'],allocation['item_id'])
                elif allocation['item_id'] is None and payment['order_id'] in selected_orders and product_id is None and printer_id is None:
                    scoped_fees+=share
                    if payment['kind']=='cash':scoped_incoming+=allocation['amount_cents']
        if scoped:
            incoming=scoped_incoming
            sale_fees=scoped_fees
            refunds=sum(r['amount_cents'] for r in self.db.execute('SELECT r.*,c.order_id FROM refunds r JOIN cancellations c ON c.id=r.cancellation_id WHERE r.paid_on BETWEEN ? AND ?',(start,end)) if r['order_id'] in selected_orders) if product_id is None and printer_id is None else 0
        freight=0;retained=0
        for o in self.db.execute('SELECT o.*,c.created_at AS cancelled_at,c.retained_cents FROM orders o LEFT JOIN cancellations c ON c.order_id=o.id'):
            if o['id'] not in selected_orders:continue
            if product_id is None and printer_id is None:
                freight+=o['freight_cents']*(int(start<=o['created_at'][:10]<=end)-int(o['cancelled_at'] is not None and start<=o['cancelled_at'][:10]<=end))
                if o['cancelled_at'] and start<=o['cancelled_at'][:10]<=end:retained+=o['retained_cents']
        gross=sum(r['sales_cents'] for r in sale_rows)+freight
        cpv=sum(r['cost_cents'] for r in sale_rows)
        pending=sum(r['pending_quantity'] for r in sale_rows)
        sales_orders={r['order_id'] for r in sale_rows if start<=r['approved_on']<=end and not (r['cancelled_on'] and r['cancelled_on']<=end)}
        grouped_products={};grouped_printers={}
        for r in sale_rows:
            for container,key in ((grouped_products,r['product_id']),(grouped_printers,r['printer_id'])):
                group=container.setdefault(key,{'id':key,'sales_cents':0,'cost_cents':0,'quantity':0,'pending_quantity':0,'discount_cents':0})
                for column in ('sales_cents','cost_cents','quantity','pending_quantity','discount_cents'):group[column]+=r[column]
        for group in (*grouped_products.values(),*grouped_printers.values()):group['gross_result_cents']=group['sales_cents']-group['cost_cents']
        production=[]
        for r in self.db.execute('''SELECT a.*,o.printer_id,o.code,o.item_id,CASE WHEN ro.op_id IS NULL THEN a.created_at ELSE c.completed_at END AS recognized_at FROM production_attempts a JOIN production_orders o ON o.id=a.op_id LEFT JOIN recipe_orders ro ON ro.op_id=o.id LEFT JOIN production_completions c ON c.op_id=o.id WHERE substr(CASE WHEN ro.op_id IS NULL THEN a.created_at ELSE c.completed_at END,1,10) BETWEEN ? AND ?''',(start,end)):
            if printer_id is not None and r['printer_id']!=printer_id:continue
            item=self.db.execute('SELECT order_id FROM order_items WHERE id=?',(r['item_id'],)).fetchone() if r['item_id'] else None
            if (client_id is not None or status is not None) and (not item or item[0] not in eligible_orders):continue
            for a in json.loads(r['actual']):
                e=self.db.execute('SELECT e.*,v.product_id FROM production_entries e JOIN variants v ON v.id=e.variant_id WHERE e.id=?',(a['entry_id'],)).fetchone()
                if product_id is not None and e['product_id']!=product_id:continue
                rejected=self.db.execute("SELECT count(*) FROM production_pieces pp JOIN inspections i ON i.id=(SELECT MAX(ii.id) FROM inspections ii WHERE ii.piece_id=pp.piece_id AND substr(ii.created_at,1,10)<=?) WHERE pp.attempt_id=? AND pp.entry_id=? AND i.result='rejected'",(end,r['id'],a['entry_id'])).fetchone()[0]
                loss=a['loss_cents']+(int((Decimal(a['existing_cents']-a['loss_cents'])*rejected/a['produced']).quantize(Decimal('1'),rounding=ROUND_HALF_UP)) if a['produced'] else 0)
                printer=json.loads(self.db.execute('SELECT planned FROM production_orders WHERE id=?',(r['op_id'],)).fetchone()[0])['printer']
                components=split(a['machine_cents'],[printer[k] for k in ('investment_hour_cents','energy_hour_cents','maintenance_hour_cents')]) if a['machine_cents'] else [0,0,0]
                production.append({'source':f'OP {r["code"]} / tentativa {r["id"]} / modelo {a["entry_id"]}','date':r['recognized_at'][:10],'printer_id':r['printer_id'],'product_id':e['product_id'],'cost_cents':a['existing_cents'],'reference_cents':a['reference_cents'],'loss_cents':loss,'failed':a['failed'],'rejected':rejected,'investment_cents':components[0],'energy_cents':components[1],'maintenance_reserve_cents':components[2]})
        # Independent calculator confirmations also remain visible; never CPV/cash.
        for r in self.db.execute('SELECT * FROM calculations WHERE actual IS NOT NULL AND substr(confirmed_at,1,10) BETWEEN ? AND ?',(start,end)):
            if printer_id is not None and r['printer_id']!=printer_id:continue
            if product_id is not None or client_id is not None or status is not None:continue
            a=json.loads(r['actual']);printer=a['printer'];machine=cents(a['machine_cost']);components=split(machine,[printer[k] for k in ('investment_hour_cents','energy_hour_cents','maintenance_hour_cents')]) if machine else [0,0,0]
            production.append({'source':f'Cálculo #{r["id"]} • {r["title"]}','date':r['confirmed_at'][:10],'printer_id':r['printer_id'],'product_id':None,'cost_cents':cents(a.get('acquisition_production_cost') or a['total_cost']),'reference_cents':cents(a['total_cost']),'loss_cents':0,'failed':0,'rejected':0,'investment_cents':components[0],'energy_cents':components[1],'maintenance_reserve_cents':components[2]})
        balances=[r for r in receivables if r['order_id'] in selected_orders]
        # Product/printer filters cannot claim complete order debts belong to one item.
        if product_id is not None or printer_id is not None:
            balances=[];seen_items=set()
            for row in sale_rows:
                if row['item_id'] in seen_items:continue
                seen_items.add(row['item_id'])
                item=self.db.execute('SELECT * FROM order_items WHERE id=?',(row['item_id'],)).fetchone()
                paid=self.db.execute('SELECT COALESCE(SUM(a.amount_cents),0) FROM payment_allocations a JOIN payments p ON p.id=a.payment_id WHERE a.item_id=? AND p.paid_on<=?',(item['id'],end)).fetchone()[0]
                amount=portion(item['total_cents'],item['id']);received=portion(paid,item['id'])
                balances.append({'id':item['id'],'order_id':item['order_id'],'code':row['order'],'due_on':None,'amount_cents':amount,'paid_cents':received,'balance_cents':0 if row['status']=='cancelled' else amount-received,'status':row['status']})
        payable=self.payables(end)
        stock_losses=[]
        for loss in self.db.execute('SELECT * FROM losses WHERE occurred_on BETWEEN ? AND ?',(start,end)):
            if client_id is not None or status is not None:continue  # Unassigned stock losses have no commercial client.
            if product_id is not None or printer_id is not None:
                if loss['entity_kind']!='piece':continue
                matches=0;matched_cost=0
                for piece in self.db.execute('SELECT p.*,v.product_id,r.calculation_id FROM loss_pieces lp JOIN pieces p ON p.id=lp.piece_id JOIN variants v ON v.id=p.variant_id JOIN receipts r ON r.id=p.receipt_id WHERE lp.loss_id=?',(loss['id'],)):
                    linked=self.db.execute('SELECT o.printer_id FROM production_pieces pp JOIN production_entries e ON e.id=pp.entry_id JOIN production_orders o ON o.id=e.op_id WHERE pp.piece_id=?',(piece['id'],)).fetchone()
                    calc=self.db.execute('SELECT printer_id FROM calculations WHERE id=?',(piece['calculation_id'],)).fetchone() if piece['calculation_id'] else None
                    printer=linked[0] if linked else calc[0] if calc else None
                    if (product_id is None or piece['product_id']==product_id) and (printer_id is None or printer==printer_id):
                        matches+=1
                        frozen=self.db.execute('SELECT cost_cents FROM stock_movements WHERE operation_key=?',(f'loss:{loss["id"]}:{piece["id"]}',)).fetchone()
                        matched_cost+=frozen[0] if frozen else piece['unit_cost_cents']
                if not matches:continue
                filtered_loss=dict(loss);filtered_loss['cost_cents']=matched_cost;filtered_loss['quantity_milli']=matches*1000
                stock_losses.append(filtered_loss)
            else:stock_losses.append(dict(loss))
        written_off=sum(r['cost_cents'] for r in stock_losses)
        production_adjustments=self.production_loss_events(start,end,product_id,printer_id,eligible_orders if client_id is not None or status is not None else None)
        production_loss_expense=sum(r['amount_cents'] for r in production_adjustments)
        metrics={'sold_cents':gross,'received_gross_cents':incoming,'received_net_cents':incoming-sale_fees,'refunded_cents':refunds,'receivable_cents':sum(r['balance_cents'] for r in balances),'payable_cents':sum(r['balance_cents'] for r in payable),'expenses_paid_cents':expenses,'cost_of_sales_cents':cpv,'operating_paid_cents':operating,'payment_fees_cents':sale_fees,'retained_cents':retained,'commercial_result_cents':gross+retained-cpv-scoped_fees-(0 if scoped else operating)-written_off-production_loss_expense,'stock_loss_cents':written_off,'unabsorbed_production_loss_cents':production_loss_expense,'cash_flow_cents':sum(r['amount_cents'] for r in cash),'cash_opening_cents':sum(r['amount_cents'] for r in self.cash_events(end=date.fromisoformat(start).isoformat()) if r['date']<start),'pieces_sold':sum(r['quantity'] for r in sale_rows),'ticket_average':str(money(Decimal(sum(r['sales_cents'] for r in sale_rows if r['order_id'] in sales_orders)+sum(o['freight_cents'] for o in self.db.execute('SELECT * FROM orders') if o['id'] in sales_orders and product_id is None and printer_id is None))/100/len(sales_orders))) if sales_orders else None,'commercial_discounts_cents':sum(r['discount_cents'] for r in sale_rows),'production_cost_cents':sum(r['cost_cents'] for r in production),'production_loss_included_cents':sum(r['loss_cents'] for r in production),'pending_cost_quantity':pending,'capital_in_cents':sum(r['amount_cents'] for r in cash if r['kind']=='capital_in'),'capital_out_cents':-sum(r['amount_cents'] for r in cash if r['kind']=='capital_out')}
        metrics['cash_closing_cents']=metrics['cash_opening_cents']+metrics['cash_flow_cents']
        return {'start':start,'end':end,'scoped':scoped,'metrics':metrics,'sales':sale_rows,'cash':cash,'payables':payable,'receivables':balances,'production':production,'products':list(grouped_products.values()),'printers':list(grouped_printers.values()),'stock_losses':stock_losses,'production_adjustments':production_adjustments,'reconciliation':self.reconcile(),'notes':['Caixa, despesas e contas a pagar são consolidados; filtros de cliente/produto/impressora/situação aplicam-se ao relatório comercial e à produção.','Resultado comercial gerencial: venda líquida de cancelamentos + retenções - CPV confirmado - taxas atribuíveis - despesas operacionais adicionais pagas - perdas de estoque baixadas - perdas não absorvidas de produção. Filtro comercial exclui despesas gerais não atribuídas.','Perdas não absorvidas de tentativa são custo sem caixa adicional; primeira conclusão reverte a parcela absorvida no custo físico, evitando duplicação no CPV. Absorção de perda de período anterior pode gerar ajuste positivo de resultado no período atual.', 'Perdas de estoque são baixas de custo existente sem caixa adicional. Falhas de OP já absorvidas nas boas não são subtraídas novamente. Custos de produção não baixados permanecem identificados separadamente, sem venda presumida.', 'CPV é reconhecido na baixa física e revertido somente no retorno físico; resultado é provisório enquanto houver peças sem custo de baixa.','Pagamentos de energia/manutenção/estoque/equipamentos são caixa; não são subtraídos novamente do resultado que já contém custo de produção apropriado.','Saldos a receber/pagar são posições até a data final, incluindo obrigações anteriores ao início. Frete, retenção e reembolso são identificados por pedido; não são atribuídos ao produto/impressora sem documento de origem específico.']}

    def reconcile(self):
        issues=[]
        if self.db.execute('PRAGMA foreign_key_check').fetchall():issues.append('Vínculos do banco inválidos.')
        for p in self.db.execute('SELECT * FROM payments'):
            expected=p['amount_cents']-p['fee_cents'] if p['kind']=='cash' else 0
            if p['net_cents']!=expected:issues.append(f'Pagamento {p["id"]}: líquido divergente.')
            for table,key in (('payment_allocations','payment_id'),('installment_allocations','payment_id')):
                value=self.db.execute(f'SELECT COALESCE(SUM(amount_cents),0) FROM {table} WHERE {key}=?',(p['id'],)).fetchone()[0]
                if value!=p['amount_cents']:issues.append(f'Pagamento {p["id"]}: alocação {table} divergente.')
        for r in self.db.execute('SELECT * FROM orders'):
            amount=self.db.execute('SELECT COALESCE(SUM(total_cents),0) FROM order_items WHERE order_id=?',(r['id'],)).fetchone()[0]
            if amount+r['freight_cents']!=r['total_cents']:issues.append(f'Pedido {r["id"]}: itens/frete não reconciliam.')
        for r in self.db.execute('SELECT c.*,m.cost_cents AS original FROM financial_costs c JOIN stock_movements m ON m.id=c.movement_id'):
            if r['cost_cents']!=r['original']:issues.append(f'CPV {r["id"]}: diverge da baixa histórica.')
        for r in self.db.execute('SELECT i.id,i.amount_cents,COALESCE(SUM(p.amount_cents),0) AS paid FROM payable_installments i LEFT JOIN payable_payments p ON p.installment_id=i.id GROUP BY i.id'):
            if r['paid']>r['amount_cents']:issues.append(f'Conta/parcela {r["id"]}: pagamento excedente.')
        for r in self.db.execute('SELECT p.id,p.amount_cents,COALESCE(SUM(i.amount_cents),0) AS total FROM payables p LEFT JOIN payable_installments i ON i.payable_id=p.id GROUP BY p.id'):
            if r['amount_cents']!=r['total']:issues.append(f'Conta {r["id"]}: parcelas divergentes.')
        expected=self.db.execute("SELECT COALESCE(SUM(net_cents),0) FROM payments WHERE kind='cash'").fetchone()[0]-self.db.execute('SELECT COALESCE(SUM(amount_cents),0) FROM refunds').fetchone()[0]-self.db.execute('SELECT COALESCE(SUM(amount_cents+fee_cents),0) FROM payable_payments').fetchone()[0]+self.db.execute("SELECT COALESCE(SUM(CASE WHEN kind IN('capital_in','opening_in') THEN amount_cents ELSE -amount_cents END),0) FROM finance_entries").fetchone()[0]
        if expected!=sum(r['amount_cents'] for r in self.cash_events()):issues.append('Caixa não reconcilia com pagamentos, reembolsos, despesas e movimentos do proprietário.')
        return {'status':'ok' if not issues else 'divergent','issues':issues,'cash_balance_cents':expected,'source_costs':self.db.execute('SELECT count(*) FROM financial_costs').fetchone()[0]}
