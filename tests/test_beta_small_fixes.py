from PySide6.QtWidgets import QApplication,QDialog
from PySide6.QtCore import Qt
from drheeklab.phase2_ui import FilamentDialog
from drheeklab.ui import Window
from drheeklab.finance import Finance
from drheeklab.sales import Sales
from drheeklab.stock_totals import stock_totals
from test_recipe_flow import system,inspect
APP=QApplication.instance() or QApplication([])


def test_new_used_filament_with_unknown_amount_without_editing(system):
    store,p,*_=system;form=FilamentDialog(p.catalog)
    assert form.unknown.isEnabled() and form.fields['state'].isEnabled()
    for k,v in {'name':'Rolo usado','brand':'Marca','color':'Azul','purchase':'100','reference_per_g':'0.1','initial_grams':''}.items():form.fields[k].setText(v)
    form.unknown.setChecked(True)
    assert form.fields['state'].currentData()=='open' and not form.remaining.isEnabled()
    form.submit();assert form.result()==QDialog.Accepted,form.error.text()
    row=p.catalog.get('filaments',form.saved_id)
    assert row['state']=='open' and row['remaining_mg'] is None and row['initial_mg'] is None
    assert stock_totals(p.inventory)['filament_unknown']==1
    assert not Finance(store).report()['cash']


def test_new_full_filament_still_starts_full_and_open_can_have_known_balance(system):
    store,p,*_=system
    for state,expected in [('new',500000),('open',200000)]:
        form=FilamentDialog(p.catalog)
        for k,v in {'name':state,'brand':'Marca','color':'Azul','purchase':'50','reference_per_g':'0.1','initial_grams':'500'}.items():form.fields[k].setText(v)
        form.fields['state'].setCurrentIndex(form.fields['state'].findData(state))
        if state=='open':form.remaining.setText('200')
        form.submit();assert form.result()==QDialog.Accepted,form.error.text()
        row=p.catalog.get('filaments',form.saved_id);assert row['remaining_mg']==expected and row['state']==state


def test_production_price_cost_times_two_except_accessories_and_stock_quote_match(system):
    store,p,spool,product,variant,project,_=system
    # Machine1.10 + filament1 + auxiliary1 =3.10; accessory10.
    p.save_recipe(variant,1,project,60,[(spool,'10')],'1','PLA',extras=[{'name':'Luz RGB','quantity':'1','unit_cost':'10'}])
    window=Window(store);window.navigate(2)
    index=window.presentation.product_ids.index(product)
    assert window.presentation.product_table.item(index,3).text()=='R$ 16,20' #3.10*2+10
    assert 'R$ 16,20' in window.products_page.gallery.item(0).text()
    assert p.products.get('products',product)['suggested_price_cents'] is None
    op=p.create_from_recipe(variant,1,'Operador');p.start(op);p.confirm_from_recipe(op);inspect(system,op);p.complete(op)
    sale=Sales(store);piece=p.inventory.pieces()[0]
    quote=sale.stock_sale_quote([piece['id']])
    assert quote['cost_cents']==1310 and quote['suggested_cents']==1620
    from drheeklab.stock_sale_ui import StockSaleDialog
    form=StockSaleDialog(sale,window);form.pieces.item(0,0).setCheckState(Qt.Checked)
    assert form.fields['actual_total'].text()=='16.2'
    assert '100,00%' in form.actual_summary.text()
    assert 'Acessórios pelo custo: R$ 10,00' in form.actual_summary.text()
    form.close()
    # Separate sale accessory also passes through at cost, without markup.
    _,ids=p.inventory.receive_accessory(name='Outra luz',quantity=1,source='Compra',state='available',condition='Nova',operation_key='luz',total_cost='5',reviewer='QA')
    assert sale.stock_sale_quote([piece['id']],ids)['suggested_cents']==2120
    window.close()
