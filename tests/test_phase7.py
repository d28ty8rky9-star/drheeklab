from pathlib import Path
from datetime import date,timedelta
import hashlib
import json
import sqlite3
import pytest
from pypdf import PdfReader
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage,QColor
from drheeklab.storage import Storage,SCHEMA_VERSION,MIGRATIONS
from drheeklab.documents import Documents
from drheeklab.notifications import Notifications
from drheeklab.lifecycle import Lifecycle
from drheeklab.products import Products
from drheeklab.finance import Finance
from drheeklab.catalog import Catalog
from drheeklab.sales import Sales
from drheeklab.production import Production,CHECKS
from drheeklab.security import Auth
from drheeklab.backup import create_backup,verify_backup,digest,daily_backup
from drheeklab.recovery import RecoverySession,RecoveryTarget

APP=QApplication.instance() or QApplication([])
TODAY=date.today().isoformat()

@pytest.fixture
def system(tmp_path):
    store=Storage(tmp_path/'data');products=Products(store)
    product=products.save({'name':'Suporte','category':'functional','description':'Descrição pública','suggested_price':'30','planned_cost':'10'})
    variant=products.variants(product)[0]['id'];photos={}
    for key,color in [('front','red'),('back','green'),('detail','blue')]:
        img=QImage(40,30,QImage.Format_RGB32);img.fill(QColor(color));path=tmp_path/(key+'.png');assert img.save(str(path));photos[key]=path
    photo=products.import_media(product,photos['front'],'photo')
    source=tmp_path/'model.stl';source.write_text('solid test');project=products.import_media(product,source,'project')
    store.set('logo',None)
    yield store,Documents(store),products,product,variant,photo,project,photos
    try:store.close()
    except sqlite3.ProgrammingError:pass


def text(path):return '\n'.join(p.extract_text() for p in PdfReader(path).pages)


def test_catalog_embeds_photo_price_only_selected_and_freezes_data(system,tmp_path):
    store,d,products,product,variant,photo,project,photos=system
    identifier=d.emit_catalog([{'variant_id':variant,'price':'25','description':'Oferta escolhida'}]);path=d.path(identifier);before=path.read_bytes();body=text(path)
    assert 'Suporte' in body and 'Oferta escolhida' in body and '25,00' in body
    assert '10,00' not in body and 'Custo' not in body and 'Logotipo oficial não configurado' in body
    assert any('/XObject' in page['/Resources'] for page in PdfReader(path).pages)
    products.save({'name':'Novo nome','category':'decorative','suggested_price':'99','planned_cost':'66'},product)
    copied=d.export(identifier,tmp_path/'share.pdf');assert copied.read_bytes()==before
    assert d.path(identifier).read_bytes()==before and d.get(identifier)['version']==1
    second=d.emit_catalog([{'variant_id':variant,'price':'29'}]);assert d.get(second)['version']==2 and 'Novo nome' in text(d.path(second))
    with pytest.raises(ValueError):d.emit_catalog([{'variant_id':variant,'price':'2'},{'variant_id':variant,'price':'3'}])


def test_brand_embedded_and_old_document_survives_logo_change(system,tmp_path):
    store,d,products,product,variant,photo,project,photos=system
    logo=store.home/'Marca'/'logo.png';logo.write_bytes(photos['front'].read_bytes());store.set('logo','Marca/logo.png')
    first=d.emit_catalog([{'variant_id':variant,'price':'30'}]);before=d.path(first).read_bytes();snapshot=json.loads(d.get(first)['snapshot'])
    assert snapshot['brand']['sha256']==digest(logo) and snapshot['brand']['status']=='Marca configurada'
    store.set('logo',None);assert d.path(first).read_bytes()==before
    store.set('logo','../outside.png')
    with pytest.raises(ValueError):d.emit_catalog([{'variant_id':variant,'price':'30'}])
    assert len(d.rows())==1


def test_finance_pdf_snapshot_criteria_and_old_values_preserved(system):
    store,d,*_=system;f=Finance(store);f.entry('capital_in','100','Capital','Titular')
    first=d.emit_finance();path=d.path(first);before=path.read_bytes();body=text(path)
    assert 'Caixa consolidado' in body and '100,00' in body and 'CPV' in body and 'não' in body
    f.entry('capital_out','10','Retirada','Titular');assert d.path(first).read_bytes()==before
    snap=json.loads(d.get(first)['snapshot']);assert snap['data']['metrics']['cash_closing_cents']==10000
    second=d.emit_finance();assert d.get(second)['version']==2
    assert json.loads(d.get(second)['snapshot'])['data']['metrics']['cash_closing_cents']==9000


def production(system):
    store,d,products,product,variant,photo,project,photos=system;p=Production(store)
    spool=p.catalog.save_filament({'brand':'Marca','material':'PLA','color':'Azul','name':'PLA','purchase':'100','initial_grams':'1000','remaining_grams':'1000','reference_per_g':'0.2'})
    op=p.create(1,60,[{'variant_id':variant,'project_id':project,'quantity':1,'filaments':[(spool,'10')]}],'QA','0,2 mm / 15%')
    p.start(op);p.confirm(op,60,[{'entry_id':p.entries(op)[0]['id'],'consumptions':{spool:'10'}}])
    piece=p.pieces(op)[0];p.inspect(op,piece['id'],'approved',{k:{'result':'ok'} for k in CHECKS[piece['category']]},photos,'Inspetor');p.complete(op)
    return p,op


def test_production_pdf_inspection_photos_params_and_immutable_costs(system):
    store,d,*_=system;p,op=production(system)
    first=d.emit_production(op);before=d.path(first).read_bytes();body=text(d.path(first))
    assert 'FR-001' in body and 'Inspetor' in body and 'Conforme' in body and '0,2 mm / 15%' in body and '2,10' in body
    snap=json.loads(d.get(first)['snapshot']);assert len(snap['data']['inspections'][0]['photos'])==3
    p.revalidate(op,'Novos parâmetros','Ajuste do teste');assert d.path(first).read_bytes()==before
    second=d.emit_production(op);assert d.get(second)['version']==2 and 'Novos parâmetros' in text(d.path(second))


def test_failed_document_render_rolls_back_sequence_and_file(system,monkeypatch):
    store,d,products,product,variant,*_=system
    def fail(*args):raise ValueError('Falha de PDF')
    monkeypatch.setattr('drheeklab.documents.render',fail)
    with pytest.raises(ValueError):d.emit_catalog([{'variant_id':variant,'price':'30'}])
    assert d.rows()==[] and not list((store.home/'Catálogos').glob('*.pdf'))
    assert store.db.execute("SELECT count(*) FROM document_sequences WHERE kind='CAT'").fetchone()[0]==0


def test_archive_photo_project_document_restore_keeps_files_and_block_active_op(system):
    store,d,products,product,variant,photo,project,photos=system;l=Lifecycle(store)
    document=d.emit_catalog([{'variant_id':variant,'price':'30'}]);before=d.path(document).read_bytes()
    l.archive('generated_documents',document,True,'Antigo');assert d.rows()==[] and len(d.rows(archived=True))==1
    l.archive('generated_documents',document,False,'Recuperar');assert d.path(document).read_bytes()==before
    photo_path=products.media_path(photo,'photo');l.archive('product_photos',photo,True,'Fora da galeria');assert products.media(product,'photo')==[] and photo_path.exists()
    with pytest.raises(ValueError):d.emit_catalog([{'variant_id':variant,'price':'30'}])
    l.archive('product_photos',photo,False,'Voltar à galeria');assert len(products.media(product,'photo'))==1
    l.archive('project_versions',project,True,'Versão antiga');assert products.media(product,'project')==[]
    l.archive('project_versions',project,False,'Recuperar versão')
    p,op=production(system);p.revalidate(op,'Revalidar','Teste')
    with pytest.raises(ValueError,match='ativa'):l.archive('project_versions',project,True,'Não deve')


def test_parent_restore_order_and_financial_cancel_not_in_trash(system):
    store,d,products,product,variant,*_=system;l=Lifecycle(store)
    l.archive('variants',variant,True,'Fora de linha');l.archive('products',product,True,'Fora de linha')
    with pytest.raises(ValueError):l.archive('variants',variant,False,'Recuperar')
    l.archive('products',product,False,'Recuperar');l.archive('variants',variant,False,'Recuperar')
    with pytest.raises(ValueError):l.archive('orders',1,False,'Reviver cancelamento')
    assert l.rows()==[]


def test_notifications_due_low_delivery_quotes_maintenance_and_seen_no_money_effect(system):
    store,d,products,product,variant,*_=system;catalog=Catalog(store);sales=Sales(store);f=Finance(store)
    catalog.save_filament({'brand':'Marca','material':'PLA','color':'Azul','name':'Pouco','purchase':'10','initial_grams':'100','remaining_grams':'20','reference_per_g':'0.2','state':'open'})
    catalog.save_filament({'brand':'Marca','material':'PLA','color':'Preto','name':'Desconhecido','purchase':'10','initial_grams':None,'remaining_grams':None,'reference_per_g':'0.2','state':'open'})
    client=sales.save_client({'name':'Cliente'});past=(date.today()-timedelta(days=1)).isoformat();soon=(date.today()+timedelta(days=3)).isoformat()
    order=sales.create_order(client,[{'variant_id':variant,'quantity':1,'unit_price':'30'}],due_on=past);quote=sales.create_quote(client,[{'variant_id':variant,'quantity':1,'unit_price':'30'}],valid_until=soon)
    bill=f.create_payable('Conta',9,'10',first_due=soon);catalog.add_maintenance(1,TODAY,'Preventiva',next_due=soon)
    n=Notifications(store);rows=n.refresh();assert {r['kind'] for r in rows}=={'filament','receivable','payable','delivery','quote','maintenance'}
    assert sum(r['kind']=='filament' for r in rows)==1
    before=f.report()['metrics'];key=next(r['key'] for r in rows if r['kind']=='payable');n.mark(key,1)
    assert next(r for r in n.refresh() if r['key']==key)['snoozed'] and f.report()['metrics']==before
    installment=f.payables()[0];f.pay(installment['id'],'1')
    changed=next(r for r in n.refresh() if r['key']==key);assert not changed['read'] and not changed['snoozed']
    f.pay(installment['id'],'9');assert not any(r['key']==key for r in n.refresh())
    sales.reject_quote(quote,'Sem interesse');assert not any(r['kind']=='quote' for r in n.refresh())


def test_notification_reappears_after_condition_resolved(system):
    store,*_=system;c=Catalog(store);spool=c.save_filament({'brand':'Marca','material':'PLA','color':'Azul','name':'Pouco','purchase':'10','initial_grams':'1000','remaining_grams':'20','reference_per_g':'0.2','state':'open'})
    n=Notifications(store);n.refresh();n.mark(f'filament:{spool}');assert n.refresh()[0]['read']
    data={'brand':'Marca','material':'PLA','color':'Azul','name':'Pouco','purchase':'10','initial_grams':'1000','remaining_grams':'500','reference_per_g':'0.2','state':'open'}
    c.save_filament(data,spool,'Saldo corrigido');assert n.refresh()==[]
    c.save_filament({**data,'remaining_grams':'20'},spool,'Novo consumo estimado');assert not n.refresh()[0]['read']


def test_audit_filters_are_literal_and_contain_reason(system):
    store,*_=system;l=Lifecycle(store);f=Finance(store);f.entry('capital_in','1','% literal','Titular')
    assert len(l.audit(reason='%'))==1 and l.audit(reason='_SQL_wildcard_')==[]
    assert any('financeiro' in r['operation'] for r in l.audit(operation='financeiro',start=TODAY,end=TODAY))


def test_backup_general_pdfs_transfer_and_corrupt_database_recovery(system,tmp_path):
    store,d,products,product,variant,*_=system
    Auth(store).create('Senha segura de QA');document=d.emit_catalog([{'variant_id':variant,'price':'30'}]);before=d.path(document).read_bytes();backup=create_backup(store);assert verify_backup(backup,'test')
    with RecoverySession(backup,'test') as session:
        assert Auth(session.source).verify('Senha segura de QA')
        destination=tmp_path/'another-pc'
        with pytest.raises(ValueError):session.apply(destination)
        assert not destination.exists()
        rollback=session.apply(destination,confirmed=True);assert rollback.exists()
    reopened=Storage(destination)
    try:assert Documents(reopened).path(document).read_bytes()==before and Auth(reopened).verify('Senha segura de QA')
    finally:reopened.close()
    store.close();damaged=b'not a sqlite database';store.path.write_bytes(damaged)
    with RecoverySession(backup,'test') as session:rollback=session.apply(store.root,confirmed=True)
    assert (rollback/'Banco de Dados'/'drheeklab.sqlite3').read_bytes()==damaged
    restored=Storage(store.root)
    try:
        assert Documents(restored).path(document).read_bytes()==before
        event=restored.db.execute("SELECT previous FROM audit WHERE operation='restauração' ORDER BY id DESC LIMIT 1").fetchone()
        assert json.loads(event[0])['database_integrity'] is False
    finally:restored.close()


def test_recovery_rejects_wrong_environment_and_newer_target(system,tmp_path):
    store,*_=system;backup=create_backup(store)
    with pytest.raises(ValueError):RecoverySession(backup,'production')
    destination=tmp_path/'future';target=RecoveryTarget(destination,'test')
    with target.db:target.db.execute('PRAGMA user_version=99')
    target.close()
    with RecoverySession(backup,'test') as session:
        with pytest.raises(ValueError,match='rebaixar'):session.apply(destination,confirmed=True)
    with sqlite3.connect(destination/'TESTES'/'Banco de Dados'/'drheeklab.sqlite3') as db:assert db.execute('PRAGMA user_version').fetchone()[0]==99


def old_database(root,version=6):
    path=root/'TESTES'/'Banco de Dados'/'drheeklab.sqlite3';path.parent.mkdir(parents=True)
    with sqlite3.connect(path) as db:
        for v in range(1,version+1):
            for statement in MIGRATIONS[v]:db.execute(statement)
        db.execute(f'PRAGMA user_version={version}');db.execute("INSERT INTO drafts VALUES('old','preserved','timestamp')")
    return path


def test_full_preupdate_backup_and_failure_preserves_old_schema(tmp_path,monkeypatch):
    root=tmp_path/'old';path=old_database(root)
    monkeypatch.setitem(MIGRATIONS,7,MIGRATIONS[7]+('INVALID SQL',))
    with pytest.raises(sqlite3.OperationalError):Storage(root)
    with sqlite3.connect(path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0]==6 and db.execute("SELECT value FROM drafts WHERE key='old'").fetchone()[0]=='preserved'
        assert not db.execute("SELECT name FROM sqlite_master WHERE name='generated_documents'").fetchone()
    archives=list((root/'TESTES'/'Backups').glob('*.zip'));assert len(archives)==1 and verify_backup(archives[0],'test')
    assert list((root/'TESTES'/'Logs').glob('migration-failed-*.json'))


def test_financial_version_stream_normalizes_empty_filters(system):
    store,d,*_=system
    first=d.emit_finance();second=d.emit_finance(client_id=None,product_id=None,printer_id=None,status=None)
    assert d.get(first)['stream']==d.get(second)['stream'] and d.get(second)['version']==2


def test_daily_backup_once_and_generated_pdf_hash_is_verified(system):
    store,d,products,product,variant,*_=system
    d.emit_catalog([{'variant_id':variant,'price':'30'}]);first=daily_backup(store)
    assert first and daily_backup(store) is None and verify_backup(first,'test')
    path=d.path(d.rows()[0]['id']);path.write_bytes(b'altered')
    with pytest.raises(ValueError):create_backup(store)


def test_restore_copy_failure_rolls_back_original_tree(system,tmp_path,monkeypatch):
    store,d,products,product,variant,*_=system
    d.emit_catalog([{'variant_id':variant,'price':'30'}]);backup=create_backup(store);before=store.path.read_bytes()
    import drheeklab.backup as module
    original=module.shutil.copytree
    def fail_on_replacing_database(source,destination,*args,**kwargs):
        if Path(source).name=='Banco de Dados' and Path(source).parent.name.startswith('tmp'):
            raise OSError('Falha de disco simulada')
        return original(source,destination,*args,**kwargs)
    with RecoverySession(backup,'test') as session:
        monkeypatch.setattr(module.shutil,'copytree',fail_on_replacing_database)
        with pytest.raises(OSError):session.apply(store.root,confirmed=True)
    # Closing the original connection avoids read/write ambiguity after rollback.
    store.close();reopened=Storage(store.root)
    try:
        assert Products(reopened).search()[0]['name']=='Suporte'
        assert Documents(reopened).path(1).is_file() and reopened.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    finally:reopened.close()
