from decimal import Decimal
import json
import sqlite3
import pytest
from drheeklab.storage import Storage, SCHEMA_VERSION
from drheeklab.catalog import Catalog
from drheeklab.pricing import calculate, cost_per_gram, hourly_cost, brl, number, compare
from drheeklab.backup import create_backup, restore_backup, verify_backup

@pytest.fixture
def catalog(tmp_path):
    store = Storage(tmp_path)
    yield Catalog(store)
    store.close()


def spool(catalog, **overrides):
    data = dict(brand='Marca', material='PLA', color='Azul', name='PLA azul', purchase='100',
                initial_grams='1000', remaining_grams='1000', reference_per_g='0.1', state='new')
    data.update(overrides)
    return catalog.save_filament(data)


def printer_data(row, **overrides):
    data = {key: row[key] for key in ('manufacturer', 'model', 'identifier', 'acquired_on', 'accumulated_minutes', 'status')}
    for key in ('purchase', 'investment_hour', 'energy_hour', 'maintenance_hour'):
        data[key] = str(Decimal(row[key + '_cents']) / 100)
    data.update(overrides)
    return data


def spool_data(row, **overrides):
    data = {key: row[key] for key in ('brand', 'material', 'color', 'name', 'supplier', 'purchased_on', 'reference_per_g', 'state')}
    data['purchase'] = str(Decimal(row['purchase_cents']) / 100)
    data['initial_grams'] = None if row['initial_mg'] is None else str(Decimal(row['initial_mg']) / 1000)
    data['remaining_grams'] = None if row['remaining_mg'] is None else str(Decimal(row['remaining_mg']) / 1000)
    data.update(overrides)
    return data


def test_seeded_printer_and_defaults_are_exact(catalog):
    row = catalog.get('printers', 1)
    assert (row['manufacturer'], row['model']) == ('Bambu Lab', 'A1 Mini')
    assert row['purchase_cents'] == 240000
    assert (row['investment_hour_cents'], row['energy_hour_cents'], row['maintenance_hour_cents']) == (75, 10, 25)
    assert hourly_cost(row) == Decimal('1.10')
    assert catalog.storage.get('markup_percent') == '200'
    assert catalog.storage.get('low_filament_grams') == '100'
    catalog.save_printer(printer_data(row, energy_hour='0.20'), 1)
    catalog.storage.migrate()
    assert hourly_cost(catalog.get('printers', 1)) == Decimal('1.20')
    assert len(catalog.rows('printers')) == 1


def test_cost_per_gram_and_free_material(catalog):
    assert cost_per_gram('99.90', '1000') == Decimal('0.0999')
    assert cost_per_gram('0', '1000') == 0
    identifier = spool(catalog, purchase='0', reference_per_g='0.12')
    assert catalog.acquisition_per_g(catalog.get('filaments', identifier)) == 0
    result = catalog.estimate(1, 0, [(identifier, '100')])
    assert result['total_cost'] == '12.00'
    assert result['suggested_total'] == '36.00'


def test_unknown_initial_weight_does_not_invent_acquisition_cost(catalog):
    identifier = spool(catalog, initial_grams=None, remaining_grams=None, state='open')
    assert catalog.acquisition_per_g(catalog.get('filaments', identifier)) is None
    assert catalog.estimate(1, 0, [(identifier, '10')])['material_cost'] == '1.00'


def test_multiple_filaments_auxiliary_and_units(catalog):
    first = spool(catalog, reference_per_g='0.10')
    second = spool(catalog, name='PETG vermelho', material='PETG', reference_per_g='0.20')
    result = catalog.estimate(1, 120, [(first, '100'), (second, '50')], auxiliary='7.80', quantity=3)
    assert result['machine_cost'] == '2.20'
    assert result['material_cost'] == '20.00'
    assert result['total_cost'] == '30.00'
    assert result['unit_cost'] == '10.00'
    assert result['suggested_total'] == '90.00'
    assert result['suggested_unit'] == '30.00'


def test_manual_final_price_discount_is_not_applied_twice(catalog):
    identifier = spool(catalog)
    result = catalog.estimate(1, 0, [(identifier, '300')], final='35')
    assert result['total_cost'] == '30.00'
    assert result['suggested_total'] == '90.00'
    assert result['final_total'] == '35.00'
    assert result['adjustment_kind'] == 'desconto'
    assert result['adjustment_amount'] == '55.00'
    assert result['adjustment_percent'] == '61.11'
    assert result['commercial_result'] == '5.00'


@pytest.mark.parametrize('final,kind,amount,result', [
    ('100', 'acréscimo', '10.00', '70.00'),
    ('90', 'sem alteração', '0.00', '60.00'),
    ('0', 'desconto', '90.00', '-30.00')])
def test_final_price_above_equal_or_zero(catalog, final, kind, amount, result):
    identifier = spool(catalog)
    snapshot = catalog.estimate(1, 0, [(identifier, '300')], final=final)
    assert snapshot['adjustment_kind'] == kind
    assert snapshot['adjustment_amount'] == amount
    assert snapshot['commercial_result'] == result
    assert snapshot['final_total'] == str(Decimal(final).quantize(Decimal('.01')))


def test_zero_cost_and_zero_base_percent_are_explicit(catalog):
    identifier = spool(catalog, purchase='0', reference_per_g='0')
    result = catalog.estimate(1, 0, [(identifier, '10')], final='5')
    assert result['total_cost'] == '0.00'
    assert result['suggested_total'] == '0.00'
    assert result['adjustment_percent'] is None
    assert compare(result, {**result, 'total_cost': '1.00'})['percent'] is None


def test_rounding_is_half_up_per_line_and_totals_reconcile(catalog):
    identifier = spool(catalog, reference_per_g='0.005')
    result = catalog.estimate(1, 0, [(identifier, '1')], quantity=3)
    assert result['material_cost'] == '0.01'
    assert result['suggested_total'] == '0.03'
    assert sum(Decimal(row['cost']) for row in result['filaments']) == Decimal(result['material_cost'])
    assert brl('1234.56') == 'R$ 1.234,56'
    assert brl('-55.1') == 'R$ -55,10'


@pytest.mark.parametrize('value', ['NaN', 'Infinity', '-1', '', True, 0.1, '1000000001'])
def test_invalid_decimals_are_rejected(value):
    with pytest.raises(ValueError):
        number(value)


def test_numeric_precision_and_quantity_validation(catalog):
    identifier = spool(catalog)
    with pytest.raises(ValueError):
        catalog.estimate(1, 60, [(identifier, '1')], final='1.001')
    with pytest.raises(ValueError):
        catalog.estimate(1, 60, [(identifier, '1.0001')])
    for quantity in (0, -1, '1.5'):
        with pytest.raises(ValueError):
            catalog.estimate(1, 60, [(identifier, '1')], quantity=quantity)
    assert number('1.234,56', places=2) == Decimal('1234.56')


def test_printer_edit_maintenance_and_hour_correction_audit(catalog):
    row = catalog.get('printers', 1)
    with pytest.raises(ValueError, match='Justificativa'):
        catalog.save_printer(printer_data(row, accumulated_minutes=120), 1)
    catalog.save_printer(printer_data(row, accumulated_minutes=120), 1, 'Leitura do contador físico')
    catalog.add_maintenance(1, '2026-01-01', 'Limpeza e lubrificação', '25.50', '2026-02-01')
    event = catalog.maintenance(1)[0]
    assert event['cost_cents'] == 2550
    assert event['next_due'] == '2026-02-01'
    assert catalog.get('printers', 1)['accumulated_minutes'] == 120
    assert catalog.storage.db.execute("SELECT reason FROM audit WHERE operation='edição' ORDER BY id DESC LIMIT 1").fetchone()[0] == 'Leitura do contador físico'
    duplicate = printer_data(row)
    with pytest.raises(sqlite3.IntegrityError):
        catalog.save_printer(duplicate)


def test_different_printers_have_independent_rates(catalog):
    printer = catalog.save_printer(dict(manufacturer='Outra', model='Modelo', identifier='B-02', purchase='500',
                                       investment_hour='2.00', energy_hour='0.40', maintenance_hour='0.60'))
    identifier = spool(catalog)
    assert catalog.estimate(printer, 60, [(identifier, '10')])['machine_cost'] == '3.00'
    assert catalog.estimate(1, 60, [(identifier, '10')])['machine_cost'] == '1.10'


def test_filament_adjustments_require_reason_and_low_alert(catalog):
    identifier = spool(catalog, remaining_grams='100', state='open')
    assert [r['id'] for r in catalog.low_filaments()] == [identifier]
    row = catalog.get('filaments', identifier)
    with pytest.raises(ValueError, match='Justificativa'):
        catalog.save_filament(spool_data(row, remaining_grams='200'), identifier)
    catalog.save_filament(spool_data(row, remaining_grams='200'), identifier, 'Pesagem confirmada')
    assert catalog.low_filaments() == []
    catalog.defaults('150', '250')
    assert catalog.storage.get('markup_percent') == '150'
    assert [r['id'] for r in catalog.low_filaments()] == [identifier]
    assert catalog.estimate(1, 0, [(identifier, '100')])['suggested_total'] == '25.00'


@pytest.mark.parametrize('override', [
    {'remaining_grams': '1001'}, {'initial_grams': '0'}, {'reference_per_g': '-0.1'},
    {'state': 'finished', 'remaining_grams': '1'}, {'remaining_grams': None, 'state': 'new'},
    {'purchased_on': '2026-02-30'}, {'brand': ''}])
def test_invalid_filament_is_not_saved(catalog, override):
    with pytest.raises(ValueError):
        spool(catalog, **override)
    assert catalog.rows('filaments') == []


def test_planning_does_not_consume_stock_or_machine_time(catalog):
    identifier = spool(catalog)
    calculation = catalog.save_calculation('Teste', 1, 60, [(identifier, '10')])
    assert catalog.get('calculations', calculation)['actual'] is None
    assert catalog.get('filaments', identifier)['remaining_mg'] == 1000000
    assert catalog.get('printers', 1)['accumulated_minutes'] == 0
    assert catalog.storage.get('last_filament_id') == identifier
    assert catalog.db.execute('SELECT count(*) FROM filament_consumption').fetchone()[0] == 0


def test_confirmed_consumption_and_hours_are_atomic_and_once_only(catalog):
    identifier = spool(catalog)
    calculation = catalog.save_calculation('Previsto', 1, 60, [(identifier, '100')])
    result = catalog.confirm_actual(calculation, 120, {identifier: '120'})
    assert result == {'planned': '11.10', 'actual': '14.20', 'difference': '3.10', 'percent': '27.93'}
    assert catalog.get('filaments', identifier)['remaining_mg'] == 880000
    assert catalog.get('filaments', identifier)['state'] == 'open'
    assert catalog.get('printers', 1)['accumulated_minutes'] == 120
    movement = catalog.db.execute('SELECT * FROM filament_consumption').fetchone()
    assert movement['consumed_mg'] == 120000
    assert movement['previous_mg'] == 1000000
    assert movement['remaining_mg'] == 880000
    with pytest.raises(ValueError, match='já foi confirmado'):
        catalog.confirm_actual(calculation, 120, {identifier: '120'})
    assert catalog.get('filaments', identifier)['remaining_mg'] == 880000
    assert catalog.get('printers', 1)['accumulated_minutes'] == 120


def test_unknown_balance_stays_null_while_consumption_is_logged(catalog):
    unknown = spool(catalog, name='Aberto', state='open', remaining_grams=None)
    calculation = catalog.save_calculation('Sem pesagem', 1, 60, [(unknown, '30')])
    catalog.confirm_actual(calculation, 30, {unknown: '25'})
    assert catalog.get('filaments', unknown)['remaining_mg'] is None
    assert catalog.low_filaments() == []
    movement = catalog.db.execute('SELECT * FROM filament_consumption').fetchone()
    assert movement['previous_mg'] is None and movement['remaining_mg'] is None
    assert movement['consumed_mg'] == 25000


def test_insufficient_balance_rolls_back_every_filament_and_hours(catalog):
    first = spool(catalog)
    second = spool(catalog, remaining_grams='1', state='open')
    calculation = catalog.save_calculation('Lote', 1, 60, [(first, '10'), (second, '10')])
    with pytest.raises(ValueError, match='Saldo insuficiente'):
        catalog.confirm_actual(calculation, 60, {first: '10', second: '10'})
    assert catalog.get('filaments', first)['remaining_mg'] == 1000000
    assert catalog.get('filaments', second)['remaining_mg'] == 1000
    assert catalog.get('printers', 1)['accumulated_minutes'] == 0
    assert catalog.get('calculations', calculation)['actual'] is None
    assert catalog.db.execute('SELECT count(*) FROM filament_consumption').fetchone()[0] == 0


def test_balance_at_zero_finishes_spool(catalog):
    identifier = spool(catalog, remaining_grams='10', state='open')
    calculation = catalog.save_calculation('Finalizar', 1, 0, [(identifier, '10')])
    catalog.confirm_actual(calculation, 0, {identifier: '10'})
    assert catalog.get('filaments', identifier)['remaining_mg'] == 0
    assert catalog.get('filaments', identifier)['state'] == 'finished'
    with pytest.raises(ValueError, match='finalizado'):
        catalog.estimate(1, 60, [(identifier, '10')])


def test_historical_rates_remain_frozen_after_catalog_changes(catalog):
    identifier = spool(catalog)
    calculation = catalog.save_calculation('Histórico', 1, 60, [(identifier, '10')], final='5')
    before = catalog.get('calculations', calculation)['planned']
    catalog.save_filament(spool_data(catalog.get('filaments', identifier), reference_per_g='0.5'), identifier)
    catalog.save_printer(printer_data(catalog.get('printers', 1), investment_hour='5'), 1)
    catalog.defaults('100', '100')
    assert catalog.get('calculations', calculation)['planned'] == before
    catalog.confirm_actual(calculation, 60, {identifier: '20'})
    actual = json.loads(catalog.get('calculations', calculation)['actual'])
    assert actual['machine_cost'] == '1.10'
    assert actual['material_cost'] == '2.00'
    assert actual['final_total'] == '5.00'
    assert actual['markup'] == '200'
    assert actual['commercial_result'] == '1.90'


def test_archive_restore_does_not_delete_history(catalog):
    identifier = spool(catalog)
    calculation = catalog.save_calculation('Preservar', 1, 60, [(identifier, '10')])
    catalog.archive('filaments', identifier, True, 'Sem uso')
    assert catalog.rows('filaments') == []
    assert catalog.rows('filaments', archived=True)[0]['id'] == identifier
    with pytest.raises(ValueError):
        catalog.estimate(1, 60, [(identifier, '10')])
    assert catalog.get('calculations', calculation)['planned']
    catalog.archive('filaments', identifier, False, 'Voltar ao uso')
    assert catalog.rows('filaments')[0]['id'] == identifier


def test_duplicate_spool_offline_printer_and_missing_consumptions(catalog):
    identifier = spool(catalog)
    with pytest.raises(ValueError, match='duas vezes'):
        catalog.estimate(1, 60, [(identifier, '10'), (identifier, '20')])
    calculation = catalog.save_calculation('Previsto', 1, 60, [(identifier, '10')])
    with pytest.raises(ValueError, match='cada carretel'):
        catalog.confirm_actual(calculation, 60, {})
    catalog.save_printer(printer_data(catalog.get('printers', 1), status='maintenance'), 1)
    with pytest.raises(ValueError, match='operacional'):
        catalog.estimate(1, 60, [(identifier, '10')])


def test_calculations_persist_and_backups_include_phase2(tmp_path):
    store = Storage(tmp_path)
    catalog = Catalog(store)
    identifier = spool(catalog)
    calculation = catalog.save_calculation('Permanente', 1, 60, [(identifier, '10')])
    catalog.confirm_actual(calculation, 60, {identifier: '15'})
    path = create_backup(store)
    assert verify_backup(path, 'test')
    catalog.save_filament(spool_data(catalog.get('filaments', identifier), remaining_grams='500'), identifier, 'Ajuste posterior')
    restore_backup(store, path)
    reopened = Storage(tmp_path)
    current = Catalog(reopened)
    assert current.get('filaments', identifier)['remaining_mg'] == 985000
    assert current.get('calculations', calculation)['actual']
    assert current.get('printers', 1)['accumulated_minutes'] == 60
    reopened.close()


def test_real_phase1_upgrade_preserves_password_notes_preferences_and_backup(tmp_path, monkeypatch):
    import drheeklab.storage as module
    from drheeklab.security import Auth
    with monkeypatch.context() as patch:
        patch.setattr(module, 'SCHEMA_VERSION', 1)
        old = Storage(tmp_path)
        old.set('theme', 'light')
        old.save_draft('home_notes', 'Anotação antiga')
        Auth(old).create('senha preservada')
        old_backup = create_backup(old)
        old.close()
    updated = Storage(tmp_path)
    assert updated.db.execute('PRAGMA user_version').fetchone()[0] == SCHEMA_VERSION
    assert Auth(updated).verify('senha preservada')
    assert updated.get('theme') == 'light'
    assert updated.load_draft('home_notes') == 'Anotação antiga'
    assert len(Catalog(updated).rows('printers')) == 1
    assert len(list((updated.home / 'Backups').glob('pre-migration-*.sqlite3'))) == 1
    restore_backup(updated, old_backup)
    migrated = Storage(tmp_path)
    assert migrated.load_draft('home_notes') == 'Anotação antiga'
    assert Auth(migrated).verify('senha preservada')
    assert len(Catalog(migrated).rows('printers')) == 1
    migrated.close()

def test_reference_price_and_acquisition_cost_are_distinct_for_free_spools(catalog):
    identifier = spool(catalog, purchase='0', reference_per_g='0.1')
    result = catalog.estimate(1, 60, [(identifier, '100')])
    assert result['total_cost'] == '11.10'
    assert result['suggested_total'] == '33.30'
    assert result['acquisition_material_cost'] == '0.00'
    assert result['acquisition_production_cost'] == '1.10'
    assert result['acquisition_commercial_result'] == '32.20'


def test_unknown_acquisition_is_not_reported_as_zero(catalog):
    identifier = spool(catalog, initial_grams=None, remaining_grams=None, state='open')
    result = catalog.estimate(1, 60, [(identifier, '10')])
    assert result['total_cost'] == '2.10'
    assert result['acquisition_material_cost'] is None
    assert result['acquisition_production_cost'] is None
    assert result['acquisition_commercial_result'] is None


def test_confirm_failure_in_audit_rolls_back_snapshot_stock_and_hours(catalog, monkeypatch):
    identifier = spool(catalog)
    calculation = catalog.save_calculation('Transação', 1, 60, [(identifier, '10')])
    def fail(*args):
        raise RuntimeError('Simulated I/O failure')
    monkeypatch.setattr(catalog.storage, 'audit', fail)
    with pytest.raises(RuntimeError):
        catalog.confirm_actual(calculation, 60, {identifier: '10'})
    assert catalog.get('filaments', identifier)['remaining_mg'] == 1000000
    assert catalog.get('printers', 1)['accumulated_minutes'] == 0
    assert catalog.get('calculations', calculation)['actual'] is None
    assert catalog.db.execute('SELECT COUNT(*) FROM filament_consumption').fetchone()[0] == 0

@pytest.mark.parametrize('value', ['1.2,00', '1.23.456,00', '1,2,3', '1.234,5e2'])
def test_malformed_brazilian_numbers_are_not_silently_reinterpreted(value):
    with pytest.raises(ValueError):
        number(value)
