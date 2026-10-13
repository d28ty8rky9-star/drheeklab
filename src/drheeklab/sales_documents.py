"""Immutable customer PDFs and owned attachments; monetary values stay integers."""
from pathlib import Path
from decimal import Decimal
from xml.sax.saxutils import escape
import json
import shutil
import uuid
from io import BytesIO
from PySide6.QtGui import QImageReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from .storage import now
from .backup import digest
from .pricing import brl
from .transactions import transaction


def owned_path(storage, relative, expected=None):
    root = storage.home.resolve()
    rel = Path(relative)
    path = (root / rel).resolve()
    if rel.is_absolute() or len(rel.parts) != 2 or rel.parts[0] not in ('Orçamentos', 'Pedidos e Comprovantes') or not path.is_relative_to(root):
        raise ValueError('Caminho de documento fora do armazenamento permitido.')
    if not path.is_file():
        raise ValueError('Documento não encontrado. Restaure backup completo.')
    if expected and digest(path) != expected:
        raise ValueError('Documento emitido foi alterado externamente; restaure o original.')
    return path


def import_attachment(storage, source, order_id=None, quote_id=None, item_id=None, item_index=None, kind='reference', created=None):
    source = Path(source)
    if not source.is_file() or not source.stat().st_size:
        raise ValueError('Anexo inexistente ou vazio.')
    suffix = source.suffix.lower()
    allowed = ('.png','.jpg','.jpeg','.pdf') if kind == 'delivery' else ('.png','.jpg','.jpeg','.stl','.3mf')
    if suffix not in allowed:
        raise ValueError('Use foto PNG/JPEG ou STL/3MF; comprovantes de entrega também aceitam PDF.')
    if suffix in ('.png','.jpg','.jpeg') and QImageReader(str(source)).read().isNull():
        raise ValueError('Imagem de referência inválida.')
    if suffix == '.pdf':
        with source.open('rb') as file:
            if not file.read(5).startswith(b'%PDF-'):
                raise ValueError('Comprovante PDF inválido.')
    folder = (storage.home/'Pedidos e Comprovantes').resolve()
    if not folder.is_relative_to(storage.home.resolve()):
        raise ValueError('Pasta de documentos fora do armazenamento.')
    target = folder/(uuid.uuid4().hex+suffix)
    made = False
    try:
        with source.open('rb') as original, target.open('xb') as output:
            made = True
            if created is not None:
                created.append(target)
            shutil.copyfileobj(original,output)
        identifier = storage.db.execute('INSERT INTO sales_attachments(order_id,quote_id,item_id,item_index,kind,path,original_name,sha256,created_at) VALUES(?,?,?,?,?,?,?,?,?)',
            (order_id,quote_id,item_id,item_index,kind,target.relative_to(storage.home.resolve()).as_posix(),source.name,digest(target),now())).lastrowid
        storage.audit('anexo comercial',f'sales_attachments:{identifier}',None,{'original_name':source.name,'kind':kind})
        return identifier
    except Exception:
        if made:
            target.unlink(missing_ok=True)
        raise


def render_pdf(storage, path, data):
    styles=getSampleStyleSheet()
    styles['Title'].textColor=colors.HexColor('#6d41c7')
    styles['Heading2'].textColor=colors.HexColor('#087eaa')
    def paragraph(value, style='BodyText'):
        return Paragraph(escape(str(value)).replace('\n','<br/>'),styles[style])
    def currency(value):
        return brl(Decimal(value)/100)
    story=[]
    logo=storage.get('logo')
    if logo:
        candidate=(storage.home/logo).resolve()
        if (storage.home/'Marca').resolve().is_relative_to(storage.home.resolve()) and candidate.is_relative_to((storage.home/'Marca').resolve()) and candidate.is_file():
            image=Image(str(candidate)); image._restrictSize(110,110); story.append(image)
        else:
            story.append(paragraph('Logotipo oficial não configurado'))
    else:
        story.append(paragraph('Logotipo oficial não configurado'))
    story.extend([paragraph('Dr. Heek Lab','Title'),paragraph(data['title'],'Heading2'),paragraph('Versão '+str(data['version'])+' • '+data['emitted_date']),Spacer(1,12)])
    customer=data['client']
    story.append(paragraph('Cliente: '+customer['name']))
    for key,label in (('phone','Telefone'),('email','E-mail')):
        if customer.get(key): story.append(paragraph(label+': '+customer[key]))
    story.append(Spacer(1,12))
    rows=[[paragraph('Item'),paragraph('Qtd.'),paragraph('Preço unitário'),paragraph('Total')]]
    for row in data['items']:
        rows.append([paragraph(row['description']),paragraph(row['quantity']),paragraph(currency(row['unit_price_cents'])),paragraph(currency(row['total_cents']))])
    listing=Table(rows,colWidths=[265,40,100,100],repeatRows=1,splitInRow=1)
    listing.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6e0f3')),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#ccccdd')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    story.extend([listing,Spacer(1,12),paragraph('Frete: '+currency(data['freight_cents'])),paragraph('TOTAL: '+currency(data['total_cents']),'Heading2')])
    if data.get('valid_until'):
        story.append(paragraph('Validade: '+data['valid_until']))
    if data.get('due_on'):
        story.append(paragraph('Prazo de entrega: '+data['due_on']))
    if data['kind']=='order':
        story.extend([Spacer(1,12),paragraph('Histórico de pagamentos','Heading2')])
        if not data['payments']: story.append(paragraph('Nenhum pagamento registrado.'))
        for payment in data['payments']:
            story.append(paragraph(payment['paid_on']+' • '+payment['method']+' • '+currency(payment['amount_cents'])))
        story.append(paragraph('Total recebido em pagamentos: '+currency(data['cash_received_cents'])))
        if data['credit_applied_cents']:
            story.append(paragraph('Crédito do cliente aplicado: '+currency(data['credit_applied_cents'])))
        story.append(paragraph('Saldo restante: '+currency(data['balance_cents']),'Heading2'))
        if data['state']=='cancelled':
            cancel=data['cancellation']
            story.append(paragraph('PEDIDO CANCELADO','Heading2'))
            story.append(paragraph('Motivo: '+cancel['reason']))
            story.append(paragraph('Reembolso: '+currency(cancel['refund_cents'])+' • Crédito para compra futura: '+currency(cancel['credit_cents'])+' • Retenção justificada: '+currency(cancel['retained_cents'])))
        elif not data['balance_cents']:
            story.append(paragraph('QUITADO','Heading2'))
        story.append(paragraph('Comprovante comercial. Não é nota fiscal.'))
    else:
        story.append(paragraph('Situação: '+{'pending':'Pendente','approved':'Aprovado','rejected':'Rejeitado','expired':'Vencido'}[data['state']]))
        story.append(paragraph('Orçamento: não representa pagamento nem confirmação de pedido.'))
    if data.get('notes'):
        story.extend([Spacer(1,12),paragraph('Observações: '+data['notes'])])
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8); canvas.setFillColor(colors.HexColor('#6d41c7'))
        canvas.drawString(44,25,'Dr. Heek Lab • '+data['title']+' • versão '+str(data['version']))
        canvas.drawRightString(A4[0]-44,25,'Página '+str(doc.page))
    output=BytesIO()
    SimpleDocTemplate(output,pagesize=A4,rightMargin=44,leftMargin=44,topMargin=35,bottomMargin=45).build(story,onFirstPage=footer,onLaterPages=footer)
    return output.getvalue()


def emit(storage, data, *, order_id=None, quote_id=None, created=None):
    if (order_id is None)==(quote_id is None):
        raise ValueError('Informe somente pedido ou orçamento.')
    with transaction(storage.db):
        column,identifier=('order_id',order_id) if order_id is not None else ('quote_id',quote_id)
        version=storage.db.execute(f'SELECT COALESCE(MAX(version),0)+1 FROM sales_documents WHERE {column}=?',(identifier,)).fetchone()[0]
        folder='Pedidos e Comprovantes' if order_id is not None else 'Orçamentos'
        directory=(storage.home/folder).resolve()
        if not directory.is_relative_to(storage.home.resolve()):
            raise ValueError('Pasta de documentos fora do armazenamento.')
        target=directory/(data['code']+f'-v{version}-'+uuid.uuid4().hex+'.pdf')
        snapshot={**data,'version':version}
        made=False
        try:
            content=render_pdf(storage,target,snapshot)
            with target.open('xb') as output:
                made=True
                if created is not None: created.append(target)
                output.write(content)
            relative=target.relative_to(storage.home.resolve()).as_posix()
            result=storage.db.execute('INSERT INTO sales_documents(order_id,quote_id,version,path,sha256,snapshot,created_at) VALUES(?,?,?,?,?,?,?)',
                (order_id,quote_id,version,relative,digest(target),json.dumps(snapshot,ensure_ascii=False),now())).lastrowid
            storage.audit('documento comercial emitido',f'sales_documents:{result}',None,{'version':version,'path':relative})
            return result
        except Exception:
            if made: target.unlink(missing_ok=True)
            raise
