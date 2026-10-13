import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox, QFileDialog, QInputDialog
from PySide6.QtGui import QImage, QColor
from drheeklab.storage import Storage
from drheeklab.products import Products
from drheeklab.inventory import Inventory
from drheeklab.ui import Window
from drheeklab.phase3_ui import ProductDialog, VariantDialog, MaterialDialog, ReceiptDialog, ReviewDialog, ReserveDialog, LossDialog, ConsumeMaterialDialog

APP=QApplication.instance() or QApplication([])


def fields(dialog, data):
    for key,value in data.items():
        dialog.fields[key].setText(value)


def test_real_product_forms_gallery_search_media_import_and_variants(tmp_path,monkeypatch):
    store=Storage(tmp_path/'data')
    products=Products(store)
    window=Window(store); window.show(); window.navigate(2)
    product=ProductDialog(products,parent=window)
    product.submit()
    assert product.result()!=QDialog.Accepted
    fields(product,{'name':'Organizador modular','description':'Suporte de ferramentas','planned_cost':'10,00','suggested_price':'30,00','settings':'0,2 mm; preenchimento 15%','quality_notes':'Verificar encaixe'})
    product.submit(); assert product.result()==QDialog.Accepted
    variant=VariantDialog(products,product.saved_id,parent=window)
    fields(variant,{'name':'Grande azul','size':'20 cm','color':'Azul','material':'PETG','planned_cost':'15,00','suggested_price':'45,00'})
    variant.submit(); assert variant.result()==QDialog.Accepted
    page=window.products_page; page.refresh(); page.select_product(product.saved_id)
    assert page.gallery.count()==1
    assert page.variants_table.rowCount()==2
    assert 'Verificar encaixe' in page.info.text()
    page.search.setText('petg'); assert page.gallery.count()==1
    page.search.setText('inexistente'); assert page.gallery.count()==0
    page.search.clear(); page.select_product(product.saved_id)
    image=QImage(80,60,QImage.Format_RGB32); image.fill(QColor('#3366aa'))
    path=tmp_path/'foto real.png'; assert image.save(str(path))
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *args: (str(path),''))
    page.import_file('photo')
    assert page.photo_table.rowCount()==1
    assert not page.gallery.item(0).icon().isNull()
    project=tmp_path/'modelo.stl'; project.write_text('solid model\nendsolid model\n')
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *args: (str(project),''))
    monkeypatch.setattr(QInputDialog,'getText',lambda *args: ('Versão de encaixe',True))
    page.import_file('project')
    assert page.project_table.rowCount()==1
    assert page.project_table.item(0,4).text()=='Versão de encaixe'
    window.close()


def test_stock_ui_receipt_personal_reinspection_reservation_release_and_loss(tmp_path,monkeypatch):
    store=Storage(tmp_path)
    products=Products(store); inventory=Inventory(store)
    product=products.save({'name':'Suporte','category':'functional'})
    variant=products.variants(product)[0]['id']
    window=Window(store); window.show(); window.navigate(3)
    dialog=ReceiptDialog(inventory,window)
    fields(dialog,{'quantity':'3','total_cost':'10,01','source':'Cadastro das peças existentes','condition':'Uso pessoal, marcas superficiais'})
    dialog.fields['state'].setCurrentIndex(dialog.fields['state'].findData('personal'))
    dialog.submit(); assert dialog.result()==QDialog.Accepted
    page=window.stock_page; page.refresh()
    assert page.stock_table.item(0,2).text()=='3'
    assert page.stock_table.item(0,4).text()=='0'
    review=ReviewDialog(inventory,[dialog.piece_ids[0]],window)
    fields(review,{'condition':'Usada, aprovada após nova verificação','reviewer':'Proprietário'})
    review.submit(); assert review.result()==QDialog.Accepted
    reserve=ReserveDialog(inventory,variant,window)
    fields(reserve,{'quantity':'1','reference':'Reserva de cliente para futura venda'})
    reserve.submit(); assert reserve.result()==QDialog.Accepted
    inventory.finish_reservation(reserve.saved_id,'release','Cliente desistiu')
    loss=LossDialog(inventory,'piece',[dialog.piece_ids[1]],window)
    fields(loss,{'reason':'Quebra','occurred_on':'03/01/2026','notes':'Falha física identificada'})
    monkeypatch.setattr(QMessageBox,'question',lambda *args: QMessageBox.Yes)
    loss.submit(); assert loss.result()==QDialog.Accepted
    page.refresh()
    assert page.stock_table.item(0,2).text()=='2'
    assert page.stock_table.item(0,4).text()=='1'
    assert page.stock_table.item(0,7).text()=='1'
    assert page.losses_table.rowCount()==1
    window.close()
    reopened=Storage(tmp_path)
    assert Inventory(reopened).summary()[0]['physical']==2
    assert Inventory(reopened).get('pieces',dialog.piece_ids[0])['condition']=='Usada, aprovada após nova verificação'
    reopened.close()


def test_material_forms_consumption_adjustments_and_losses(tmp_path,monkeypatch):
    store=Storage(tmp_path)
    inventory=Inventory(store)
    dialog=MaterialDialog(inventory)
    fields(dialog,{'name':'Ímã','unit':'unidade','balance':'10','reference_per_unit':'0,50','reason':'Compra inicial'})
    dialog.submit(); assert dialog.result()==QDialog.Accepted
    consume=ConsumeMaterialDialog(inventory,dialog.saved_id)
    fields(consume,{'quantity':'2','reason':'Montagem do suporte'})
    consume.submit(); assert consume.result()==QDialog.Accepted
    assert inventory.get('materials',dialog.saved_id)['balance_milli']==8000
    loss=LossDialog(inventory,'material',dialog.saved_id)
    fields(loss,{'quantity':'1','reason':'Ímã quebrado','occurred_on':'03/01/2026'})
    monkeypatch.setattr(QMessageBox,'question',lambda *args: QMessageBox.No)
    loss.submit(); assert loss.result()!=QDialog.Accepted
    assert inventory.get('materials',dialog.saved_id)['balance_milli']==8000
    monkeypatch.setattr(QMessageBox,'question',lambda *args: QMessageBox.Yes)
    loss.submit(); assert loss.result()==QDialog.Accepted
    assert inventory.get('materials',dialog.saved_id)['balance_milli']==7000
    store.close()


def test_available_receipt_requires_explicit_prior_check(tmp_path):
    store=Storage(tmp_path)
    products=Products(store); inventory=Inventory(store)
    product=products.save({'name':'Peça','category':'decorative'})
    dialog=ReceiptDialog(inventory)
    fields(dialog,{'source':'Entrada existente','condition':'Nova','reviewer':'Responsável'})
    dialog.fields['state'].setCurrentIndex(dialog.fields['state'].findData('available'))
    dialog.submit(); assert dialog.result()!=QDialog.Accepted
    assert inventory.pieces()==[]
    dialog.checked.setChecked(True); dialog.submit()
    assert dialog.result()==QDialog.Accepted
    assert inventory.summary()[0]['available']==1
    store.close()
