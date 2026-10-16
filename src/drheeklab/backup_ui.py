"""Explicit encryption choice and assisted least-privilege Windows scheduling."""
from PySide6.QtWidgets import QInputDialog, QLineEdit, QMessageBox, QLabel, QPushButton, QFileDialog, QDialogButtonBox
from .backup_crypto import is_encrypted,validate_password
from .phase2_ui import FormDialog
from .scheduler import install_task,remove_task,export_task

def ask_password(parent,confirm=False):
    password,ok=QInputDialog.getText(parent,'Senha de backup','Senha de criptografia (mínimo 12 caracteres). Pode ser diferente do login. Guarde separadamente; não há recuperação sem ela.',QLineEdit.Password)
    if not ok:return None,False
    validate_password(password)
    if confirm:
        repeated,ok=QInputDialog.getText(parent,'Confirmar senha de backup','Digite novamente. A senha não será salva no aplicativo.',QLineEdit.Password)
        if not ok:return None,False
        if password!=repeated:raise ValueError('Senhas de backup não conferem.')
    return password,True

def backup_password(path,parent=None):
    if not is_encrypted(path):return None,True
    return ask_password(parent)

def choose_encryption(parent):
    choice=QMessageBox.question(parent,'Proteção do backup','Criptografar este backup com senha?\nSim: AES-256-GCM; senha não é salva.\nNão: ZIP sem criptografia; proteja a pasta e o dispositivo.',QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel,QMessageBox.Yes)
    if choice==QMessageBox.Cancel:return None,False
    return ask_password(parent,confirm=True) if choice==QMessageBox.Yes else (None,True)

class ScheduleDialog(FormDialog):
    def __init__(self,storage,parent=None):
        super().__init__('Backup diário com aplicativo fechado',parent);self.storage=storage;self.resize(650,400)
        info=QLabel('Windows: tarefa do usuário atual, sem privilégios elevados, enquanto conectado. Executa diariamente e ao entrar no Windows; tenta novamente a cada hora.\nBackup agendado é ZIP NÃO criptografado; proteja a pasta/dispositivo. Para backup criptografado, use Criar backup completo. Senhas não são gravadas na tarefa.');info.setWordWrap(True);self.form.addRow(info)
        self.line('hour','Horário local do Windows (HH:MM)',(storage.get('backup_task') or {}).get('hour','18:00'))
        self.line('destination','Destino (vazio: Backups deste ambiente)',(storage.get('backup_task') or {}).get('destination') or '')
        select=QPushButton('Escolher pasta, pendrive ou HD');select.clicked.connect(self.select);self.form.addRow(select)
        export=QPushButton('Exportar XML para importar no Agendador de Tarefas');export.clicked.connect(self.export);self.form.addRow(export)
        remove=QPushButton('Remover somente a tarefa deste ambiente');remove.clicked.connect(self.remove);self.form.addRow(remove)
        self.findChild(QDialogButtonBox).button(QDialogButtonBox.Save).setText('Criar / atualizar tarefa')
    def select(self):
        path=QFileDialog.getExistingDirectory(self,'Destino de backup')
        if path:self.fields['destination'].setText(path)
    def persist(self):
        values=self.values();install_task(self.storage,values['hour'],values['destination'] or None)
    def export(self):
        path,_=QFileDialog.getSaveFileName(self,'Exportar tarefa assistida','DrHeekLab-backup.xml','Tarefa (*.xml)')
        if not path:return
        try:
            values=self.values();export_task(self.storage,path,values['hour'],values['destination'] or None)
            QMessageBox.information(self,'Configuração assistida','XML salvo. No Agendador de Tarefas, use Importar tarefa, confira usuário, horário, ambiente e destino. Use privilégios normais e não forneça senha de backup na tarefa.')
        except (ValueError,OSError) as error:QMessageBox.warning(self,'Agendamento',str(error))
    def remove(self):
        if QMessageBox.question(self,'Remover agendamento','Remover somente a tarefa deste ambiente? Backups e dados serão preservados.',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return
        try:remove_task(self.storage);self.accept()
        except ValueError as error:QMessageBox.warning(self,'Agendamento',str(error))
