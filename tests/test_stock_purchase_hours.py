import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import json
import sqlite3
from decimal import Decimal
import pytest
from PySide6.QtWidgets import QApplication,QDialog
from drheeklab.storage import Storage
from drheeklab.inventory import Inventory
from drheeklab.products import Products
from drheeklab.production import Production
from drheeklab.finance import Finance
from drheeklab.sales import Sales
from drheeklab.search import search
from drheeklab.ui import Window
from drheeklab.phase3_ui import ReceiptDialog,ProductDialog
from drheeklab.recipe_ui import RecipeDialog
from drheeklab.time_input import hours_to_minutes,minutes_to_hours
APP=QApplication.instance() or QApplication([])

@pytest.mark.parametrize('hours,minutes',[('1,5',90),('2',120),('0,25',15),('0',0),('0.5',30),('0,025',2)])
def test_hours_are_converted_without_float_errors(hours,minutes):
    assert hours_to_minutes(hours)==minutes

@pytest.mark.parametrize('invalid',['-1','texto','NaN','Infinity',True])
def test_invalid_hours_are_rejected(invalid):
    with pytest.raises(ValueError):hours_to_minutes(invalid)

def test_old_minutes_roundtrip_without_rewriting_history():
    for minutes in (1,7,59,60,71,90,120,1440,54321):
        assert hours_to_minutes(minutes_to_hours(minutes))==minutes

def test_purchase_created_directly_in_stock_and_sold_without_production(tmp_path):
    store=Storage(tmp_path);inventory=Inventory(store);finance=Finance(store)
    receipt,pieces=inventory.receive_purchased('Scorpion comprado',1,'Compra de colecionável','available','Novo', 'scorpion',total_cost='50',reviewer='Proprietário',suggested_price='80')
    assert len(inventory.pieces())==1 and inventory.pieces()[0]['unit_cost_cents']==5000
    assert not Products(store).search()  # no production catalog item
    assert Products(store).search(include_stock=True)[0]['name']=='Scorpion comprado'
    assert not Production(store).queue() and not finance.report()['production']
    assert not store.db.execute('SELECT * FROM production_recipes').fetchall()
    assert search(store,'Scorpion')[0]['area']==3
    assert finance.report()['metrics']['cash_flow_cents']==0
    sales=Sales(store);client=sales.save_client({'name':'Comprador'});variant=inventory.pieces()[0]['variant_id']
    order=sales.create_order(client,[{'variant_id':variant,'quantity':1,'unit_price':'80','fulfillment':'stock'}])
    sales.receive_payment(order,'80','pix');sales.deliver(order,'deliver','pickup')
    report=finance.report()
    assert report['metrics']['cost_of_sales_cents']==5000
    assert report['metrics']['commercial_result_cents']==3000
    assert report['metrics']['received_net_cents']==8000
    assert not report['production']
    with pytest.raises(sqlite3.IntegrityError):inventory.receive_purchased('Duplicado',1,'Compra','available','Novo','scorpion',total_cost='10',reviewer='QA')
    assert len(Products(store).search(include_stock=True))==1  # no orphan item on duplicate receipt
    store.close()

def test_invalid_purchase_rolls_back_catalog_and_stock(tmp_path):
    store=Storage(tmp_path);inventory=Inventory(store)
    with pytest.raises(ValueError):inventory.receive_purchased('Peça',1,'Compra','available','Nova','bad',total_cost='50',reviewer='')
    assert not inventory.pieces()
    assert not Products(store).all_variants()
    assert store.db.execute('SELECT count(*) FROM purchased_products').fetchone()[0]==0
    store.close()

def test_real_stock_form_works_with_empty_production_catalog(tmp_path):
    store=Storage(tmp_path);window=Window(store);window.navigate(3)
    form=ReceiptDialog(window.stock_page.inventory,window)
    form.fields['entry_kind'].setCurrentIndex(form.fields['entry_kind'].findData('purchased'))
    assert form.fields['variant_id'].isHidden() and form.fields['calculation_id'].isHidden()
    for key,value in {'name':'Scorpion KA comprado','quantity':'1','total_cost':'50','source':'Compra particular','condition':'Novo e revisado','reviewer':'Proprietário','suggested_price':'80'}.items():form.fields[key].setText(value)
    form.fields['state'].setCurrentIndex(form.fields['state'].findData('available'));form.checked.setChecked(True)
    form.submit();assert form.result()==QDialog.Accepted,form.error.text()
    window.stock_page.refresh();assert window.stock_page.pieces_table.rowCount()==1
    window.navigate(2);assert window.products_page.gallery.count()==0
    window.navigate(4)
    assert 'R$ 50,00' in window.finance_page.stock_value_label.text()
    assert window.finance_page.product.findData(1)>=0
    assert window.finance_page.report_data['metrics']['cash_flow_cents']==0
    window.close()

def test_hours_and_live_demonstrative_cost_do_not_touch_finance(tmp_path):
    store=Storage(tmp_path/'data');production=Production(store)
    spool=production.catalog.save_filament({'name':'PLA','brand':'Teste','material':'PLA','color':'Azul','initial_grams':'1000','remaining_grams':'1000','purchase':'100','reference_per_g':'0.2'})
    product_form=ProductDialog(production.products);product_form.fields['name'].setText('Dragão');product_form.fields['estimated_hours'].setText('1,5');product_form.submit()
    assert product_form.result()==QDialog.Accepted
    product=product_form.saved_id;assert production.products.get('products',product)['estimated_minutes']==90
    path=tmp_path/'dragao.stl';path.write_text('solid dragon');production.products.import_media(product,path,'project')
    variant=production.products.variants(product)[0]['id']
    window=Window(store);window.navigate(2);window.products_page.select_product(product)
    assert window.production_page.piece_table.isColumnHidden(4)
    form=RecipeDialog(production,variant,window);assert form.fields['hours'].text()=='1.5'
    form.fields['parameters'].setText('0,2 mm / 15%');form.editor.filaments[0][1].setText('25');form.editor.aux.setText('2')
    assert 'R$ 6,15' in form.preview.text()  # 2.5 material + 1.65 machine + 2 additional
    form.fields['hours'].setText('2');assert 'R$ 6,70' in form.preview.text()
    form.editor.aux.setText('3');assert 'R$ 7,70' in form.preview.text()
    form.submit();assert form.result()==QDialog.Accepted,form.error.text()
    window.products_page.refresh();window.products_page.select_product(product)
    assert 'R$ 7,70' in window.workshop.production_value.text()
    assert 'Demonstrativo' in window.workshop.production_value.text()
    assert 'Valor de produção: R$ 7,70' in window.products_page.gallery.item(0).text()
    table=window.presentation.product_table
    assert table.item(0,4).text()=='R$ 7,70'
    assert production.recipe(variant)['data']['minutes']==120
    assert not Finance(store).report()['production'] and not production.inventory.pieces()
    assert production.catalog.get('filaments',spool)['remaining_mg']==1000000
    reopen=RecipeDialog(production,variant,window);assert reopen.fields['hours'].text()=='2';reopen.reject()
    window.close()

def test_calculator_old_minute_draft_converts_to_hours(tmp_path):
    store=Storage(tmp_path)
    store.save_draft('calculator',json.dumps({'title':'Legado','minutes':'90','quantity':'1','markup':'200','auxiliary':'0','final':'','printer':1,'filaments':[]}))
    window=Window(store)
    assert window.calculator.hours.text()=='1.5'
    window.calculator.save_draft()
    assert json.loads(store.load_draft('calculator'))['hours']=='1.5'
    window.close()
