"""The requested planning -> queue -> inspected stock flow, without cash duplication."""
import json
from datetime import date,timedelta
import pytest
from PySide6.QtGui import QImage,QColor
from drheeklab.storage import Storage
from drheeklab.production import Production,CHECKS
from drheeklab.finance import Finance
from drheeklab.sales import Sales
from drheeklab.backup import create_backup,verify_backup

@pytest.fixture
def system(tmp_path):
    store=Storage(tmp_path/'data');production=Production(store)
    spool=production.catalog.save_filament({'name':'PLA azul','brand':'Teste','material':'PLA','color':'Azul','purchase':'100','initial_grams':'1000','remaining_grams':'1000','reference_per_g':'0.2'})
    product=production.products.save({'name':'Dragão luminoso','category':'decorative'})
    variant=production.products.variants(product)[0]['id']
    source=tmp_path/'dragon.stl';source.write_text('solid dragon\nendsolid dragon')
    project=production.products.import_media(product,source,'project')
    photos={}
    for view,color in [('front','red'),('back','green'),('detail','blue')]:
        image=QImage(30,20,QImage.Format_RGB32);image.fill(QColor(color))
        path=tmp_path/(view+'.png');assert image.save(str(path));photos[view]=path
    yield store,production,spool,product,variant,project,photos
    store.close()

def recipe(system,minutes=60,grams='10',aux='1.00'):
    _,p,spool,_,variant,project,_=system
    return p.save_recipe(variant,1,project,minutes,[(spool,grams)],aux,'0,2 mm / 15% / 210 C')

def inspect(system,op):
    _,p,*_=system
    for piece in p.pieces(op):
        checks={key:{'result':'ok'} for key in CHECKS[piece['category']]}
        p.inspect(op,piece['id'],'approved',checks,system[-1],'QA','Peça revisada; acabamento conforme.')

def test_full_flow_cost_only_at_completion_and_sale_cpv_once(system):
    store,p,spool,product,variant,project,_=system;f=Finance(store)
    recipe(system)
    assert p.recipe(variant)['revision']==1
    assert not p.inventory.pieces() and not f.report()['production']
    assert f.report()['metrics']['cash_flow_cents']==0
    op=p.create_from_recipe(variant,2,'Operador','high')
    assert p.get(op)['priority']=='high' and p.entries(op)[0]['quantity']==2
    assert json.loads(p.get(op)['planned'])['minutes']==120
    assert json.loads(p.entries(op)[0]['planned'])['filaments'][0]['grams']=='20'
    assert p.catalog.get('filaments',spool)['remaining_mg']==1000000
    assert not f.report()['production'] and not p.inventory.pieces()
    p.start(op);p.confirm_from_recipe(op)
    assert len(p.pieces(op))==2  # internal inspection candidates, not stocked goods
    assert not p.inventory.pieces() and p.inventory.summary()[0]['physical']==0
    assert not f.report()['production'] and f.report()['metrics']['production_cost_cents']==0
    assert not [r for r in p.inventory.movements() if r['piece_id']]
    with pytest.raises(ValueError,match='individualmente'):p.complete(op)
    assert store.db.execute('SELECT count(*) FROM production_completions').fetchone()[0]==0
    inspect(system,op);assert not p.inventory.pieces()
    result=p.complete(op)
    assert result['total_cents']==620  # 20g R$2 + 120min R$2.20 + auxiliaries R$2
    assert sum(r['unit_cost_cents'] for r in p.inventory.pieces())==620
    assert p.inventory.summary()[0]['available']==2
    report=f.report();assert report['metrics']['production_cost_cents']==620
    assert report['metrics']['cost_of_sales_cents']==0
    assert report['metrics']['cash_flow_cents']==0 and not report['payables']
    assert store.db.execute('SELECT count(*) FROM production_completions').fetchone()[0]==1
    with pytest.raises(ValueError):p.complete(op)
    assert f.report()['metrics']['production_cost_cents']==620
    sales=Sales(store);client=sales.save_client({'name':'Cliente'})
    order=sales.create_order(client,[{'variant_id':variant,'quantity':2,'unit_price':'20','fulfillment':'stock'}])
    sales.deliver(order,'deliver','pickup')
    report=f.report();assert report['metrics']['cost_of_sales_cents']==620
    assert report['metrics']['commercial_result_cents']==3380
    assert report['metrics']['cash_flow_cents']==0
    assert f.report()['metrics']['cost_of_sales_cents']==620
    assert verify_backup(create_backup(store),store.environment)

def test_completion_date_and_reinspection_do_not_change_cost(system):
    store,p,_,_,variant,*_=system;f=Finance(store);recipe(system)
    op=p.create_from_recipe(variant,1,'Operador');p.start(op);p.confirm_from_recipe(op)
    earlier=(date.today()-timedelta(days=2)).isoformat();today=date.today().isoformat()
    store.db.execute('UPDATE production_attempts SET created_at=? WHERE op_id=?',(earlier+'T12:00:00+00:00',op));store.db.commit()
    inspect(system,op);p.complete(op)
    assert f.report(earlier,earlier)['metrics']['production_cost_cents']==0
    assert f.report(today,today)['metrics']['production_cost_cents']==310
    event=dict(store.db.execute('SELECT * FROM production_completions').fetchone())
    inspect(system,op);assert len(p.inventory.pieces())==1  # published units stay tracked
    p.complete(op)
    assert dict(store.db.execute('SELECT * FROM production_completions').fetchone())==event
    assert f.report()['metrics']['production_cost_cents']==310

def test_frozen_recipe_and_catalog_edits_do_not_rewrite_order(system):
    store,p,spool,product,variant,*_=system;recipe(system)
    op=p.create_from_recipe(variant,1,'Operador')
    recipe(system,minutes=30,grams='50',aux='0')
    assert p.recipe(variant)['revision']==2 and p.recipe_order(op)['revision']==1
    p.products.save({'name':'Dragão renomeado','category':'decorative'},product)
    store.db.execute('UPDATE printers SET energy_hour_cents=999 WHERE id=1')
    store.db.execute('UPDATE filaments SET purchase_cents=90000 WHERE id=?',(spool,));store.db.commit()
    p.start(op);p.confirm_from_recipe(op);inspect(system,op);p.complete(op)
    assert p.summary(op)['total_cents']==310  # original costs/amounts, not new recipe

def test_notes_three_distinct_photos_and_atomic_failed_confirmation(system):
    store,p,spool,_,variant,*_=system;recipe(system)
    op=p.create_from_recipe(variant,1,'Operador');p.start(op)
    store.db.execute('UPDATE filaments SET remaining_mg=1 WHERE id=?',(spool,));store.db.commit()
    with pytest.raises(ValueError,match='Saldo insuficiente'):p.confirm_from_recipe(op)
    assert not p.pieces(op) and p.get(op)['state']=='printing'
    assert store.db.execute('SELECT count(*) FROM production_attempts').fetchone()[0]==0
    assert p.catalog.get('printers',1)['accumulated_minutes']==0
    store.db.execute('UPDATE filaments SET remaining_mg=1000000 WHERE id=?',(spool,));store.db.commit()
    p.confirm_from_recipe(op);piece=p.pieces(op)[0];checks={k:{'result':'ok'} for k in CHECKS[piece['category']]}
    with pytest.raises(ValueError,match='Observações'):p.inspect(op,piece['id'],'approved',checks,system[-1],'QA')
    same={key:system[-1]['front'] for key in system[-1]}
    with pytest.raises(ValueError,match='distintas'):p.inspect(op,piece['id'],'approved',checks,same,'QA','Conforme')
    assert not p.inventory.pieces() and not Finance(store).report()['production']

def test_failed_attempts_absorbed_once_and_reprint_keeps_deferred_recognition(system):
    store,p,_,_,variant,*_=system;recipe(system)
    op=p.create_from_recipe(variant,2,'Operador');p.start(op)
    p.confirm_from_recipe(op,failed=2,reason='Falha de adesão')
    assert not Finance(store).report()['production']
    assert not Finance(store).report()['production_adjustments']
    p.start(op);p.confirm_from_recipe(op);inspect(system,op);p.complete(op)
    report=Finance(store).report()
    assert report['metrics']['production_cost_cents']==1240
    assert report['metrics']['unabsorbed_production_loss_cents']==0
    assert sum(r['unit_cost_cents'] for r in p.inventory.pieces())==1240
    reprint=p.reprint(op,'Operador');assert p.recipe_order(reprint)
    p.start(reprint);p.confirm_from_recipe(reprint)
    assert Finance(store).report()['metrics']['production_cost_cents']==1240
    assert len(p.inventory.pieces())==2

def test_manual_purchase_and_legacy_records_preserved(system):
    store,p,spool,_,variant,project,_=system
    p.inventory.receive(variant,1,'Peça comprada','available','Nova','bought',total_cost='50',reviewer='Proprietário')
    assert p.inventory.pieces()[0]['unit_cost_cents']==5000
    op=p.create(1,60,[{'variant_id':variant,'project_id':project,'quantity':1,'filaments':[(spool,'10')]}],'Operador','PLA')
    p.start(op);p.confirm(op,60,[{'entry_id':p.entries(op)[0]['id'],'consumptions':{spool:'10'}}])
    assert len(p.inventory.pieces())==2
    assert Finance(store).report()['metrics']['production_cost_cents']==210  # historical flow unchanged
    assert not Finance(store).report()['cash']
