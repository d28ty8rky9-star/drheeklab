"""Encrypted backup, background maintenance and installer preflight regressions."""
from pathlib import Path
import json
import subprocess
import sys
import sqlite3
import xml.etree.ElementTree as ET
from types import SimpleNamespace
import pytest
from PySide6.QtCore import QLockFile
from PySide6.QtWidgets import QMessageBox,QInputDialog
from drheeklab.storage import Storage
from drheeklab.backup import create_backup,verify_backup,restore_backup
from drheeklab.backup_crypto import is_encrypted,decrypt_file,encrypt_file
from drheeklab.recovery import RecoverySession
from drheeklab.security import Auth
from drheeklab.maintenance import run_backup,backup_main,prepare_update
from drheeklab.scheduler import task_xml,task_name,NS
from test_phase7 import system

PASSWORD='Senha independente de backup 2026'

def test_backup_closes_every_temporary_sqlite_connection_even_with_live_references(system,monkeypatch):
    store,*_=system;connections=[];connect=sqlite3.connect
    class TrackedConnection(sqlite3.Connection):
        explicitly_closed=False
        def close(self):
            super().close();self.explicitly_closed=True
    def tracked(*args,**kwargs):
        kwargs['factory']=TrackedConnection
        connection=connect(*args,**kwargs);connections.append(connection);return connection
    monkeypatch.setattr(sqlite3,'connect',tracked)
    path=create_backup(store)
    assert verify_backup(path,'test')
    assert connections and all(c.explicitly_closed for c in connections)

def test_encrypted_transfer_includes_media_documents_and_original_login(system,tmp_path):
    store,documents,products,product,variant,photo,project,photos=system
    Auth(store).create('Senha de login preservada');store.save_draft('home_notes','anotação protegida')
    identifier=documents.emit_catalog([{'variant_id':variant,'price':'25'}]);before=documents.path(identifier).read_bytes()
    destination=tmp_path/'external';path=create_backup(store,destination,password=PASSWORD)
    assert path.suffix=='.hbk' and is_encrypted(path) and not list(destination.glob('*.zip'))
    assert b'anota' not in path.read_bytes()
    assert verify_backup(path,'test',password=PASSWORD)
    with RecoverySession(path,'test',password=PASSWORD) as session:
        assert Auth(session.source).verify('Senha de login preservada')
        session.apply(tmp_path/'other-computer',confirmed=True)
    restored=Storage(tmp_path/'other-computer')
    try:
        from drheeklab.documents import Documents
        assert Documents(restored).path(identifier).read_bytes()==before
        assert restored.load_draft('home_notes')=='anotação protegida'
        assert Auth(restored).verify('Senha de login preservada')
        assert not Auth(restored).verify(PASSWORD)
    finally:restored.close()
    assert PASSWORD.encode() not in store.path.read_bytes()
    assert PASSWORD not in '\n'.join(str(tuple(r)) for r in store.db.execute('SELECT * FROM audit'))

@pytest.mark.parametrize('kind',['wrong-password','ciphertext','header','truncated'])
def test_bad_encrypted_backup_cannot_replace_existing_state(system,tmp_path,kind):
    store,*_=system;store.set('protected',123);path=create_backup(store,password=PASSWORD)
    damaged=tmp_path/'damaged.hbk';data=bytearray(path.read_bytes());password=PASSWORD
    if kind=='wrong-password':password='Outra senha suficientemente longa'
    elif kind=='ciphertext':data[70]^=1
    elif kind=='header':data[10]^=1
    else:data=data[:-20]
    damaged.write_bytes(data)
    with pytest.raises(ValueError):restore_backup(store,damaged,password=password)
    assert store.get('protected')==123
    assert not list(store.root.glob('*rollback*'))
    assert not list((store.home/'Backups').glob('*.part'))

def test_encryption_requires_password_and_never_clobbers_existing_output(system,tmp_path):
    store,*_=system;path=create_backup(store,password=PASSWORD)
    with pytest.raises(ValueError,match='criptografado'):verify_backup(path,'test')
    with pytest.raises(ValueError,match='12'):create_backup(store,password='curta')
    output=tmp_path/'keep';output.write_bytes(b'keep')
    with pytest.raises(FileExistsError):decrypt_file(path,output,PASSWORD)
    assert output.read_bytes()==b'keep'
    plain=create_backup(store)
    assert plain.suffix=='.zip' and verify_backup(plain,'test')
    with pytest.raises(FileExistsError):encrypt_file(plain,output,PASSWORD)
    assert output.read_bytes()==b'keep'

def test_backup_rejects_symlinks_without_leaking_external_file(system,tmp_path):
    store,*_=system;outside=tmp_path/'private.txt';outside.write_text('external secret')
    link=store.home/'Marca'/'link.txt'
    try:link.symlink_to(outside)
    except (OSError,NotImplementedError):pytest.skip('Criação de symlink requer privilégio do sistema operacional')
    with pytest.raises(ValueError,match='simbólicos'):create_backup(store)
    assert not list((store.home/'Backups').glob('*.zip'))

def test_backup_output_failure_cleans_owned_partial(system,tmp_path,monkeypatch):
    store,*_=system
    import drheeklab.backup_crypto as crypto
    def fail(source,destination,password):Path(destination).write_bytes(b'partial');raise OSError('disco cheio simulado')
    monkeypatch.setattr(crypto,'encrypt_file',fail)
    with pytest.raises(OSError):create_backup(store,tmp_path/'target',password=PASSWORD)
    assert not list((tmp_path/'target').iterdir())
    assert store.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'

def test_background_daily_deduplicates_and_preserves_schema_login(system,tmp_path):
    store,*_=system;Auth(store).create('Senha de login original');root=store.root;store.close()
    first=run_backup(root,'test',destination=tmp_path/'external',daily=True)
    assert first['status']=='passed' and verify_backup(first['backup'],'test')
    assert run_backup(root,'test',daily=True)['status']=='already-backed-up'
    assert len(list((tmp_path/'external').glob('*.zip')))==1
    reopened=Storage(root)
    try:assert Auth(reopened).verify('Senha de login original')
    finally:reopened.close()

def test_background_respects_live_ui_lock_and_does_not_initialize_database(system,tmp_path):
    store,*_=system;lock=QLockFile(str(store.root/'.test.lock'));assert lock.tryLock(100)
    try:
        assert run_backup(store.root,'test')['status']=='busy'
        assert not list((store.home/'Backups').glob('*.zip'))
        with pytest.raises(ValueError,match='instâncias'):prepare_update(store.root)
    finally:lock.unlock()
    with pytest.raises(ValueError,match='ainda não criado'):run_backup(tmp_path/'empty','production')
    assert not list((tmp_path/'empty').rglob('*.sqlite3'))

def test_background_failure_logs_and_leaves_database(system,monkeypatch):
    store,*_=system
    import drheeklab.maintenance as module
    def fail(*args,**kwargs):raise OSError('permissão negada simulada')
    monkeypatch.setattr(module,'create_backup',fail)
    assert backup_main(store.root,'test')==1
    log=json.loads(next((store.home/'Logs').glob('backup-job-*.json')).read_text())
    assert log['status']=='failed' and log['type']=='OSError'
    assert store.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'

def test_real_headless_cli_without_display_uses_only_selected_environment(system,tmp_path):
    store,*_=system;production=Storage(store.root,'production');production.set('protected',456);production.close();root=store.root;store.close()
    result=subprocess.run([sys.executable,'-m','drheeklab','--scheduled-backup','--environment','test','--data-dir',str(root),'--backup-destination',str(tmp_path/'external')],capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr
    assert len(list((tmp_path/'external').glob('*.zip')))==1
    production=Storage(root,'production')
    try:
        assert production.get('protected')==456
        assert not list((production.home/'Backups').glob('*.zip'))
    finally:production.close()

def test_preupdate_all_existing_environments_backed_up_before_changes(system):
    store,*_=system;store.save_draft('home_notes','preservado');production=Storage(store.root,'production');production.set('protected',999);production.close()
    result=prepare_update(store.root)
    assert result['status']=='passed' and {r['environment'] for r in result['environments']}=={'test','production'}
    for row in result['environments']:assert verify_backup(row['backup'],row['environment'])
    assert store.load_draft('home_notes')=='preservado'

def test_preupdate_newer_schema_blocks_without_downgrade(system):
    store,*_=system;store.db.execute('PRAGMA user_version=99');store.db.commit()
    with pytest.raises(RuntimeError,match='incompatível'):prepare_update(store.root)
    assert store.db.execute('PRAGMA user_version').fetchone()[0]==99

def test_task_xml_contains_no_password_least_privilege_quoted_paths(tmp_path):
    text=task_xml(tmp_path/'data & business','test','21:30',tmp_path/'external & disk',sid='S-1-5-21-123',executable=r'C:\Program Files\DrHeekLab\DrHeekLab.exe',frozen=True)
    tree=ET.fromstring(text);n={'t':NS}
    assert tree.find('.//t:RunLevel',n).text=='LeastPrivilege'
    assert tree.find('.//t:LogonType',n).text=='InteractiveToken'
    args=tree.find('.//t:Arguments',n).text
    assert '--scheduled-backup' in args and '--environment test' in args and '"' in args
    assert 'password' not in text and '21:30:00' in text
    assert task_name(tmp_path,'test')!=task_name(tmp_path,'production')
    with pytest.raises(ValueError):task_xml(tmp_path,'test','25:30',sid='S-1')

def test_scheduler_success_failure_and_assisted_export_are_honest(system,tmp_path,monkeypatch):
    store,*_=system
    import drheeklab.scheduler as module
    monkeypatch.setattr(module,'IS_WINDOWS',True);monkeypatch.setattr(module,'current_sid',lambda:'S-1-5-21-123')
    calls=[]
    def run(args,**kwargs):calls.append(args);return SimpleNamespace(returncode=0)
    monkeypatch.setattr(module.subprocess,'run',run)
    assert module.install_task(store,'19:45')['encrypted'] is False
    assert calls[-1][0:2]==['schtasks','/Create']
    output=tmp_path/'assist.xml';module.export_task(store,output)
    assert ET.fromstring(output.read_text(encoding='utf-16')).tag=='{'+NS+'}Task'
    module.remove_task(store);assert store.get('backup_task') is None
    monkeypatch.setattr(module.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=1))
    with pytest.raises(ValueError):module.install_task(store)
    assert store.get('backup_task') is None

def test_encryption_dialog_cancel_and_password_confirmation(monkeypatch):
    from drheeklab.backup_ui import choose_encryption
    monkeypatch.setattr(QMessageBox,'question',lambda *a:QMessageBox.Cancel)
    assert choose_encryption(None)==(None,False)
    monkeypatch.setattr(QMessageBox,'question',lambda *a:QMessageBox.No)
    assert choose_encryption(None)==(None,True)
    monkeypatch.setattr(QMessageBox,'question',lambda *a:QMessageBox.Yes)
    values=iter([(PASSWORD,True),('senha diferente longa',True)])
    monkeypatch.setattr(QInputDialog,'getText',lambda *a:next(values))
    with pytest.raises(ValueError,match='conferem'):choose_encryption(None)

def test_headless_encrypted_cli_password_not_in_logs_or_arguments(system,tmp_path):
    store,*_=system;root=store.root;store.close()
    args=[sys.executable,'-m','drheeklab','--backup-now','--environment','test','--data-dir',str(root),'--backup-destination',str(tmp_path/'external'),'--backup-password-stdin']
    result=subprocess.run(args,input=PASSWORD+'\n',capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr
    backup=next((tmp_path/'external').glob('*.hbk'));assert verify_backup(backup,'test',password=PASSWORD)
    assert PASSWORD not in result.stdout+result.stderr+' '.join(args)
    assert all(PASSWORD not in f.read_text() for f in (root/'TESTES'/'Logs').glob('backup-job-*.json'))

def test_ui_manual_encrypted_backup_and_bad_restore_keep_data(system,tmp_path,monkeypatch):
    from drheeklab.ui import Window
    from PySide6.QtWidgets import QFileDialog
    import drheeklab.backup_ui as module
    store,*_=system;store.set('protected',987);window=Window(store)
    monkeypatch.setattr(QFileDialog,'getExistingDirectory',lambda *a:str(tmp_path/'external'))
    monkeypatch.setattr(module,'choose_encryption',lambda *a:(PASSWORD,True))
    monkeypatch.setattr(QMessageBox,'information',lambda *a:QMessageBox.Ok)
    window.manual_backup();backup=next((tmp_path/'external').glob('*.hbk'))
    assert verify_backup(backup,'test',password=PASSWORD)
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *a:(str(backup),''))
    monkeypatch.setattr(module,'backup_password',lambda *a:('Senha incorreta bastante longa',True))
    warnings=[];monkeypatch.setattr(QMessageBox,'warning',lambda *a:warnings.append(a[2]))
    def forbidden(*args):raise AssertionError('Confirmação destrutiva não pode ocorrer antes da autenticação do backup')
    monkeypatch.setattr(QMessageBox,'question',forbidden)
    window.restore()
    assert warnings and 'incorreta' in warnings[0]
    assert store.get('protected')==987 and not getattr(window,'restored',False)
    window.close()

def test_schedule_dialog_reports_plaintext_and_platform_limit(system):
    from drheeklab.backup_ui import ScheduleDialog
    from PySide6.QtWidgets import QLabel
    import drheeklab.scheduler as module
    store,*_=system;dialog=ScheduleDialog(store)
    assert any('NÃO criptografado' in label.text() for label in dialog.findChildren(QLabel))
    if not module.IS_WINDOWS:
        with pytest.raises(ValueError,match='Windows'):dialog.persist()
    dialog.close()

def test_encrypted_backup_does_not_change_financial_metrics_or_stock(system):
    from drheeklab.finance import Finance
    from drheeklab.inventory import Inventory
    store,*_=system;finance=Finance(store)
    finance.entry('capital_in','123.45','Aporte de auditoria','QA')
    before=finance.report()['metrics'];stock=Inventory(store).summary()
    create_backup(store,password=PASSWORD)
    assert finance.report()['metrics']==before
    assert Inventory(store).summary()==stock
