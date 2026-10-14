"""One workspace: select a catalog piece and create an ordinary production order."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QSplitter,QScrollArea,QLabel,QPushButton,QMessageBox
from .recipe_ui import RecipeOrderDialog
from .visual import action_style
from .pricing import brl
from decimal import Decimal

class WorkshopPage(QWidget):
    def __init__(self,products,production):
        super().__init__();self.products_page=products;self.production_page=production
        box=QVBoxLayout(self);box.setContentsMargins(0,0,0,0)
        row=QHBoxLayout();self.recipe_button=QPushButton('Ficha de produção / custos');self.recipe_button.clicked.connect(self.edit_recipe);row.addWidget(self.recipe_button);self.selection=QLabel('Selecione uma peça no catálogo para produzir.');self.selection.setWordWrap(True);row.addWidget(self.selection,1)
        self.produce_button=QPushButton('Produzir esta peça');action_style(self.produce_button);self.produce_button.clicked.connect(self.produce);row.addWidget(self.produce_button);box.addLayout(row)
        self.production_value=QLabel('Valor de produção: preencha a ficha da peça.');self.production_value.setWordWrap(True);box.addWidget(self.production_value)
        self.details_button=QPushButton('Ficha da peça: variantes, fotos e arquivos');self.details_button.setCheckable(True);self.details_button.toggled.connect(products.tabs.setVisible)
        products.layout().addWidget(self.details_button);products.tabs.hide()
        self.splitter=QSplitter(Qt.Horizontal);self.splitter.addWidget(products);self.splitter.addWidget(production)
        products.setMinimumWidth(320);production.setMinimumWidth(580);self.splitter.setSizes([400,750]);self.splitter.setChildrenCollapsible(False)
        wrapper=QScrollArea();wrapper.setWidgetResizable(True);wrapper.setWidget(self.splitter);box.addWidget(wrapper,1)
        production.new_order_button.clicked.disconnect()
        production.new_order_button.clicked.connect(self.produce)
        products._selection_changed=self.update_selection
        products.gallery.itemSelectionChanged.connect(self.update_selection)
        products.variants_table.itemSelectionChanged.connect(self.update_selection)
        self.update_selection()

    def update_selection(self):
        identifier=self.products_page.selected_product(False)
        if identifier is None:
            self.selection.setText('Selecione uma peça no catálogo para produzir.');self.produce_button.setEnabled(False);self.production_value.setText('Valor de produção: selecione uma peça.');return
        product=self.products_page.products.get('products',identifier)
        self.selection.setText(product['code']+' • '+product['name'])
        row=self.products_page.variants_table.currentRow()
        selected_archived=0<=row<len(self.products_page.variant_rows) and self.products_page.variant_rows[row]['archived']
        variants=self.products_page.variant_rows
        chosen=variants[row] if 0<=row<len(variants) else next((v for v in variants if not v['archived']),None)
        recipe=self.production_page.production.recipe(chosen['id']) if chosen else None
        self.selection.setText(product['code']+' • '+product['name']+(' • Ficha de produção salva' if recipe else ' • Preencha a ficha de produção'))
        if recipe:
            estimate=recipe['data']['estimate'];cost=estimate.get('acquisition_production_cost')
            self.production_value.setText('Valor de produção: '+brl(Decimal(cost if cost is not None else estimate['total_cost']))+' por peça • '+chosen['name']+' • Demonstrativo; Financeiro somente após conclusão e entrada no Estoque.')
        else:self.production_value.setText('Valor de produção: preencha e salve a ficha desta variante.')
        self.produce_button.setEnabled(not product['archived'] and not selected_archived)

    def prepare_order(self):
        """Prefill a form only; nothing is persisted until its normal validation succeeds."""
        p=self.products_page;identifier=p.selected_product(False)
        if identifier is None:raise ValueError('Selecione uma peça no catálogo.')
        product=p.products.active_product(identifier)
        variants=p.products.variants(identifier)
        variants=[v for v in variants if not v['archived']]
        if not variants:raise ValueError('Cadastre ou restaure uma variante na ficha da peça.')
        row=p.variants_table.currentRow()
        selected=p.variant_rows[row]['id'] if 0<=row<len(p.variant_rows) else None
        if selected is not None and not any(v['id']==selected for v in variants):
            raise ValueError('Selecione uma variante ativa para produzir.')
        variant=next((v for v in variants if v['id']==selected),variants[0])
        projects=[r for r in p.products.media(identifier,'project') if not r['archived']]
        if not projects:raise ValueError('Esta peça não tem STL/3MF ativo. Importe o arquivo na ficha da peça antes de produzir.')
        return RecipeOrderDialog(self.production_page.production,variant['id'],self)

    def edit_recipe(self):
        # Both entry points open the complete piece form; no second cost form.
        self.products_page.edit()

    def produce(self):
        try:dialog=self.prepare_order()
        except ValueError as err:QMessageBox.information(self,'Preparar produção',str(err));return
        if dialog.exec():
            self.production_page.refresh();self.production_page.tabs.setCurrentIndex(0)
            rows=self.production_page.rows
            for i,row in enumerate(rows):
                if row['id']==dialog.saved_id:self.production_page.queue_table.selectRow(i);break

    def refresh(self):
        self.products_page.refresh();self.production_page.refresh();self.update_selection()
