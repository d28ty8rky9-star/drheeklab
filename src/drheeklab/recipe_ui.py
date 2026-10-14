"""Production specification editor and minimal recipe-based OP dialogs."""
from decimal import Decimal
from PySide6.QtWidgets import QLabel,QPushButton
from .phase2_ui import FormDialog
from .phase5_ui import EntryEditor
from .production import PRIORITIES
from .pricing import brl

class RecipeDialog(FormDialog):
    def __init__(self,production,variant_id,parent=None):
        super().__init__('Ficha de produção — dados por peça',parent)
        self.production=production;self.variant_id=variant_id;self.resize(760,700)
        variant=production.products.active_variant(variant_id);product=production.products.active_product(variant['product_id'])
        self.form.addRow(QLabel(product['name']+' / '+variant['name']))
        self.combo('printer','Impressora',{p['id']:p['identifier'] for p in production.catalog.rows('printers') if p['status']=='operational'},product['printer_id'] or 1)
        self.line('minutes','Tempo por peça (min)',product['estimated_minutes'] or 60)
        self.line('parameters','Parâmetros de impressão *',product['settings'])
        self.editor=EntryEditor(production,recipe=True);self.form.addRow(self.editor)
        index=next(i for i in range(self.editor.variant.count()) if self.editor.variant.itemData(i)[0]==variant_id)
        self.editor.variant.setCurrentIndex(index);self.editor.variant.setEnabled(False)
        self.editor.quantity.setText('1');self.editor.quantity.setReadOnly(True)
        self.editor.weight.hide()
        projects=production.products.media(product['id'],'project')
        preferred=next((p for p in projects if p['is_preferred'] and not p['archived']),None)
        if preferred:self.editor.project.setCurrentIndex(self.editor.project.findData(preferred['id']))
        if product['filament_id']:
            combo=self.editor.filaments[0][0];combo.setCurrentIndex(combo.findData(product['filament_id']))
        saved=production.recipe(variant_id)
        if saved:
            data=saved['data'];self.fields['printer'].setCurrentIndex(self.fields['printer'].findData(data['printer_id']))
            self.fields['minutes'].setText(str(data['minutes']));self.fields['parameters'].setText(data['parameters'])
            self.editor.project.setCurrentIndex(self.editor.project.findData(data['project_id']))
            for row in list(self.editor.filaments):self.editor.remove_spool(row)
            for f in data['estimate']['filaments']:
                self.editor.add_spool();combo,grams,_=self.editor.filaments[-1]
                combo.setCurrentIndex(combo.findData(f['id']));grams.setText(str(f['grams']))
            self.editor.aux.setText(str(data['estimate']['auxiliary']))
        self.preview=QLabel();self.preview.setWordWrap(True);self.form.addRow(self.preview)
        estimate=QPushButton('Calcular custo da ficha');estimate.clicked.connect(self.show_estimate);self.form.addRow(estimate)
        self.preview.setText(self.preview.text()+' • Valores por unidade.')
        self.form.addRow(QLabel('Salvar a ficha não movimenta estoque e não registra custo no Financeiro.'))
        self.show_estimate()

    def estimate(self):
        v=self.values();entry=self.editor.value()
        return self.production.catalog.estimate(v['printer'],v['minutes'],entry['filaments'],entry['auxiliary'],1)

    def show_estimate(self):
        try:
            estimate=self.estimate();cost=estimate.get('acquisition_production_cost')
            # The estimate is planning; accounting uses the frozen acquisition
            # parameters when known, otherwise the reference cost.
            if cost is None:
                from .pricing import calculate
                e=self.editor.value();cost=calculate(estimate['printer'],self.values()['minutes'],estimate['filaments'],e['auxiliary'],1,actual=True).get('acquisition_production_cost')
            self.preview.setText('Custo por peça: '+brl(Decimal(cost if cost is not None else estimate['total_cost']))+' • Referência: '+brl(Decimal(estimate['total_cost'])))
        except ValueError as error:self.preview.setText(str(error))

    def persist(self):
        v=self.values();entry=self.editor.value()
        self.production.save_recipe(self.variant_id,v['printer'],entry['project_id'],v['minutes'],entry['filaments'],entry['auxiliary'],v['parameters'])

class RecipeOrderDialog(FormDialog):
    def __init__(self,production,variant_id,parent=None):
        super().__init__('Nova OP — produzir peça cadastrada',parent)
        self.production=production;self.variant_id=variant_id
        recipe=production.recipe(variant_id)
        if not recipe:raise ValueError('Salve os dados em Ficha de produção antes de criar a OP.')
        variant=production.products.active_variant(variant_id);product=production.products.active_product(variant['product_id'])
        self.form.addRow(QLabel(product['name']+' / '+variant['name']))
        self.form.addRow(QLabel('Arquivo, filamento, consumo, tempo e parâmetros serão copiados da ficha salva.'))
        self.line('quantity','Quantidade',1);self.line('responsible','Responsável *')
        self.combo('priority','Prioridade',PRIORITIES,'normal')
        choices={None:'Para estoque'}
        for row in production.db.execute("SELECT i.*,o.code FROM order_items i JOIN orders o ON o.id=i.order_id WHERE o.state='approved' ORDER BY i.id DESC"):
            choices[row['id']]=row['code']+' • '+row['description']
        self.combo('item','Pedido vinculado',choices,None)

    def persist(self):
        v=self.values();self.saved_id=self.production.create_from_recipe(self.variant_id,v['quantity'],v['responsible'],v['priority'],v['item'])

class RecipeConfirmDialog(FormDialog):
    def __init__(self,production,identifier,parent=None):
        super().__init__('Impressão terminada — preparar inspeção',parent)
        self.production=production;self.identifier=identifier
        self.form.addRow(QLabel('Consumo e tempo serão usados conforme a ficha copiada para esta OP.'))
        self.line('failed','Peças perdidas durante a impressão',0)
        self.line('reason','Motivo das perdas (se houver)')
        adjust=QPushButton('Consumo ou tempo diferente da ficha? Ajustar esta tentativa')
        adjust.clicked.connect(self.adjust);self.form.addRow(adjust)
        self.form.addRow(QLabel('As peças só entrarão no Estoque após inspeção com fotos, observações e conclusão da OP.'))

    def adjust(self):
        from .phase5_ui import ConfirmDialog
        import json
        dialog=ConfirmDialog(self.production,self.identifier,self)
        dialog.fields['minutes'].setText(str(json.loads(self.production.get(self.identifier)['planned'])['minutes']))
        if dialog.exec():self.accept()

    def persist(self):
        v=self.values();self.production.confirm_from_recipe(self.identifier,v['failed'],v['reason'])
