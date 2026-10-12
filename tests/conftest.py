"""Release Qt widgets before QApplication/interpreter shutdown.

Several UI modules share one QApplication. Hidden dialogs and Python signal
cycles otherwise leave native widgets alive when module globals are cleared.
Clean up after each test so application-wide styles do not revisit hidden
widgets from earlier tests. The suite must return a normal process exit.
"""
import gc
import pytest
from PySide6.QtCore import QCoreApplication,QEvent
from PySide6.QtWidgets import QApplication


@pytest.fixture(autouse=True)
def release_qt_widgets_after_test():
    yield
    app=QApplication.instance()
    if app is not None:
        widgets=app.topLevelWidgets()
        if not widgets:return
        for widget in widgets:
            widget.deleteLater()
        QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)
        app.processEvents()
        gc.collect()
