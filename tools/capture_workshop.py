"""Capture the unified workspace with isolated demonstration records."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
from tempfile import TemporaryDirectory
from PySide6.QtWidgets import QApplication
from drheeklab.storage import Storage
from drheeklab.ui import Window
from drheeklab.products import Products
app=QApplication.instance() or QApplication([])
out=Path('docs/capturas-producao-unificada');out.mkdir(exist_ok=True)
with TemporaryDirectory(prefix='drheek-workshop-') as temp:
    storage=Storage(Path(temp)/'data');products=Products(storage)
    for name in ['Suporte articulado','Vaso geométrico','Organizador modular']:
        identifier=products.save({'name':name+' • demonstração','category':'functional','settings':'0,2 mm / 15%','estimated_minutes':'90'})
        project=Path(temp)/(str(identifier)+'.stl');project.write_text('solid model\nendsolid model');products.import_media(identifier,project,'project')
    window=Window(storage);window.resize(1600,1000);window.show();window.navigate(2)
    window.products_page.select_product(1);app.processEvents();window.grab().save(str(out/'producao.png'))
    window.workshop.details_button.setChecked(True);app.processEvents();window.grab().save(str(out/'ficha.png'))
    window.close()
