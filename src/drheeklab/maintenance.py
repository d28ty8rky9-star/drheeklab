"""Headless backups/pre-update checks, protected by the same UI environment lock."""
import argparse
import json
from pathlib import Path
from datetime import datetime
import sys
from PySide6.QtCore import QLockFile,QCoreApplication
from .storage import Storage,ENVIRONMENTS
from .backup import create_backup,daily_backup
from . import __version__

def run_backup(root,environment,*,destination=None,daily=False,password=None):
    root=Path(root).resolve();home=root/ENVIRONMENTS[environment]
    # Never initialize an empty environment from a background job.
    if not (home/'Banco de Dados'/'drheeklab.sqlite3').is_file():
        raise ValueError('Ambiente ainda não criado; abra o aplicativo antes de agendar backup.')
    lock=QLockFile(str(root/('.'+environment+'.lock')))
    if not lock.tryLock(100):return {'status':'busy','environment':environment}
    storage=None
    try:
        storage=Storage(root,environment,migrate=False)
        today=datetime.now().date().isoformat()
        if daily and storage.get('last_daily_backup')==today:return {'status':'already-backed-up','environment':environment}
        path=create_backup(storage,destination,password=password)
        if daily:storage.set('last_daily_backup',today)
        return {'status':'passed','version':__version__,'environment':environment,'backup':str(path),'encrypted':password is not None}
    finally:
        if storage:storage.close()
        lock.unlock()

def log_result(root,environment,result):
    directory=Path(root)/ENVIRONMENTS[environment]/'Logs';directory.mkdir(parents=True,exist_ok=True)
    path=directory/('backup-job-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.json')
    path.write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')

def backup_main(root,environment,**options):
    try:
        result=run_backup(root,environment,**options)
        log_result(root,environment,result)
        return 0
    except Exception as error:
        try:log_result(root,environment,{'status':'failed','error':str(error),'type':type(error).__name__})
        except OSError:pass
        if sys.stderr is not None:print('Backup não concluído: '+str(error),file=sys.stderr)
        return 1

def prepare_update(root):
    results=[];locks=[];stores=[]
    try:
        for environment,folder in ENVIRONMENTS.items():
            if not (Path(root)/folder/'Banco de Dados'/'drheeklab.sqlite3').is_file():continue
            lock=QLockFile(str(Path(root)/('.'+environment+'.lock')))
            if not lock.tryLock(100):raise ValueError('Feche todas as instâncias antes de atualizar. Ambiente em uso: '+folder)
            locks.append(lock)
            storage=Storage(root,environment,migrate=False);stores.append(storage)
            version=storage.db.execute('PRAGMA user_version').fetchone()[0]
            results.append({'environment':environment,'schema':version,'backup':str(create_backup(storage))})
        return {'status':'passed','target_version':__version__,'environments':results,'data_preserved':True}
    finally:
        for storage in stores:storage.close()
        for lock in locks:lock.unlock()

def preflight_main():
    parser=argparse.ArgumentParser(description='Backup verificado antes de instalar/atualizar Dr. Heek Lab')
    parser.add_argument('--data-dir',type=Path,required=True);parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args();app=QCoreApplication.instance() or QCoreApplication([])
    args.report.unlink(missing_ok=True)
    try:
        result=prepare_update(args.data_dir)
        args.report.write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
        return 0
    except Exception as error:
        args.report.write_text(json.dumps({'status':'failed','error':str(error)},ensure_ascii=False),encoding='utf-8')
        return 1
