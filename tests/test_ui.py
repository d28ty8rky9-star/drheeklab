import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication, QDialog
from drheeklab.storage import Storage
from drheeklab.ui import Login, Window, AREAS

APP = QApplication.instance() or QApplication([])

def test_first_login_and_reauthentication(tmp_path):
    store = Storage(tmp_path)
    dialog = Login(store)
    dialog.password.setText("senha de testes")
    dialog.confirm.setText("senha diferente")
    dialog.submit()
    assert dialog.result() != QDialog.Accepted
    dialog.confirm.setText("senha de testes")
    dialog.submit()
    assert dialog.result() == QDialog.Accepted
    login = Login(store)
    login.password.setText("errada")
    login.submit()
    assert login.result() != QDialog.Accepted
    login.password.setText("senha de testes")
    login.submit()
    assert login.result() == QDialog.Accepted
    store.close()

def test_navigation_theme_sidebar_and_draft_recovery(tmp_path):
    store = Storage(tmp_path)
    window = Window(store)
    window.show()
    APP.processEvents()
    assert window.isVisible()
    assert window.pages.count() == 8
    for index, name in enumerate(AREAS):
        window.buttons[index].click()
        assert window.pages.currentIndex() == index
        assert window.page_title.text() == name
    window.toggle_theme()
    window.toggle_sidebar()
    window.notes.setPlainText("Rascunho recuperável")
    window.save_draft()
    window.close()
    reopened = Storage(tmp_path)
    second = Window(reopened)
    assert second.theme == "light"
    assert second.collapsed is True
    assert second.notes.toPlainText() == "Rascunho recuperável"
    second.close()

def test_single_instance_lock(tmp_path):
    from PySide6.QtCore import QLockFile
    first = QLockFile(str(tmp_path / '.test.lock'))
    second = QLockFile(str(tmp_path / '.test.lock'))
    assert first.tryLock(0)
    assert not second.tryLock(0)
    first.unlock()
    assert second.tryLock(0)
    second.unlock()
