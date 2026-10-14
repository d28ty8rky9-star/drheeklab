"""Disposable demonstration captures; no user records touched."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from tempfile import TemporaryDirectory
from pathlib import Path
from PySide6.QtWidgets import QApplication
from drheeklab.storage import Storage
from drheeklab.production import Production
from drheeklab.recipe_ui import RecipeDialog
from drheeklab.ui import Window
app=QApplication.instance() or QApplication([])
out=Path('docs/capturas-extras-producao');out.mkdir(parents=True,exist_ok=True)
with TemporaryDirectory(prefix='drheek-extras-') as temp:
    store=Storage(Path(temp)/'data');p=Production(store)
    spool=p.catalog.save_filament({'name':'PLA azul • demonstração','brand':'Exemplo','material':'PLA','color':'Azul','purchase':'100','initial_grams':'1000','remaining_grams':'1000','reference_per_g':'0.2'})
    product=p.products.save({'name':'Chaveiro dragão • demonstração','category':'decorative','estimated_minutes':90,'settings':'0,2 mm / 15%','filament_id':spool})
    path=Path(temp)/'chaveiro.stl';path.write_text('solid demonstration');project=p.products.import_media(product,path,'project');variant=p.products.variants(product)[0]['id']
    p.save_recipe(variant,1,project,90,[(spool,'25')],'0','0,2 mm / 15%',extras=[{'name':'Argola','quantity':'1','unit_cost':'0.5'},{'name':'Embalagem','quantity':'1','unit_cost':'1'}])
    window=Window(store);window.show();window.navigate(2)
    form=RecipeDialog(p,variant,window);form.show();app.processEvents();form.grab().save(str(out/'filamentos-horas.png'))
    form.tabs.setCurrentIndex(1);app.processEvents();form.grab().save(str(out/'extras.png'))
    form.close();window.close()
