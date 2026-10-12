"""Verified offline recovery even when current schema/media/database cannot open."""
from pathlib import Path
import sqlite3
import tempfile
from .backup import unpack_verified,create_backup,restore_backup
from .storage import Storage,FOLDERS,ENVIRONMENTS

class RecoveryTarget:
    def __init__(self,root,environment):
        if environment not in ENVIRONMENTS:raise ValueError('Ambiente inválido.')
        self.root=Path(root);self.environment=environment;self.home=self.root/ENVIRONMENTS[environment]
        for folder in FOLDERS:(self.home/folder).mkdir(parents=True,exist_ok=True)
        self.path=self.home/'Banco de Dados'/'drheeklab.sqlite3';self.db=sqlite3.connect(self.path)
    def close(self):self.db.close()
    def audit(self,*args,**kwargs):return Storage.audit(self,*args,**kwargs)

class RecoverySession:
    def __init__(self,backup,environment,*,password=None):
        self.environment=environment;self.original=Path(backup);self._temp=tempfile.TemporaryDirectory(prefix='drheek-recovery-');self.source=None
        try:
            root=Path(self._temp.name);home=root/ENVIRONMENTS[environment]
            home.mkdir();unpack_verified(self.original,home,environment,password=password)
            self.source=Storage(root,environment,migrate=False)
        except BaseException:self.close();raise
    def apply(self,root,*,confirmed=False):
        if confirmed is not True:raise ValueError('Confirmação explícita é obrigatória para restaurar.')
        # Login may have set a first password in the verified temporary copy.
        # Keep it in the restored database, without modifying the input ZIP.
        prepared=create_backup(self.source)
        target=RecoveryTarget(root,self.environment)
        try:return restore_backup(target,prepared)
        finally:target.close()
    def close(self):
        if self.source:self.source.close();self.source=None
        self._temp.cleanup()
    def __enter__(self):return self
    def __exit__(self,*args):self.close()


def run_recovery(root,environment,backup,parent=None):
    from PySide6.QtWidgets import QMessageBox
    from .ui import Login
    from .backup_ui import backup_password
    password,ok=backup_password(backup,parent)
    if not ok:return 0
    with RecoverySession(backup,environment,password=password) as session:
        dialog=Login(session.source);dialog.setWindowTitle('Recuperação • acesso ao backup verificado')
        if dialog.exec()!=Login.Accepted:return 0
        question=f'Restaurar {session.original.name} em {Path(root)/ENVIRONMENTS[environment]}?\nOs dados atuais serão substituídos e preservados em uma pasta de rollback. Use a senha do backup ao abrir novamente.'
        if QMessageBox.question(parent,'Confirmar recuperação',question,QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return 0
        rollback=session.apply(root,confirmed=True)
        QMessageBox.information(parent,'Recuperação concluída','Estado anterior preservado em:\n'+str(rollback)+'\nAbra o aplicativo novamente.');return 0
