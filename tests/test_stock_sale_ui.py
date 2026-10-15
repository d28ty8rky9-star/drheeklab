from PySide6.QtWidgets import QApplication,QDialog
from drheeklab.ui import Window
from drheeklab.stock_sale_ui import StockSaleDialog
from drheeklab.phase3_ui import ReceiptDialog
from test_recipe_flow import system
from test_stock_sale import prepared
APP=QApplication.instance() or QApplication([])


def test_new_sale_client_stock_accessories_and_real_price_without_retyping(system):
    store,p,*_=system;sales,client,produced,bought,accessories=prepared(system)
    window=Window(store);window.navigate(1)
    assert window.sales_page.new_sale_button.text()=='Nova venda'
    assert [window.sales_page.tabs.tabText(i) for i in range(5)]==['Vendas','Orçamentos','Clientes','Contas a pagar e receber','Precificação']
    form=StockSaleDialog(sales,window);form.fields['client'].setCurrentIndex(form.fields['client'].findData(client))
    form.pieces.selectRow(next(i for i,r in enumerate(form.piece_rows) if r['id']==bought[1]))
    form.accessories.selectRow(next(i for i,r in enumerate(form.accessory_rows) if r['id']==accessories[1]))
    assert form.fields['actual_total'].text()=='65'
    assert 'R$ 80,00' in form.summary.text()
    form.fields['actual_total'].setText('60');form.fields['actual_total'].setModified(True);form.recalculate()
    assert 'R$ 75,00' in form.actual_summary.text()
    form.submit();assert form.result()==QDialog.Accepted,form.error.text()
    assert sales.financial(form.saved_id)['total']==7500
    window.close()


def test_stock_accessory_form_and_sale_breakdown_use_historical_cost(system):
    store,p,*_=system;sales,client,produced,bought,accessories=prepared(system)
    window=Window(store);window.navigate(3)
    assert 'Acessórios' in [window.stock_page.tabs.tabText(i) for i in range(window.stock_page.tabs.count())]
    assert window.stock_page.accessories_table.rowCount()==2
    form=ReceiptDialog(p.inventory,window);form.fields['entry_kind'].setCurrentIndex(form.fields['entry_kind'].findData('accessory'))
    for key,value in {'name':'Argola','quantity':'2','total_cost':'2','source':'Compra','condition':'Nova','reviewer':'QA'}.items():form.fields[key].setText(value)
    form.fields['state'].setCurrentIndex(form.fields['state'].findData('available'));form.checked.setChecked(True);form.submit()
    assert form.result()==QDialog.Accepted,form.error.text()
    dialog=StockSaleDialog(sales,window)
    dialog.pieces.selectRow(next(i for i,r in enumerate(dialog.piece_rows) if r['id']==produced[0]))
    details=dialog.details.toPlainText()
    assert 'Tempo total da tentativa' in details and 'Filamento' in details and 'já inclui rateio' in details
    assert 'Custo da unidade: R$ 3,10' in details
    window.close()


def test_sales_accounts_share_finance_obligations_and_payments(system):
    from drheeklab.phase6_ui import PayableDialog,PayDialog
    store,*_=system
    window=Window(store);page=window.sales_page
    form=PayableDialog(page.finance,page)
    form.fields['description'].setText('Conta de teste');form.fields['amount'].setText('20')
    form.submit();assert form.result()==QDialog.Accepted,form.error.text()
    page.refresh();assert page.payables_table.rowCount()==1
    payment=PayDialog(page.finance,page.payable_rows[0],page)
    payment.submit();assert payment.result()==QDialog.Accepted,payment.error.text()
    page.refresh();assert page.payable_rows[0]['balance_cents']==0
    window.finance_page.refresh()
    assert window.finance_page.report_data['payables'][0]['paid_cents']==2000
    window.close()
