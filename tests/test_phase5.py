import json
import sqlite3
from decimal import Decimal
import pytest
from PySide6.QtGui import QImage,QColor
from drheeklab.storage import Storage,MIGRATIONS,SCHEMA_VERSION
from drheeklab.production import Production,CHECKS,split
from drheeklab.backup import create_backup,verify_backup,restore_backup
from drheeklab.sales import Sales

@pytest.fixture
def system(tmp_path):
    store=Storage(tmp_path/'data');p=Production(store)
    spool=p.catalog.save_filament({'brand':'Marca','material':'PLA','color':'Azul','name':'PLA azul','initial_grams':'1000','remaining_grams':'1000','purchase':'100','reference_per_g':'0.20'})
    product=p.products.save({'name':'Peça','category':'functional'})
    variant=p.products.variants(product)[0]['id']
    source=tmp_path/'model.stl';source.write_text('solid test\nendsolid test')
    project=p.products.import_media(product,source,'project')
    photos={}
    for view,color in [('front','#ff0000'),('back','#00ff00'),('detail','#0000ff')]:
        image=QImage(40,30,QImage.Format_RGB32);image.fill(QColor(color));path=tmp_path/(view+'.png');assert image.save(str(path));photos[view]=path
    yield store,p,spool,product,variant,project,photos
    try:store.close()
    except sqlite3.ProgrammingError:pass


def create(system,qty=5,grams='50',**kwargs):
    _,p,spool,_,variant,project,_=system
    return p.create(1,60,[{'variant_id':variant,'project_id':project,'quantity':qty,'filaments':[(spool,grams)]}],'Operador','0,2 mm / 15% / PLA',**kwargs)


def confirm(system,op,failed=0,grams='50',minutes=60,progress='100',reason=''):
    _,p,spool,*_=system
    return p.confirm(op,minutes,[{'entry_id':p.entries(op)[0]['id'],'consumptions':{spool:grams},'failed':failed}],progress,reason)


def inspect_all(system,op,reject_last=False):
    _,p,_,_,_,_,photos=system
    for index,piece in enumerate(p.pieces(op)):
        checklist={k:{'result':'ok'} for k in CHECKS[piece['category']]}
        result='rejected' if reject_last and index==len(p.pieces(op))-1 else 'approved'
        p.inspect(op,piece['id'],result,checklist,photos,'Inspetor','Defeito de adesão' if result=='rejected' else '')


def test_five_printed_one_rejected_four_good_without_double_cost(system):
    store,p,spool,_,variant,_,_=system;op=create(system)
    p.start(op);confirm(system,op)
    assert p.catalog.get('printers',1)['accumulated_minutes']==60
    assert p.catalog.get('filaments',spool)['remaining_mg']==950000
    assert p.inventory.summary()[0]['available']==0
    with pytest.raises(ValueError,match='já|Inicie'):confirm(system,op)
    with pytest.raises(ValueError,match='individualmente'):p.complete(op)
    with pytest.raises(ValueError,match='três fotos'):p.inventory.review([p.pieces(op)[0]['id']],'approved','Bom','Outro')
    inspect_all(system,op,True);result=p.complete(op)
    assert result['produced']==5 and result['good']==4 and result['rejected']==1
    assert result['total_cents']==610 and result['reference_cents']==1110
    assert result['effective_unit']=='1.53'
    pieces=p.pieces(op)
    assert sum(r['unit_cost_cents'] for r in pieces)==610
    assert sorted(r['unit_cost_cents'] for r in pieces)==[0,152,152,153,153]
    assert p.inventory.summary()[0]['available']==4
    rejected=[r['id'] for r in pieces if r['inspection_result']=='rejected']
    loss=p.inventory.discard_pieces(rejected,'Reprovada','reject-discard')
    assert p.inventory.get('losses',loss)['cost_cents']==0  # already absorbed
    with pytest.raises(ValueError):p.inventory.reserve(variant,5,'Pedido','too-many')
    p.inventory.reserve(variant,4,'Pedido','four-good')
    assert p.catalog.get('printers',1)['accumulated_minutes']==60


def test_partial_failure_progress_is_editable_and_zero_good_has_no_unit_cost(system):
    _,p,spool,*_=system;op=create(system);p.start(op)
    assert p.suggested_consumption(op,'20')==[{spool:'10.000'}]
    confirm(system,op,failed=5,grams='12',minutes=15,progress='20',reason='Descolamento')
    s=p.summary(op);assert s['total_cents']==148 and s['failed']==5 and s['effective_unit'] is None
    assert s['loss_included_cents']==148 and p.get(op)['state']=='waiting'
    assert p.catalog.get('filaments',spool)['remaining_mg']==988000
    p.start(op);confirm(system,op);inspect_all(system,op);s=p.complete(op)
    assert s['attempts']==2 and s['total_cents']==758 and s['effective_unit']=='1.52'
    assert sum(r['unit_cost_cents'] for r in p.pieces(op))==758
    assert p.catalog.get('printers',1)['accumulated_minutes']==75


def test_partial_failed_count_total_cost_allocated_to_survivors(system):
    _,p,*_=system;op=create(system);p.start(op);confirm(system,op,failed=1,reason='Uma peça perdida')
    inspect_all(system,op);s=p.complete(op)
    assert s['produced']==4 and s['good']==4 and s['failed']==1
    assert s['total_cents']==610 and s['loss_included_cents']==122 and s['effective_unit']=='1.53'
    assert sum(r['unit_cost_cents'] for r in p.pieces(op))==610


def test_all_rejected_cannot_complete_or_reserve(system):
    _,p,_,_,variant,_,photos=system;op=create(system,qty=1);p.start(op);confirm(system,op)
    piece=p.pieces(op)[0];checks={k:{'result':'ok'} for k in CHECKS[piece['category']]}
    p.inspect(op,piece['id'],'rejected',checks,photos,'QA','Trinca')
    with pytest.raises(ValueError,match='Nenhuma'):p.complete(op)
    with pytest.raises(ValueError):p.inventory.reserve(variant,1,'Pedido','blocked')
    with pytest.raises(ValueError,match='Conclua'):p.inventory.discard_pieces([piece['id']],'Trinca','discard')
    assert p.summary(op)['effective_unit'] is None


@pytest.mark.parametrize('fault',['missing_photo','duplicate_photo','invalid_photo','missing_check','na_reason','fail_approved','notes_missing'])
def test_inspection_requires_real_evidence_and_full_checklist(system,fault,tmp_path):
    store,p,_,_,_,_,photos=system;op=create(system,qty=1);p.start(op);confirm(system,op)
    piece=p.pieces(op)[0];checks={k:{'result':'ok'} for k in CHECKS[piece['category']]};photos=dict(photos);result='approved'
    if fault=='missing_photo':photos.pop('detail')
    if fault=='duplicate_photo':photos['detail']=photos['front']
    if fault=='invalid_photo':path=tmp_path/'bad.png';path.write_text('invalid');photos['detail']=path
    if fault=='missing_check':checks.pop('fit')
    if fault=='na_reason':checks['fit']={'result':'na','reason':''}
    if fault=='fail_approved':checks['fit']={'result':'fail','reason':'Não encaixa'}
    if fault=='notes_missing':result='notes'
    before=set((store.home/'Fotos dos Produtos').iterdir())
    with pytest.raises(ValueError):p.inspect(op,piece['id'],result,checks,photos,'QA')
    assert store.db.execute('SELECT COUNT(*) FROM inspections').fetchone()[0]==0
    assert set((store.home/'Fotos dos Produtos').iterdir())==before


def test_nonapplicable_with_reason_and_inspection_history(system):
    store,p,_,_,_,_,photos=system;op=create(system,qty=1);p.start(op);confirm(system,op)
    piece=p.pieces(op)[0];checks={k:{'result':'ok'} for k in CHECKS[piece['category']]};checks['fit']={'result':'na','reason':'Sem encaixe neste modelo'}
    first=p.inspect(op,piece['id'],'notes',checks,photos,'QA','Marca leve, sem impacto funcional')
    second=p.inspect(op,piece['id'],'approved',checks,photos,'QA')
    assert store.db.execute('SELECT valid FROM inspections WHERE id=?',(first,)).fetchone()[0]==0
    assert store.db.execute('SELECT count(*) FROM inspection_photos').fetchone()[0]==6
    p.complete(op)
    assert p.summary(op)['good']==1


def test_mixed_batch_allocates_machine_once_by_grams_and_separate_spools(system,tmp_path):
    store,p,spool,_,variant,project,_=system
    spool2=p.catalog.save_filament({'brand':'Marca','material':'PETG','color':'Verde','name':'PETG','initial_grams':'1000','remaining_grams':'1000','purchase':'200','reference_per_g':'0.4'})
    product2=p.products.save({'name':'Vaso','category':'decorative'});variant2=p.products.variants(product2)[0]['id']
    file=tmp_path/'vaso.3mf';file.write_bytes(b'opaque project');project2=p.products.import_media(product2,file,'project')
    op=p.create(1,60,[{'variant_id':variant,'project_id':project,'quantity':1,'filaments':[(spool,'10')]},{'variant_id':variant2,'project_id':project2,'quantity':2,'filaments':[(spool2,'30')]}],'QA','PLA/PETG compatibility checked')
    plan=json.loads(p.get(op)['planned']);assert plan['machine_cents']==110
    assert [json.loads(e['planned'])['machine_cost'] for e in p.entries(op)]==['0.28','0.82']
    p.start(op);entries=p.entries(op)
    p.confirm(op,60,[{'entry_id':entries[0]['id'],'consumptions':{spool:'10'}},{'entry_id':entries[1]['id'],'consumptions':{spool2:'30'}}])
    assert p.catalog.get('printers',1)['accumulated_minutes']==60
    assert p.catalog.get('filaments',spool)['remaining_mg']==990000
    assert p.catalog.get('filaments',spool2)['remaining_mg']==970000
    inspect_all(system,op);s=p.complete(op)
    assert s['total_cents']==810 and s['reference_cents']==1510
    assert sum(r['unit_cost_cents'] for r in p.pieces(op))==810


def test_manual_allocation_and_invalid_project_or_spool(system):
    store,p,spool,product,variant,project,_=system
    with pytest.raises(ValueError,match='Justificativa'):create(system,weights=['1'])
    op=create(system,weights=['1'],allocation_reason='Uma única mesa');assert json.loads(p.get(op)['planned'])['weights']==['1']
    with pytest.raises(ValueError):create(system,weights=['0'],allocation_reason='Zero')
    with pytest.raises(ValueError,match='duas vezes'):
        p.create(1,60,[{'variant_id':variant,'project_id':project,'quantity':1,'filaments':[(spool,'10'),(spool,'20')]}],'QA','Settings')
    assert len(p.queue())==1


def test_insufficient_balance_rolls_back_every_model_and_hours(system):
    store,p,spool,*_=system;op=create(system);p.start(op)
    with pytest.raises(ValueError,match='Saldo insuficiente'):confirm(system,op,grams='1001')
    assert p.catalog.get('printers',1)['accumulated_minutes']==0
    assert p.catalog.get('filaments',spool)['remaining_mg']==1000000
    assert p.get(op)['state']=='printing' and p.summary(op)['attempts']==0
    assert store.db.execute('SELECT count(*) FROM receipts').fetchone()[0]==0


def test_queue_priorities_reorder_preserves_creation_and_one_machine(system):
    _,p,*_=system;a=create(system);b=create(system);c=create(system,priority='high')
    old=p.get(a)['created_at'];p.reorder([b,a],'normal')
    assert [r['id'] for r in p.queue()]==[c,b,a]
    assert p.get(a)['created_at']==old
    with pytest.raises(ValueError):p.reorder([a],'normal')
    p.priority(a,'high');assert p.get(a)['created_at']==old
    p.start(a)
    with pytest.raises(ValueError,match='já possui'):p.start(b)


def test_reprint_new_code_and_current_rates_preserves_old_actual(system):
    _,p,spool,*_=system;op=create(system);p.start(op);confirm(system,op);old=p.summary(op)
    row=p.catalog.get('filaments',spool)
    p.catalog.save_filament({'brand':row['brand'],'material':row['material'],'color':row['color'],'name':row['name'],'purchase':'150','initial_grams':'1000','remaining_grams':'950','reference_per_g':'0.5','state':'open'},spool)
    new=p.reprint(op,'QA')
    assert p.get(new)['code']!=p.get(op)['code'] and p.get(new)['parent_id']==op
    assert json.loads(p.get(new)['planned'])['reference_cents']==2610
    assert p.summary(op)==old and p.summary(new)['attempts']==0
    assert p.catalog.get('printers',1)['accumulated_minutes']==60


def test_revalidation_invalidates_inspections_and_upstream_changes(system):
    store,p,_,product,variant,_,_=system;op=create(system,qty=1);p.start(op);confirm(system,op);inspect_all(system,op);p.complete(op)
    p.products.save({'name':'Atualizada','category':'decorative'},product)
    with pytest.raises(ValueError,match='revalidação'):p.inventory.reserve(variant,1,'Pedido','changed')
    p.revalidate(op,'Novos parâmetros','Produto alterado')
    assert p.get(op)['revision']==2 and p.pieces(op)[0]['inspection_result'] is None
    assert p.inventory.summary()[0]['available']==0 and p.pieces(op)[0]['category']=='decorative'
    with pytest.raises(ValueError):p.complete(op)
    inspect_all(system,op);p.complete(op);assert p.catalog.get('printers',1)['accumulated_minutes']==60
    p.inventory.reserve(variant,1,'Pedido','reserve')
    with pytest.raises(ValueError,match='reservadas'):p.revalidate(op,'Other','Teste')


def test_cancelled_order_existing_production_keeps_cost_and_can_finish_stock(system):
    _,p,_,_,variant,_,_=system;sales=Sales(p.storage);client=sales.save_client({'name':'Cliente'})
    order=sales.create_order(client,[{'variant_id':variant,'quantity':5,'unit_price':'5','fulfillment':'production'}]);item=sales.items(order)[0]['id']
    op=create(system,item_id=item);p.start(op);confirm(system,op)
    sales.cancel(order,'Desistência')
    inspect_all(system,op);p.complete(op)
    assert p.summary(op)['total_cents']==610 and p.inventory.summary()[0]['available']==5
    with pytest.raises(ValueError,match='cancelado'):p.reprint(op,'QA')


def test_order_delivery_return_reinspection_does_not_resurrect_other_issued_units(system):
    store,p,_,_,variant,_,_=system;sales=Sales(store);client=sales.save_client({'name':'Cliente'})
    order=sales.create_order(client,[{'variant_id':variant,'quantity':2,'unit_price':'5','fulfillment':'production'}]);item=sales.items(order)[0]['id']
    op=create(system,qty=2,item_id=item);p.start(op);confirm(system,op);inspect_all(system,op);p.complete(op)
    sales.reserve_item(item);sales.deliver(order,'deliver','pickup');pieces=p.pieces(op);originalcost=[r['unit_cost_cents'] for r in pieces]
    sales.cancel(order,'Devolução');sales.return_cancelled_pieces(order,[pieces[0]['id']],'Retorno real')
    assert p.pieces(op)[0]['inspection_result'] is None
    with pytest.raises(ValueError,match='três fotos'):p.inventory.review([pieces[0]['id']],'approved','Boa','QA')
    inspect_all_one=pieces[0]['id'];checks={k:{'result':'ok'} for k in CHECKS[pieces[0]['category']]}
    p.inspect(op,inspect_all_one,'approved',checks,system[-1],'QA');p.complete(op)
    assert [r['state'] for r in p.pieces(op)]==['available','issued']
    assert [r['unit_cost_cents'] for r in p.pieces(op)]==originalcost
    assert p.catalog.get('printers',1)['accumulated_minutes']==60


def test_backup_photos_and_recovery_after_missing_photo(system):
    store,p,*_=system;op=create(system,qty=1);p.start(op);confirm(system,op);inspect_all(system,op)
    backup=create_backup(store);assert verify_backup(backup,'test')
    photo=store.db.execute('SELECT id,path FROM inspection_photos LIMIT 1').fetchone();(store.home/photo['path']).unlink()
    with pytest.raises(ValueError,match='ausente'):p.complete(op)
    with pytest.raises(ValueError):create_backup(store)
    root=store.root;restore_backup(store,backup);restored=Storage(root)
    try:
        restoredp=Production(restored);assert restoredp.photo_path(photo['id']).exists();restoredp.complete(op)
        assert restored.db.execute('PRAGMA foreign_key_check').fetchall()==[]
    finally:restored.close()


def test_version4_migration_preserves_old_data_and_backup(tmp_path):
    root=tmp_path/'data';path=root/'TESTES'/'Banco de Dados'/'drheeklab.sqlite3';path.parent.mkdir(parents=True)
    with sqlite3.connect(path) as db:
        for version in range(1,5):
            for statement in MIGRATIONS[version]:db.execute(statement)
        db.execute('PRAGMA user_version=4');db.execute("INSERT INTO drafts VALUES('old','preserved','timestamp')")
    store=Storage(root)
    try:
        assert store.db.execute('PRAGMA user_version').fetchone()[0]==SCHEMA_VERSION
        assert store.load_draft('old')=='preserved' and list((store.home/'Backups').glob('pre-migration-*.sqlite3'))
        assert store.db.execute('PRAGMA foreign_key_check').fetchall()==[]
    finally:store.close()


def test_integer_allocation_conserves_centavos():
    assert split(110,['10','30'])==[28,82]
    assert split(1,[1,1,1])==[1,0,0]
    assert sum(split(12345,['0.33','0.66','0.01']))==12345


def test_unknown_spool_balance_and_reference_basis_are_preserved(system):
    store,p,_,_,variant,project,_=system
    spool=p.catalog.save_filament({'brand':'Marca','material':'PLA','color':'Preto','name':'Saldo desconhecido','initial_grams':None,'remaining_grams':None,'purchase':'80','reference_per_g':'0.25','state':'open'})
    op=p.create(1,60,[{'variant_id':variant,'project_id':project,'quantity':1,'filaments':[(spool,'10')]}],'QA','Settings')
    p.start(op);p.confirm(op,60,[{'entry_id':p.entries(op)[0]['id'],'consumptions':{spool:'10'}}])
    assert p.catalog.get('filaments',spool)['remaining_mg'] is None
    assert p.summary(op)['total_cents']==360
    assert store.db.execute('SELECT cost_basis FROM receipts').fetchone()[0]=='reference'
    inspect_all(system,op);p.complete(op)


def test_same_spool_across_models_debits_once_and_combined_shortage_rolls_back(system):
    store,p,spool,_,variant,project,_=system
    op=p.create(1,60,[{'variant_id':variant,'project_id':project,'quantity':1,'filaments':[(spool,'600')]},{'variant_id':variant,'project_id':project,'quantity':1,'filaments':[(spool,'600')]}],'QA','Settings')
    p.start(op);entries=p.entries(op)
    with pytest.raises(ValueError,match='Saldo insuficiente'):
        p.confirm(op,60,[{'entry_id':e['id'],'consumptions':{spool:'600'}} for e in entries])
    assert p.summary(op)['attempts']==0 and p.catalog.get('printers',1)['accumulated_minutes']==0
    p.confirm(op,60,[{'entry_id':e['id'],'consumptions':{spool:'400'}} for e in entries])
    assert p.catalog.get('filaments',spool)['remaining_mg']==200000
    assert store.db.execute("SELECT count(*) FROM stock_movements WHERE operation_key LIKE 'op:%:filament:%'").fetchone()[0]==1


def test_changed_photo_or_upstream_data_blocks_already_reserved_delivery(system):
    store,p,_,product,variant,_,_=system;sales=Sales(store);client=sales.save_client({'name':'Cliente'})
    order=sales.create_order(client,[{'variant_id':variant,'quantity':1,'unit_price':'5','fulfillment':'production'}]);item=sales.items(order)[0]['id']
    op=create(system,qty=1,item_id=item);p.start(op);confirm(system,op);inspect_all(system,op);p.complete(op);sales.reserve_item(item)
    row=store.db.execute('SELECT path FROM inspection_photos LIMIT 1').fetchone();path=store.home/row[0];original=path.read_bytes();path.write_bytes(b'altered')
    with pytest.raises(ValueError,match='alterada'):sales.deliver(order,'deliver','pickup')
    assert p.pieces(op)[0]['state']=='reserved' and sales.delivery(order)['state']=='waiting'
    path.write_bytes(original);p.products.save({'name':'Produto atualizado','category':'functional'},product)
    with pytest.raises(ValueError,match='revalidação'):sales.deliver(order,'deliver','pickup')
    assert p.pieces(op)[0]['state']=='reserved'


def test_reprint_replaces_finished_spool_and_uses_new_spool_rates(system):
    _,p,spool,*_=system;op=create(system,grams='1000');p.start(op);confirm(system,op,grams='1000')
    assert p.catalog.get('filaments',spool)['state']=='finished'
    with pytest.raises(ValueError,match='finalizado'):p.reprint(op,'QA')
    new=p.catalog.save_filament({'brand':'Marca','material':'PLA','color':'Branco','name':'Substituto','initial_grams':'1000','remaining_grams':'1000','purchase':'200','reference_per_g':'0.3'})
    reprint=p.reprint(op,'QA',{spool:new})
    assert json.loads(p.entries(reprint)[0]['planned'])['filaments'][0]['id']==new
    assert json.loads(p.get(reprint)['planned'])['reference_cents']==30110


def test_photo_path_rejects_escape_and_problem_links_product_and_op(system):
    store,p,_,product,*_=system;op=create(system,qty=1)
    pk=p.problem(op,product,'detail','Fragilidade de ponta','QA')
    assert p.problems(product)[0]['id']==pk and p.problems(product)[0]['code']==p.get(op)['code']
    with pytest.raises(ValueError):p.problem(op,999,'detail','Other','QA')
    p.start(op);confirm(system,op);inspect_all(system,op)
    row=store.db.execute('SELECT id FROM inspection_photos LIMIT 1').fetchone()
    with store.db:store.db.execute("UPDATE inspection_photos SET path='../outside.png' WHERE id=?",(row[0],))
    with pytest.raises(ValueError,match='inválida'):p.photo_path(row[0])


def test_manual_mixed_rateio_is_documented_and_conserves_machine(system):
    _,p,spool,_,variant,project,_=system
    entry={'variant_id':variant,'project_id':project,'quantity':1,'filaments':[(spool,'10')]}
    op=p.create(1,60,[entry,entry],'QA','Settings',weights=['1','3'],allocation_reason='Segundo modelo exige mais atenção de máquina')
    snapshots=[json.loads(e['planned']) for e in p.entries(op)]
    assert [s['machine_cost'] for s in snapshots]==['0.28','0.82']
    assert json.loads(p.get(op)['planned'])['allocation_reason']=='Segundo modelo exige mais atenção de máquina'
    assert sum(Decimal(s['machine_cost']) for s in snapshots)==Decimal('1.10')


def test_custom_order_production_selects_variant_without_stock_or_commercial_changes(system):
    store,p,_,_,variant,_,_=system;sales=Sales(store);client=sales.save_client({'name':'Cliente'})
    order=sales.create_order(client,[{'description':'Projeto personalizado aprovado','quantity':1,'unit_price':'30','fulfillment':'production'}]);item=sales.items(order)[0];snapshot=item['snapshot']
    assert item['variant_id'] is None and p.inventory.pieces()==[]
    op=create(system,qty=1,item_id=item['id'])
    assert store.db.execute('SELECT variant_id FROM order_fulfillment WHERE item_id=?',(item['id'],)).fetchone()[0]==variant
    p.start(op);confirm(system,op);inspect_all(system,op);p.complete(op)
    sales.reserve_item(item['id']);sales.deliver(order,'deliver','pickup')
    after=sales.get('order_items',item['id'])
    assert after['snapshot']==snapshot and after['description']=='Projeto personalizado aprovado' and after['total_cents']==3000
    assert p.pieces(op)[0]['state']=='issued' and p.catalog.get('printers',1)['accumulated_minutes']==60
