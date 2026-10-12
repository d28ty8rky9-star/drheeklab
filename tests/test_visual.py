import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from drheeklab.storage import Storage
from drheeklab.ui import Window
from drheeklab.products import Products
from drheeklab.sales import Sales

APP=QApplication.instance() or QApplication([])

def test_product_table_keeps_selection_and_edit_target(tmp_path):
    store=Storage(tmp_path);products=Products(store)
    first=products.save({'name':'Primeira peça','category':'functional'})
    second=products.save({'name':'Segunda peça','category':'decorative'})
    window=Window(store);page=window.products_page
    window.presentation.toggle_products(page)
    table=window.presentation.product_table
    table.selectRow(window.presentation.product_ids.index(second))
    assert page.selected_product(False)==second
    page.search.setText('Primeira')
    assert table.rowCount()==1
    table.selectRow(0)
    assert page.selected_product(False)==first
    window.presentation.toggle_products(page)
    assert page.selected_product(False)==first
    window.close()

def test_filter_preserves_original_row_identity_and_reports(tmp_path):
    store=Storage(tmp_path);sales=Sales(store)
    sales.save_client({'name':'Aurora'});second=sales.save_client({'name':'Prisma'})
    window=Window(store);page=window.sales_page
    search=next(search for search,table in window.presentation.filters if table is page.client_table)
    search.setText('Prisma')
    assert page.client_table.isRowHidden(0)
    assert not page.client_table.isRowHidden(1)
    page.client_table.selectRow(1)
    assert page.selected(page.client_table,page.client_rows)==second
    page.refresh()
    assert page.client_table.isRowHidden(0)
    assert window.presentation.strips[1].cards[0].value.text()=='R$ 0,00'
    window.close()

def test_order_payment_status_uses_existing_financial_balances(tmp_path):
    store=Storage(tmp_path);sales=Sales(store);client=sales.save_client({'name':'Cliente'})
    orders=[sales.create_order(client,[{'description':'Peça','quantity':1,'unit_price':'50','fulfillment':'production'}]) for _ in range(3)]
    sales.receive_payment(orders[1],'20');sales.receive_payment(orders[2],'50')
    window=Window(store);page=window.sales_page
    statuses={row['id']:page.order_table.item(i,9).text() for i,row in enumerate(page.order_rows)}
    assert [statuses[order] for order in orders]==['Pendente','Parcial','Quitado']
    assert [sales.financial(order)['balance'] for order in orders]==[5000,3000,0]
    window.close()

def test_original_signal_refresh_keeps_text_filter_applied(tmp_path):
    store=Storage(tmp_path);sales=Sales(store)
    first=sales.save_client({'name':'Aurora'});second=sales.save_client({'name':'Prisma'})
    sales.archive_client(first,True,'Teste');sales.archive_client(second,True,'Teste')
    window=Window(store);page=window.sales_page
    search=next(search for search,table in window.presentation.filters if table is page.client_table)
    search.setText('Prisma');page.trash.setChecked(True)
    assert page.client_table.rowCount()==2
    assert page.client_table.isRowHidden(0)
    assert not page.client_table.isRowHidden(1)
    window.close()

def test_official_branding_icons_and_scrollable_sidebar(tmp_path):
    from drheeklab import __version__
    from drheeklab.menu_icons import menu_icons
    window=Window(Storage(tmp_path));window.show();window.resize(780,560);APP.processEvents()
    assert not window.logo.pixmap().isNull()
    assert not window.windowIcon().isNull()
    assert window.logo.parentWidget() is window.sidebar
    assert __version__ in window.brand_version.text()
    assert all(not icon.isNull() for icon in menu_icons())
    assert all(not button.icon().isNull() for button in window.buttons)
    window.sidebar_scroll.ensureWidgetVisible(window.buttons[-1]);APP.processEvents()
    window.buttons[-1].click()
    assert window.pages.currentIndex()==7
    window.toggle_sidebar();APP.processEvents()
    assert not window.brand_version.isVisible()
    assert all(button.text()=='' for button in window.buttons)
    window.buttons[0].click();assert window.pages.currentIndex()==0
    window.close()
