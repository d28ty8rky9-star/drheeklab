"""Production inputs inside the actual New/Edit piece form."""
from decimal import Decimal
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QTabWidget,QLabel,QLineEdit,QPushButton,QFileDialog,QFormLayout,QListWidget
from .phase5_ui import EntryEditor
from .extras_ui import ExtrasEditor
from .production_extras import calculate_extras
from .pricing import number,brl
from .time_input import hours_to_minutes,minutes_to_hours

class ProductProductionFields(QWidget):
    def __init__(self,dialog,production,product_id=None,variant_id=None):
        super().__init__(dialog);self.dialog=dialog;self.production=production;self.variant_id=variant_id
        box=QVBoxLayout(self);box.setContentsMargins(0,0,0,0)
        self.editor=EntryEditor(production,recipe=True)
        self.editor.variant.setCurrentIndex(-1)
        if variant_id is not None:
            index=next((i for i in range(self.editor.variant.count()) if self.editor.variant.itemData(i)[0]==variant_id),-1)
            self.editor.variant.setCurrentIndex(index)
        self.file_path=QLineEdit();self.file_path.setReadOnly(True);self.file_path.setPlaceholderText('STL/3MF opcional no cadastro; obrigatório para gerar OP')
        file_row=QHBoxLayout();file_row.addWidget(self.file_path)
        choose=QPushButton('Adicionar STL/3MF');choose.clicked.connect(self.choose_file);file_row.addWidget(choose)
        self.editor.layout().addLayout(file_row)
        saved=production.recipe(variant_id) if variant_id else None
        data=saved['data'] if saved else None
        self.saved_recipe=saved
        if data:
            dialog.fields['printer_id'].setCurrentIndex(dialog.fields['printer_id'].findData(data['printer_id']))
            dialog.fields['estimated_hours'].setText(minutes_to_hours(data['minutes']))
            dialog.fields['settings'].setText(data['parameters'])
            self.editor.project.setCurrentIndex(self.editor.project.findData(data['project_id']))
            for entry in list(self.editor.filaments):self.editor.remove_spool(entry)
            for f in data['estimate']['filaments']:
                self.editor.add_spool();combo,grams,_=self.editor.filaments[-1]
                combo.setCurrentIndex(combo.findData(f['id']));grams.setText(f['grams'])
            self.editor.aux.setText(data.get('auxiliary_base',data['estimate']['auxiliary']))
        else:
            # No invented consumption for a newly entered idea.
            self.editor.filaments[0][1].clear()
            recommended=dialog.fields['filament_id'].currentData()
            if recommended is not None:self.editor.filaments[0][0].setCurrentIndex(self.editor.filaments[0][0].findData(recommended))
        self.extras=ExtrasEditor(data.get('extras',[]) if data else [])
        self.tabs=QTabWidget();self.tabs.addTab(self.editor,'Filamentos e arquivos');self.tabs.addTab(self.extras,'Extras • argolas e acessórios');box.addWidget(self.tabs)
        variant=production.products.get('variants',variant_id) if variant_id else {}
        details=QWidget();details_form=QFormLayout(details);self.variant_fields={}
        for key,label,default in [('name','Nome da variante','Padrão'),('size','Tamanho',''),('color','Cor',''),('material','Material','')]:
            field=QLineEdit(variant.get(key,default));self.variant_fields[key]=field;details_form.addRow(label,field)
        self.tabs.addTab(details,'Variante')
        photos=QWidget();photos_box=QVBoxLayout(photos);self.photo_paths=[];self.photo_list=QListWidget();photos_box.addWidget(self.photo_list)
        for photo in production.products.media(product_id,'photo') if product_id else []:self.photo_list.addItem(photo['original_name'])
        add_photo=QPushButton('Adicionar fotos da peça');add_photo.clicked.connect(self.choose_photos);photos_box.addWidget(add_photo)
        self.tabs.addTab(photos,'Fotos')
        self.preview=QLabel();self.preview.setWordWrap(True);box.addWidget(self.preview)
        note=QLabel('Valor demonstrativo. Salvar a peça não movimenta estoque nem Financeiro. A OP usa estes dados salvos.');note.setWordWrap(True);box.addWidget(note)
        self.editor.changed=self.update_preview
        for combo,grams,_ in self.editor.filaments:
            combo.currentIndexChanged.connect(self.update_preview);grams.textChanged.connect(self.update_preview)
        self.editor.aux.textChanged.connect(self.update_preview);self.extras.changed.connect(self.update_preview)
        for key in ('printer_id','estimated_hours'):
            field=dialog.fields[key]
            (field.currentIndexChanged if hasattr(field,'currentIndexChanged') else field.textChanged).connect(self.update_preview)
        self.update_preview()

    def choose_file(self):
        path,_=QFileDialog.getOpenFileName(self,'Arquivo da peça','','Projetos (*.stl *.3mf)')
        if path:self.file_path.setText(path)

    def choose_photos(self):
        from pathlib import Path
        paths,_=QFileDialog.getOpenFileNames(self,'Fotos da peça','','Fotos (*.png *.jpg *.jpeg)')
        for path in paths:
            if path not in self.photo_paths:self.photo_paths.append(path);self.photo_list.addItem(Path(path).name)

    def configured(self):
        return bool(self.saved_recipe or self.extras.rows or self.editor.aux.text().strip() not in ('','0','0.00','0,00') or any(g.text().strip() for _,g,_ in self.editor.filaments))

    def inputs(self):
        dialog=self.dialog;rows,total=calculate_extras(self.extras.value())
        base=number(self.editor.aux.text(),'Outros custos adicionais',places=2)
        filaments=[(c.currentData(),g.text()) for c,g,_ in self.editor.filaments]
        minutes=hours_to_minutes(dialog.fields['estimated_hours'].text())
        if minutes<1:raise ValueError('Informe o tempo por peça em horas (mínimo de um minuto).')
        snapshot=self.production.catalog.estimate(dialog.fields['printer_id'].currentData(),minutes,filaments,str(base+total),1)
        return snapshot,filaments,rows,str(base),minutes

    def update_preview(self,*args):
        try:
            snapshot,*_=self.inputs();value=snapshot.get('acquisition_production_cost')
            value=value if value is not None else snapshot['total_cost']
            self.preview.setText('Valor de produção por peça: '+brl(Decimal(value))+' • Referência: '+brl(Decimal(snapshot['total_cost'])))
            self.dialog.fields['planned_cost'].setReadOnly(True);self.dialog.fields['planned_cost'].setText(value)
        except ValueError as error:
            self.preview.setText('Cálculo automático: '+str(error))
            configured=self.configured();self.dialog.fields['planned_cost'].setReadOnly(bool(configured))
            if configured:self.dialog.fields['planned_cost'].clear()
