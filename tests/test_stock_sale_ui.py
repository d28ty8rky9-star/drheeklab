from PySide6.QtCore import Qt
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
    form.pieces.item(next(i for i,r in enumerate(form.piece_rows) if r['id']==bought[1]),0).setCheckState(Qt.Checked)
    form.accessories.item(next(i for i,r in enumerate(form.accessory_rows) if r['id']==accessories[1]),0).setCheckState(Qt.Checked)
    assert form.fields['actual_total'].text()=='80'
    assert 'R$ 80,00' in form.summary.text()
    form.fields['actual_total'].setText('75');form.fields['actual_total'].setModified(True);form.recalculate()
    assert 'R$ 75,00' in form.actual_summary.text()
    assert 'Lucro bruto: R$ 10,00' in form.actual_summary.text()
    assert '20,00%' in form.actual_summary.text()
    form.submit();assert form.result()==QDialog.Accepted,form.error.text()
    assert sales.financial(form.saved_id)['total']==7500
    window.close()


def test_stock_accessory_form_and_sale_breakdown_use_historical_cost(system):
    store,p,*_=system;sales,client,produced,bought,accessories=prepared(system)
    window=Window(store);window.navigate(3)
    assert 'Acessórios' in [window.stock_page.tabs.tabText(i) for i in range(window.stock_page.tabs.count())]
    assert window.stock_page.accessories_table.rowCount()==2
    assert window.stock_page.pieces_table.rowCount()==4
    assert 'Auxiliares' not in [window.stock_page.tabs.tabText(i) for i in range(window.stock_page.tabs.count())]
    assert window.stock_page.totals['piece_cents']==10620
    assert window.stock_page.totals['accessory_cents']==3000
    form=ReceiptDialog(p.inventory,window);form.fields['entry_kind'].setCurrentIndex(form.fields['entry_kind'].findData('accessory'))
    for key,value in {'name':'Argola','quantity':'2','total_cost':'2','source':'Compra','condition':'Nova','reviewer':'QA'}.items():form.fields[key].setText(value)
    form.fields['state'].setCurrentIndex(form.fields['state'].findData('available'));form.checked.setChecked(True);form.submit()
    assert form.result()==QDialog.Accepted,form.error.text()
    dialog=StockSaleDialog(sales,window)
    dialog.pieces.item(next(i for i,r in enumerate(dialog.piece_rows) if r['id']==produced[0]),0).setCheckState(Qt.Checked)
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


def test_checkbox_selection_survives_filter_and_total_does_not_add_accessory_twice(system):
    store,p,*_=system;sales,client,produced,bought,accessories=prepared(system)
    form=StockSaleDialog(sales)
    row=next(i for i,r in enumerate(form.piece_rows) if r['id']==produced[0])
    form.pieces.item(row,0).setCheckState(Qt.Checked)
    form.accessories.item(0,0).setCheckState(Qt.Checked)
    assert form.fields['actual_total'].text()=='21.2'
    form.filter_stock(form.pieces,'Scorpion')
    assert form.quote()['suggested_cents']==2120
    form.fields['actual_total'].setText('30');form.fields['actual_total'].setModified(True)
    assert 'Lucro bruto: R$ 11,90' in form.actual_summary.text()
    assert '383,87%' in form.actual_summary.text()
    form.fields['client'].setCurrentIndex(form.fields['client'].findData(client))
    form.submit();assert form.result()==QDialog.Accepted,form.error.text()
    assert sales.financial(form.saved_id)['total']==3000
    assert sales.items(form.saved_id)[1]['unit_price_cents']==1500


def test_issued_units_hidden_from_stock_but_journal_and_return_preserved(system):
    store,p,*_=system;sales,client,produced,bought,accessories=prepared(system)
    window=Window(store);page=window.stock_page
    sale=sales.create_stock_sale(client,[bought[0]],[accessories[0]])
    page.refresh()
    assert bought[0] in {r['id'] for r in page.piece_rows}
    assert accessories[0] in {r['id'] for r in page.accessory_rows}
    sales.deliver(sale,'send','shipping',carrier='Correios');page.refresh()
    assert bought[0] not in {r['id'] for r in page.piece_rows}
    assert accessories[0] not in {r['id'] for r in page.accessory_rows}
    assert {r['piece_id'] for r in p.inventory.movements() if r['kind']=='issue'}=={bought[0],accessories[0]}
    assert p.inventory.get('pieces',bought[0])['state']=='issued'
    sales.cancel(sale,'Devolução')
    sales.return_cancelled_pieces(sale,[bought[0],accessories[0]],'Retorno conferido');page.refresh()
    assert bought[0] in {r['id'] for r in page.piece_rows}
    assert accessories[0] in {r['id'] for r in page.accessory_rows}
    assert next(r for r in page.accessory_rows if r['id']==accessories[0])['state']=='quarantine'
    window.close()
