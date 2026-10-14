"""Capture the actual New piece dialog with isolated demonstration data."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from tempfile import TemporaryDirectory
from pathlib import Path
from PySide6.QtWidgets import QApplication
from drheeklab.storage import Storage
from drheeklab.production import Production
from drheeklab.phase3_ui import ProductDialog
from drheeklab.ui import Window
app=QApplication.instance() or QApplication([])
out=Path('docs/capturas-cadastro-producao');out.mkdir(parents=True,exist_ok=True)
with TemporaryDirectory(prefix='drheek-piece-') as temp:
    store=Storage(Path(temp)/'data');p=Production(store)
    ids=[p.catalog.save_filament({'name':name+' • demonstração','brand':'Exemplo','material':'PLA','color':name,'purchase':'100','initial_grams':'1000','remaining_grams':'1000','reference_per_g':'0.2'}) for name in ('Azul','Branco')]
    window=Window(store);window.resize(1600,1000);window.show();window.navigate(2)
    form=ProductDialog(p.products,parent=window)
    form.fields['name'].setText('DRAGÃO • demonstração');form.fields['printer_id'].setCurrentIndex(form.fields['printer_id'].findData(1));form.fields['estimated_hours'].setText('10');form.fields['settings'].setText('0,2 mm / 15%')
    controls=form.production_fields;controls.editor.filaments[0][1].setText('100');controls.editor.add_spool()
    combo,grams,_=controls.editor.filaments[1];combo.setCurrentIndex(combo.findData(ids[1]));grams.setText('50')
    controls.extras.add({'name':'Argola','quantity':'2','unit_cost':'0.5'})
    form.show();app.processEvents();form.grab().save(str(out/'nova-peca-completa.png'))
    controls.tabs.setCurrentIndex(1);app.processEvents();form.grab().save(str(out/'extras-na-nova-peca.png'))
    form.close();window.close()
