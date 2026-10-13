import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication,QDialog
from PySide6.QtGui import QImage,QColor
from drheeklab.storage import Storage
from drheeklab.production import Production
from drheeklab.phase5_ui import OrderDialog,ConfirmDialog,InspectionDialog
from drheeklab.ui import Window

APP=QApplication.instance() or QApplication([])


def setup(tmp_path):
    store=Storage(tmp_path/'data');p=Production(store)
    p.catalog.save_filament({'brand':'Marca','material':'PLA','color':'Azul','name':'PLA','initial_grams':'1000','remaining_grams':'1000','purchase':'100','reference_per_g':'0.2'})
    product=p.products.save({'name':'Suporte','category':'functional'})
    path=tmp_path/'suporte.stl';path.write_text('solid support');p.products.import_media(product,path,'project')
    return store,p


def test_production_ui_create_confirm_checklist_photos_and_complete(tmp_path):
    store,p=setup(tmp_path)
    form=OrderDialog(p);form.fields['responsible'].setText('Operador');form.fields['parameters'].setText('0,2 mm / 15% / 210 C');form.editors[0].quantity.setText('2')
    form.submit();assert form.result()==QDialog.Accepted,form.error.text();op=form.saved_id;p.start(op)
    confirm=ConfirmDialog(p,op);confirm.fields['minutes'].setText('60');confirm.submit()
    assert confirm.result()==QDialog.Accepted,confirm.error.text()
    for piece in p.pieces(op):
        inspect=InspectionDialog(p,op,piece);inspect.fields['responsible'].setText('QA')
        inspect.submit();assert inspect.result()!=QDialog.Accepted  # no default pass
        for combo,reason in inspect.checks.values():combo.setCurrentIndex(combo.findData('ok'))
        for index,(key,field) in enumerate(inspect.photos.items()):
            image=QImage(30,20,QImage.Format_RGB32);image.fill(QColor(['red','green','blue'][index]));path=tmp_path/(key+'.png');assert image.save(str(path));field.setText(str(path))
        inspect.submit();assert inspect.result()==QDialog.Accepted,inspect.error.text()
    p.complete(op)
    window=Window(store);window.show();window.navigate(2);APP.processEvents()
    assert window.pages.currentWidget()==window.workshop
    assert window.production_page.queue_table.rowCount()==1
    assert window.production_page.piece_table.rowCount()==2
    assert 'Concluída' in window.production_page.queue_table.item(0,2).text()
    assert window.production_page.tabs.widget(1).toPlainText().count('PO-')>=12
    window.resize(1100,700);APP.processEvents()
    window.grab().save(str(tmp_path/'production.png'))
    window.close();APP.processEvents()
    assert not window.production_page.timer.isActive()


def test_mixed_editor_remove_add_and_no_catalog_errors(tmp_path):
    store=Storage(tmp_path/'data');p=Production(store)
    form=OrderDialog(p);form.add();assert len(form.editors)==2
    form.fields['responsible'].setText('QA');form.fields['parameters'].setText('0,2 mm');form.submit()
    assert form.result()!=QDialog.Accepted and 'Cadastre' in form.error.text()
    form.reject();store.close()
