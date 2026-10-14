"""Document center, local sharing copies, notifications, audit and recycle bin."""
from datetime import date
from decimal import Decimal
from pathlib import Path
import csv
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QDialog,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QComboBox,QCheckBox,QPushButton,QTabWidget,QFileDialog,QMessageBox,QTableWidget,QTableWidgetItem
from .phase2_ui import FormDialog,button,table,fill_table,date_iso,scroll
from .phase4_ui import open_local
from .documents import Documents,KINDS
from .notifications import Notifications
from .lifecycle import Lifecycle
from .products import Products
from .finance_exports import csv_safe


class FinancePDFDialog(FormDialog):
    def __init__(self,documents,parent=None,filters=None):
        super().__init__('Emitir relatório financeiro PDF',parent);self.documents=documents;self.filters=filters or {}
        self.line('start','Início',date.today().replace(day=1).strftime('%d/%m/%Y'));self.line('end','Final',date.today().strftime('%d/%m/%Y'))
        self.form.addRow(QLabel('Valores, filtros, critérios e marca serão preservados nesta versão. Relatório interno.'))
    def persist(self):
        v=self.values();self.saved_id=self.documents.emit_finance(date_iso(v['start']),date_iso(v['end']),**self.filters)


class ProductionPDFDialog(FormDialog):
    def __init__(self,documents,parent=None):
        super().__init__('Emitir relatório de produção PDF',parent);self.documents=documents
        rows=list(documents.db.execute('SELECT id,code FROM production_orders ORDER BY id DESC'));choices={r['id']:r['code'] for r in rows};self.combo('op','Ordem de produção',choices,next(iter(choices),None))
    def persist(self):self.saved_id=self.documents.emit_production(self.values()['op'])


class CatalogPDFDialog(FormDialog):
    def __init__(self,documents,parent=None):
        super().__init__('Catálogo PDF para compartilhamento manual',parent);self.resize(850,700);self.documents=documents
        self.line('title','Título','Catálogo Dr. Heek Lab');self.line('notes','Observações da oferta')
        self.listing=QTableWidget(0,4);self.listing.setHorizontalHeaderLabels(['Incluir','Modelo / variante','Preço escolhido (R$)','Descrição resumida'])
        self.listing.setMinimumHeight(320);self.form.addRow(self.listing);self.rows=[];products=Products(documents.storage)
        for product in products.search(include_stock=True):
            for variant in products.variants(product['id']):
                if variant['archived']:continue
                index=self.listing.rowCount();self.listing.insertRow(index);check=QCheckBox();self.listing.setCellWidget(index,0,check)
                self.listing.setItem(index,1,QTableWidgetItem(product['name']+' / '+variant['name']));self.listing.item(index,1).setFlags(Qt.ItemIsEnabled)
                price=variant['suggested_price_cents'] if variant['suggested_price_cents'] is not None else product['suggested_price_cents']
                self.listing.setItem(index,2,QTableWidgetItem(str(Decimal(price)/100) if price is not None else ''));self.listing.setItem(index,3,QTableWidgetItem(product['description'][:600]));self.rows.append((variant['id'],check))
        self.listing.resizeColumnsToContents();self.form.addRow(QLabel('Selecione produtos e confira preços. Fotos devem estar importadas em Produtos. A cópia é um PDF portátil; envio pelo WhatsApp é manual.'))
    def persist(self):
        items=[{'variant_id':variant,'price':self.listing.item(i,2).text(),'description':self.listing.item(i,3).text()} for i,(variant,check) in enumerate(self.rows) if check.isChecked()]
        self.saved_id=self.documents.emit_catalog(items,self.values()['title'],self.values()['notes'])


class AuditPage(QWidget):
    def __init__(self,storage,parent=None):
        super().__init__(parent);self.lifecycle=Lifecycle(storage);box=QVBoxLayout(self);filters=QHBoxLayout();box.addLayout(filters)
        self.start=QLineEdit();self.start.setPlaceholderText('Início DD/MM/AAAA');self.end=QLineEdit();self.end.setPlaceholderText('Final DD/MM/AAAA');filters.addWidget(self.start);filters.addWidget(self.end)
        self.operation=QLineEdit();self.operation.setPlaceholderText('Operação');self.record=QLineEdit();self.record.setPlaceholderText('Registro');self.reason=QLineEdit();self.reason.setPlaceholderText('Justificativa')
        row=QHBoxLayout();box.addLayout(row)
        for field in (self.operation,self.record,self.reason):row.addWidget(field)
        button('Pesquisar',self.refresh,row);self.listing=table(['ID','Data/hora','Operação','Registro','Anterior','Novo','Justificativa']);box.addWidget(self.listing)
        button('Exportar auditoria CSV',self.export,box);self.refresh()
    def refresh(self):
        try:
            self.rows=self.lifecycle.audit(date_iso(self.start.text()),date_iso(self.end.text()),self.operation.text(),self.record.text(),self.reason.text())
            fill_table(self.listing,[[r[k] or '' for k in ('id','created_at','operation','record','previous','current','reason')] for r in self.rows])
        except ValueError as err:QMessageBox.warning(self,'Auditoria',str(err))
    def export(self):
        self.refresh();path,_=QFileDialog.getSaveFileName(self,'Exportar auditoria',str(self.lifecycle.storage.home/'Relatórios'/'auditoria.csv'),'CSV (*.csv)')
        if not path:return
        try:
            with Path(path).open('w',encoding='utf-8-sig',newline='') as file:
                columns=('id','created_at','operation','record','previous','current','reason');writer=csv.writer(file,delimiter=';');writer.writerow(columns)
                for row in self.rows:writer.writerow([csv_safe(row[k] or '') for k in columns])
            QMessageBox.information(self,'Auditoria exportada',path)
        except OSError as err:QMessageBox.warning(self,'Auditoria',str(err))


class TrashPage(QWidget):
    def __init__(self,storage,parent=None):
        super().__init__(parent);self.lifecycle=Lifecycle(storage);box=QVBoxLayout(self)
        label=QLabel('Arquivamento lógico preserva dados e arquivos. Restauração exige motivo e mantém vínculos históricos. Cancelamentos financeiros, perdas e peças entregues não são revividos pela lixeira.');label.setWordWrap(True);box.addWidget(label)
        self.archived=QCheckBox('Mostrar arquivados para restaurar');self.archived.setChecked(True);self.archived.toggled.connect(self.refresh);box.addWidget(self.archived)
        self.listing=table(['Tipo','ID','Registro']);box.addWidget(self.listing);row=QHBoxLayout();box.addLayout(row);button('Atualizar',self.refresh,row);button('Arquivar / restaurar selecionado',self.change,row);self.refresh()
    def refresh(self):
        self.rows=self.lifecycle.rows(self.archived.isChecked());fill_table(self.listing,[(r['type'],r['id'],r['name']) for r in self.rows])
    def change(self):
        index=self.listing.currentRow()
        if index<0:QMessageBox.information(self,'Lixeira','Selecione um registro.');return
        row=self.rows[index];archived=not self.archived.isChecked();dialog=FormDialog('Arquivar' if archived else 'Restaurar',self);dialog.line('reason','Justificativa *')
        dialog.persist=lambda:self.lifecycle.archive(row['table'],row['id'],archived,dialog.values()['reason'])
        if dialog.exec():self.refresh()


class DocumentCenter(QDialog):
    def __init__(self,storage,parent=None):
        super().__init__(parent);self.setWindowTitle('Documentos, auditoria e lixeira');self.resize(1100,720);self.documents=Documents(storage)
        box=QVBoxLayout(self);tabs=QTabWidget();box.addWidget(tabs);page=QWidget();layout=QVBoxLayout(page);row=QHBoxLayout();layout.addLayout(row)
        for label,kind,dialog in [('PDF financeiro','finance',FinancePDFDialog),('PDF produção','production',ProductionPDFDialog),('Catálogo PDF','catalog',CatalogPDFDialog)]:button(label,lambda checked=False,d=dialog:self.emit(d),row)
        self.kind=QComboBox();self.kind.addItem('Todos',None)
        for key,label in KINDS.items():self.kind.addItem(label,key)
        row.addWidget(self.kind);self.kind.currentIndexChanged.connect(self.refresh);self.listing=table(['ID','Código','Tipo','Versão','Título','Emitido','Marca']);layout.addWidget(self.listing)
        controls=QHBoxLayout();layout.addLayout(controls);button('Abrir PDF',self.open,controls);button('Exportar cópia para compartilhar',self.export,controls);button('Arquivar PDF',self.archive,controls);button('Atualizar',self.refresh,controls)
        self.notice=QLabel('Os PDFs mantêm dados e marca da emissão. Importe o logotipo original em Configurações; ausência é identificada como documento de revisão.');self.notice.setWordWrap(True);layout.addWidget(self.notice)
        tabs.addTab(page,'PDFs e catálogos');tabs.addTab(AuditPage(storage,self),'Auditoria');tabs.addTab(TrashPage(storage,self),'Lixeira');self.refresh()
    def refresh(self):
        import json
        self.rows=self.documents.rows(self.kind.currentData());fill_table(self.listing,[(r['id'],r['code'],KINDS[r['kind']],r['version'],r['title'],r['created_at'][:19],json.loads(r['snapshot'])['brand']['status']) for r in self.rows])
    def selected(self):
        i=self.listing.currentRow()
        if i<0:raise ValueError('Selecione um documento.')
        return self.rows[i]['id']
    def act(self,fn):
        try:fn()
        except (ValueError,OSError) as err:QMessageBox.warning(self,'Documento',str(err))
    def emit(self,dialog_type):
        dialog=dialog_type(self.documents,self)
        if dialog.exec():self.refresh()
    def open(self):self.act(lambda:open_local(self,self.documents.path(self.selected())))
    def export(self):
        def run():
            identifier=self.selected();row=self.documents.get(identifier);path,_=QFileDialog.getSaveFileName(self,'Exportar cópia PDF',row['code']+'.pdf','PDF (*.pdf)')
            if path:self.documents.export(identifier,path);QMessageBox.information(self,'Cópia pronta',path+'\nCompartilhe manualmente pelo WhatsApp ou outro canal.')
        self.act(run)
    def archive(self):
        def run():
            identifier=self.selected();d=FormDialog('Arquivar PDF mantendo o arquivo original',self);d.line('reason','Justificativa *');d.persist=lambda:self.documents.archive(identifier,True,d.values()['reason'])
            if d.exec():self.refresh()
        self.act(run)


class NotificationDialog(QDialog):
    def __init__(self,storage,parent=None):
        super().__init__(parent);self.setWindowTitle('Notificações');self.resize(850,520);self.center=Notifications(storage);self.window=parent
        box=QVBoxLayout(self);self.show_snoozed=QCheckBox('Mostrar alertas adiados');self.show_snoozed.toggled.connect(self.refresh);box.addWidget(self.show_snoozed)
        self.listing=table(['Prioridade','Alerta','Detalhes','Leitura']);box.addWidget(self.listing);row=QHBoxLayout();box.addLayout(row)
        button('Abrir área',self.open_area,row);button('Marcar lido',lambda:self.mark(),row);button('Adiar um dia',lambda:self.mark(1),row);button('Atualizar',self.refresh,row)
        label=QLabel('Ler ou adiar um alerta não registra pagamento, manutenção nem entrega. O alerta se encerra quando a condição de origem é resolvida.');label.setWordWrap(True);box.addWidget(label);self.refresh()
    def refresh(self):
        self.rows=[r for r in self.center.refresh() if self.show_snoozed.isChecked() or not r['snoozed']];fill_table(self.listing,[({'urgent':'Urgente','warning':'Atenção','info':'Informação'}[r['severity']],r['title'],r['detail'],'Lido' if r['read'] else 'Novo') for r in self.rows])
    def selected(self):
        i=self.listing.currentRow()
        if i<0:raise ValueError('Selecione um alerta.')
        return self.rows[i]
    def mark(self,days=None):
        try:self.center.mark(self.selected()['key'],days);self.refresh()
        except ValueError as err:QMessageBox.warning(self,'Notificações',str(err))
    def open_area(self):
        try:
            row=self.selected();self.center.mark(row['key']);self.accept()
            if self.window:self.window.navigate(row['area']);self.window.refresh_notifications()
        except ValueError as err:QMessageBox.warning(self,'Notificações',str(err))
