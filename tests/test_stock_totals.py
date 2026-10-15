from drheeklab.stock_totals import stock_totals
from test_recipe_flow import system
from test_stock_sale import prepared

def test_stock_totals_separate_accessories_and_ignore_unknown_filament_cost(system):
    store,p,*_=system;sales,client,produced,bought,accessories=prepared(system)
    p.catalog.save_filament({'name':'Desconhecido','brand':'Teste','material':'PLA','color':'Branco','purchase':'200','reference_per_g':'0.2','state':'open'})
    before=store.db.total_changes
    t=stock_totals(p.inventory)
    assert t['filament_mg']==980000 and t['filament_cents']==9800
    assert t['filament_unknown']==1 and t['filament_unvalued']==1
    assert t['piece_count']==4 and t['piece_cents']==10620
    assert t['accessory_count']==2 and t['accessory_cents']==3000
    assert store.db.total_changes==before
    sale=sales.create_stock_sale(client,[bought[0]],[accessories[0]])
    assert stock_totals(p.inventory)==t # reservations stay physically held
    sales.deliver(sale,'deliver','pickup')
    t=stock_totals(p.inventory)
    assert t['piece_count']==3 and t['piece_cents']==5620
    assert t['accessory_count']==1 and t['accessory_cents']==1500


def test_new_filament_full_purchase_value_reduces_with_actual_consumption(system):
    from drheeklab.phase2_ui import FilamentDialog,CatalogPage
    from PySide6.QtWidgets import QApplication,QDialog
    from test_recipe_flow import recipe
    app=QApplication.instance() or QApplication([])
    store,p,*_=system
    form=FilamentDialog(p.catalog)
    for key,value in {'name':'Novo rolo','brand':'Teste','color':'Preto','purchase':'120','initial_grams':'500','reference_per_g':'0.24'}.items():form.fields[key].setText(value)
    assert form.remaining.text()=='500'
    form.submit();assert form.result()==QDialog.Accepted,form.error.text()
    row=p.catalog.get('filaments',form.saved_id)
    from drheeklab.stock_totals import filament_value
    assert row['remaining_mg']==500000 and filament_value(row)==12000
    variant=system[4];project=system[5]
    p.save_recipe(variant,1,project,60,[(form.saved_id,'50')],'0','0,2 mm')
    op=p.create_from_recipe(variant,1,'Operador');p.start(op);p.confirm_from_recipe(op)
    row=p.catalog.get('filaments',form.saved_id)
    assert row['remaining_mg']==450000 and filament_value(row)==10800
    assert CatalogPage.filament_value_label(row)=='R$ 108,00'
    assert not store.db.execute('SELECT 1 FROM payable_payments').fetchone()
