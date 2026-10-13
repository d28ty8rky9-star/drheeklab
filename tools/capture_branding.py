"""Capture the final home/sidebar and About using isolated TESTES data."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
from tempfile import TemporaryDirectory
from PySide6.QtWidgets import QApplication,QTabWidget
from drheeklab.storage import Storage
from drheeklab.ui import Window
from drheeklab import __version__
app=QApplication.instance() or QApplication([])
out=Path('docs')/('capturas-'+__version__);out.mkdir(parents=True,exist_ok=True)
with TemporaryDirectory(prefix='drheek-branding-') as temp:
    window=Window(Storage(Path(temp)));window.resize(1440,960);window.show();app.processEvents()
    window.grab().save(str(out/'inicio.png'))
    window.navigate(6)
    tabs=next(t for t in window.pages.widget(6).findChildren(QTabWidget) if any(t.tabText(i)=='Sobre' for i in range(t.count())))
    tabs.setCurrentIndex(next(i for i in range(tabs.count()) if tabs.tabText(i)=='Sobre'))
    app.processEvents();window.grab().save(str(out/'sobre.png'))
    window.toggle_sidebar();app.processEvents();window.grab().save(str(out/'menu-recolhido.png'))
    window.close();app.processEvents()
