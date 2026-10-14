import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import pytest
from PySide6.QtWidgets import QApplication,QDialog
from drheeklab.storage import Storage
from drheeklab.ui import Window,AREAS
from drheeklab.products import Products
from drheeklab.catalog import Catalog
APP=QApplication.instance() or QApplication([])

def test_selected_piece_prepares_and_creates_normal_order(tmp_path,monkeypatch):
    store=Storage(tmp_path/'data');products=Products(store)
    spool=Catalog(store).save_filament(dict(name='PLA',brand='Teste',material='PLA',color='Azul',initial_grams='1000',remaining_grams='1000',purchase='100',reference_per_g='0.1'))
    products.save({'name':'Outra peça','category':'functional'})
    product=products.save({'name':'Escolhida','category':'functional','settings':'0,2 mm / 15%','estimated_minutes':'90','printer_id':1,'filament_id':spool})
    variant=products.save_variant(product,{'name':'Grande','size':'20 cm','color':'Azul','material':'PLA'})
    path=tmp_path/'modelo.stl';path.write_text('solid model\nendsolid model')
    project=products.import_media(product,path,'project')
    window=Window(store);window.navigate(2);window.products_page.select_product(product)
    window.products_page.variants_table.selectRow(next(i for i,r in enumerate(window.products_page.variant_rows) if r['id']==variant))
    from drheeklab.production import Production
    Production(store).save_recipe(variant,1,project,90,[(spool,'10')],'0','0,2 mm / 15%')
    before=store.db.total_changes;dialog=window.workshop.prepare_order()
    assert store.db.total_changes==before
    assert dialog.variant_id==variant
    assert set(dialog.fields)=={'quantity','responsible','priority','item'}
    dialog.fields['responsible'].setText('Operador');dialog.fields['quantity'].setText('2')
    monkeypatch.setattr(window.workshop,'prepare_order',lambda:dialog)
    monkeypatch.setattr(dialog,'exec',lambda:(dialog.submit(),dialog.result())[1])
    window.workshop.produce_button.click()
    assert dialog.result()==QDialog.Accepted,dialog.error.text()
    window.production_page.refresh()
    assert window.production_page.queue_table.rowCount()==1
    assert window.production_page.production.entries(dialog.saved_id)[0]['variant_id']==variant
    assert Catalog(store).get('filaments',spool)['remaining_mg']==1000000
    assert AREAS.count('Produção')==1 and 'Produtos' not in AREAS
    assert window.pages.currentWidget() is window.workshop
    window.close()

def test_missing_file_and_archived_piece_do_not_create_order(tmp_path):
    store=Storage(tmp_path);products=Products(store)
    product=products.save({'name':'Comprada pronta','category':'functional'})
    window=Window(store);window.navigate(2);window.products_page.select_product(product)
    with pytest.raises(ValueError,match='STL/3MF'):window.workshop.prepare_order()
    assert not window.production_page.production.queue()
    products.archive('products',product,True,'Arquivada')
    window.products_page.trash.setChecked(True);window.products_page.select_product(product)
    assert not window.workshop.produce_button.isEnabled()
    window.workshop.details_button.setChecked(True)
    assert not window.products_page.tabs.isHidden()
    window.close()

def test_archived_selected_variant_is_not_replaced_by_another(tmp_path):
    store=Storage(tmp_path/'data');products=Products(store)
    product=products.save({'name':'Suporte','category':'functional'})
    archived=products.save_variant(product,{'name':'Antiga'})
    products.archive('variants',archived,True,'Fora de linha')
    window=Window(store);window.navigate(2);window.products_page.select_product(product)
    window.products_page.variant_trash.setChecked(True);window.products_page.variants_table.selectRow(0)
    assert not window.workshop.produce_button.isEnabled()
    with pytest.raises(ValueError,match='variante ativa'):window.workshop.prepare_order()
    assert not window.production_page.production.queue()
    window.close()
