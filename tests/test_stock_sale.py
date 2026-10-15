import pytest,json
from drheeklab.sales import Sales
from drheeklab.finance import Finance
from test_recipe_flow import system,recipe,inspect


def prepared(system):
    store,p,*_=system;sales=Sales(store);client=sales.save_client({'name':'Cliente'})
    recipe(system);variant=system[4];op=p.create_from_recipe(variant,2,'Operador');p.start(op);p.confirm_from_recipe(op);inspect(system,op);p.complete(op)
    produced=[r['id'] for r in p.inventory.pieces()]
    _,bought=p.inventory.receive_purchased('Scorpion',2,'Compra','available','Novo','resale',total_cost='100',reviewer='QA')
    _,accessories=p.inventory.receive_accessory(name='Luz RGB',quantity=2,source='Compra luz',state='available',condition='Nova',operation_key='rgb',total_cost='30',reviewer='QA')
    return sales,client,produced,bought,accessories


def test_markups_and_accessory_prices_are_exact_and_readonly(system):
    store,p,*_=system;sales,client,produced,bought,accessories=prepared(system)
    before=store.db.total_changes
    quote=sales.stock_sale_quote([produced[0]],[accessories[0]])
    assert quote['cost_cents']==1810 and quote['suggested_cents']==2120  # production 3.10*2 + RGB15
    quote=sales.stock_sale_quote([bought[0]],[accessories[0]])
    assert quote['cost_cents']==6500 and quote['suggested_cents']==8000  # purchased50*1.3 + RGB15
    assert store.db.total_changes==before
    assert not Finance(store).report()['cash']


def test_exact_unit_reserved_and_accessory_not_marked_up_on_manual_price(system):
    store,p,*_=system;sales,client,produced,bought,accessories=prepared(system)
    order=sales.create_stock_sale(client,[bought[1]],[accessories[1]],actual_total='75')
    items=sales.items(order)
    assert [i['unit_price_cents'] for i in items]==[6000,1500]
    assert p.inventory.get('pieces',bought[1])['state']=='reserved'
    assert p.inventory.get('pieces',bought[0])['state']=='available'
    assert p.inventory.get('pieces',accessories[0])['state']=='available'
    assert json.loads(items[0]['snapshot'])['pricing']['markup_percent']==30
    sales.receive_payment(order,'75','pix');sales.deliver(order,'deliver','pickup')
    report=Finance(store).report()
    assert report['metrics']['cost_of_sales_cents']==6500
    assert report['metrics']['commercial_result_cents']==1000
    assert report['metrics']['received_net_cents']==7500
    assert report['metrics']['production_cost_cents']==620  # existing OP unchanged, no duplicate
    count=store.db.execute('SELECT count(*) FROM financial_costs').fetchone()[0]
    Finance(store).report();assert store.db.execute('SELECT count(*) FROM financial_costs').fetchone()[0]==count==2
    with pytest.raises(ValueError):sales.create_stock_sale(client,[bought[1]])


def test_produced_sale_with_extra_delivery_cancel_and_return_preserves_cost(system):
    store,p,*_=system;sales,client,produced,bought,accessories=prepared(system)
    order=sales.create_stock_sale(client,[produced[1]],[accessories[1]])
    assert sales.financial(order)['total']==2120
    sales.deliver(order,'deliver','pickup')
    assert Finance(store).report()['metrics']['cost_of_sales_cents']==1810
    assert {r['id'] for r in sales.returnable_pieces(order)}=={produced[1],accessories[1]}
    assert p.inventory.get('pieces',produced[0])['state']=='available'
    sales.cancel(order,'Cliente desistiu')
    sales.return_cancelled_pieces(order,[produced[1],accessories[1]],'Retorno físico conferido')
    assert Finance(store).report()['metrics']['cost_of_sales_cents']==0
    assert p.inventory.get('pieces',accessories[1])['state']=='quarantine'
    assert p.inventory.get('pieces',accessories[1])['unit_cost_cents']==1500


def test_ineligible_duplicate_units_and_under_accessory_cost_roll_back(system):
    store,p,*_=system;sales,client,produced,bought,accessories=prepared(system)
    with pytest.raises(ValueError):sales.create_stock_sale(client,[bought[0]],[accessories[0]],actual_total='10')
    with pytest.raises(ValueError):sales.create_stock_sale(client,[bought[0],bought[0]])
    with pytest.raises(ValueError):sales.create_stock_sale(client,[bought[0]],[produced[0]])
    assert not sales.orders()
    assert p.inventory.get('pieces',bought[0])['state']=='available'
    order=sales.create_stock_sale(client,[bought[0]])
    with pytest.raises(ValueError):sales.create_stock_sale(client,[bought[1],bought[0]])
    assert len(sales.orders())==1
    assert p.inventory.get('pieces',bought[1])['state']=='available'
