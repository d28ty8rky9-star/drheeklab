import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
from PySide6.QtWidgets import QApplication,QDialog,QMessageBox
from PySide6.QtGui import QImage,QColor
from drheeklab.storage import Storage
from drheeklab.documents import Documents
from drheeklab.products import Products
from drheeklab.phase7_ui import CatalogPDFDialog,FinancePDFDialog,DocumentCenter,NotificationDialog,TrashPage,AuditPage
from drheeklab.recovery import RecoverySession,run_recovery
from drheeklab.backup import create_backup
from drheeklab.security import Auth
from drheeklab.catalog import Catalog
from drheeklab.ui import Window,Login

APP=QApplication.instance() or QApplication([])


def setup(tmp_path):
    store=Storage(tmp_path/'data');products=Products(store);product=products.save({'name':'Peça','category':'decorative','suggested_price':'30'})
    variant=products.variants(product)[0]['id'];image=QImage(30,20,QImage.Format_RGB32);image.fill(QColor('blue'));photo=tmp_path/'piece.png';assert image.save(str(photo));products.import_media(product,photo,'photo')
    return store,variant


def test_catalog_finance_forms_document_center_and_audit_ui(tmp_path):
    store,variant=setup(tmp_path);documents=Documents(store)
    form=CatalogPDFDialog(documents);form.rows[0][1].setChecked(True);form.listing.item(0,2).setText('25');form.submit();assert form.result()==QDialog.Accepted,form.error.text()
    financial=FinancePDFDialog(documents);financial.submit();assert financial.result()==QDialog.Accepted,financial.error.text()
    center=DocumentCenter(store);assert center.listing.rowCount()==2
    audit=AuditPage(store);audit.operation.setText('documento emitido');audit.refresh();assert audit.listing.rowCount()==2
    center.close();store.close()


def test_notification_badge_and_dialog_read_does_not_remove_condition(tmp_path):
    store,variant=setup(tmp_path);Catalog(store).save_filament({'brand':'Marca','material':'PLA','color':'Azul','name':'Pouco','purchase':'10','initial_grams':'100','remaining_grams':'20','reference_per_g':'0.2','state':'open'})
    window=Window(store);window.show();APP.processEvents();assert '(1)' in window.notification_button.text()
    dialog=NotificationDialog(store,window);dialog.listing.selectRow(0);dialog.mark();window.refresh_notifications();assert '(0)' in window.notification_button.text() and dialog.listing.rowCount()==1
    dialog.listing.selectRow(0);dialog.open_area();assert window.pages.currentIndex()==4
    window.close();APP.processEvents();assert not window.notification_timer.isActive()


def test_restore_flow_requires_confirmation_no_data_change_on_no(tmp_path,monkeypatch):
    store,variant=setup(tmp_path);Auth(store).create('Senha segura de QA');backup=create_backup(store);store.close();destination=tmp_path/'destination'
    def authenticate(dialog):
        dialog.password.setText('Senha segura de QA');dialog.submit();return dialog.result()
    monkeypatch.setattr(Login,'exec',authenticate);monkeypatch.setattr(QMessageBox,'question',lambda *args:QMessageBox.No)
    assert run_recovery(destination,'test',backup)==0 and not destination.exists()
    monkeypatch.setattr(QMessageBox,'question',lambda *args:QMessageBox.Yes);monkeypatch.setattr(QMessageBox,'information',lambda *args:QMessageBox.Ok)
    assert run_recovery(destination,'test',backup)==0
    reopened=Storage(destination)
    try:assert Auth(reopened).verify('Senha segura de QA') and Products(reopened).search()[0]['name']=='Peça'
    finally:reopened.close()


def test_finance_page_pdf_preserves_selected_filter(tmp_path,monkeypatch):
    store,variant=setup(tmp_path);window=Window(store);window.navigate(4)
    monkeypatch.setattr('drheeklab.phase6_ui.open_local',lambda *args:None)
    page=window.finance_page;product=Products(store).search()[0]['id'];page.product.setCurrentIndex(page.product.findData(product));page.pdf()
    import json
    row=Documents(store).rows()[0];snapshot=json.loads(row['snapshot']);assert snapshot['data']['scoped'] is True
    window.close();APP.processEvents()


def test_startup_failure_offers_graphical_recovery_without_command_line(tmp_path,monkeypatch):
    store,variant=setup(tmp_path);Auth(store).create('Senha segura de QA');backup=create_backup(store);root=store.root;path=store.path;store.close();path.write_bytes(b'broken database')
    import drheeklab.app as module
    monkeypatch.setattr(module.sys,'argv',['drheeklab','--environment','test','--data-dir',str(root)])
    monkeypatch.setattr(QMessageBox,'exec',lambda self:0)
    monkeypatch.setattr(QMessageBox,'clickedButton',lambda self:next(b for b in self.buttons() if b.text()=='Recuperar de backup'))
    monkeypatch.setattr(module.QFileDialog,'getOpenFileName',lambda *args:(str(backup),''))
    def authenticate(dialog):
        dialog.password.setText('Senha segura de QA');dialog.submit();return dialog.result()
    monkeypatch.setattr(Login,'exec',authenticate);monkeypatch.setattr(QMessageBox,'question',lambda *args:QMessageBox.Yes);monkeypatch.setattr(QMessageBox,'information',lambda *args:QMessageBox.Ok)
    assert module.main()==0
    reopened=Storage(root)
    try:assert Auth(reopened).verify('Senha segura de QA') and Products(reopened).search()[0]['name']=='Peça'
    finally:reopened.close()
