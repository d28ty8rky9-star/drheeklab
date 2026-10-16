from pathlib import Path
import tomllib
from PySide6.QtWidgets import QApplication,QLabel
from drheeklab import __version__,__display_version__
from drheeklab.storage import Storage,SCHEMA_VERSION
from drheeklab.ui import Window

APP=QApplication.instance() or QApplication([])
ROOT=Path(__file__).resolve().parents[1]


def test_beta_identity_matches_interface_and_windows_update_configuration(tmp_path):
    assert __version__=='2.9.10' and __display_version__=='2.9.10 Beta'
    metadata=tomllib.loads((ROOT/'pyproject.toml').read_text())
    assert metadata['project']['version']==__version__
    store=Storage(tmp_path/'data');window=Window(store)
    assert __display_version__ in window.windowTitle()
    assert __display_version__ in window.brand_version.text()
    assert any(__display_version__ in label.text() for label in window.findChildren(QLabel))
    assert SCHEMA_VERSION==10
    installer=(ROOT/'packaging/installer.iss').read_text()
    assert '#define AppVersion "'+__version__+'"' in installer
    assert 'AppId={{485013A4-F44F-47DF-9C89-9CECB56946A0}' in installer
    assert 'AppVerName=Dr. Heek Lab {#AppVersion} Beta' in installer
    workflow=(ROOT/'.github/workflows/windows.yml').read_text()
    assert 'DrHeekLab-2.9.10-Beta-Setup.exe' in workflow
    assert 'DrHeekLab-Windows-2.9.10-Beta' in workflow
    version_info=(ROOT/'packaging/version_info.txt').read_text()
    assert 'filevers=(2,9,10,0)' in version_info and "'ProductVersion','2.9.10 Beta'" in version_info
    window.close();store.close()
