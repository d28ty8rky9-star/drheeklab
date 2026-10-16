"""Immutable branded internal reports and public catalogs; no live PDF views."""
from decimal import Decimal
from io import BytesIO
import hashlib
import json
from pathlib import Path
import shutil
from uuid import uuid4
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from .storage import now
from .transactions import transaction
from .catalog import required
from .pricing import cents,brl
from .backup import digest
from .products import Products
from .finance import Finance
from .production import Production
from .sales import Sales
from . import __version__

KINDS={'finance':'Relatório financeiro','production':'Relatório de produção','catalog':'Catálogo de produtos'}
LABELS={'sold_cents':'Total vendido','received_gross_cents':'Recebido bruto','received_net_cents':'Recebido líquido','refunded_cents':'Reembolsado','receivable_cents':'A receber','payable_cents':'A pagar','expenses_paid_cents':'Despesas pagas','cost_of_sales_cents':'CPV confirmado','commercial_result_cents':'Resultado gerencial','cash_flow_cents':'Fluxo de caixa','cash_opening_cents':'Saldo inicial do período','cash_closing_cents':'Saldo final','pieces_sold':'Peças vendidas','ticket_average':'Ticket médio (R$)','commercial_discounts_cents':'Descontos informativos','production_cost_cents':'Custo de produção','production_loss_included_cents':'Perdas incluídas na produção','unabsorbed_production_loss_cents':'Perdas não absorvidas/ajustes','stock_loss_cents':'Perdas de estoque','pending_cost_quantity':'Peças com custo de baixa pendente','capital_in_cents':'Aportes','capital_out_cents':'Retiradas','operating_paid_cents':'Operacionais adicionais pagos','payment_fees_cents':'Taxas','retained_cents':'Retenções'}


class Documents:
    def __init__(self,storage):self.storage,self.db=storage,storage.db

    def rows(self,kind=None,archived=False):
        if kind is not None and kind not in KINDS:raise ValueError('Documento inválido.')
        return [dict(r) for r in self.db.execute('SELECT * FROM generated_documents WHERE archived=?'+(' AND kind=?' if kind else '')+' ORDER BY id DESC',(int(archived),kind) if kind else (int(archived),))]

    def get(self,identifier):
        r=self.db.execute('SELECT * FROM generated_documents WHERE id=?',(identifier,)).fetchone()
        if not r:raise ValueError('Documento não encontrado.')
        return dict(r)

    def path(self,identifier):
        r=self.get(identifier);root=self.storage.home.resolve();rel=Path(r['path']);path=(root/rel).resolve()
        if rel.is_absolute() or len(rel.parts)!=2 or rel.parts[0] not in ('Relatórios','Catálogos') or not path.is_relative_to(root):raise ValueError('Referência de documento inválida.')
        if not path.is_file() or digest(path)!=r['sha256']:raise ValueError('PDF ausente ou alterado. Restaure backup completo.')
        return path

    def brand(self):
        rel=self.storage.get('logo')
        if not rel:return {'logo':None,'name':'Dr. Heek Lab','primary':'#6d41c7','secondary':'#087eaa','status':'Logotipo oficial não configurado — documento de revisão'}
        root=self.storage.home.resolve();relative=Path(rel);path=(root/relative).resolve()
        if relative.is_absolute() or len(relative.parts)!=2 or relative.parts[0]!='Marca' or not path.is_relative_to(root) or not path.is_file():raise ValueError('Logo configurado não foi encontrado. Importe o original em Configurações ou restaure backup.')
        from PySide6.QtGui import QImageReader
        if QImageReader(str(path)).read().isNull():raise ValueError('Logo configurado não é uma imagem válida.')
        return {'logo':rel,'sha256':digest(path),'name':'Dr. Heek Lab','primary':'#6d41c7','secondary':'#087eaa','status':'Marca configurada'}

    def emit_finance(self,start=None,end=None,**filters):
        with transaction(self.db):
            data=Finance(self.storage).report(start,end,**filters)
            criteria={'start':data['start'],'end':data['end'],**{key:filters.get(key) for key in ('client_id','product_id','printer_id','status')}}
            stream=hashlib.sha256(json.dumps(criteria,sort_keys=True).encode()).hexdigest()
            return self._emit('finance',stream,'Relatório financeiro • '+data['start']+' a '+data['end'],data)

    def emit_production(self,identifier):
        with transaction(self.db):
            p=Production(self.storage);op=p.get(identifier);pieces=p.pieces(identifier);entries=p.entries(identifier)
            inspections=[]
            for piece in pieces:
                for i in self.db.execute('SELECT * FROM inspections WHERE piece_id=? ORDER BY id',(piece['id'],)):
                    row=dict(i);row['photos']=[dict(f) for f in self.db.execute('SELECT * FROM inspection_photos WHERE inspection_id=?',(i['id'],))]
                    for photo in row['photos']:p.photo_path(photo['id'])
                    inspections.append(row)
            data={'order':op,'entries':entries,'summary':p.summary(identifier),'pieces':pieces,'inspections':inspections,'attempts':[dict(r) for r in self.db.execute('SELECT * FROM production_attempts WHERE op_id=? ORDER BY id',(identifier,))],'problems':[dict(r) for r in self.db.execute('SELECT * FROM production_problems WHERE op_id=? ORDER BY id',(identifier,))]}
            return self._emit('production',str(identifier),'Relatório de produção • '+op['code'],data)

    def emit_catalog(self,selections,title='Catálogo de produtos',notes=''):
        if not selections or len(selections)>500:raise ValueError('Selecione de 1 a 500 variantes para o catálogo.')
        with transaction(self.db):
            products=Products(self.storage);items=[];seen=set()
            for selected in selections:
                variant=products.active_variant(selected['variant_id']);model=products.active_product(variant['product_id'])
                if variant['id'] in seen:raise ValueError('Variante repetida no catálogo.')
                seen.add(variant['id']);price=cents(selected['price'],'Preço de venda do catálogo')
                photos=products.media(model['id'],'photo');photo=next((r for r in photos if r['is_primary']),photos[0] if photos else None)
                if not photo:raise ValueError('Importe uma foto de '+model['name']+' em Produtos antes de incluí-lo no catálogo.')
                products.media_path(photo['id'],'photo')
                items.append({'product_id':model['id'],'variant_id':variant['id'],'name':model['name']+' / '+variant['name'],'description':str(selected.get('description',model['description'][:600])),'price_cents':price,'photo':{k:photo[k] for k in ('path','sha256','original_name')}})
            stream=hashlib.sha256(json.dumps(sorted(seen)).encode()).hexdigest()
            return self._emit('catalog',stream,required(title,'Título do catálogo'),{'items':items,'notes':str(notes)})

    def _emit(self,kind,stream,title,data):
        # Called inside the public transaction; files removed on any local error.
        version=self.db.execute('SELECT COALESCE(MAX(version),0)+1 FROM generated_documents WHERE kind=? AND stream=?',(kind,stream)).fetchone()[0]
        code=Sales(self.storage).code({'finance':'RF','production':'RP','catalog':'CAT'}[kind]);folder='Catálogos' if kind=='catalog' else 'Relatórios'
        target=(self.storage.home/folder).resolve()/(code+'-v'+str(version)+'-'+uuid4().hex+'.pdf')
        if not target.is_relative_to(self.storage.home.resolve()):raise ValueError('Pasta do documento fora do armazenamento.')
        snapshot={'kind':kind,'title':title,'code':code,'version':version,'app_version':__version__,'created_at':now(),'brand':self.brand(),'data':data}
        made=False
        try:
            content=render(self.storage,snapshot)
            with target.open('xb') as file:made=True;file.write(content)
            identifier=self.db.execute('INSERT INTO generated_documents(code,kind,stream,version,title,path,sha256,snapshot,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(code,kind,stream,version,title,target.relative_to(self.storage.home.resolve()).as_posix(),digest(target),json.dumps(snapshot,ensure_ascii=False),snapshot['created_at'])).lastrowid
            self.storage.audit('documento emitido',f'generated_documents:{identifier}',None,{'code':code,'kind':kind,'version':version,'sha256':digest(target)})
            return identifier
        except BaseException:
            if made:target.unlink(missing_ok=True)
            raise

    def archive(self,identifier,archived,reason):
        required(reason,'Justificativa')
        with transaction(self.db):
            before=self.get(identifier)
            if not archived:self.path(identifier)
            self.db.execute('UPDATE generated_documents SET archived=? WHERE id=?',(int(archived),identifier))
            self.storage.audit('documento arquivado' if archived else 'documento restaurado',f'generated_documents:{identifier}',before,self.get(identifier),reason)

    def export(self,identifier,destination):
        path=self.path(identifier);target=Path(destination)
        if target.suffix.lower()!='.pdf':raise ValueError('Escolha arquivo PDF para compartilhar.')
        if target.resolve()==path.resolve():raise ValueError('O PDF emitido já está nesse caminho; escolha outro destino para a cópia.')
        shutil.copyfile(path,target)
        if digest(target)!=self.get(identifier)['sha256']:raise ValueError('Cópia exportada não confere com o documento emitido.')
        with transaction(self.db):self.storage.audit('documento exportado',f'generated_documents:{identifier}',None,{'sha256':digest(target)},'Cópia para compartilhamento manual')
        return target


def render(storage,snapshot):
    styles=getSampleStyleSheet();styles['Title'].textColor=colors.HexColor(snapshot['brand']['primary']);styles['Heading2'].textColor=colors.HexColor(snapshot['brand']['secondary']);styles['BodyText'].fontSize=9;styles['BodyText'].leading=12
    def p(value,style='BodyText'):return Paragraph(escape(str(value)).replace('\n','<br/>'),styles[style])
    def money(value):return brl(Decimal(value)/100)
    story=[];brand=snapshot['brand']
    if brand['logo']:
        image=Image(str(storage.home/brand['logo']));image._restrictSize(95,95);story.append(image)
    else:story.append(p(brand['status']))
    story.extend([p(brand['name'],'Title'),p(snapshot['title'],'Heading2'),p(snapshot['code']+' • versão '+str(snapshot['version'])+' • aplicativo '+snapshot['app_version']+' • '+snapshot['created_at'][:10]),Spacer(1,12)])
    wide=snapshot['kind']=='finance';size=landscape(A4) if wide else A4;width=size[0]-88
    def grid(headers,rows,widths=None):
        cells=[[p(h) for h in headers]]+[[p(v) for v in row] for row in rows]
        if len(cells)==1:cells.append([p('Sem registros')]+[p('') for _ in headers[1:]])
        table=Table(cells,colWidths=widths or [width/len(headers)]*len(headers),repeatRows=1,splitInRow=1)
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6e0f3')),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#ccccdd')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.extend([table,Spacer(1,12)])
    data=snapshot['data']
    if snapshot['kind']=='finance':
        story.append(p('Relatório gerencial interno. Não é documento fiscal.'))
        grid(['Indicador','Valor'],[(LABELS.get(k,k),money(v) if k.endswith('_cents') else str(v) if v is not None else 'Sem dados') for k,v in data['metrics'].items()],[width*.65,width*.35])
        for title in data['notes']:story.append(p(title))
        story.extend([Spacer(1,12),p('Reconciliação: '+data['reconciliation']['status'],'Heading2')])
        for issue in data['reconciliation']['issues']:story.append(p(issue))
        sections=[('Vendas', ['Pedido','Descrição','Peças','Venda','CPV','Pendente'],[(r['order'],r['description'],r['quantity'],money(r['sales_cents']),money(r['cost_cents']),r['pending_quantity']) for r in data['sales']]),('Caixa consolidado',['Data','Origem','Descrição','Movimento'],[(r['date'],r['source'],r['description'],money(r['amount_cents'])) for r in data['cash']]),('Contas a pagar',['Descrição','Fornecedor','Vencimento','Previsto','Pago','Saldo'],[(r['description'],r['supplier'],r['due_on'] or 'Sem data',money(r['amount_cents']),money(r['paid_cents']),money(r['balance_cents'])) for r in data['payables']]),('Contas a receber',['Pedido','Vencimento','Previsto','Recebido','Saldo'],[(r['code'],r['due_on'] or 'Sem data',money(r['amount_cents']),money(r['paid_cents']),money(r['balance_cents'])) for r in data['receivables']]),('Produção',['Origem','Data','Custo','Referência','Perda incluída'],[(r['source'],r['date'],money(r['cost_cents']),money(r['reference_cents']),money(r['loss_cents'])) for r in data['production']]),('Perdas e absorção',['OP','Data','Evento','Ajuste'],[(r['op'],r['date'],'Perda' if r['kind']=='loss' else 'Absorção no custo',money(r['amount_cents'])) for r in data['production_adjustments']]),('Perdas de estoque',['Data','Motivo','Custo baixado'],[(r['occurred_on'],r['reason'],money(r['cost_cents'])) for r in data['stock_losses']])]
        for key in ('products','printers'):sections.append(('Resultados por '+('produto' if key=='products' else 'impressora'),['Identificação','Peças','Vendido','CPV','Resultado bruto'],[(r['id'] or 'Sem identificação',r['quantity'],money(r['sales_cents']),money(r['cost_cents']),money(r['gross_result_cents'])) for r in data[key]]))
        for title,heads,rows in sections:story.extend([PageBreak(),p(title,'Heading2')]);grid(heads,rows)
    elif snapshot['kind']=='production':
        op=data['order'];story.extend([p('Relatório interno de produção e qualidade. Organização inspirada em práticas ISO; não é certificação.'),p('Responsável: '+op['responsible']),p('Estado: '+{'waiting':'Aguardando','printing':'Imprimindo','inspection':'Aguardando inspeção','completed':'Concluída'}[op['state']]+' • revisão '+str(op['revision'])),p('Parâmetros: '+op['parameters']),p('Planejadas: '+str(data['summary']['planned'])+' • Produzidas: '+str(data['summary']['produced'])+' • Boas: '+str(data['summary']['good'])+' • Reprovadas: '+str(data['summary']['rejected'])+' • Perdidas: '+str(data['summary']['failed'])),p('Impressora: '+json.loads(op['planned'])['printer']['identifier']+' • tempo previsto '+str(json.loads(op['planned'])['minutes'])+' min'),p('Previsto por referência: '+money(data['summary']['planned_reference_cents'])),p('Custo existente: '+money(data['summary']['total_cents'])+' • Por referência: '+money(data['summary']['reference_cents'])+' • Efetivo por boa: '+(brl(data['summary']['effective_unit']) if data['summary']['effective_unit'] else 'Sem aprovadas'))])
        grid(['Modelo/variante','Quantidade','Arquivo/versão'],[(e['product_name']+' / '+e['variant_name'],e['quantity'],json.loads(e['planned'])['project']['original_name']+' • v'+str(json.loads(e['planned'])['project']['version'])) for e in data['entries']])
        for a in data['attempts']:
            story.extend([p('Tentativa '+str(a['id'])+' • '+a['created_at']+' • '+str(a['minutes'])+' min • progresso '+a['progress']+'%','Heading2'),p('Motivo: '+a['reason'])])
            for actual in json.loads(a['actual']):
                entry=next(e for e in data['entries'] if e['id']==actual['entry_id'])
                story.append(p(entry['product_name']+' / '+entry['variant_name']+' • Produzidas '+str(actual['produced'])+' • Perdidas '+str(actual['failed'])+' • Custo existente '+money(actual['existing_cents'])+' • Referência '+money(actual['reference_cents'])))
                grid(['Carretel','Material/cor','Consumo real (g)','Custo por referência'],[(f['name'],f['material']+' / '+f['color'],f['grams'],brl(f['cost'])) for f in actual['cost']['filaments']])
        for inspection in data['inspections']:
            story.extend([PageBreak(),p('FR-001 • peça '+str(inspection['piece_id'])+' • inspeção '+str(inspection['id']),'Heading2'),p('Responsável: '+inspection['responsible']+' • '+inspection['created_at']),p('Resultado: '+{'approved':'Aprovada','notes':'Aprovada com observações leves','rejected':'Reprovada'}[inspection['result']]+' • '+('Vigente' if inspection['valid'] else 'Histórico')),p(inspection['notes'])])
            from .production import CHECK_LABELS,VIEWS
            grid(['Item','Resultado','Justificativa'],[(CHECK_LABELS[k],{'ok':'Conforme','fail':'Reprovado','na':'Não aplicável'}[v['result']],v.get('reason','')) for k,v in json.loads(inspection['checklist']).items()])
            for photo in inspection['photos']:
                image=Image(str(storage.home/photo['path']));image._restrictSize(190,135);story.extend([p(VIEWS[photo['view']]),image,Spacer(1,6)])
        for r in data['problems']:story.extend([p('Problema do produto '+str(r['product_id'])+' • '+r['kind'],'Heading2'),p(r['description']+' • '+r['responsible'])])
    else:
        for index,item in enumerate(data['items']):
            image=Image(str(storage.home/item['photo']['path']));image._restrictSize(170,145)
            story.extend([p(item['name'],'Heading2'),image,Spacer(1,6),p(item['description']),p(money(item['price_cents']),'Heading2'),Spacer(1,15)])
            if index<len(data['items'])-1:story.append(PageBreak())
        if data['notes']:story.append(p(data['notes']))
        story.append(p('Catálogo comercial. Para compartilhar por WhatsApp, envie manualmente a cópia PDF exportada.'))
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor(brand['primary']));canvas.drawString(44,25,snapshot['code']+' • versão '+str(snapshot['version'])+' • Dr. Heek Lab');canvas.drawRightString(size[0]-44,25,'Página '+str(doc.page))
    output=BytesIO();SimpleDocTemplate(output,pagesize=size,leftMargin=44,rightMargin=44,topMargin=35,bottomMargin=45).build(story,onFirstPage=footer,onLaterPages=footer)
    return output.getvalue()
