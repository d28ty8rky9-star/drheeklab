import json
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox
from drheeklab.storage import Storage
from drheeklab.catalog import Catalog
from drheeklab.ui import Window
from drheeklab.phase2_ui import PrinterDialog, FilamentDialog, ActualDialog, PricingDefaults, MaintenanceDialog

APP = QApplication.instance() or QApplication([])


def set_fields(dialog, fields):
    for key, value in fields.items():
        dialog.fields[key].setText(value)


def new_spool(catalog, parent=None):
    dialog = FilamentDialog(catalog, parent=parent)
    set_fields(dialog, {'brand': 'Marca', 'color': 'Azul', 'name': 'PLA azul', 'purchase': '100', 'reference_per_g': '0.1'})
    dialog.submit()
    assert dialog.result() == QDialog.Accepted
    return dialog.saved_id


def test_forms_save_edit_and_validate_printer_filament_maintenance(tmp_path):
    store = Storage(tmp_path)
    catalog = Catalog(store)
    printer = PrinterDialog(catalog)
    printer.submit()
    assert printer.result() != QDialog.Accepted
    set_fields(printer, {'manufacturer': 'Bambu Lab', 'model': 'A1', 'identifier': 'A1-02', 'acquired_on': '02/01/2026', 'purchase': '2400,00'})
    printer.submit()
    assert printer.result() == QDialog.Accepted
    assert catalog.get('printers', printer.saved_id)['acquired_on'] == '2026-01-02'
    assert '1,10' in printer.total.text()
    spool_id = new_spool(catalog)
    edit = FilamentDialog(catalog, spool_id)
    edit.unknown.setChecked(True)
    edit.fields['reason'].setText('Carretel aberto sem pesagem confiável')
    edit.submit()
    assert edit.result() == QDialog.Accepted
    assert catalog.get('filaments', spool_id)['remaining_mg'] is None
    assert catalog.get('filaments', spool_id)['state'] == 'open'
    maintenance = MaintenanceDialog(catalog, 1, None)
    set_fields(maintenance, {'performed_on': '03/01/2026', 'description': 'Lubrificação', 'cost': '20,00', 'next_due': '03/02/2026'})
    maintenance.submit()
    assert maintenance.result() == QDialog.Accepted
    assert catalog.maintenance(1)[0]['cost_cents'] == 2000
    defaults = PricingDefaults(store, None)
    set_fields(defaults, {'markup': '150', 'threshold': '80'})
    defaults.submit()
    assert defaults.result() == QDialog.Accepted
    assert store.get('markup_percent') == '150'
    store.close()


def test_calculator_ui_saves_exact_example_then_confirms_real_cost(tmp_path, monkeypatch):
    store = Storage(tmp_path)
    catalog = Catalog(store)
    spool_id = new_spool(catalog)
    window = Window(store)
    window.show()
    window.navigate(1)
    calculator = window.calculator
    calculator.title.setText('Exemplo aprovado')
    calculator.minutes.setText('0')
    calculator.final.setText('35')
    calculator.spool_rows[0][2].setText('300')
    calculator.preview()
    text = calculator.result.toPlainText()
    assert 'Preço sugerido TOTAL: R$ 90,00' in text
    assert 'Preço final TOTAL: R$ 35,00' in text
    assert 'Desconto: R$ 55,00 • 61,11%' in text
    assert 'Resultado à referência antes de outras despesas: R$ 5,00' in text
    calculator.save()
    identifier = calculator.last_saved_id
    assert identifier is not None
    assert catalog.get('filaments', spool_id)['remaining_mg'] == 1000000
    actual = ActualDialog(catalog, identifier, calculator)
    actual.fields[str(spool_id)].setText('310')
    actual.fields['minutes'].setText('60')
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.Yes)
    actual.submit()
    assert actual.result() == QDialog.Accepted
    assert catalog.get('filaments', spool_id)['remaining_mg'] == 690000
    assert catalog.get('printers', 1)['accumulated_minutes'] == 60
    window.navigate(3)
    assert window.filaments_page.table.item(0, 5).text() == '690 g'
    window.close()
    reopened = Storage(tmp_path)
    assert Catalog(reopened).get('calculations', identifier)['actual']
    reopened.close()


def test_actual_dialog_cancel_does_not_consume(tmp_path, monkeypatch):
    store = Storage(tmp_path)
    catalog = Catalog(store)
    spool_id = new_spool(catalog)
    calculation = catalog.save_calculation('Cancelar confirmação', 1, 60, [(spool_id, '10')])
    dialog = ActualDialog(catalog, calculation)
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.No)
    dialog.submit()
    assert dialog.result() != QDialog.Accepted
    assert catalog.get('calculations', calculation)['actual'] is None
    assert catalog.get('filaments', spool_id)['remaining_mg'] == 1000000
    store.close()


def test_calculator_draft_autosaves_and_suggests_last_spool_on_restart(tmp_path):
    store = Storage(tmp_path)
    catalog = Catalog(store)
    spool_id = new_spool(catalog)
    catalog.save_calculation('Último carretel', 1, 60, [(spool_id, '10')])
    window = Window(store)
    window.show()
    window.navigate(1)
    calculator = window.calculator
    assert calculator.spool_rows[0][1].currentData() == spool_id
    calculator.title.setText('Rascunho incompleto')
    calculator.final.setText('15,75')
    calculator.spool_rows[0][2].setText('123,456')
    QTest.qWait(800)
    draft = json.loads(store.load_draft('calculator'))
    assert draft['title'] == 'Rascunho incompleto'
    assert draft['filaments'] == [[spool_id, '123,456']]
    window.close()
    reopened = Storage(tmp_path)
    restored = Window(reopened)
    assert restored.calculator.title.text() == 'Rascunho incompleto'
    assert restored.calculator.final.text() == '15,75'
    assert restored.calculator.spool_rows[0][2].text() == '123,456'
    restored.close()


def test_known_low_balance_is_visible_in_home_and_inventory(tmp_path):
    store = Storage(tmp_path)
    catalog = Catalog(store)
    spool_id = new_spool(catalog)
    row = catalog.get('filaments', spool_id)
    catalog.db.execute('UPDATE filaments SET remaining_mg=50000 WHERE id=?', (spool_id,))
    catalog.db.commit()
    window = Window(store)
    assert 'PLA azul' in window.low_alert.text()
    assert 'PLA azul' in window.filaments_page.alert.text()
    window.close()
