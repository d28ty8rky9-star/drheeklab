from PySide6.QtWidgets import QApplication
from drheeklab.ui import Window
from test_recipe_flow import system
from test_stock_sale import prepared
APP=QApplication.instance() or QApplication([])


def test_home_finance_production_and_stock_refresh_with_unknown_spool(system):
    store,p,*_=system;sales,client,produced,bought,accessories=prepared(system)
    p.catalog.save_filament({'name':'Sem saldo','brand':'Teste','material':'PLA','color':'Preto','purchase':'200','reference_per_g':'0.2','state':'open'})
    window=Window(store);window.navigate(0);view=window.presentation
    assert len(view.home_strip.cards)==3
    assert len(view.production_strip.cards)==4
    assert view.home_stock_strip.cards[0].value.text()=='R$ 98,00'
    assert '2 filamentos' in view.home_stock_strip.cards[0].detail.text()
    assert '0,98 kg' in view.home_stock_strip.cards[0].detail.text()
    assert 'desconhecido: 1' in view.home_stock_strip.cards[0].detail.text()
    assert view.home_stock_strip.cards[1].value.text()=='R$ 30,00'
    assert view.home_stock_strip.cards[2].value.text()=='R$ 234,20'
    order=sales.create_stock_sale(client,[bought[0]],[accessories[0]])
    sales.deliver(order,'deliver','pickup');window.navigate(0)
    assert view.home_stock_strip.cards[1].value.text()=='R$ 15,00'
    assert view.home_stock_strip.cards[2].value.text()=='R$ 169,20'
    window.close()
