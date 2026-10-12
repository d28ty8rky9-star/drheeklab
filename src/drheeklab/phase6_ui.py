"""Offline finance: expenses, actual payments, owner funding and reports."""
from datetime import date
from decimal import Decimal
import json
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QComboBox,QPushButton,QTabWidget,QMessageBox,QFileDialog,QTextEdit,QDialog
from .finance import Finance,TREATMENTS,ENTRY_KINDS,STATUS
from .finance_exports import export_csv,export_excel,NAMES
from .phase2_ui import FormDialog,button,table,fill_table,date_iso,date_br,scroll
from .phase4_ui import InstallmentEditor,currency,open_local
from .sales import Sales,PAYMENT_METHODS
from .products import Products
from .catalog import Catalog
from .pricing import cents


class PayableDialog(FormDialog):
    def __init__(self,finance,parent=None):
        super().__init__('Nova conta a pagar / despesa',parent);self.finance=finance
        self.line('description','Descrição *');choices={r['id']:r['name'] for r in finance.categories()};self.combo('category','Categoria *',choices,next(iter(choices),None))
        self.line('supplier','Fornecedor');self.line('amount','Valor total (R$)');self.line('incurred','Data da obrigação',date.today().strftime('%d/%m/%Y'))
        self.line('count','Número de parcelas',1);self.line('due','Primeiro vencimento','','DD/MM/AAAA; vazio = sem vencimento')
        self.installments=InstallmentEditor(self);self.form.addRow(self.installments);generate=QPushButton('Distribuir parcelas — valores/datas editáveis');generate.clicked.connect(self.generate);self.form.addRow(generate)
        note=QLabel('Cadastrar a conta não registra pagamento. Energia/manutenção apropriadas e compras de estoque têm tratamento separado do custo de produção.');note.setWordWrap(True);self.form.addRow(note)
    def generate(self):
        try:self.installments.fill(Sales.split_installments(cents(self.fields['amount'].text()),self.fields['count'].text(),date_iso(self.fields['due'].text())))
        except ValueError as err:self.error.setText(str(err))
    def persist(self):
        v=self.values();plan=self.installments.values() if self.installments.listing.rowCount() else None
        self.saved_id=self.finance.create_payable(v['description'],v['category'],v['amount'],v['supplier'],date_iso(v['incurred']),plan,v['count'],date_iso(v['due']))


def proof_field(dialog):
    field=dialog.line('proof','Comprovante (opcional)');field.setReadOnly(True);choose=QPushButton('Selecionar PDF / foto')
    def select():
        path,_=QFileDialog.getOpenFileName(dialog,'Comprovante','','Comprovantes (*.pdf *.png *.jpg *.jpeg)')
        if path:field.setText(path)
    choose.clicked.connect(select);dialog.form.addRow(choose)


class PayDialog(FormDialog):
    def __init__(self,finance,row,parent=None):
        super().__init__('Registrar pagamento efetivo',parent);self.finance=finance;self.row=row
        self.form.addRow(QLabel(row['description']+' • saldo '+currency(row['balance_cents'])))
        self.line('amount','Valor pago da parcela (R$)',str(Decimal(row['balance_cents'])/100));self.line('fee','Taxa adicional efetivamente paga (R$)','0');self.line('paid_on','Data efetiva',date.today().strftime('%d/%m/%Y'))
        self.combo('method','Meio de pagamento',{k:v for k,v in PAYMENT_METHODS.items() if k!='customer_credit'},'pix');proof_field(self)
    def persist(self):
        v=self.values();self.saved_id=self.finance.pay(self.row['id'],v['amount'],v['method'],v['fee'],date_iso(v['paid_on']),v['proof'] or None)


class OwnerDialog(FormDialog):
    def __init__(self,finance,parent=None):
        super().__init__('Aporte, retirada ou saldo inicial',parent);self.finance=finance
        self.combo('kind','Movimentação',ENTRY_KINDS,'capital_in');self.line('amount','Valor (R$)');self.line('description','Descrição / justificativa *');self.line('responsible','Responsável *');self.line('day','Data efetiva',date.today().strftime('%d/%m/%Y'));proof_field(self)
        note=QLabel('Aporte não é venda; retirada não é despesa operacional. Para corrigir, estorne com motivo, preservando o histórico.');note.setWordWrap(True);self.form.addRow(note)
    def persist(self):
        v=self.values();self.saved_id=self.finance.entry(v['kind'],v['amount'],v['description'],v['responsible'],date_iso(v['day']),v['proof'] or None)


class PurchaseDialog(FormDialog):
    def __init__(self,finance,parent=None):
        super().__init__('Comprar filamento — estoque e conta integrados',parent);self.finance=finance
        for key,label,default in [('brand','Marca *',''),('material','Material *','PLA'),('color','Cor *',''),('name','Nome comercial *',''),('purchase','Valor da compra (R$)',''),('initial_grams','Peso recebido (g)','1000'),('reference_per_g','Referência de custo (R$/g)','0.10'),('supplier','Fornecedor',''),('purchased_on','Data de compra',date.today().strftime('%d/%m/%Y')),('count','Parcelas','1'),('due','Primeiro vencimento','')]:self.line(key,label,default)
        choices={r['id']:r['name'] for r in finance.categories() if r['treatment']=='inventory'};self.combo('category','Categoria de compra',choices,next(iter(choices),None))
        self.combo('paid','Pagamento',{False:'Somente registrar obrigação',True:'Já pago integralmente'},False);self.combo('method','Meio de pagamento',{k:v for k,v in PAYMENT_METHODS.items() if k!='customer_credit'},'pix');proof_field(self)
        note=QLabel('Use este fluxo para um carretel novo. Para carretel já cadastrado, vincule a compra existente; isso preserva o saldo.');note.setWordWrap(True);self.form.addRow(note)
    def persist(self):
        v=self.values();data={k:v[k] for k in ('brand','material','color','name','purchase','initial_grams','reference_per_g','supplier')};data['purchased_on']=date_iso(v['purchased_on'])
        self.saved_id,self.spool_id=self.finance.purchase_filament(data,v['category'],count=v['count'],first_due=date_iso(v['due']),paid=v['paid'],method=v['method'],proof=v['proof'] or None)


class MaterialPurchaseDialog(FormDialog):
    def __init__(self,finance,parent=None):
        super().__init__('Compra de material auxiliar',parent);self.finance=finance
        choices={r['id']:r['name']+' • '+r['unit'] for r in CatalogMaterials(finance)};self.combo('material','Material *',choices,next(iter(choices),None))
        categories={r['id']:r['name'] for r in finance.categories() if r['treatment']=='inventory'};self.combo('category','Categoria da compra',categories,2 if 2 in categories else next(iter(categories),None))
        self.line('quantity','Quantidade na unidade cadastrada');self.line('amount','Valor total (R$)');self.line('supplier','Fornecedor');self.line('count','Parcelas',1);self.line('due','Primeiro vencimento');self.combo('paid','Pagamento',{False:'Somente obrigação',True:'Pago integralmente'},False)
    def persist(self):
        v=self.values();self.saved_id=self.finance.purchase_material(v['material'],v['quantity'],v['amount'],v['supplier'],v['count'],date_iso(v['due']),v['paid'],category_id=v['category'])


def CatalogMaterials(finance):
    from .inventory import Inventory
    return Inventory(finance.storage).materials()


class CategoryDialog(FormDialog):
    def __init__(self,finance,identifier=None,parent=None):
        super().__init__('Categoria de despesas',parent);self.finance=finance;self.identifier=identifier;row=finance.get('expense_categories',identifier) if identifier else {}
        self.line('name','Nome *',row.get('name',''));self.combo('treatment','Tratamento',TREATMENTS,row.get('treatment','operating'))
        note=QLabel('Alterações valem para novas contas. Contas anteriores preservam sua classificação. Recursos apropriados na produção não são subtraídos outra vez do resultado comercial.');note.setWordWrap(True);self.form.addRow(note)
    def persist(self):v=self.values();self.saved_id=self.finance.save_category(v['name'],v['treatment'],self.identifier)


class FinancePage(QWidget):
    def __init__(self,storage,parent=None):
        super().__init__(parent);self.finance=Finance(storage);self.storage=storage
        box=QVBoxLayout(self);filters=QHBoxLayout();box.addLayout(filters)
        self.start=QLineEdit(date.today().replace(day=1).strftime('%d/%m/%Y'));self.end=QLineEdit(date.today().strftime('%d/%m/%Y'));self.start.setMaximumWidth(115);self.end.setMaximumWidth(115)
        filters.addWidget(QLabel('De'));filters.addWidget(self.start);filters.addWidget(QLabel('até'));filters.addWidget(self.end);button('Atualizar',self.reload,filters)
        self.client=QComboBox();self.product=QComboBox();self.printer=QComboBox();self.status=QComboBox();self.status.addItem('Todas as situações',None)
        for key,label in STATUS.items():self.status.addItem(label,key)
        f=QHBoxLayout();box.addLayout(f)
        for label,combo in [('Cliente',self.client),('Produto',self.product),('Impressora',self.printer),('Situação',self.status)]:f.addWidget(QLabel(label));f.addWidget(combo,1)
        self.metrics_label=QLabel();self.metrics_label.setWordWrap(True);box.addWidget(self.metrics_label)
        self.tabs=QTabWidget();box.addWidget(self.tabs)
        self.tables={}
        for key,headers in [('sales',['Pedido','Descrição','Produto','Impressora','Peças','Vendido','CPV','Desconto','Custo pendente','Situação']),('cash',['Data','Origem','Meio de pagamento','Descrição','Movimento']),('payables',['Parcela','Descrição','Categoria','Fornecedor','Previsto','Vencimento','Pago','Saldo','Situação']),('receivables',['Pedido','Parcela','Previsto','Vencimento','Recebido','Saldo','Situação']),('production',['Origem','Data','Impressora','Custo','Referência','Perda incluída','Reserva manutenção']),('production_adjustments',['Data','OP','Produto','Impressora','Tratamento','Custo líquido']),('stock_losses',['Data','Tipo','Motivo','Quantidade','Unidade','Custo baixado']),('products',['Produto','Peças','Vendido','CPV','Resultado bruto','Custo pendente']),('printers',['Impressora','Peças','Vendido','CPV','Resultado bruto','Custo pendente'])]:
            page=QWidget();layout=QVBoxLayout(page);listing=table(headers);layout.addWidget(listing);self.tables[key]=listing
            if key=='payables':
                actions=QHBoxLayout();layout.addLayout(actions);button('Nova conta',lambda:self.dialog(PayableDialog(self.finance,self)),actions);button('Pagar parcela',self.pay,actions);button('Cancelar sem pagamento',self.cancel,actions);button('Comprovantes',self.proofs,actions)
                buys=QHBoxLayout();layout.addLayout(buys);button('Comprar filamento',lambda:self.dialog(PurchaseDialog(self.finance,self)),buys);button('Comprar material auxiliar',lambda:self.dialog(MaterialPurchaseDialog(self.finance,self)),buys);button('Vincular carretel existente',self.link_purchase,buys)
            if key=='cash':
                actions=QHBoxLayout();layout.addLayout(actions);button('Aporte / retirada / saldo inicial',lambda:self.dialog(OwnerDialog(self.finance,self)),actions);button('Estornar movimento do proprietário',self.reverse,actions);button('Abrir comprovante do movimento',self.entry_proof,actions)
            if key=='receivables':button('Registrar recebimento do pedido',self.receive,layout)
            self.tabs.addTab(page,NAMES[key])
        self.categories_table=table(['ID','Categoria','Tratamento','Arquivada']);page=QWidget();layout=QVBoxLayout(page);layout.addWidget(self.categories_table);actions=QHBoxLayout();layout.addLayout(actions);button('Nova categoria',lambda:self.dialog(CategoryDialog(self.finance,parent=self)),actions);button('Editar categoria',self.category_edit,actions);button('Arquivar / restaurar',self.category_archive,actions);self.tabs.addTab(page,'Categorias')
        self.details=QTextEdit();self.details.setReadOnly(True);self.tabs.addTab(self.details,'Reconciliação e critérios')
        exports=QHBoxLayout();box.addLayout(exports);self.csv_dataset=QComboBox()
        for key,label in NAMES.items():self.csv_dataset.addItem(label,key)
        self.csv_dataset.setCurrentIndex(self.csv_dataset.findData('cash'));exports.addWidget(self.csv_dataset);button('Exportar CSV',self.csv, exports);button('Exportar Excel completo',self.excel,exports);button('Emitir PDF',self.pdf,exports)
        self.refresh()

    def reload(self):self.act(self.refresh)
    def act(self,fn):
        try:fn()
        except (ValueError,OSError) as err:QMessageBox.warning(self,'Verifique o financeiro',str(err))
    def dialog(self,dialog):
        if dialog.exec():self.refresh()
    def select(self,key):
        index=self.tables[key].currentRow();rows=self.report_data[key]
        if index<0 or index>=len(rows):raise ValueError('Selecione um registro.')
        return rows[index]
    def combo_fill(self,combo,choices):
        old=combo.currentData();combo.clear();combo.addItem('Todos',None)
        for code,label in choices:combo.addItem(label,code)
        combo.setCurrentIndex(max(0,combo.findData(old)))
    def refresh(self):
        sales=Sales(self.storage);products=Products(self.storage);catalog=Catalog(self.storage)
        self.combo_fill(self.client,[(r['id'],r['name']) for r in sales.clients()+sales.clients(True)])
        self.combo_fill(self.product,[(r['id'],r['name']) for r in products.search()+products.search(archived=True)])
        self.combo_fill(self.printer,[(r['id'],r['identifier']) for r in catalog.rows('printers')+catalog.rows('printers',True)])
        r=self.finance.report(date_iso(self.start.text()),date_iso(self.end.text()),self.client.currentData(),self.product.currentData(),self.printer.currentData(),self.status.currentData());self.report_data=r;m=r['metrics']
        self.metrics_label.setText('Vendido: '+currency(m['sold_cents'])+' • CPV: '+currency(m['cost_of_sales_cents'])+' • Resultado gerencial: '+currency(m['commercial_result_cents'])+'\nRecebido bruto: '+currency(m['received_gross_cents'])+' • Líquido: '+currency(m['received_net_cents'])+' • A receber: '+currency(m['receivable_cents'])+' • Peças vendidas: '+str(m['pieces_sold'])+' • Ticket: '+(currency(cents(m['ticket_average'])) if m['ticket_average'] else 'sem pedidos')+'\nCaixa consolidado no período: '+currency(m['cash_flow_cents'])+' • Saldo final: '+currency(m['cash_closing_cents'])+' • Despesas pagas consolidadas: '+currency(m['expenses_paid_cents'])+' • A pagar: '+currency(m['payable_cents'])+'\nCustos de baixa pendentes: '+str(m['pending_cost_quantity'])+' peças. Resultado provisório enquanto pendente. Perdas de produção incluídas: '+currency(m['production_loss_included_cents']))
        fill_table(self.tables['sales'],[(x['order'],x['description'],x['product_id'] or 'Personalizado',x['printer_id'] or 'Sem identificação',x['quantity'],currency(x['sales_cents']),currency(x['cost_cents']),currency(x['discount_cents']),x['pending_quantity'],STATUS[x['status']]) for x in r['sales']])
        kinds={'sale_payment':'Recebimento venda','sale_fee':'Taxa da venda','refund':'Reembolso','payable_payment':'Pagamento conta','payable_fee':'Taxa do pagamento',**ENTRY_KINDS}
        fill_table(self.tables['cash'],[(date_br(x['date']),kinds[x['kind']],PAYMENT_METHODS.get(x['method'],''),x['description'],currency(x['amount_cents'])) for x in r['cash']])
        fill_table(self.tables['payables'],[(x['id'],x['description'],x['category'],x['supplier'],currency(x['amount_cents']),date_br(x['due_on']),currency(x['paid_cents']),currency(x['balance_cents']),STATUS[x['status']]) for x in r['payables']])
        fill_table(self.tables['receivables'],[(x['code'],x['id'],currency(x['amount_cents']),date_br(x['due_on']),currency(x['paid_cents']),currency(x['balance_cents']),STATUS[x['status']]) for x in r['receivables']])
        fill_table(self.tables['production'],[(x['source'],date_br(x['date']),x['printer_id'],currency(x['cost_cents']),currency(x['reference_cents']),currency(x['loss_cents']),currency(x['maintenance_reserve_cents'])) for x in r['production']])
        fill_table(self.tables['production_adjustments'],[(date_br(x['date']),x['op'],x['product_id'],x['printer_id'],'Perda da tentativa' if x['kind']=='loss' else 'Absorção no custo das peças',currency(x['amount_cents'])) for x in r['production_adjustments']])
        fill_table(self.tables['stock_losses'],[(date_br(x['occurred_on']),{'piece':'Peça','filament':'Filamento','material':'Material auxiliar'}[x['entity_kind']],x['reason'],str(Decimal(x['quantity_milli'])/1000),x['unit'],currency(x['cost_cents'])) for x in r['stock_losses']])
        for key in ('products','printers'):fill_table(self.tables[key],[(x['id'] or 'Sem identificação',x['quantity'],currency(x['sales_cents']),currency(x['cost_cents']),currency(x['gross_result_cents']),x['pending_quantity']) for x in r[key]])
        self.category_rows=self.finance.categories()+self.finance.categories(True);fill_table(self.categories_table,[(x['id'],x['name'],TREATMENTS[x['treatment']],'Sim' if x['archived'] else 'Não') for x in self.category_rows])
        self.details.setPlainText('RECONCILIAÇÃO: '+('Sem divergências detectadas' if r['reconciliation']['status']=='ok' else '\n'.join(r['reconciliation']['issues']))+'\n\n'+'\n\n'.join(r['notes']))
        if getattr(self, '_after_refresh', None): self._after_refresh()

    def pay(self):self.act(lambda:self.dialog(PayDialog(self.finance,self.select('payables'),self)))
    def cancel(self):
        def run():
            row=self.select('payables');d=FormDialog('Cancelar obrigação sem pagamento',self);d.line('reason','Justificativa *');d.persist=lambda:self.finance.cancel_payable(row['payable_id'],d.values()['reason']);self.dialog(d)
        self.act(run)
    def link_purchase(self):
        def run():
            row=self.select('payables');d=FormDialog('Vincular compra já cadastrada — saldo preservado',self);choices={s['id']:s['name']+' • '+currency(s['purchase_cents']) for s in Catalog(self.storage).rows('filaments')};d.combo('spool','Carretel',choices,next(iter(choices),None));d.persist=lambda:self.finance.link_existing_purchase(row['payable_id'],d.values()['spool']);self.dialog(d)
        self.act(run)
    def proofs(self):
        def run():
            row=self.select('payables');proofs=[dict(x) for x in self.finance.db.execute('SELECT f.* FROM finance_proofs f JOIN payable_payments p ON p.id=f.payment_id JOIN payable_installments i ON i.id=p.installment_id WHERE i.payable_id=?',(row['payable_id'],))]
            if not proofs:raise ValueError('Nenhum comprovante anexado aos pagamentos desta conta.')
            d=FormDialog('Comprovantes da conta',self);d.combo('proof','Comprovante',{x['id']:x['original_name'] for x in proofs},proofs[0]['id']);d.persist=lambda:open_local(self,self.finance.proof_path(d.values()['proof']));d.exec()
        self.act(run)
    def reverse(self):
        def run():
            row=self.select('cash')
            if not row['source'].startswith('entry:'):raise ValueError('Somente movimentos do proprietário são estornados aqui. Pagamentos de vendas e contas preservam seus registros de origem.')
            identifier=int(row['source'].split(':')[1]);d=FormDialog('Estorno do movimento do proprietário',self);d.line('reason','Motivo *');d.line('responsible','Responsável *');d.persist=lambda:self.finance.reverse_entry(identifier,d.values()['reason'],d.values()['responsible']);self.dialog(d)
        self.act(run)
    def entry_proof(self):
        def run():
            row=self.select('cash')
            if not row['source'].startswith('entry:'):raise ValueError('Selecione um movimento do proprietário.')
            proof=self.finance.db.execute('SELECT id FROM finance_proofs WHERE entry_id=?',(int(row['source'].split(':')[1]),)).fetchone()
            if not proof:raise ValueError('Movimento sem comprovante.')
            open_local(self,self.finance.proof_path(proof[0]))
        self.act(run)
    def receive(self):
        from .phase4_ui import PaymentDialog
        self.act(lambda:self.dialog(PaymentDialog(Sales(self.storage),self.select('receivables')['order_id'],self)))
    def category_selected(self):
        index=self.categories_table.currentRow()
        if index<0:raise ValueError('Selecione uma categoria.')
        return self.category_rows[index]
    def category_edit(self):self.act(lambda:self.dialog(CategoryDialog(self.finance,self.category_selected()['id'],self)))
    def category_archive(self):
        def run():
            row=self.category_selected();d=FormDialog('Arquivar/restaurar categoria',self);d.line('reason','Justificativa *');d.persist=lambda:self.finance.archive_category(row['id'],not row['archived'],d.values()['reason']);self.dialog(d)
        self.act(run)
    def csv(self):
        def run():
            self.refresh();path,_=QFileDialog.getSaveFileName(self,'Exportar CSV',str(self.storage.home/'Relatórios'/'financeiro.csv'),'CSV (*.csv)')
            if path:export_csv(self.report_data,path,self.csv_dataset.currentData());QMessageBox.information(self,'Relatório exportado',path)
        self.act(run)
    def excel(self):
        def run():
            self.refresh();path,_=QFileDialog.getSaveFileName(self,'Exportar Excel',str(self.storage.home/'Relatórios'/'financeiro.xlsx'),'Excel (*.xlsx)')
            if path:export_excel(self.report_data,path);QMessageBox.information(self,'Relatório exportado',path)
        self.act(run)

    def pdf(self):
        def run():
            from .documents import Documents
            self.refresh();documents=Documents(self.storage)
            identifier=documents.emit_finance(date_iso(self.start.text()),date_iso(self.end.text()),client_id=self.client.currentData(),product_id=self.product.currentData(),printer_id=self.printer.currentData(),status=self.status.currentData())
            open_local(self,documents.path(identifier))
        self.act(run)
