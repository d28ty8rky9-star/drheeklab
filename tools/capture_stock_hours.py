"""Demonstration-only Qt captures of hours, planning cost and purchased stock."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
from tempfile import TemporaryDirectory
from PySide6.QtWidgets import QApplication
from drheeklab.storage import Storage
from drheeklab.production import Production
from drheeklab.ui import Window
from drheeklab.recipe_ui import RecipeDialog
from drheeklab.phase3_ui import ReceiptDialog
app=QApplication.instance() or QApplication([])
out=Path('docs/capturas-estoque-horas');out.mkdir(parents=True,exist_ok=True)
with TemporaryDirectory(prefix='drheek-stock-hours-') as temp:
    store=Storage(Path(temp)/'data');p=Production(store)
    spool=p.catalog.save_filament({'name':'PLA azul • demonstração','brand':'Exemplo','material':'PLA','color':'Azul','purchase':'100','initial_grams':'1000','remaining_grams':'1000','reference_per_g':'0.2'})
    product=p.products.save({'name':'Dragão luminoso • demonstração','category':'decorative','settings':'0,2 mm / 15%','estimated_minutes':90,'filament_id':spool})
    path=Path(temp)/'dragao.stl';path.write_text('solid demonstration');project=p.products.import_media(product,path,'project')
    variant=p.products.variants(product)[0]['id'];p.save_recipe(variant,1,project,90,[(spool,'25')],'2','0,2 mm / 15%')
    window=Window(store);window.resize(1600,1000);window.show();window.navigate(2);window.products_page.select_product(product)
    app.processEvents();window.grab().save(str(out/'valor-producao.png'))
    form=RecipeDialog(p,variant,window);form.show();app.processEvents();form.grab().save(str(out/'ficha-horas.png'));form.close()
    window.navigate(3);form=ReceiptDialog(window.stock_page.inventory,window)
    form.fields['entry_kind'].setCurrentIndex(form.fields['entry_kind'].findData('purchased'))
    for key,value in {'name':'Scorpion comprado • demonstração','quantity':'1','total_cost':'50','source':'Compra particular • demonstração','condition':'Novo e revisado','reviewer':'Proprietário','suggested_price':'80'}.items():form.fields[key].setText(value)
    form.fields['state'].setCurrentIndex(form.fields['state'].findData('available'));form.checked.setChecked(True)
    form.show();app.processEvents();form.grab().save(str(out/'nova-peca-comprada.png'));form.persist();form.close()
    window.stock_page.refresh();window.stock_page.tabs.setCurrentIndex(2);app.processEvents();window.grab().save(str(out/'estoque.png'))
    window.navigate(4);window.finance_page.tabs.setCurrentIndex(4);app.processEvents();window.grab().save(str(out/'financeiro.png'))
    window.close()
