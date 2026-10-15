"""One new sale form: client, actual stock units, detail and automatic price."""
from decimal import Decimal
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog,QLabel,QPushButton,QHBoxLayout,QVBoxLayout,QWidget,QTabWidget,QTextEdit,QTableWidget,QLineEdit
from .phase2_ui import FormDialog,table,fill_table
from .pricing import brl

class StockSaleDialog(FormDialog):
    def __init__(self,sales,parent=None):
        super().__init__('Nova venda — selecionar peças do Estoque',parent);self.sales=sales;self.resize(1050,850)
        self.combo('client','Cliente *',{None:'Selecione o cliente',**{c['id']:c['name'] for c in sales.clients()}},None)
        client=QPushButton('Novo cliente');client.clicked.connect(self.new_client);self.form.addRow(client)
        self.stock_tabs=QTabWidget();self.form.addRow(self.stock_tabs)
        self.pieces=table(['Marcar','Unidade','Peça / variante','Origem','Custo','Preço sugerido'])
        self.accessories=table(['Marcar','Unidade','Acessório','Custo / preço'])
        for listing in (self.pieces,self.accessories):listing.setSelectionMode(QTableWidget.ExtendedSelection);listing.setMinimumHeight(210)
        for listing,label in ((self.pieces,'Peças disponíveis'),(self.accessories,'Adicionar acessórios')):
            page=QWidget();layout=QVBoxLayout(page);search=QLineEdit();search.setPlaceholderText('Buscar nome, variante ou unidade...');layout.addWidget(search);layout.addWidget(listing)
            search.textChanged.connect(lambda text,t=listing:self.filter_stock(t,text))
            self.stock_tabs.addTab(page,label)
        self.form.addRow(QLabel('Selecione uma ou mais unidades. Produzidas: custo + 100%. Compradas: custo + 30%. Acessórios: custo sem acréscimo.'))
        self.details=QTextEdit();self.details.setReadOnly(True);self.details.setMinimumHeight(150);self.form.addRow('Custos registrados',self.details)
        self.summary=QLabel();self.summary.setWordWrap(True);self.form.addRow(self.summary)
        self.line('actual_total','Valor total da venda (peças + acessórios, R$)','')
        reset=QPushButton('Usar o total sugerido');reset.clicked.connect(self.use_suggested);self.form.addRow(reset)
        self.actual_summary=QLabel();self.actual_summary.setWordWrap(True);self.form.addRow(self.actual_summary)
        self.fields['actual_total'].textChanged.connect(self.update_actual_total)
        self.line('notes','Observações','')
        self.form.addRow(QLabel('Salvar a venda reserva as unidades selecionadas. Registre pagamento e entrega nos detalhes da venda.'))
        self.piece_rows=[];self.accessory_rows=[]
        for row in sales.inventory.pieces():
            if row['state']=='available':
                try:choice=sales.stock_choice(row['id'])
                except ValueError:continue
                (self.accessory_rows if choice['kind']=='accessory' else self.piece_rows).append(choice)
        money=lambda v:brl(Decimal(v)/100)
        fill_table(self.pieces,[('',p['id'],p['product_name']+' / '+p['variant_name'],'Produzida • +100%' if p['kind']=='produced' else 'Comprada • +30%',money(p['unit_cost_cents']),money(p['suggested_cents'])) for p in self.piece_rows])
        fill_table(self.accessories,[('',p['id'],p['product_name'],money(p['unit_cost_cents'])) for p in self.accessory_rows])
        for listing in (self.pieces,self.accessories):
            for row in range(listing.rowCount()):
                item=listing.item(row,0);item.setFlags(Qt.ItemIsEnabled|Qt.ItemIsUserCheckable);item.setCheckState(Qt.Unchecked)
            listing.itemChanged.connect(self.recalculate)
        self.recalculate()

    def filter_stock(self,listing,text):
        for row in range(listing.rowCount()):
            hidden=text.casefold() not in ' '.join(listing.item(row,c).text() for c in range(listing.columnCount())).casefold()
            listing.setRowHidden(row,hidden)
        self.recalculate()

    def selected_ids(self,table,rows):
        return [rows[i]['id'] for i in range(table.rowCount()) if table.item(i,0).checkState()==Qt.Checked]

    def quote(self):
        return self.sales.stock_sale_quote(self.selected_ids(self.pieces,self.piece_rows),self.selected_ids(self.accessories,self.accessory_rows))

    def new_client(self):
        from .phase4_ui import ClientDialog
        dialog=ClientDialog(self.sales,parent=self)
        if dialog.exec()==QDialog.Accepted:
            combo=self.fields['client'];combo.clear();combo.addItem('Selecione o cliente',None)
            for client in self.sales.clients():combo.addItem(client['name'],client['id'])
            combo.setCurrentIndex(combo.findData(dialog.saved_id))

    def use_suggested(self):
        try:self.fields['actual_total'].setText(str(Decimal(self.quote()['suggested_cents'])/100))
        except ValueError as error:self.error.setText(str(error))

    def recalculate(self,*args):
        from .stock_sale import render_stock_cost
        try:
            quote=self.quote();self.summary.setText('Preço mínimo (custos totais): '+brl(Decimal(quote['cost_cents'])/100)+' • Preço sugerido: '+brl(Decimal(quote['suggested_cents'])/100))
            self.details.setPlainText('\n\n'.join(render_stock_cost(p) for p in quote['items']))
            if not self.fields['actual_total'].isModified():self.fields['actual_total'].setText(str(Decimal(quote['suggested_cents'])/100))
            self.update_actual_total()
        except ValueError as error:self.summary.setText(str(error));self.details.clear();self.actual_summary.clear()

    def update_actual_total(self,*args):
        from .pricing import cents
        try:
            quote=self.quote();accessories=sum(p['unit_cost_cents'] for p in quote['items'] if p['kind']=='accessory')
            total=cents(self.fields['actual_total'].text());base=quote['cost_cents']-accessories;profit=total-quote['cost_cents']
            percent=str((Decimal(profit)*100/base).quantize(Decimal('0.01'))).replace('.',',')+'%' if base else 'não calculável (custo das peças zero)'
            self.actual_summary.setText('Total vendido: '+brl(Decimal(total)/100)+' • '+('Lucro bruto: ' if profit>=0 else 'Prejuízo bruto: ')+brl(Decimal(abs(profit))/100)+' • Sobre o custo das peças: '+percent+' • Acessórios pelo custo: '+brl(Decimal(accessories)/100))
        except ValueError:self.actual_summary.setText('Informe um valor total válido.')

    def persist(self):
        v=self.values()
        if v['client'] is None:raise ValueError('Selecione ou cadastre o cliente.')
        from .pricing import cents
        final_total=v['actual_total'] if v['actual_total'].strip() else None
        self.saved_id=self.sales.create_stock_sale(v['client'],self.selected_ids(self.pieces,self.piece_rows),self.selected_ids(self.accessories,self.accessory_rows),final_total,notes=v['notes'])
