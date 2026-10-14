"""Actual Qt captures using disposable demonstration data, never the user's DB."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
from tempfile import TemporaryDirectory
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage,QColor
from drheeklab.storage import Storage
from drheeklab.production import Production,CHECKS
from drheeklab.ui import Window
from drheeklab.recipe_ui import RecipeDialog
app=QApplication.instance() or QApplication([])
out=Path('docs/capturas-fluxo-producao');out.mkdir(parents=True,exist_ok=True)
with TemporaryDirectory(prefix='drheek-recipe-') as temp:
    store=Storage(Path(temp)/'data');p=Production(store)
    spool=p.catalog.save_filament({'name':'PLA azul • demonstração','brand':'Exemplo','material':'PLA','color':'Azul','purchase':'100','initial_grams':'1000','remaining_grams':'1000','reference_per_g':'0.2'})
    product=p.products.save({'name':'Dragão luminoso • demonstração','category':'decorative','settings':'0,2 mm / 15% / 210 C','estimated_minutes':60,'filament_id':spool})
    source=Path(temp)/'dragao.stl';source.write_text('solid demonstration\nendsolid demonstration')
    project=p.products.import_media(product,source,'project');variant=p.products.variants(product)[0]['id']
    p.save_recipe(variant,1,project,60,[(spool,'25')],'1','0,2 mm / 15% / 210 C')
    window=Window(store);window.resize(1600,1000);window.show();window.navigate(2);window.products_page.select_product(product)
    form=RecipeDialog(p,variant,window);form.show();app.processEvents();form.grab().save(str(out/'ficha-producao.png'));form.close()
    form=window.workshop.prepare_order();form.fields['quantity'].setText('2');form.fields['responsible'].setText('Operador • demonstração');form.show();app.processEvents();form.grab().save(str(out/'nova-op.png'));form.persist();op=form.saved_id;form.close()
    window.workshop.refresh();app.processEvents();window.grab().save(str(out/'producao.png'))
    p.start(op);p.confirm_from_recipe(op)
    photos={}
    for view,color in [('front','red'),('back','green'),('detail','blue')]:
        image=QImage(40,30,QImage.Format_RGB32);image.fill(QColor(color));path=Path(temp)/(view+'.png');image.save(str(path));photos[view]=path
    for piece in p.pieces(op):
        p.inspect(op,piece['id'],'approved',{key:{'result':'ok'} for key in CHECKS[piece['category']]},photos,'QA • demonstração','Acabamento e detalhes revisados.')
    p.complete(op)
    window.navigate(3);window.stock_page.tabs.setCurrentIndex(2);app.processEvents();window.grab().save(str(out/'estoque.png'))
    window.navigate(4);window.finance_page.tabs.setCurrentIndex(4);app.processEvents();window.grab().save(str(out/'financeiro.png'))
    window.close()
