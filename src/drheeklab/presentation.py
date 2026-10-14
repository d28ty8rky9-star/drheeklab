"""Visual adapters over existing read-only domain reports."""
from datetime import date
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit,QTableWidget,QListView,QFrame,QScrollArea,QBoxLayout
from .visual import MetricStrip,MetricCard,BarChart,action_style,modern_table
from .phase4_ui import currency
from .phase2_ui import minutes_label
from .production import STATES

class ModernPresentation:
    def __init__(self,window):
        self.window=window;self.strips={}
        pages={1:window.sales_page,2:window.production_page,3:window.stock_page,4:window.finance_page}
        titles={1:['Vendido no mês','Recebido líquido no mês','A receber • total','Pedidos em andamento'],2:list(STATES.values()),3:['Carretéis cadastrados','Filamento baixo','Peças reservadas','Peças disponíveis'],4:['Vendido','Recebido líquido','A receber','Resultado gerencial']}
        for index,page in pages.items():
            strip=MetricStrip(titles[index]);page.layout().insertWidget(0,strip);self.strips[index]=strip
            page._after_refresh=lambda i=index:self.refresh(i)
        home=window.pages.widget(0).widget();layout=home.layout()
        # Keep notes, imported official logo and all shortcuts.
        layout.itemAt(1).widget().setText('Visão financeira do mês e acompanhamento da produção. Valores do ambiente ativo.')
        window.business_summary.hide()
        shortcuts=QHBoxLayout()
        for button in home.findChildren(QPushButton):
            layout.removeWidget(button);shortcuts.addWidget(button)
        layout.insertLayout(2,shortcuts)
        self.home_strip=MetricStrip(titles[1]);layout.insertWidget(2,self.home_strip)
        self.home_chart=BarChart('Vendas e recebimentos • mês atual');layout.insertWidget(3,self.home_chart)
        self.production_strip=MetricStrip(titles[2]);layout.insertWidget(4,self.production_strip)
        self.finance_extra=MetricStrip(['Despesas pagas','A pagar','Caixa no período','Saldo final']);window.finance_page.layout().insertWidget(1,self.finance_extra)
        self.finance_chart=BarChart('Vendas e caixa • período selecionado');window.finance_page.layout().insertWidget(1,self.finance_chart)
        # A view switch keeps the same selected product and handlers.
        products=window.products_page
        products.gallery.setWordWrap(True);products.gallery.setTextElideMode(Qt.ElideNone)
        from PySide6.QtCore import QSize
        products.gallery.setGridSize(QSize(245,215))
        products.gallery.setSpacing(8);products.gallery.setMinimumHeight(220)
        from .phase2_ui import table
        self.product_table=table(['Código','Peça','Categoria','Preço','Valor de produção (demonstrativo)'])
        self.product_table.hide();products.layout().insertWidget(3,self.product_table)
        self.product_table.itemSelectionChanged.connect(lambda:self.select_table_product(products))
        products._after_refresh=lambda:self.sync_product_table(products)
        self.sync_product_table(products)
        switch=QPushButton('Alternar cartões / tabela');switch.clicked.connect(lambda:self.toggle_products(products));products.layout().insertWidget(1,switch)
        for button in products.findChildren(QPushButton):
            if button.text()=='Novo produto':button.setText('Nova peça')
        # Printer cards supplement the original editable table and maintenance history.
        self.printer_cards=QWidget();self.printer_cards.setLayout(QHBoxLayout())
        wrapper=QScrollArea();wrapper.setWidgetResizable(True);wrapper.setWidget(self.printer_cards);wrapper.setMaximumHeight(195)
        window.printers_page.layout().insertWidget(0,wrapper)
        window.printers_page._after_refresh=lambda:self.refresh(5)
        # Filter hides only display rows: domain row indices and selections remain intact.
        self.filters=[]
        for page in (window.sales_page,window.production_page,window.stock_page,window.finance_page,window.printers_page):
            for table in page.findChildren(QTableWidget):
                box=table.parentWidget().layout()
                if not isinstance(box,QBoxLayout):continue
                search=QLineEdit();search.setPlaceholderText('Filtrar esta tabela…');search.setClearButtonEnabled(True)
                position=box.indexOf(table)
                if position>=0:
                    box.insertWidget(position,search);self.filters.append((search,table))
                    search.textChanged.connect(lambda text,t=table:self.filter_table(t,text))
        window.low_alert.setObjectName('alert')
        for button in window.findChildren(QPushButton):action_style(button)
        for table in window.findChildren(QTableWidget):modern_table(table)
        self.refresh(5)
        # Scroll the content at smaller window sizes without clipping actions.
        for page in (window.sales_page,window.production_page,window.products_page,window.stock_page,window.finance_page,window.printers_page):
            body=QWidget();body.setLayout(page.layout())
            wrapper=QScrollArea();wrapper.setWidgetResizable(True);wrapper.setWidget(body)
            outer=QVBoxLayout(page);outer.setContentsMargins(0,0,0,0);outer.addWidget(wrapper)

    def sync_product_table(self,page):
        from .phase2_ui import fill_table
        from .products import CATEGORIES
        rows=page.products.search(page.search.text(),page.category.currentData(),page.trash.isChecked())
        self.product_table.blockSignals(True)
        fill_table(self.product_table,[(r['code'],r['name'],CATEGORIES.get(r['category'],r['category']),currency(r['suggested_price_cents']) if r['suggested_price_cents'] is not None else 'Não informado',page.products.production_cost_label(r['id'])) for r in rows])
        self.product_ids=[r['id'] for r in rows]
        selected=page.selected_product(False)
        self.product_table.clearSelection();self.product_table.setCurrentCell(-1,-1)
        if selected in self.product_ids:self.product_table.selectRow(self.product_ids.index(selected))
        self.product_table.blockSignals(False)
    def select_table_product(self,page):
        row=self.product_table.currentRow()
        if 0<=row<len(self.product_ids):page.select_product(self.product_ids[row])
    def toggle_products(self,page):
        cards=not page.gallery.isHidden()
        self.sync_product_table(page)
        page.gallery.setVisible(not cards);self.product_table.setVisible(cards)
    @staticmethod
    def filter_table(table,text):
        text=text.casefold()
        for row in range(table.rowCount()):
            hidden=not any(text in table.item(row,col).text().casefold() for col in range(table.columnCount()) if table.item(row,col))
            table.setRowHidden(row,hidden)
            if hidden and table.currentRow()==row:
                table.clearSelection();table.setCurrentCell(-1,-1)

    def refresh(self,index):
        w=self.window
        if index in (0,1):
            m=w.sales_page.sales.indicators();values=[currency(m['sold']),currency(m['net_received']),currency(m['receivable']),m['active_orders']]
            self.strips[1].set_values(values);self.home_strip.set_values(values)
            self.home_chart.set_values([('Vendido',m['sold'],values[0]),('Recebido líquido',m['net_received'],values[1])])
        if index in (0,2):
            rows=w.production_page.production.queue();values=[sum(r['state']==state for r in rows) for state in STATES]
            self.strips[2].set_values(values);self.production_strip.set_values(values)
        if index==3:
            rows=w.stock_page.inventory.summary()
            self.strips[3].set_values([len(w.filaments_page.catalog.rows('filaments')),len(w.filaments_page.catalog.low_filaments()),sum(r['reserved'] for r in rows),sum(r['available'] for r in rows)])
        if index==3:
            m=w.finance_page.report_data['metrics'];self.finance_extra.set_values([currency(m[k]) for k in ('expenses_paid_cents','payable_cents','cash_flow_cents','cash_closing_cents')]);self.strips[4].set_values([currency(m[k]) for k in ('sold_cents','received_net_cents','receivable_cents','commercial_result_cents')])
            self.finance_chart.set_values([(label,m[key],currency(m[key])) for label,key in [('Vendido','sold_cents'),('Recebido líquido','received_net_cents'),('Despesas pagas','expenses_paid_cents')]])
        if index==4:
            box=self.printer_cards.layout()
            while box.count():
                widget=box.takeAt(0).widget();widget.hide();widget.deleteLater()
            for row in w.printers_page.rows:
                from .catalog import PRINTER_STATES
                from .pricing import hourly_cost,brl
                card=MetricCard(row['identifier'],PRINTER_STATES[row['status']],row['manufacturer']+' '+row['model']+'\n'+minutes_label(row['accumulated_minutes'])+' • '+brl(hourly_cost(row))+'/h',accent='blue')
                select=QPushButton('Selecionar impressora');select.clicked.connect(lambda checked=False,i=w.printers_page.rows.index(row):w.printers_page.table.selectRow(i));action_style(select);card.layout().addWidget(select);box.addWidget(card)
            if not box.count():box.addWidget(QLabel('Nenhuma impressora cadastrada. Use Nova impressora para começar.'))
        for search,table in self.filters:self.filter_table(table,search.text())
