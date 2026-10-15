import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication,QDialog
from PySide6.QtGui import QImage,QColor
from drheeklab.storage import Storage
from drheeklab.ui import Window
from drheeklab.production import Production
from drheeklab.recipe_ui import RecipeDialog,RecipeConfirmDialog
from drheeklab.phase5_ui import InspectionDialog
APP=QApplication.instance() or QApplication([])

def test_real_recipe_minimal_op_inspection_stock_and_finance(tmp_path,monkeypatch):
    store=Storage(tmp_path/'data');p=Production(store)
    spool=p.catalog.save_filament({'name':'PLA','brand':'Teste','material':'PLA','color':'Azul','purchase':'100','initial_grams':'1000','remaining_grams':'1000','reference_per_g':'0.2'})
    product=p.products.save({'name':'Dragão','category':'decorative','settings':'0,2 mm / 15%','estimated_minutes':60,'filament_id':spool})
    variant=p.products.variants(product)[0]['id']
    path=tmp_path/'dragon.stl';path.write_text('solid dragon');project=p.products.import_media(product,path,'project')
    window=Window(store);window.show();window.navigate(2);window.products_page.select_product(product)
    form=RecipeDialog(p,variant,window)
    assert form.editor.project.currentData()==project
    assert form.editor.filaments[0][0].currentData()==spool
    form.editor.filaments[0][1].setText('25');form.editor.aux.setText('1');form.show_estimate()
    assert 'R$ 4,60' in form.preview.text()
    form.submit();assert form.result()==QDialog.Accepted,form.error.text()
    assert not p.inventory.pieces()
    reopen=RecipeDialog(p,variant,window)
    assert reopen.editor.filaments[0][1].text()=='25'
    assert reopen.fields['hours'].text()=='1';reopen.reject()
    order=window.workshop.prepare_order();order.fields['quantity'].setText('2');order.fields['responsible'].setText('Operador')
    assert set(order.fields)=={'quantity','responsible','priority','item'}
    monkeypatch.setattr(window.workshop,'prepare_order',lambda:order)
    monkeypatch.setattr(order,'exec',lambda:(order.submit(),order.result())[1])
    window.workshop.produce_button.click();assert order.result()==QDialog.Accepted,order.error.text()
    op=order.saved_id;p.start(op)
    confirm=RecipeConfirmDialog(p,op,window);confirm.submit();assert confirm.result()==QDialog.Accepted,confirm.error.text()
    window.navigate(3);stock=window.stock_page
    tabs=[stock.tabs.tabText(i) for i in range(stock.tabs.count())]
    assert 'Estoque de peças' in tabs and 'Peças prontas' not in tabs and 'Peças físicas' not in tabs
    assert stock.pieces_table.rowCount()==0
    window.navigate(4);assert window.finance_page.tables['production'].rowCount()==0
    for piece in p.pieces(op):
        form=InspectionDialog(p,op,piece,window);form.fields['responsible'].setText('QA');form.fields['notes'].setText('Acabamento revisado.')
        for combo,reason in form.checks.values():combo.setCurrentIndex(combo.findData('ok'))
        for index,(key,field) in enumerate(form.photos.items()):
            image=QImage(20,20,QImage.Format_RGB32);image.fill(QColor(['red','green','blue'][index]));path=tmp_path/(key+'.png');assert image.save(str(path));field.setText(str(path))
        form.submit();assert form.result()==QDialog.Accepted,form.error.text()
    p.complete(op);window.navigate(3)
    assert stock.pieces_table.rowCount()==2
    assert stock.pieces_table.item(0,4).text()=='R$ 4,60'
    stock.pieces_table.selectRow(0)
    from drheeklab.phase3_ui import ReserveDialog
    monkeypatch.setattr(ReserveDialog,'exec',lambda dialog:(dialog.fields['reference'].setText('Cliente'),dialog.submit(),dialog.result())[-1])
    stock.reserve();assert stock.reservations_table.rowCount()==1
    window.navigate(4)
    assert window.finance_page.tables['production'].rowCount()==1
    assert 'R$ 9,20' in window.finance_page.stock_value_label.text()
    assert window.finance_page.report_data['metrics']['cash_flow_cents']==0
    window.navigate(2)
    assert window.production_page.piece_table.isColumnHidden(4)
    assert 'Custo' not in window.production_page.summary_label.text()
    window.close()
