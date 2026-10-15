from datetime import timezone,timedelta
from drheeklab.event_dates import event_day
from drheeklab.finance import Finance
from drheeklab.ui import Window
from PySide6.QtWidgets import QApplication
from test_recipe_flow import system
from test_stock_sale import prepared

APP=QApplication.instance() or QApplication([])


def test_sent_unpaid_sale_in_local_day_receivables_and_cards(system,monkeypatch):
    import drheeklab.finance as module
    zone=timezone(timedelta(hours=-3))
    monkeypatch.setattr(module,'event_day',lambda v:event_day(v,zone))
    store,p,*_=system;sales,client,produced,bought,accessories=prepared(system)
    order=sales.create_stock_sale(client,[bought[0]],[accessories[0]],actual_total='150')
    sales.deliver(order,'send','shipping',carrier='Correios')
    store.db.execute("UPDATE orders SET created_at='2026-10-15T01:00:00+00:00' WHERE id=?",(order,));store.db.commit()
    finance=Finance(store)
    report=finance.report('2026-10-01','2026-10-14')
    assert report['metrics']['sold_cents']==15000
    assert report['metrics']['receivable_cents']==15000
    assert report['metrics']['received_net_cents']==0
    assert report['receivables'][0]['balance_cents']==15000
    assert not finance.report('2026-10-01','2026-10-13')['receivables']
    window=Window(store);page=window.finance_page
    page.start.setText('01/10/2026');page.end.setText('14/10/2026');window.navigate(4)
    assert page.tables['receivables'].rowCount()==1
    assert window.presentation.strips[4].cards[0].value.text()=='R$ 150,00'
    assert window.presentation.strips[4].cards[2].value.text()=='R$ 150,00'
    assert window.presentation.strips[4].cards[1].value.text()=='R$ 0,00'
    window.close()


def test_timestamp_local_date_without_changing_stored_timestamp():
    zone=timezone(timedelta(hours=-3))
    assert event_day('2026-10-15T01:00:00+00:00',zone)=='2026-10-14'
    assert event_day('2026-10-15T04:00:00+00:00',zone)=='2026-10-15'
    assert event_day('2026-10-14',zone)=='2026-10-14'
    assert event_day(None,zone) is None


def test_client_receivable_separate_from_credit_updates_with_payment_and_cancel(system):
    store,p,*_=system;sales,client,produced,bought,accessories=prepared(system)
    order=sales.create_stock_sale(client,[bought[0]],actual_total='150')
    window=Window(store);window.navigate(1);page=window.sales_page
    assert page.client_table.item(0,4).text()=='R$ 150,00'
    assert page.client_table.item(0,5).text()=='R$ 0,00'
    assert page.client_table.item(0,6).text()=='R$ 150,00'
    assert page.client_table.item(0,7).text()=='R$ 0,00'
    sales.receive_payment(order,'50','pix');page.refresh()
    assert page.client_table.item(0,5).text()=='R$ 50,00'
    assert page.client_table.item(0,6).text()=='R$ 100,00'
    sales.cancel(order,'Desistência',refund='50');page.refresh()
    assert page.client_table.item(0,4).text()=='R$ 0,00'
    assert page.client_table.item(0,5).text()=='R$ 0,00'
    assert page.client_table.item(0,6).text()=='R$ 0,00'
    window.close()
