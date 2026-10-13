"""One workspace: select a catalog piece and create an ordinary production order."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QSplitter,QScrollArea,QLabel,QPushButton,QMessageBox
from .phase5_ui import OrderDialog
from .visual import action_style

class WorkshopPage(QWidget):
    def __init__(self,products,production):
        super().__init__();self.products_page=products;self.production_page=production
        box=QVBoxLayout(self);box.setContentsMargins(0,0,0,0)
        row=QHBoxLayout();self.selection=QLabel('Selecione uma peça no catálogo para produzir.');self.selection.setWordWrap(True);row.addWidget(self.selection,1)
        self.produce_button=QPushButton('Produzir esta peça');action_style(self.produce_button);self.produce_button.clicked.connect(self.produce);row.addWidget(self.produce_button);box.addLayout(row)
        self.details_button=QPushButton('Ficha da peça: variantes, fotos e arquivos');self.details_button.setCheckable(True);self.details_button.toggled.connect(products.tabs.setVisible)
        products.layout().addWidget(self.details_button);products.tabs.hide()
        self.splitter=QSplitter(Qt.Horizontal);self.splitter.addWidget(products);self.splitter.addWidget(production)
        products.setMinimumWidth(320);production.setMinimumWidth(580);self.splitter.setSizes([400,750]);self.splitter.setChildrenCollapsible(False)
        wrapper=QScrollArea();wrapper.setWidgetResizable(True);wrapper.setWidget(self.splitter);box.addWidget(wrapper,1)
        products._selection_changed=self.update_selection
        products.gallery.itemSelectionChanged.connect(self.update_selection)
        products.variants_table.itemSelectionChanged.connect(self.update_selection)
        self.update_selection()

    def update_selection(self):
        identifier=self.products_page.selected_product(False)
        if identifier is None:
            self.selection.setText('Selecione uma peça no catálogo para produzir.');self.produce_button.setEnabled(False);return
        product=self.products_page.products.get('products',identifier)
        self.selection.setText(product['code']+' • '+product['name']);self.produce_button.setEnabled(not product['archived'])

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
        variant=next((v for v in variants if v['id']==selected),variants[0])
        projects=[r for r in p.products.media(identifier,'project') if not r['archived']]
        if not projects:raise ValueError('Esta peça não tem STL/3MF ativo. Importe o arquivo na ficha da peça antes de produzir.')
        project=next((r for r in projects if r['is_preferred']),max(projects,key=lambda r:r['version']))
        dialog=OrderDialog(self.production_page.production,self)
        editor=dialog.editors[0]
        index=next(i for i in range(editor.variant.count()) if editor.variant.itemData(i)[0]==variant['id'] and editor.variant.itemData(i)[1]==identifier)
        editor.variant.setCurrentIndex(index)
        editor.project.setCurrentIndex(editor.project.findData(project['id']))
        if product['printer_id'] is not None:
            index=dialog.fields['printer'].findData(product['printer_id'])
            if index>=0:dialog.fields['printer'].setCurrentIndex(index)
        if product['filament_id'] is not None and editor.filaments:
            index=editor.filaments[0][0].findData(product['filament_id'])
            if index>=0:editor.filaments[0][0].setCurrentIndex(index)
        dialog.fields['parameters'].setText(product['settings'])
        if product['estimated_minutes']>0:dialog.fields['minutes'].setText(str(product['estimated_minutes']))
        return dialog

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
