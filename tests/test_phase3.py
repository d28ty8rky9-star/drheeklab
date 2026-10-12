from pathlib import Path
from decimal import Decimal
import json
import sqlite3
import pytest
from PySide6.QtGui import QImage, QColor
from drheeklab.storage import Storage, SCHEMA_VERSION
from drheeklab.products import Products
from drheeklab.inventory import Inventory
from drheeklab.catalog import Catalog
from drheeklab.backup import create_backup, verify_backup, restore_backup

@pytest.fixture
def system(tmp_path):
    storage = Storage(tmp_path / 'data')
    yield storage, Products(storage), Inventory(storage)
    try:
        storage.close()
    except sqlite3.ProgrammingError:
        pass


def product_variant(products):
    identifier = products.save({'name': 'Suporte', 'category': 'functional', 'planned_cost': '10', 'suggested_price': '30'})
    return identifier, products.variants(identifier)[0]['id']


def photo(path, color='#00aacc'):
    image = QImage(64, 48, QImage.Format_RGB32)
    image.fill(QColor(color))
    assert image.save(str(path))
    return path


def receipt(inventory, variant, qty=3, cost='10.01', state='available', key='opening'):
    return inventory.receive(variant, qty, 'Entrada inicial documentada', state, 'Nova, verificada', key,
                             total_cost=cost, reviewer='Responsável')


def test_product_codes_variants_search_and_recommendations(system):
    store, products, inventory = system
    first, variant = product_variant(products)
    second = products.save({'name': 'Vaso', 'category': 'decorative', 'printer_id': 1, 'settings': '0,2 mm / 15%', 'quality_notes': 'Evitar excesso de suportes'})
    assert products.get('products', first)['code'] == 'MOD-0001'
    assert products.get('products', second)['code'] == 'MOD-0002'
    assert products.get('variants', variant)['name'] == 'Padrão'
    alt = products.save_variant(first, {'name': 'Grande', 'size': '20 cm', 'color': 'Azul', 'material': 'PETG', 'planned_cost': '15', 'suggested_price': '45'})
    assert products.get('variants', alt)['planned_cost_cents'] == 1500
    assert [r['id'] for r in products.search('petg')] == [first]
    assert [r['id'] for r in products.search('mod-0002')] == [second]
    assert [r['id'] for r in products.search('', 'functional')] == [first]
    assert products.search('%') == []
    products.archive('products', first, True, 'Sem uso')
    assert [r['id'] for r in products.search()] == [second]
    assert products.search(archived=True)[0]['id'] == first
    products.archive('products', first, False, 'Voltar ao catálogo')
    assert len(products.search()) == 2
    assert products.get('variants', alt)['planned_cost_cents'] == 1500


@pytest.mark.parametrize('data', [{'name': None}, {'name': ''}, {'name': 'Nome', 'category': 'wrong'}, {'name':'Nome', 'planned_cost':'-1'}, {'name':'Nome', 'estimated_minutes':'1.5'}, {'name':'Nome','printer_id':999}])
def test_invalid_products_do_not_create_rows(system, data):
    store, products, inventory = system
    with pytest.raises(ValueError):
        products.save(data)
    assert products.search() == []


def test_variant_cost_snapshot_is_frozen(system):
    store, products, inventory = system
    product, variant = product_variant(products)
    catalog = Catalog(store)
    spool = catalog.save_filament({'brand':'Marca','material':'PLA','color':'Preto','name':'PLA','purchase':'100','initial_grams':'1000','remaining_grams':'1000','reference_per_g':'0.1'})
    calc = catalog.save_calculation('Lote', 1, 120, [(spool, '100')], quantity=2)
    identifier = products.save_variant(product, {'name':'Preto','calculation_id':calc})
    row = products.get('variants', identifier)
    assert row['planned_cost_cents'] == 610
    assert row['suggested_price_cents'] == 1830
    original = row['cost_snapshot']
    products.save({'name':'Suporte atualizado','category':'functional','planned_cost':'99','suggested_price':'299'}, product)
    assert products.get('variants', identifier)['cost_snapshot'] == original
    other, _ = product_variant(products)
    with pytest.raises(ValueError, match='outro produto'):
        products.save_variant(other, {'name':'Mover'}, identifier)


def test_media_import_copies_original_and_keeps_versions_and_preferences(system, tmp_path):
    store, products, inventory = system
    product, variant = product_variant(products)
    first_photo = photo(tmp_path / 'frente.png')
    second_photo = photo(tmp_path / 'verso.png', '#aa3366')
    p1 = products.import_media(product, first_photo, 'photo')
    p2 = products.import_media(product, second_photo, 'photo')
    assert products.get('product_photos', p1)['is_primary'] == 1
    products.choose_media(product, p2, 'photo')
    assert products.get('product_photos', p1)['is_primary'] == 0
    assert products.get('product_photos', p2)['is_primary'] == 1
    first_photo.unlink()
    assert products.media_path(p1, 'photo').exists()
    source = tmp_path / 'modelo.stl'
    source.write_text('solid original\nendsolid original\n')
    v1 = products.import_media(product, source, 'project', 'Primeira versão')
    original_bytes = products.media_path(v1, 'project').read_bytes()
    source.write_text('solid revised\nendsolid revised\n')
    v2 = products.import_media(product, source, 'project', 'Suportes revisados')
    assert products.get('project_versions', v1)['version'] == 1
    assert products.get('project_versions', v2)['version'] == 2
    assert products.get('project_versions', v2)['is_preferred'] == 1
    assert products.media_path(v1, 'project').read_bytes() == original_bytes
    products.choose_media(product, v1, 'project')
    assert products.get('project_versions', v1)['is_preferred'] == 1
    assert products.get('project_versions', v2)['is_preferred'] == 0
    products.archive('products', product, True, 'Arquivar')
    assert products.media_path(v1, 'project').exists()


def test_invalid_or_cross_product_files_and_external_modification_are_rejected(system, tmp_path):
    store, products, inventory = system
    first, _ = product_variant(products); other, _ = product_variant(products)
    invalid = tmp_path / 'fake.jpg'; invalid.write_bytes(b'not an image')
    with pytest.raises(ValueError, match='Foto inválida'):
        products.import_media(first, invalid, 'photo')
    with pytest.raises(ValueError):
        products.import_media(first, invalid, 'project')
    original = tmp_path / 'modelo.stl'; original.write_text('solid\nendsolid\n')
    identifier = products.import_media(first, original, 'project')
    with pytest.raises(ValueError, match='outro produto'):
        products.choose_media(other, identifier, 'project')
    stored = products.media_path(identifier, 'project')
    stored.write_bytes(b'changed outside')
    with pytest.raises(ValueError, match='alterado fora'):
        products.media_path(identifier, 'project')
    store.db.execute("UPDATE project_versions SET path='../outside.stl' WHERE id=?", (identifier,)); store.db.commit()
    with pytest.raises(ValueError, match='fora do armazenamento'):
        products.media_path(identifier, 'project')


def test_failed_file_import_removes_only_its_new_copy(system, tmp_path, monkeypatch):
    store, products, inventory = system
    product, _ = product_variant(products)
    source = photo(tmp_path / 'photo.png')
    original = source.read_bytes()
    def fail(*args):
        raise RuntimeError('Audit failed')
    monkeypatch.setattr(store, 'audit', fail)
    with pytest.raises(RuntimeError):
        products.import_media(product, source, 'photo')
    assert source.read_bytes() == original
    assert products.media(product, 'photo') == []
    assert list((store.home / 'Fotos dos Produtos').iterdir()) == []


def test_bambu_launch_uses_argv_without_shell_and_preserves_manual_settings(system, tmp_path, monkeypatch):
    store, products, inventory = system
    product, _ = product_variant(products)
    source = tmp_path / 'model.stl'; source.write_text('solid\nendsolid\n')
    version = products.import_media(product, source, 'project')
    executable = tmp_path / 'Bambu Studio.exe'; executable.write_bytes(b'test launcher')
    store.set('bambu_studio_path', str(executable))
    calls = []
    monkeypatch.setattr('drheeklab.products.subprocess.Popen', lambda args, **kwargs: calls.append((args, kwargs)))
    products.open_project(version)
    assert calls == [([str(executable), str(products.media_path(version, 'project'))], {'shell': False})]
    assert products.get('products', product)['settings'] == ''


def test_stock_cost_allocation_reconciles_and_reservation_does_not_reduce_physical(system):
    store, products, inventory = system
    product, variant = product_variant(products)
    receipt_id, ids = receipt(inventory, variant)
    assert [inventory.get('pieces', key)['unit_cost_cents'] for key in ids] == [334,334,333]
    assert sum(inventory.get('pieces', key)['unit_cost_cents'] for key in ids) == 1001
    initial = inventory.summary()[0]
    assert (initial['physical'],initial['available'],initial['reserved']) == (3,3,0)
    reservation = inventory.reserve(variant, 2, 'Referência do cliente', 'reserve-1')
    reserved = inventory.summary()[0]
    assert (reserved['physical'],reserved['available'],reserved['reserved']) == (3,1,2)
    assert [p['id'] for p in inventory.pieces() if p['state']=='reserved'] == ids[:2]
    inventory.finish_reservation(reservation, 'release', 'Reserva cancelada')
    released = inventory.summary()[0]
    assert (released['physical'],released['available'],released['reserved']) == (3,3,0)
    with pytest.raises(ValueError, match='já foi'):
        inventory.finish_reservation(reservation, 'release', 'Repetir')


def test_issue_uses_existing_cost_once_and_never_rebuilds_it(system):
    store, products, inventory = system
    product, variant = product_variant(products)
    receipt(inventory, variant)
    reserved = inventory.reserve(variant, 2, 'Entrega física', 'reserve')
    assert inventory.finish_reservation(reserved, 'issue', 'Saída justificada') == 668
    row = inventory.summary()[0]
    assert (row['physical'],row['available'],row['reserved'],row['issued']) == (1,1,0,2)
    with pytest.raises(ValueError):
        inventory.finish_reservation(reserved, 'issue', 'Não duplicar')
    assert store.db.execute("SELECT count(*) FROM stock_movements WHERE kind='issue'").fetchone()[0] == 2
    assert store.db.execute('SELECT sum(unit_cost_cents) FROM pieces').fetchone()[0] == 1001


def test_personal_stock_requires_reinspection_and_rejected_pieces_stay_unavailable(system):
    store, products, inventory = system
    product, variant = product_variant(products)
    _, ids = receipt(inventory, variant, state='personal')
    with pytest.raises(ValueError, match='disponível'):
        inventory.reserve(variant, 1, 'Tentativa', 'reserve')
    inventory.review([ids[0]], 'rejected', 'Marcas de uso precisam ser verificadas', 'Proprietário')
    assert inventory.get('pieces', ids[0])['state'] == 'quarantine'
    inventory.review([ids[1]], 'approved', 'Usada, sem defeitos funcionais', 'Proprietário')
    assert inventory.get('pieces', ids[1])['state'] == 'available'
    assert inventory.get('pieces', ids[1])['unit_cost_cents'] == 334
    summary = inventory.summary()[0]
    assert (summary['physical'],summary['available'],summary['personal'],summary['quarantine']) == (3,1,1,1)
    assert store.db.execute('SELECT count(*) FROM piece_reviews').fetchone()[0] == 2
    inventory.reserve(variant, 1, 'Futura venda de usada', 'used-reserve')
    with pytest.raises(ValueError):
        inventory.review([ids[1]], 'approved', 'Repetir depois da reserva', 'Proprietário')


def test_discard_records_existing_cost_date_notes_and_cannot_be_duplicated(system):
    store, products, inventory = system
    product, variant = product_variant(products)
    _, ids = receipt(inventory, variant)
    loss = inventory.discard_pieces([ids[0]], 'Quebra', 'loss', '2026-01-02', 'Queda no transporte interno')
    row = inventory.get('losses', loss)
    assert row['cost_cents'] == 334
    assert row['quantity_milli'] == 1000
    assert row['occurred_on'] == '2026-01-02'
    assert row['notes'] == 'Queda no transporte interno'
    assert inventory.summary()[0]['physical'] == 2
    with pytest.raises(ValueError):
        inventory.discard_pieces([ids[0]], 'Mesmo descarte', 'new-key')
    assert len(inventory.losses()) == 1
    assert sum(p['unit_cost_cents'] for p in inventory.pieces()) == 1001


def test_reservation_and_discard_failure_are_atomic(system, monkeypatch):
    store, products, inventory = system
    product, variant = product_variant(products)
    _, ids = receipt(inventory, variant)
    with pytest.raises(ValueError):
        inventory.reserve(variant, 4, 'Sem quantidade', 'too-many')
    assert inventory.reservations() == []
    reserve = inventory.reserve(variant, 1, 'Reservada', 'res')
    with pytest.raises(ValueError):
        inventory.discard_pieces([ids[1],ids[0]], 'Um item reservado', 'loss')
    assert inventory.get('pieces', ids[1])['state'] == 'available'
    assert inventory.losses() == []
    inventory.finish_reservation(reserve,'release','Liberar')
    def fail(*args):
        raise RuntimeError('Audit failed')
    monkeypatch.setattr(store,'audit',fail)
    with pytest.raises(RuntimeError):
        inventory.discard_pieces(ids, 'Rollback', 'audit-failure')
    assert inventory.losses() == []
    assert all(p['state']=='available' for p in inventory.pieces())
    assert inventory.summary()[0]['physical'] == 3


def test_duplicate_operations_rollback_and_archival_preserves_physical_stock(system):
    store, products, inventory = system
    product, variant = product_variant(products)
    receipt(inventory, variant)
    with pytest.raises(sqlite3.IntegrityError):
        receipt(inventory,variant)
    assert len(inventory.pieces()) == 3
    reservation = inventory.reserve(variant, 1, 'Cliente', 'res')
    with pytest.raises(ValueError, match='Libere'):
        products.archive('products', product, True, 'Tentativa')
    inventory.finish_reservation(reservation, 'release', 'Liberar')
    products.archive('products', product, True, 'Arquivar sem apagar estoque')
    assert inventory.summary()[0]['physical'] == 3
    with pytest.raises(ValueError, match='Restaure'):
        inventory.reserve(variant, 1, 'Novo', 'archived-reserve')
    products.archive('products', product, False, 'Restaurar')
    assert inventory.reserve(variant, 1, 'Novo', 'restored-reserve')


def test_materials_adjustments_consumption_losses_and_journal(system):
    store, products, inventory = system
    identifier = inventory.save_material({'name':'Ímã','unit':'unidade','balance':'10','reference_per_unit':'0.50'}, reason='Compra inicial')
    with pytest.raises(ValueError):
        inventory.save_material({'name':'Ímã','unit':'unidade','balance':'20','reference_per_unit':'0.50'}, identifier)
    assert inventory.consume_material(identifier, '2', 'Produção de suporte', 'consume') == 100
    assert inventory.get('materials', identifier)['balance_milli'] == 8000
    with pytest.raises(sqlite3.IntegrityError):
        inventory.consume_material(identifier, '2', 'Não duplicar', 'consume')
    assert inventory.get('materials', identifier)['balance_milli'] == 8000
    loss = inventory.discard_material('material',identifier,'1','Ímã quebrado','loss')
    assert inventory.get('losses', loss)['cost_cents'] == 50
    assert inventory.get('losses', loss)['unit'] == 'unidade'
    assert inventory.get('materials', identifier)['balance_milli'] == 7000
    with pytest.raises(ValueError):
        inventory.consume_material(identifier,'8','Saldo insuficiente','too-much')
    inventory.save_material({'name':'Ímã','unit':'unidade','balance':'9','reference_per_unit':'0.50'}, identifier, 'Contagem corrigida')
    assert inventory.get('materials', identifier)['balance_milli'] == 9000
    assert [m['kind'] for m in reversed(inventory.movements())] == ['opening','consumption','discard','adjustment']


def test_filament_journal_includes_phase2_consumption_adjustment_and_loss(system):
    store, products, inventory = system
    catalog=Catalog(store)
    spool=catalog.save_filament({'brand':'Marca','name':'PLA','material':'PLA','color':'Azul','initial_grams':'1000','remaining_grams':'1000','purchase':'100','reference_per_g':'0.2'})
    calc=catalog.save_calculation('Teste',1,60,[(spool,'10')])
    catalog.confirm_actual(calc,60,{spool:'10'})
    loss=inventory.discard_material('filament',spool,'20','Material danificado','loss')
    assert inventory.get('losses',loss)['cost_cents']==200
    assert inventory.get('losses',loss)['cost_basis']=='acquisition'
    assert catalog.get('filaments',spool)['remaining_mg']==970000
    assert [m['kind'] for m in reversed(inventory.movements())]==['opening','consumption','discard']
    with pytest.raises(sqlite3.IntegrityError):
        inventory.discard_material('filament',spool,'20','Repetir','loss')
    assert catalog.get('filaments',spool)['remaining_mg']==970000
    unknown=catalog.save_filament({'brand':'Marca','name':'Aberto','material':'PLA','color':'Azul','initial_grams':None,'remaining_grams':None,'state':'open','purchase':'0','reference_per_g':'0.2'})
    loss=inventory.discard_material('filament',unknown,'20','Pedaço perdido','unknown-loss')
    assert catalog.get('filaments',unknown)['remaining_mg'] is None
    assert inventory.get('losses',loss)['cost_basis']=='reference'


def test_production_for_stock_reuses_confirmed_cost_without_consuming_again(system):
    store, products, inventory = system
    product,variant=product_variant(products)
    catalog=Catalog(store)
    spool=catalog.save_filament({'brand':'Marca','name':'PLA','material':'PLA','color':'Azul','initial_grams':'1000','remaining_grams':'1000','purchase':'100','reference_per_g':'0.1'})
    calc=catalog.save_calculation('Produção para estoque',1,60,[(spool,'100')],quantity=3)
    with pytest.raises(ValueError,match='Confirme'):
        inventory.receive(variant,3,'Produção','quarantine','Nova','first',calculation_id=calc)
    catalog.confirm_actual(calc,60,{spool:'100'})
    before=catalog.get('filaments',spool)['remaining_mg']
    receipt_id,ids=inventory.receive(variant,3,'Produção para estoque sem cliente','quarantine','Nova','stock',calculation_id=calc)
    assert inventory.get('receipts',receipt_id)['total_cost_cents']==1110
    assert sum(inventory.get('pieces',key)['unit_cost_cents'] for key in ids)==1110
    assert catalog.get('filaments',spool)['remaining_mg']==before==900000
    assert catalog.get('printers',1)['accumulated_minutes']==60
    with pytest.raises(sqlite3.IntegrityError):
        inventory.receive(variant,3,'Não duplicar cálculo','quarantine','Nova','other',calculation_id=calc)
    assert len(inventory.pieces())==3


def test_piece_review_and_receipt_validation_are_atomic(system):
    store, products, inventory=system
    product,variant=product_variant(products)
    with pytest.raises(ValueError):
        inventory.receive(variant,1,'Origem','available','Nova','key')
    assert inventory.pieces()==[]
    _,ids=receipt(inventory,variant,state='quarantine')
    with pytest.raises(ValueError):
        inventory.review([ids[0],ids[0]],'approved','Nova','Responsável')
    with pytest.raises(ValueError):
        inventory.review(ids,'approved','','Responsável')
    assert inventory.summary()[0]['available']==0


def test_backup_restores_media_variants_costs_reservations_losses_and_stock(system,tmp_path):
    store, products, inventory=system
    product,variant=product_variant(products)
    picture=products.import_media(product,photo(tmp_path/'real.png'),'photo')
    source=tmp_path/'model.3mf'; source.write_bytes(b'user supplied project bytes')
    project=products.import_media(product,source,'project')
    _,ids=receipt(inventory,variant)
    reservation=inventory.reserve(variant,1,'Reserva','res')
    inventory.discard_pieces([ids[1]],'Quebra','loss')
    original=inventory.summary()[0]
    snapshot=create_backup(store)
    assert verify_backup(snapshot,'test')
    products.media_path(picture,'photo').unlink()
    inventory.finish_reservation(reservation,'release','Mudança posterior')
    restore_backup(store,snapshot)
    reopened=Storage(store.root)
    restored=Inventory(reopened); assets=Products(reopened)
    assert restored.summary()[0]==original
    assert assets.media_path(picture,'photo').is_file()
    assert assets.media_path(project,'project').read_bytes()==source.read_bytes()
    assert len(restored.losses())==1
    preservation=json.loads(reopened.db.execute("SELECT previous FROM audit WHERE operation='restauração' ORDER BY id DESC LIMIT 1").fetchone()[0])
    assert preservation['linked_files_complete'] is False
    assert restored.get('reservations',reservation)['state']=='reserved'
    assert reopened.db.execute('PRAGMA foreign_key_check').fetchall()==[]
    reopened.close()


def test_real_phase2_upgrade_preserves_calculations_balances_and_journal_baseline(tmp_path,monkeypatch):
    import drheeklab.storage as module
    with monkeypatch.context() as patch:
        patch.setattr(module,'SCHEMA_VERSION',2)
        old=Storage(tmp_path)
        catalog=Catalog(old)
        spool=catalog.save_filament({'brand':'Marca','name':'PLA','material':'PLA','color':'Azul','initial_grams':'1000','remaining_grams':'1000','purchase':'100','reference_per_g':'0.1'})
        calc=catalog.save_calculation('Cálculo anterior',1,60,[(spool,'10')])
        catalog.confirm_actual(calc,60,{spool:'10'})
        actual=catalog.get('calculations',calc)['actual']
        backup=create_backup(old)
        old.close()
    upgraded=Storage(tmp_path)
    assert upgraded.db.execute('PRAGMA user_version').fetchone()[0]==SCHEMA_VERSION
    assert Catalog(upgraded).get('calculations',calc)['actual']==actual
    assert Catalog(upgraded).get('filaments',spool)['remaining_mg']==990000
    opening=Inventory(upgraded).movements()[0]
    assert opening['kind']=='opening' and opening['quantity_milli']==990000
    assert opening['current']=='990000'
    assert Products(upgraded).search()==[]
    restore_backup(upgraded,backup)
    reopened=Storage(tmp_path)
    assert Catalog(reopened).get('calculations',calc)['actual']==actual
    assert len(Inventory(reopened).movements())==1
    reopened.close()

def test_backup_rejects_missing_or_changed_linked_media(system,tmp_path):
    store,products,inventory=system
    product,variant=product_variant(products)
    pic=products.import_media(product,photo(tmp_path/'photo.png'),'photo')
    path=products.media_path(pic,'photo')
    original=path.read_bytes()
    path.write_bytes(b'changed externally')
    with pytest.raises(ValueError,match='vinculado'):
        create_backup(store)
    path.write_bytes(original)
    assert verify_backup(create_backup(store),'test')
    path.unlink()
    with pytest.raises(ValueError,match='vinculado'):
        create_backup(store)


def test_media_import_supports_relative_data_directory(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    store=Storage('data')
    products=Products(store)
    product,variant=product_variant(products)
    source=tmp_path/'relative.stl'; source.write_text('solid\nendsolid\n')
    version=products.import_media(product,source,'project')
    assert products.media_path(version,'project').is_file()
    store.close()
