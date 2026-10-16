"""Customers, proposals and immutable approved orders in the desktop UI."""
from datetime import date,timedelta,datetime
from decimal import Decimal
from pathlib import Path
import json
import uuid
from PySide6.QtCore import QTimer,QUrl,Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QComboBox,
    QCheckBox,QDialog,QTabWidget,QTextEdit,QPushButton,QFileDialog,QMessageBox,QInputDialog,QListWidget,QListWidgetItem,QAbstractItemView,QTableWidget,QTableWidgetItem)
from .sales import Sales,PAYMENT_METHODS
from .sales_documents import owned_path
from .catalog import Catalog
from .pricing import cents, brl
from .phase2_ui import FormDialog, button, table, fill_table, date_iso, date_br, decimal_cents

QUOTE_STATES={'pending':'Pendente','approved':'Aprovado','rejected':'Rejeitado','expired':'Vencido'}
DELIVERY_STATES={'waiting':'Aguardando envio/retirada','sent':'Enviado','delivered':'Entregue'}
INSTALLMENT_STATES={'pending':'Pendente','partial':'Parcial','paid':'Quitada','overdue':'Atrasada','cancelled':'Cancelada'}


def currency(value): return brl(Decimal(value)/100)


def open_local(parent,path):
    if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))):
        QMessageBox.information(parent,'Arquivo local','Nenhum visualizador encontrado. Arquivo salvo em:\n'+str(path))


class InstallmentEditor(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        box=QVBoxLayout(self)
        self.listing=QTableWidget(0,2); self.listing.setHorizontalHeaderLabels(['Valor previsto (R$)','Vencimento DD/MM/AAAA (opcional)'])
        self.listing.setMinimumHeight(150); box.addWidget(self.listing)
        controls=QHBoxLayout(); button('Adicionar parcela',lambda:self.add(),controls); button('Remover parcela selecionada',self.remove,controls); box.addLayout(controls)
    def add(self,amount='',due=''):
        index=self.listing.rowCount(); self.listing.insertRow(index)
        self.listing.setItem(index,0,QTableWidgetItem(str(amount))); self.listing.setItem(index,1,QTableWidgetItem(str(due)))
    def remove(self):
        if self.listing.currentRow()>=0:self.listing.removeRow(self.listing.currentRow())
    def fill(self,rows):
        self.listing.setRowCount(0)
        for row in rows:self.add(row['amount'],date_br(row['due_on']) if row.get('due_on') else '')
    def values(self):
        return [{'amount':self.listing.item(i,0).text() if self.listing.item(i,0) else '',
                 'due_on':date_iso(self.listing.item(i,1).text()) if self.listing.item(i,1) else None} for i in range(self.listing.rowCount())]


def plan_with_deposit(sales,total,count,first_due,deposit):
    entry=cents(deposit,'Entrada')
    if entry>total:raise ValueError('Entrada excede o total do pedido.')
    rows=[{'amount':str(Decimal(entry)/100),'due_on':date.today().isoformat()}] if entry else []
    return rows+sales.split_installments(total-entry,count,first_due)


class ClientDialog(FormDialog):
    def __init__(self,sales,identifier=None,parent=None):
        super().__init__('Editar cliente' if identifier else 'Novo cliente',parent)
        self.sales,self.identifier=sales,identifier
        row=sales.get('clients',identifier) if identifier else {}
        for key,label in (('name','Nome *'),('phone','Telefone (opcional)'),('email','E-mail (opcional)'),('notes','Observações')):
            self.line(key,label,row.get(key,''))
    def persist(self): self.saved_id=self.sales.save_client(self.values(),self.identifier)


class CommercialDialog(FormDialog):
    def __init__(self,sales,kind,parent=None):
        super().__init__('Novo orçamento' if kind=='quote' else 'Novo pedido • aprovação definitiva',parent)
        self.sales,self.kind=sales,kind
        self.loading=True; self.done_saving=False
        self.operation_key=uuid.uuid4().hex
        self.item_rows=[]
        choices={r['id']:r['name']+' • #'+str(r['id']) for r in sales.clients()}
        self.combo('client_id','Cliente *',choices,next(iter(choices),None))
        self.line('freight','Frete TOTAL cobrado (R$)','0')
        self.line('notes','Observações')
        if kind=='quote':
            self.line('valid_until','Validade',(date.today()+timedelta(days=7)).strftime('%d/%m/%Y'),'Vazio: sem validade')
        else:
            self.line('due_on','Prazo de entrega','','DD/MM/AAAA; opcional')
            self.line('installment_count','Parcelas do saldo (sem entrada)','1')
            self.line('first_due','Primeiro vencimento','','DD/MM/AAAA; opcional')
            self.line('deposit','Entrada recebida agora (R$)','0','Opcional; não é previsão de pagamento')
            self.combo('deposit_method','Meio da entrada',PAYMENT_METHODS,'pix')
            self.line('deposit_fee','Taxa da entrada (R$)','0')
            self.installments=InstallmentEditor(self); self.form.addRow(self.installments)
            prepare=QPushButton('Gerar entrada + parcelas do saldo (editáveis)'); prepare.clicked.connect(self.prepare_plan); self.form.addRow(prepare)
        self.form.addRow(QLabel('Preço informado por peça é o preço final. Frete é cobrado uma vez.\nPedidos aprovados não terão edição de itens/preços; mudanças exigem cancelamento e novo registro.'))
        add=QPushButton('Adicionar produto / item personalizado'); add.clicked.connect(lambda: self.add_item()); self.form.addRow(add)
        self.draft_label=QLabel('Rascunho recuperável; nenhum pedido/pagamento é gravado antes de Salvar.')
        self.form.addRow(self.draft_label)
        self.timer=QTimer(self); self.timer.setSingleShot(True); self.timer.setInterval(600); self.timer.timeout.connect(self.save_draft)
        self.restore_draft()
        if not self.item_rows: self.add_item()
        for item in self.fields.values():
            (item.currentIndexChanged if isinstance(item,QComboBox) else item.textChanged).connect(self.changed)
        if kind=='order':self.installments.listing.itemChanged.connect(self.changed)
        self.loading=False

    def prepare_plan(self):
        try:
            data=self.values(); prepared=self.sales.prepare_items(self.items())
            total=cents(data['freight'])+sum(row['total_cents'] for row in prepared)
            self.installments.fill(plan_with_deposit(self.sales,total,data['installment_count'],date_iso(data['first_due']),data['deposit']))
            self.changed()
        except ValueError as error:self.error.setText(str(error))

    def add_item(self,data=None):
        data=data or {}
        widget=QWidget(); layout=QVBoxLayout(widget)
        combo=QComboBox(); combo.addItem('Personalizado (descrição obrigatória)',None)
        variants=self.sales.products.all_variants()
        for row in variants: combo.addItem(row['code']+' • '+row['product_name']+' / '+row['name'],row['id'])
        combo.setCurrentIndex(combo.findData(data.get('variant_id')))
        description=QLineEdit(str(data.get('description',''))); description.setPlaceholderText('Descrição para o cliente')
        quantity=QLineEdit(str(data.get('quantity','1'))); quantity.setPlaceholderText('Quantidade')
        price=QLineEdit(str(data.get('unit_price',''))); price.setPlaceholderText('Preço final UNITÁRIO (R$)')
        fulfillment=QComboBox(); fulfillment.addItem('Produção / reservar depois','production'); fulfillment.addItem('Reservar peças disponíveis agora','stock')
        fulfillment.setCurrentIndex(fulfillment.findData(data.get('fulfillment','production')))
        layout.addWidget(combo); layout.addWidget(description)
        row=QHBoxLayout(); row.addWidget(QLabel('Qtd.')); row.addWidget(quantity); row.addWidget(QLabel('Preço final unitário (R$)')); row.addWidget(price); layout.addLayout(row)
        layout.addWidget(fulfillment)
        controls=QHBoxLayout(); file_label=QLabel()
        item={'widget':widget,'combo':combo,'description':description,'quantity':quantity,'price':price,'fulfillment':fulfillment,'files':list(data.get('files',[])),'file_label':file_label}
        button('Foto / STL / 3MF',lambda: self.choose_files(item),controls)
        button('Remover item',lambda: self.remove_item(item),controls); layout.addLayout(controls); layout.addWidget(file_label)
        file_label.setText(', '.join(Path(p).name for p in item['files']) or 'Sem anexos')
        file_label.setWordWrap(True)
        self.form.addRow(widget); self.item_rows.append(item)
        def selected(*args):
            identifier=combo.currentData()
            if identifier is not None:
                variant=self.sales.products.get('variants',identifier); product=self.sales.products.get('products',variant['product_id'])
                description.setText(product['name']+' / '+variant['name'])
                value=variant['suggested_price_cents'] if variant['suggested_price_cents'] is not None else product['suggested_price_cents']
                price.setText('' if value is None else decimal_cents(value))
            self.changed()
        combo.currentIndexChanged.connect(selected)
        for field in (description,quantity,price): field.textChanged.connect(self.changed)
        fulfillment.currentIndexChanged.connect(self.changed)
        self.changed()

    def remove_item(self,item):
        self.item_rows.remove(item); self.form.removeRow(item['widget']); self.changed()

    def choose_files(self,item):
        paths,_=QFileDialog.getOpenFileNames(self,'Referência / projeto original','','Fotos e projetos (*.png *.jpg *.jpeg *.stl *.3mf)')
        if paths:
            item['files']=list(dict.fromkeys(item['files']+paths)); item['file_label'].setText(', '.join(Path(p).name for p in item['files'])); self.changed()

    def items(self):
        return [{'variant_id':r['combo'].currentData(),'description':r['description'].text(),'quantity':r['quantity'].text(),
                 'unit_price':r['price'].text(),'fulfillment':r['fulfillment'].currentData(),'files':r['files']} for r in self.item_rows]

    def changed(self,*args):
        if not self.loading and not self.done_saving: self.timer.start()

    def save_draft(self):
        if self.done_saving: return
        data={'fields':self.values(),'items':self.items()}
        if self.kind=='order':
            data['installments_raw']=[[self.installments.listing.item(i,j).text() if self.installments.listing.item(i,j) else '' for j in range(2)] for i in range(self.installments.listing.rowCount())]
        self.sales.storage.save_draft('sales_'+self.kind,json.dumps(data,ensure_ascii=False))
        self.draft_label.setText('Rascunho salvo; orçamento/pedido ainda não confirmado.')

    def restore_draft(self):
        raw=self.sales.storage.load_draft('sales_'+self.kind)
        if not raw: return
        try:
            data=json.loads(raw)
            for key,value in data['fields'].items():
                if key not in self.fields: continue
                field=self.fields[key]
                if isinstance(field,QComboBox): field.setCurrentIndex(field.findData(value))
                else: field.setText(str(value or ''))
            for item in data['items']: self.add_item(item)
            if self.kind=='order':
                for amount,due in data.get('installments_raw',[]):self.installments.add(amount,due)
        except (ValueError,KeyError,TypeError):
            self.draft_label.setText('Rascunho incompatível; complete um novo registro.')

    def reject(self):
        self.timer.stop(); self.save_draft(); self.done_saving=True; super().reject()

    def persist(self):
        data=self.values()
        if data['client_id'] is None: raise ValueError('Cadastre e selecione um cliente.')
        items=self.items()
        if self.kind=='quote':
            self.saved_id=self.sales.create_quote(data['client_id'],items,data['freight'],date_iso(data['valid_until']),data['notes'],self.operation_key)
        else:
            prepared=self.sales.prepare_items(items)
            total=cents(data['freight'])+sum(row['total_cents'] for row in prepared)
            plan=self.installments.values() if self.installments.listing.rowCount() else plan_with_deposit(self.sales,total,data['installment_count'],date_iso(data['first_due']),data['deposit'])
            deposit=cents(data['deposit'],'Entrada')
            with self.sales.event():
                self.saved_id=self.sales.create_order(data['client_id'],items,data['freight'],date_iso(data['due_on']),data['notes'],plan,self.operation_key)
                if deposit:
                    self.sales.receive_payment(self.saved_id,data['deposit'],data['deposit_method'],data['deposit_fee'],operation_key='deposit-'+self.operation_key)
        self.timer.stop(); self.done_saving=True; self.sales.storage.save_draft('sales_'+self.kind,'')


class ApproveDialog(FormDialog):
    def __init__(self,sales,quote,parent=None):
        super().__init__('Aprovar orçamento e criar pedido sem redigitar',parent)
        self.sales,self.quote=sales,quote
        self.key=uuid.uuid4().hex
        self.line('due_on','Prazo de entrega','','DD/MM/AAAA; opcional')
        self.line('count','Parcelas do saldo (sem entrada)','1'); self.line('first_due','Primeiro vencimento','','DD/MM/AAAA; opcional')
        self.line('deposit','Entrada efetivamente recebida (R$)','0')
        self.combo('method','Meio da entrada',PAYMENT_METHODS,'pix'); self.line('fee','Taxa (R$)','0')
        self.installments=InstallmentEditor(self); self.form.addRow(self.installments)
        prepare=QPushButton('Gerar parcelas editáveis'); prepare.clicked.connect(self.prepare_plan); self.form.addRow(prepare)
    def prepare_plan(self):
        try:
            values=self.values(); row=self.sales.get('quotes',self.quote)
            self.installments.fill(plan_with_deposit(self.sales,row['total_cents'],values['count'],date_iso(values['first_due']),values['deposit']))
        except ValueError as error:self.error.setText(str(error))
    def persist(self):
        values=self.values(); row=self.sales.get('quotes',self.quote)
        plan=self.installments.values() if self.installments.listing.rowCount() else plan_with_deposit(self.sales,row['total_cents'],values['count'],date_iso(values['first_due']),values['deposit'])
        with self.sales.event():
            self.saved_id=self.sales.approve_quote(self.quote,date_iso(values['due_on']),plan)
            if cents(values['deposit']): self.sales.receive_payment(self.saved_id,values['deposit'],values['method'],values['fee'],operation_key=self.key)


class PaymentDialog(FormDialog):
    def __init__(self,sales,order,parent=None):
        super().__init__('Registrar recebimento efetivo',parent)
        self.sales,self.order=sales,order; self.key=uuid.uuid4().hex
        finance=sales.financial(order); record=sales.get('orders',order)
        self.form.addRow(QLabel('Saldo: '+currency(finance['balance'])+' • Crédito disponível do cliente: '+currency(sales.credit_balance(record['client_id']))))
        self.line('amount','Valor pago/aplicado (R$)',decimal_cents(finance['balance']))
        self.combo('method','Forma de pagamento',PAYMENT_METHODS,'pix')
        self.line('fee','Taxa de pagamento (R$)','0')
        self.line('paid_on','Data efetiva',date.today().strftime('%d/%m/%Y'))
    def persist(self):
        data=self.values()
        self.saved_id=self.sales.receive_payment(self.order,data['amount'],data['method'],data['fee'],date_iso(data['paid_on']),self.key)


class CancelDialog(FormDialog):
    def __init__(self,sales,order,parent=None):
        super().__init__('Cancelar pedido • preservar histórico e custos',parent)
        self.sales,self.order=sales,order; self.key=uuid.uuid4().hex
        finance=sales.financial(order)
        self.form.addRow(QLabel('Peças já enviadas/entregues permanecem fora do estoque até retorno físico confirmado.'))
        self.form.addRow(QLabel('Pagamentos/créditos aplicados: '+currency(finance['paid'])+'\nReembolso + crédito futuro + retenção devem somar esse valor.'))
        self.line('reason','Motivo e justificativa financeira *')
        self.line('refund','Reembolso em dinheiro (R$)',decimal_cents(finance['cash_received']))
        self.line('future_credit','Crédito para próxima compra (R$)',decimal_cents(finance['credit_applied']))
        self.line('retained','Retenção justificada (R$)','0')
        self.combo('refund_method','Meio de reembolso',{k:v for k,v in PAYMENT_METHODS.items() if k!='customer_credit'},'pix')
        self.line('refund_on','Data do reembolso',date.today().strftime('%d/%m/%Y'))
    def persist(self):
        data=self.values(); data['refund_on']=date_iso(data['refund_on'])
        if QMessageBox.question(self,'Confirmar cancelamento','Cancelar definitivamente? Reservas serão liberadas; custos e documentos anteriores serão preservados.',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:
            raise ValueError('Cancelamento não confirmado.')
        self.saved_id=self.sales.cancel(self.order,**data,operation_key=self.key)


class DeliveryDialog(FormDialog):
    def __init__(self,sales,order,parent=None):
        super().__init__('Registrar envio / entrega real',parent)
        self.sales,self.order=sales,order; self.proof=None
        previous=sales.delivery(order)
        self.combo('action','Etapa',{'send':'Registrar envio','deliver':'Registrar entrega / retirada'},'deliver' if previous['state']=='sent' else 'send')
        self.combo('mode','Modalidade',{'pickup':'Retirada presencial','shipping':'Envio por transportadora'},previous['mode'])
        self.line('carrier','Transportadora',previous['carrier']); self.line('tracking','Código de rastreio',previous['tracking'])
        self.line('occurred_on','Data efetiva',date.today().strftime('%d/%m/%Y'))
        self.proof_label=QLabel('Comprovante opcional não selecionado'); self.form.addRow(self.proof_label)
        chooser=QPushButton('Selecionar comprovante PDF / foto'); chooser.clicked.connect(self.choose_proof); self.form.addRow(chooser)
        self.form.addRow(QLabel('Todos os itens precisam de peças disponíveis reservadas antes da saída.\nA saída baixa o estoque uma vez; pagamento pode continuar pendente.'))
    def choose_proof(self):
        path,_=QFileDialog.getOpenFileName(self,'Comprovante de entrega','','Comprovante (*.pdf *.png *.jpg *.jpeg)')
        if path: self.proof=path; self.proof_label.setText(Path(path).name)
    def persist(self):
        data=self.values(); data['occurred_on']=date_iso(data['occurred_on'])
        self.sales.deliver(self.order,**data,proof=self.proof)


class ReserveOrderItemDialog(FormDialog):
    def __init__(self,sales,item,parent=None):
        super().__init__('Vincular peças disponíveis ao item do pedido',parent)
        self.sales,self.item=sales,item
        row=sales.get('order_items',item)
        choices={v['id']:v['code']+' • '+v['product_name']+' / '+v['name'] for v in sales.products.all_variants()}
        self.combo('variant_id','Variante física para atendimento',choices,row['variant_id'] if row['variant_id'] else next(iter(choices),None))
        if row['variant_id'] is not None: self.fields['variant_id'].setEnabled(False)
        self.form.addRow(QLabel('Não altera itens, quantidades ou preços aprovados. Personalizados recebem apenas o vínculo operacional para atendimento.'))
    def persist(self):
        self.saved_id=self.sales.reserve_item(self.item,self.values()['variant_id'])


class LinkCalculationDialog(FormDialog):
    def __init__(self,sales,item,parent=None):
        super().__init__('Acompanhar custos / produção pelo cálculo existente',parent)
        self.sales,self.item=sales,item
        choices={r['id']:f"#{r['id']} • {r['title']}" for r in Catalog(sales.storage).calculations()}
        self.combo('calculation_id','Cálculo previsto/confirmado',choices,next(iter(choices),None))
        self.form.addRow(QLabel('OPs, fila e inspeção formal estão disponíveis em Produção.\nO vínculo mantém os custos incorridos após cancelamento.'))
    def persist(self):
        identifier=self.values()['calculation_id']
        if identifier is None: raise ValueError('Crie primeiro o cálculo na aba Precificação.')
        self.sales.link_calculation(self.item,identifier)


class ReturnDialog(FormDialog):
    def __init__(self,sales,order,parent=None):
        super().__init__('Registrar peças efetivamente devolvidas',parent)
        self.sales,self.order=sales,order; self.key=uuid.uuid4().hex
        self.choices=QListWidget(); self.choices.setSelectionMode(QAbstractItemView.MultiSelection)
        for piece in sales.returnable_pieces(order):
            item=QListWidgetItem('Peça #'+str(piece['id'])+' • condição anterior: '+piece['condition']); item.setData(Qt.UserRole,piece['id']); self.choices.addItem(item)
        self.form.addRow('Selecione apenas peças que chegaram',self.choices)
        self.line('condition','Condição real / justificativa *')
        self.form.addRow(QLabel('Retorno mantém o custo existente e exige nova verificação antes de ficar disponível.'))
    def persist(self):
        from PySide6.QtCore import Qt
        self.sales.return_cancelled_pieces(self.order,[item.data(Qt.UserRole) for item in self.choices.selectedItems()],self.values()['condition'],self.key)


class OrderDetails(QDialog):
    def __init__(self,sales,order,parent=None):
        super().__init__(parent)
        self.sales,self.order=sales,order
        self.setWindowTitle('Pedido • detalhes e histórico'); self.resize(1000,730)
        box=QVBoxLayout(self); self.info=QLabel(); self.info.setWordWrap(True); box.addWidget(self.info)
        self.tabs=QTabWidget(); box.addWidget(self.tabs)
        self.item_table=table(['ID','Descrição','Qtd.','Preço unitário','Total','Estoque / produção']); item_page=QWidget(); ib=QVBoxLayout(item_page); ib.addWidget(self.item_table)
        controls=QHBoxLayout(); button('Reservar peças prontas',self.reserve_item,controls); button('Liberar reserva',self.release_item,controls); button('Vincular cálculo',self.link_calculation,controls); ib.addLayout(controls)
        self.tabs.addTab(item_page,'Itens e atendimento')
        self.payment_table=table(['ID','Data','Meio','Valor pago','Taxa','Líquido em caixa']); pay_page=QWidget(); pb=QVBoxLayout(pay_page); pb.addWidget(self.payment_table)
        button('Registrar pagamento / aplicar crédito',self.payment,pb); button('Ver alocação do pagamento selecionado',self.payment_allocation,pb); self.tabs.addTab(pay_page,'Pagamentos')
        self.installment_table=table(['Parcela ID','Vencimento','Previsto','Aplicado','Saldo','Situação']); self.tabs.addTab(self.installment_table,'Parcelas')
        self.documents_table=table(['ID','Versão','Emissão','Arquivo']); docs=QWidget(); db=QVBoxLayout(docs); db.addWidget(self.documents_table)
        controls=QHBoxLayout(); button('Abrir PDF selecionado',self.open_document,controls); button('Emitir nova versão',self.emit_document,controls); db.addLayout(controls); self.tabs.addTab(docs,'Comprovantes')
        self.attachment_table=table(['ID','Tipo','Arquivo original','Item']); attachments=QWidget(); ab=QVBoxLayout(attachments); ab.addWidget(self.attachment_table); button('Abrir anexo original',self.open_attachment,ab); self.tabs.addTab(attachments,'Anexos')
        bottom=QHBoxLayout(); button('Registrar envio / entrega',self.deliver,bottom); button('Cancelar pedido',self.cancel,bottom); button('Retorno físico após cancelamento',self.return_pieces,bottom); box.addLayout(bottom)
        self.refresh()
    def refresh(self):
        order=self.sales.get('orders',self.order); client=json.loads(order['client_snapshot']); f=self.sales.financial(self.order); delivery=self.sales.delivery(self.order)
        self.info.setText(order['code']+' • '+client['name']+' • '+('Cancelado' if order['state']=='cancelled' else 'Aprovado')+'\nTotal: '+currency(f['total'])+' • Recebido bruto: '+currency(f['cash_received'])+' • Crédito aplicado: '+currency(f['credit_applied'])+' • Líquido recebido: '+currency(f['net_received'])+' • Saldo: '+currency(f['balance'])+'\nEntrega: '+DELIVERY_STATES[delivery['state']]+' • Rastreamento: '+(delivery['tracking'] or '—')+' • Prazo: '+(date_br(order['due_on']) or 'não informado'))
        if order['state']=='cancelled':self.info.setText(self.info.text()+'\nReembolso: '+currency(f['refunded'])+' • Crédito futuro: '+currency(f['credited'])+' • Retenção justificada: '+currency(f['retained']))
        self.item_rows=self.sales.items(self.order)
        rows=[]
        for item in self.item_rows:
            links=self.sales.db.execute('SELECT c.id,c.actual FROM order_item_calculations l JOIN calculations c ON c.id=l.calculation_id WHERE l.item_id=?',(item['id'],)).fetchall()
            label='Sem peças reservadas'
            if item['reservation_id']:
                reservation=self.sales.inventory.get('reservations',item['reservation_id'])
                label='Reserva #'+str(item['reservation_id'])+' ('+{'reserved':'reservada','released':'liberada','issued':'baixada'}[reservation['state']]+')'
            from .production import STATES
            ops=self.sales.db.execute('SELECT code,state FROM production_orders WHERE item_id=? ORDER BY id',(item['id'],)).fetchall()
            if ops:label+=' • '+', '.join(op['code']+' '+STATES[op['state']] for op in ops)
            if links: label+=' • '+', '.join('cálculo #'+str(c['id'])+(' confirmado' if c['actual'] else ' previsto') for c in links)
            rows.append([item['id'],item['description'],item['quantity'],currency(item['unit_price_cents']),currency(item['total_cents']),label])
        fill_table(self.item_table,rows)
        self.payment_rows=self.sales.payments(self.order)
        fill_table(self.payment_table,[[r['id'],date_br(r['paid_on']),PAYMENT_METHODS[r['method']],currency(r['amount_cents']),currency(r['fee_cents']),currency(r['net_cents'])] for r in self.payment_rows])
        fill_table(self.installment_table,[[r['id'],date_br(r['due_on']) or 'Sem vencimento',currency(r['amount_cents']),currency(r['received_cents']),currency(r['balance_cents']),INSTALLMENT_STATES[r['status']]] for r in self.sales.installment_status(self.order)])
        self.document_rows=self.sales.documents(order_id=self.order)
        fill_table(self.documents_table,[[r['id'],r['version'],datetime.fromisoformat(r['created_at']).astimezone().strftime('%d/%m/%Y %H:%M'),Path(r['path']).name] for r in self.document_rows])
        self.attachment_rows=self.sales.attachments(self.order)
        fill_table(self.attachment_table,[[r['id'],'Comprovante de entrega' if r['kind']=='delivery' else 'Referência/projeto',r['original_name'],r['item_id'] or '—'] for r in self.attachment_rows])
    def selected_item(self):
        index=self.item_table.currentRow()
        if index<0: QMessageBox.information(self,'Selecione um item','Selecione uma linha nos itens.'); return None
        return self.item_rows[index]['id']
    def reserve_item(self):
        item=self.selected_item()
        if item is not None and ReserveOrderItemDialog(self.sales,item,self).exec()==QDialog.Accepted: self.refresh()
    def release_item(self):
        item=self.selected_item()
        if item is None: return
        reason,ok=QInputDialog.getText(self,'Liberar reserva do pedido','Justificativa obrigatória:')
        if ok:
            try: self.sales.release_item(item,reason); self.refresh()
            except ValueError as error: QMessageBox.warning(self,'Operação não concluída',str(error))
    def link_calculation(self):
        item=self.selected_item()
        if item is not None and LinkCalculationDialog(self.sales,item,self).exec()==QDialog.Accepted: self.refresh()
    def payment(self):
        if PaymentDialog(self.sales,self.order,self).exec()==QDialog.Accepted: self.refresh()
    def payment_allocation(self):
        index=self.payment_table.currentRow()
        if index<0:return
        payment=self.payment_rows[index]
        rows=self.sales.db.execute('SELECT a.amount_cents,i.description FROM payment_allocations a LEFT JOIN order_items i ON i.id=a.item_id WHERE payment_id=? ORDER BY a.id',(payment['id'],)).fetchall()
        lines=['Alocação aos itens mais antigos; depois frete:']
        lines.extend((r['description'] or 'Frete')+' • '+currency(r['amount_cents']) for r in rows)
        lines.append('Parcelas atendidas:')
        installments=self.sales.db.execute('SELECT a.amount_cents,i.id,i.due_on FROM installment_allocations a JOIN installments i ON i.id=a.installment_id WHERE payment_id=? ORDER BY i.id',(payment['id'],)).fetchall()
        lines.extend('Parcela #'+str(r['id'])+' • '+(date_br(r['due_on']) or 'sem vencimento')+' • '+currency(r['amount_cents']) for r in installments)
        QMessageBox.information(self,'Rastreabilidade do pagamento','\n'.join(lines))
    def cancel(self):
        if CancelDialog(self.sales,self.order,self).exec()==QDialog.Accepted: self.refresh()
    def deliver(self):
        if DeliveryDialog(self.sales,self.order,self).exec()==QDialog.Accepted: self.refresh()
    def return_pieces(self):
        if ReturnDialog(self.sales,self.order,self).exec()==QDialog.Accepted: self.refresh()
    def emit_document(self):
        try: self.sales.emit_order(self.order); self.refresh()
        except (ValueError,OSError) as error: QMessageBox.warning(self,'Emissão não concluída',str(error))
    def open_document(self):
        index=self.documents_table.currentRow()
        if index<0: return
        try: open_local(self,self.sales.document_path(self.document_rows[index]['id']))
        except ValueError as error: QMessageBox.warning(self,'Documento',str(error))
    def open_attachment(self):
        index=self.attachment_table.currentRow()
        if index<0: return
        row=self.attachment_rows[index]
        try: open_local(self,owned_path(self.sales.storage,row['path'],row['sha256']))
        except ValueError as error: QMessageBox.warning(self,'Anexo',str(error))


class SalesPage(QWidget):
    def __init__(self,storage,calculator):
        super().__init__(); self.sales=Sales(storage)
        box=QVBoxLayout(self); self.new_sale_button=button('Nova venda',self.sale_new,box); self.tabs=QTabWidget(); box.addWidget(self.tabs)
        clients=QWidget(); cb=QVBoxLayout(clients); controls=QHBoxLayout()
        button('Novo cliente',self.client_new,controls); button('Editar',self.client_edit,controls); button('Histórico',self.client_history,controls); button('Arquivar / restaurar',self.client_archive,controls)
        self.trash=QCheckBox('Lixeira'); self.trash.toggled.connect(self.refresh); controls.addWidget(self.trash); cb.addLayout(controls)
        self.client_table=table(['ID','Nome','Telefone','E-mail','Total vendido','Recebido bruto (menos reembolsos)','A receber','Crédito disponível']); cb.addWidget(self.client_table)
        quotes=QWidget(); qb=QVBoxLayout(quotes); self.quote_table=table(['ID','Código','Cliente','Total','Validade','Situação']); qb.addWidget(self.quote_table)
        controls=QHBoxLayout(); button('Novo orçamento',self.quote_new,controls); button('Aprovar → venda',self.quote_approve,controls); button('Rejeitar',self.quote_reject,controls); button('Abrir PDF',self.quote_pdf,controls); button('Nova versão PDF',self.quote_emit,controls); qb.addLayout(controls)
        orders=QWidget(); ob=QVBoxLayout(orders); self.order_table=table(['ID','Venda','Cliente','Total','Recebido bruto','Crédito aplicado','Saldo','Entrega','Situação','Pagamento']); ob.addWidget(self.order_table)
        controls=QHBoxLayout(); button('Venda sob encomenda',self.order_new,controls); button('Detalhes / pagamentos / entrega',self.order_details,controls); ob.addLayout(controls)
        self.order_table.doubleClicked.connect(lambda index:self.order_details())
        from .finance import Finance
        self.finance=Finance(storage)
        accounts=QTabWidget()
        payable=QWidget();pb=QVBoxLayout(payable)
        self.payables_table=table(['Parcela','Descrição','Categoria','Fornecedor','Previsto','Vencimento','Pago','Saldo','Situação']);pb.addWidget(self.payables_table)
        actions=QHBoxLayout();pb.addLayout(actions)
        button('Nova conta a pagar',self.payable_new,actions);button('Pagar parcela',self.payable_pay,actions)
        receivable=QWidget();rb=QVBoxLayout(receivable)
        self.receivables_table=table(['Venda','Cliente','Vencimento','Previsto','Aplicado','Saldo','Situação']);rb.addWidget(self.receivables_table)
        button('Detalhes / registrar recebimento',self.receivable_details,rb)
        accounts.addTab(payable,'A pagar');accounts.addTab(receivable,'A receber')
        self.tabs.addTab(orders,'Vendas');self.tabs.addTab(quotes,'Orçamentos');self.tabs.addTab(clients,'Clientes');self.tabs.addTab(accounts,'Contas a pagar e receber')
        self.tabs.addTab(calculator,'Precificação'); self.refresh()
    def refresh(self,*args):
        self.client_rows=self.sales.clients(self.trash.isChecked())
        self.client_totals={r['id']:self.sales.client_totals(r['id']) for r in self.client_rows}
        fill_table(self.client_table,[[r['id'],r['name'],r['phone'],r['email'],currency(self.client_totals[r['id']]['sold']),currency(self.client_totals[r['id']]['received']),currency(self.client_totals[r['id']]['receivable']),currency(self.sales.credit_balance(r['id']))] for r in self.client_rows])
        self.quote_rows=self.sales.quotes()
        fill_table(self.quote_table,[[r['id'],r['code'],json.loads(r['client_snapshot'])['name'],currency(r['total_cents']),date_br(r['valid_until']) or 'Sem validade',QUOTE_STATES[r['display_state']]] for r in self.quote_rows])
        self.order_rows=self.sales.orders(); order_values=[]; receivables=[]; self.receivable_order_ids=[]
        for row in self.order_rows:
            customer=json.loads(row['client_snapshot'])['name']; f=self.sales.financial(row['id']); delivery=self.sales.delivery(row['id'])
            order_values.append([row['id'],row['code'],customer,currency(row['total_cents']),currency(f['cash_received']),currency(f['credit_applied']),currency(f['balance']),DELIVERY_STATES[delivery['state']],'Cancelado' if row['state']=='cancelled' else 'Aprovado','Cancelado' if row['state']=='cancelled' else 'Quitado' if f['balance']==0 else 'Parcial' if f['paid'] else 'Pendente'])
            for item in self.sales.installment_status(row['id']):
                self.receivable_order_ids.append(row['id'])
                receivables.append([row['code'],customer,date_br(item['due_on']) or 'Sem vencimento',currency(item['amount_cents']),currency(item['received_cents']),currency(item['balance_cents']),INSTALLMENT_STATES[item['status']]])
        fill_table(self.order_table,order_values); fill_table(self.receivables_table,receivables)
        self.payable_rows=self.finance.payables()
        from .finance import STATUS
        fill_table(self.payables_table,[[r['id'],r['description'],r['category'],r['supplier'],currency(r['amount_cents']),date_br(r['due_on']) or 'Sem vencimento',currency(r['paid_cents']),currency(r['balance_cents']),STATUS[r['status']]] for r in self.payable_rows])
        if getattr(self, '_after_refresh', None): self._after_refresh()
    def selected(self,listing,rows):
        index=listing.currentRow()
        if index<0: QMessageBox.information(self,'Selecione um registro','Selecione uma linha.'); return None
        return rows[index]['id']
    def client_new(self):
        if ClientDialog(self.sales,parent=self).exec()==QDialog.Accepted:self.refresh()
    def client_edit(self):
        identifier=self.selected(self.client_table,self.client_rows)
        if identifier is not None and ClientDialog(self.sales,identifier,self).exec()==QDialog.Accepted:self.refresh()
    def client_archive(self):
        identifier=self.selected(self.client_table,self.client_rows)
        if identifier is None:return
        reason,ok=QInputDialog.getText(self,'Arquivar / restaurar cliente','Justificativa obrigatória; histórico será preservado:')
        if ok:
            try:self.sales.archive_client(identifier,not self.trash.isChecked(),reason);self.refresh()
            except ValueError as error: QMessageBox.warning(self,'Verifique os dados',str(error))
    def client_history(self):
        identifier=self.selected(self.client_table,self.client_rows)
        if identifier is None:return
        dialog=QDialog(self);dialog.setWindowTitle('Histórico do cliente');dialog.resize(700,450);box=QVBoxLayout(dialog);text=QTextEdit();text.setReadOnly(True)
        lines=['Crédito disponível: '+currency(self.sales.credit_balance(identifier))]
        for row in self.sales.orders(identifier):
            f=self.sales.financial(row['id']);lines.append(row['code']+' • '+currency(f['total'])+' • saldo '+currency(f['balance'])+' • '+('Cancelado' if row['state']=='cancelled' else 'Aprovado'))
            lines.extend('  '+date_br(p['paid_on'])+' • '+PAYMENT_METHODS[p['method']]+' • '+currency(p['amount_cents']) for p in self.sales.payments(row['id']))
        text.setPlainText('\n'.join(lines));box.addWidget(text);dialog.exec()
    def sale_new(self):
        from .stock_sale_ui import StockSaleDialog
        dialog=StockSaleDialog(self.sales,self)
        if dialog.exec()==QDialog.Accepted:
            self.refresh();self.tabs.setCurrentIndex(0)
            OrderDetails(self.sales,dialog.saved_id,self).exec();self.refresh()

    def quote_new(self):
        if CommercialDialog(self.sales,'quote',self).exec()==QDialog.Accepted:self.refresh()
    def order_new(self):
        if CommercialDialog(self.sales,'order',self).exec()==QDialog.Accepted:self.refresh()
    def quote_approve(self):
        identifier=self.selected(self.quote_table,self.quote_rows)
        if identifier is not None and ApproveDialog(self.sales,identifier,self).exec()==QDialog.Accepted:self.refresh()
    def quote_reject(self):
        identifier=self.selected(self.quote_table,self.quote_rows)
        if identifier is None:return
        reason,ok=QInputDialog.getText(self,'Rejeitar orçamento','Motivo:')
        if ok:
            try:self.sales.reject_quote(identifier,reason);self.refresh()
            except ValueError as error:QMessageBox.warning(self,'Verifique os dados',str(error))
    def quote_pdf(self):
        identifier=self.selected(self.quote_table,self.quote_rows)
        if identifier is None:return
        rows=self.sales.documents(quote_id=identifier)
        if rows:
            try:open_local(self,self.sales.document_path(rows[0]['id']))
            except ValueError as error:QMessageBox.warning(self,'Documento',str(error))
    def quote_emit(self):
        identifier=self.selected(self.quote_table,self.quote_rows)
        if identifier is not None:
            try:self.sales.emit_quote(identifier);self.refresh()
            except (ValueError,OSError) as error:QMessageBox.warning(self,'Emissão não concluída',str(error))
    def order_details(self):
        identifier=self.selected(self.order_table,self.order_rows)
        if identifier is not None:OrderDetails(self.sales,identifier,self).exec();self.refresh()

    def payable_new(self):
        from .phase6_ui import PayableDialog
        if PayableDialog(self.finance,self).exec()==QDialog.Accepted:self.refresh()

    def payable_pay(self):
        from .phase6_ui import PayDialog
        identifier=self.selected(self.payables_table,self.payable_rows)
        if identifier is not None:
            row=next(r for r in self.payable_rows if r['id']==identifier)
            if PayDialog(self.finance,row,self).exec()==QDialog.Accepted:self.refresh()

    def receivable_details(self):
        index=self.receivables_table.currentRow()
        if index<0:
            QMessageBox.information(self,'Selecione um registro','Selecione uma linha.');return
        OrderDetails(self.sales,self.receivable_order_ids[index],self).exec();self.refresh()
