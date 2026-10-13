"""Release evidence, historical updates and the missing global search."""
import json
import sqlite3
import sys
from importlib.resources import files
import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication,QDialog,QTextEdit
from drheeklab import __version__
from drheeklab.storage import Storage,MIGRATIONS,SCHEMA_VERSION
from drheeklab.security import Auth
from drheeklab.backup import verify_backup
from drheeklab.search import search,SearchDialog
from drheeklab.sales import Sales
from drheeklab.production import Production
from test_phase7 import system

@pytest.mark.parametrize('old_version',range(1,7))
def test_update_every_previous_schema_preserves_login_drafts_and_settings(tmp_path,old_version):
    root=tmp_path/'data';database=root/'TESTES'/'Banco de Dados'/'drheeklab.sqlite3';database.parent.mkdir(parents=True)
    with sqlite3.connect(database) as db:
        for version in range(1,old_version+1):
            for statement in MIGRATIONS[version]:db.execute(statement)
        db.execute(f'PRAGMA user_version={old_version}')
    previous=Storage(root,migrate=False)
    Auth(previous).create('Senha de atualização QA')
    previous.set('theme','light');previous.save_draft('home_notes','Histórico preservado')
    if old_version>=2:
        previous.db.execute('UPDATE printers SET investment_hour_cents=123 WHERE id=1');previous.db.commit()
    previous.close()
    current=Storage(root)
    try:
        assert current.db.execute('PRAGMA user_version').fetchone()[0]==SCHEMA_VERSION
        assert current.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert not current.db.execute('PRAGMA foreign_key_check').fetchall()
        assert Auth(current).verify('Senha de atualização QA')
        assert current.get('theme')=='light' and current.load_draft('home_notes')=='Histórico preservado'
        assert current.db.execute('SELECT investment_hour_cents FROM printers WHERE id=1').fetchone()[0]==(123 if old_version>=2 else 75)
        archives=list((current.home/'Backups').glob('*.zip'))
        assert len(archives)==1 and verify_backup(archives[0],'test')
        snapshot=next((current.home/'Backups').glob('pre-migration-*.sqlite3'))
        with sqlite3.connect(snapshot) as old:
            assert old.execute('PRAGMA user_version').fetchone()[0]==old_version
            assert old.execute("SELECT value FROM drafts WHERE key='home_notes'").fetchone()[0]=='Histórico preservado'
    finally:current.close()

def test_self_test_report_has_real_integrated_result(tmp_path,monkeypatch):
    from drheeklab.app import main
    output=tmp_path/'qa.json'
    monkeypatch.setattr(sys,'argv',['drheeklab','--self-test','--self-test-report',str(output)])
    assert main()==0
    result=json.loads(output.read_text())
    assert result['status']=='passed' and result['version']==__version__ and result['data']=='temporary only'
    assert {'restart persistence','verified backup/transfer','payables/capital/cash/CPV reconciliation'}<=set(result['checks'])

def test_failed_self_test_cannot_produce_success_report(tmp_path,monkeypatch):
    from drheeklab.app import main
    import drheeklab.smoke as smoke
    def fail():raise RuntimeError('Falha de integridade simulada')
    monkeypatch.setattr(smoke,'run',fail)
    output=tmp_path/'qa.json';output.write_text('{"status":"passed"}')
    monkeypatch.setattr(sys,'argv',['drheeklab','--self-test','--self-test-report',str(output)])
    assert main()==1
    assert json.loads(output.read_text())['status']=='failed'

@pytest.mark.parametrize('args',[['--self-test-report','unused.json'],['--self-test','--data-dir','protected'],['--self-test','--environment','production']])
def test_qa_rejects_user_data_and_report_without_qa(args,monkeypatch):
    from drheeklab.app import main
    monkeypatch.setattr(sys,'argv',['drheeklab',*args])
    with pytest.raises(SystemExit) as error:main()
    assert error.value.code==2

def test_global_search_locates_all_seven_types_without_changes(system):
    store,d,products,product,variant,photo,project,photos=system
    sales=Sales(store);client=sales.save_client({'name':'BUSCA','phone':'12345'})
    quote=sales.create_quote(client,[{'variant_id':variant,'quantity':1,'unit_price':'30','fulfillment':'production'}],notes='BUSCA')
    sales.approve_quote(quote)
    production=Production(store)
    spool=production.catalog.save_filament({'brand':'BUSCA','material':'PLA','color':'Azul','name':'BUSCA','initial_grams':'100','remaining_grams':'100','purchase':'10','reference_per_g':'0.20'})
    production.create(1,60,[{'variant_id':variant,'project_id':project,'quantity':1,'filaments':[(spool,'10')]}],'BUSCA','0,2 mm')
    store.db.execute('UPDATE products SET name=?,description=? WHERE id=?',('BUSCA','Símbolo % literal',product))
    store.db.execute('UPDATE project_versions SET notes=? WHERE id=?',('BUSCA',project));store.db.commit()
    before=store.db.total_changes
    assert {r['kind'] for r in search(store,'busca')}=={'Cliente','Pedido','Orçamento','Produto','Projeto','Filamento','Produção'}
    assert search(store,'SÍMBOLO')[0]['kind']=='Produto'
    assert len(search(store,'%'))==1 and search(store,"' OR 1=1 --")==[]
    assert len(search(store,'busca',limit=2))==2 and search(store,' ')==[]
    assert search(store,'12345')[0]['id']==client
    assert store.db.total_changes==before

def test_search_archived_history_and_ui_navigation(system):
    store,d,products,product,variant,photo,project,photos=system
    store.db.execute('UPDATE products SET archived=1 WHERE id=?',(product,));store.db.commit()
    assert search(store,'Suporte')[0]['state']=='Arquivado'
    from drheeklab.ui import Window
    window=Window(store);dialog=SearchDialog(store,window);dialog.term.setText('Suporte');dialog.refresh()
    assert dialog.listing.rowCount()>0
    dialog.listing.selectRow(0);dialog.open_area()
    assert window.pages.currentIndex()==2
    window.close()

def test_about_contains_packaged_history_and_current_version(tmp_path):
    from drheeklab.ui import Window
    window=Window(Storage(tmp_path));seen=[]
    def inspect():
        dialog=QApplication.activeModalWidget()
        assert isinstance(dialog,QDialog)
        seen.append(dialog.findChild(QTextEdit).toPlainText());dialog.accept()
    QTimer.singleShot(0,inspect);window.about()
    assert __version__ in seen[0] and '2.0.0' in seen[0]
    assert files('drheeklab').joinpath('CHANGELOG.md').read_text(encoding='utf-8')
    window.close()

def test_home_is_clean_and_notes_preserved_in_about(tmp_path):
    from drheeklab.ui import Window
    from PySide6.QtWidgets import QScrollArea,QTabWidget,QLabel
    window=Window(Storage(tmp_path));window.resize(1100,700);window.show();QApplication.processEvents()
    home=window.pages.widget(0)
    assert isinstance(home,QScrollArea)
    assert window.notes not in home.findChildren(type(window.notes))
    assert window.logo.parentWidget() is window.sidebar
    assert not window.low_alert.isVisible()
    window.navigate(6)
    tabs=next(t for t in window.pages.widget(6).findChildren(QTabWidget) if any(t.tabText(i)=='Sobre' for i in range(t.count())))
    tabs.setCurrentIndex(next(i for i in range(tabs.count()) if tabs.tabText(i)=='Sobre'))
    QApplication.processEvents()
    assert window.notes.isVisible()
    window.notes.setPlainText('Histórico preservado em Sobre');window.save_draft()
    assert window.storage.load_draft('home_notes')=='Histórico preservado em Sobre'
    assert len(window.buttons)==7
    window.close()
