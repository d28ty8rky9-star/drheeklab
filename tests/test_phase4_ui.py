import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from datetime import date,timedelta
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication,QDialog,QMessageBox
from PySide6.QtCore import Qt
from drheeklab.storage import Storage
from drheeklab.sales import Sales
from drheeklab.ui import Window
from drheeklab.phase4_ui import ClientDialog,CommercialDialog,ApproveDialog,PaymentDialog,CancelDialog,OrderDetails,DeliveryDialog,ReturnDialog

APP=QApplication.instance() or QApplication([])


def fields(dialog,data):
    for key,value in data.items():dialog.fields[key].setText(value)


def test_client_quote_approval_deposit_installments_and_receipt_ui(tmp_path):
    store=Storage(tmp_path);sales=Sales(store)
    client=ClientDialog(sales);client.submit();assert client.result()!=QDialog.Accepted
    fields(client,{'name':'Maria','phone':'1199999','email':'maria@example.com'});client.submit();assert client.result()==QDialog.Accepted
    quote=CommercialDialog(sales,'quote')
    quote.item_rows[0]['description'].setText('Peça personalizada');quote.item_rows[0]['price'].setText('100')
    quote.submit();assert quote.result()==QDialog.Accepted,quote.error.text()
    approve=ApproveDialog(sales,quote.saved_id)
    fields(approve,{'count':'2','deposit':'30','first_due':(date.today()+timedelta(days=30)).strftime('%d/%m/%Y')})
    approve.prepare_plan();assert approve.installments.listing.rowCount()==3
    approve.submit();assert approve.result()==QDialog.Accepted,approve.error.text()
    order=approve.saved_id
    assert [i['amount_cents'] for i in sales.installment_status(order)]==[3000,3500,3500]
    assert sales.financial(order)['paid']==3000
    assert sales.financial(order)['balance']==7000
    payment=PaymentDialog(sales,order);fields(payment,{'amount':'20','fee':'0.60'})
    payment.fields['method'].setCurrentIndex(payment.fields['method'].findData('credit_card'))
    payment.submit();assert payment.result()==QDialog.Accepted,payment.error.text()
    assert sales.financial(order)['net_received']==4940
    details=OrderDetails(sales,order)
    assert details.payment_table.rowCount()==2
    assert details.documents_table.rowCount()==3
    assert 'R$ 50,00' in details.info.text()
    details.close();store.close()


def test_order_form_editable_unequal_installments_and_bad_deposit_are_atomic(tmp_path):
    store=Storage(tmp_path);sales=Sales(store);sales.save_client({'name':'Cliente'})
    form=CommercialDialog(sales,'order')
    form.item_rows[0]['description'].setText('Peça');form.item_rows[0]['price'].setText('100')
    fields(form,{'installment_count':'2','deposit':'30'})
    form.prepare_plan();assert form.installments.listing.rowCount()==3
    form.installments.listing.item(1,0).setText('20');form.installments.listing.item(2,0).setText('50')
    form.submit();assert form.result()==QDialog.Accepted,form.error.text()
    assert [r['amount_cents'] for r in sales.installment_status(form.saved_id)]==[3000,2000,5000]
    invalid=CommercialDialog(sales,'order')
    invalid.item_rows[0]['description'].setText('Outra peça');invalid.item_rows[0]['price'].setText('10')
    invalid.fields['deposit'].setText('20');invalid.submit()
    assert invalid.result()!=QDialog.Accepted
    assert len(sales.orders())==1
    invalid.reject();store.close()


def test_draft_restores_items_files_and_installment_values(tmp_path):
    store=Storage(tmp_path);sales=Sales(store);sales.save_client({'name':'Cliente'})
    form=CommercialDialog(sales,'order')
    form.item_rows[0]['description'].setText('Rascunho de pedido');form.item_rows[0]['price'].setText('100')
    fields(form,{'installment_count':'2','deposit':'30'});form.prepare_plan()
    QTest.qWait(800)
    form.reject()
    next_form=CommercialDialog(sales,'order')
    assert next_form.item_rows[0]['description'].text()=='Rascunho de pedido'
    assert next_form.installments.listing.rowCount()==3
    assert next_form.fields['deposit'].text()=='30'
    assert sales.orders()==[]
    next_form.reject();store.close()


def test_cancel_delivery_and_physical_return_dialogs(tmp_path,monkeypatch):
    store=Storage(tmp_path);sales=Sales(store);client=sales.save_client({'name':'Cliente'})
    product=sales.products.save({'name':'Suporte','category':'functional'});variant=sales.products.variants(product)[0]['id']
    sales.inventory.receive(variant,1,'Inicial','available','Nova','init',total_cost='10',reviewer='Responsável')
    order=sales.create_order(client,[{'variant_id':variant,'quantity':1,'unit_price':'30','fulfillment':'stock'}])
    delivery=DeliveryDialog(sales,order)
    delivery.fields['action'].setCurrentIndex(delivery.fields['action'].findData('deliver'))
    delivery.submit();assert delivery.result()==QDialog.Accepted,delivery.error.text()
    assert sales.delivery(order)['state']=='delivered'
    sales.receive_payment(order,'30')
    cancel=CancelDialog(sales,order);cancel.fields['reason'].setText('Devolução acordada')
    monkeypatch.setattr(QMessageBox,'question',lambda *args:QMessageBox.No)
    cancel.submit();assert cancel.result()!=QDialog.Accepted
    assert sales.get('orders',order)['state']=='approved'
    monkeypatch.setattr(QMessageBox,'question',lambda *args:QMessageBox.Yes)
    cancel.submit();assert cancel.result()==QDialog.Accepted,cancel.error.text()
    returned=ReturnDialog(sales,order);returned.choices.item(0).setSelected(True)
    returned.fields['condition'].setText('Peça recebida fisicamente; aguarda verificação')
    returned.submit();assert returned.result()==QDialog.Accepted,returned.error.text()
    assert sales.inventory.summary()[0]['quarantine']==1
    assert sales.inventory.summary()[0]['available']==0
    store.close()


def test_eight_navigation_areas_and_sales_summary_are_integrated(tmp_path):
    store=Storage(tmp_path);sales=Sales(store);client=sales.save_client({'name':'Cliente'})
    order=sales.create_order(client,[{'description':'Peça','unit_price':'100'}]);sales.receive_payment(order,'30')
    window=Window(store);window.show();APP.processEvents()
    assert window.pages.count()==7
    assert 'R$ 100,00' in window.business_summary.text() and 'R$ 70,00' in window.business_summary.text()
    window.navigate(1)
    assert window.sales_page.client_table.rowCount()==1
    assert window.sales_page.order_table.rowCount()==1
    window.open_calculator()
    assert window.sales_page.tabs.currentIndex()==4
    window.close()
