import argparse
import json
import logging
import os
from pathlib import Path
import sys
from PySide6.QtWidgets import QApplication, QMessageBox, QInputDialog, QFileDialog
from PySide6.QtCore import QLockFile
from .storage import Storage, ENVIRONMENTS
from .ui import Login, Window


def main():
    parser = argparse.ArgumentParser(description="Dr. Heek Lab — Fases 1–8")
    parser.add_argument("--environment", choices=ENVIRONMENTS)
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--self-test", action="store_true", help="Validar o pacote em dados temporários, sem abrir armazenamento do usuário")
    parser.add_argument("--self-test-report", type=Path, help="Salvar resultado JSON da verificação; exige --self-test")
    parser.add_argument("--restore-backup",type=Path,help="Recuperação verificada sem abrir a aplicação normal; exige senha e confirmação")
    parser.add_argument('--scheduled-backup',action='store_true',help='Backup diário sem interface; exige ambiente já criado')
    parser.add_argument('--backup-now',action='store_true',help='Backup imediato sem interface; exige ambiente já criado')
    parser.add_argument('--backup-destination',type=Path,help='Pasta de destino do backup sem interface')
    parser.add_argument('--backup-password-stdin',action='store_true',help='Ler senha de criptografia da entrada padrão, nunca dos argumentos')
    args = parser.parse_args()
    if args.self_test_report and not args.self_test:
        parser.error("--self-test-report exige --self-test")
    backup_mode=args.scheduled_backup or args.backup_now
    if backup_mode and (args.environment is None or args.self_test or args.restore_backup or (args.scheduled_backup and args.backup_now)):
        parser.error('Backup sem interface exige --environment e não pode ser combinado com recuperação/self-test ou outro modo de backup')
    if (args.backup_destination or args.backup_password_stdin) and not backup_mode:
        parser.error('Opções de backup exigem --backup-now ou --scheduled-backup')
    if args.scheduled_backup and args.backup_password_stdin:
        parser.error('Tarefa diária não pode aguardar senha interativa; use backup criptografado manual')
    if args.backup_password_stdin and sys.stdin is None:
        parser.error('Esta versão sem console não oferece entrada padrão; use backup criptografado pela interface')
    if backup_mode:
        from PySide6.QtCore import QCoreApplication
        from .maintenance import backup_main
        app=QCoreApplication.instance() or QCoreApplication(sys.argv[:1])
        root=args.data_dir or Path(os.environ.get('DRHEEKLAB_DATA_DIR') or (r'C:\DrHeekLab' if os.name=='nt' else str(Path.home()/'DrHeekLab')))
        password=sys.stdin.readline().rstrip('\r\n') if args.backup_password_stdin else None
        return backup_main(root,args.environment,destination=args.backup_destination,daily=args.scheduled_backup,password=password)
    if args.self_test and (args.environment is not None or args.data_dir is not None or args.restore_backup is not None):
        parser.error("--self-test usa somente dados temporários; não aceita --environment/--data-dir")
    if args.self_test:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if os.name == 'nt':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('DrHeekLab.Desktop')
    app = QApplication.instance() or QApplication(sys.argv[:1])
    from importlib.resources import files
    from PySide6.QtGui import QIcon
    icon_path = Path(str(files('drheeklab').joinpath('assets/drheeklab.ico')))
    if icon_path.is_file(): app.setWindowIcon(QIcon(str(icon_path)))
    if args.self_test:
        try:
            from .smoke import run
            result=run()
            if args.self_test_report:
                args.self_test_report.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
            if sys.stdout is not None: print(json.dumps(result, ensure_ascii=False))
            return 0
        except Exception as error:
            if args.self_test_report:
                try:
                    args.self_test_report.write_text(json.dumps({'status':'failed','error':str(error)}, ensure_ascii=False), encoding="utf-8")
                except OSError:
                    pass
            if sys.stderr is not None: print("Verificação do pacote falhou: " + str(error), file=sys.stderr)
            return 1
    app.setApplicationName("Dr. Heek Lab")
    app.setOrganizationName("Dr. Heek Lab")
    root = args.data_dir or Path(os.environ.get("DRHEEKLAB_DATA_DIR") or
                                  (r"C:\DrHeekLab" if os.name == "nt" else str(Path.home() / "DrHeekLab")))
    try:
        root.mkdir(parents=True, exist_ok=True)
        selector = root / "preferences.json"
        try:
            preference = json.loads(selector.read_text(encoding="utf-8")) if selector.exists() else {}
        except json.JSONDecodeError:
            preference = {}
        environment = args.environment
        if environment is None:
            items = list(ENVIRONMENTS.values())
            selected, ok = QInputDialog.getItem(None, "Escolher ambiente", "Bancos e arquivos fisicamente separados:", items,
                                                items.index(ENVIRONMENTS.get(preference.get("environment"), "TESTES")), False)
            if not ok:
                return 0
            environment = next(key for key, value in ENVIRONMENTS.items() if value == selected)
        instance_lock = QLockFile(str(root / ("." + environment + ".lock")))
        if not instance_lock.tryLock(100):
            QMessageBox.warning(None, "Ambiente em uso", "Este ambiente já está aberto em outra instância. Feche-a antes de continuar.")
            return 1
        if args.restore_backup:
            from .recovery import run_recovery
            return run_recovery(root,environment,args.restore_backup)
        storage = Storage(root, environment)
        temporary = selector.with_suffix(".tmp")
        temporary.write_text(json.dumps({"environment": environment}), encoding="utf-8")
        temporary.replace(selector)
        logging.basicConfig(filename=storage.home / "Logs" / "application.log", level=logging.INFO,
                            format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8")
    except Exception:
        prompt=QMessageBox();prompt.setIcon(QMessageBox.Critical);prompt.setWindowTitle('Erro ao abrir armazenamento')
        prompt.setText('Não foi possível abrir os dados. O banco original será preservado. Você pode selecionar um backup verificado para recuperação.')
        recover=prompt.addButton('Recuperar de backup',QMessageBox.ActionRole);prompt.addButton('Fechar',QMessageBox.RejectRole);prompt.exec()
        if prompt.clickedButton()==recover:
            filename,_=QFileDialog.getOpenFileName(None,'Selecionar backup completo',str(root),'Backup (*.zip *.hbk)')
            if filename:
                try:
                    if not locals().get('environment'):
                        selected,ok=QInputDialog.getItem(None,'Ambiente de recuperação','Escolha o mesmo ambiente do backup',list(ENVIRONMENTS.values()),0,False)
                        if not ok:return 0
                        environment=next(k for k,v in ENVIRONMENTS.items() if v==selected)
                    # If opening failed before acquiring the environment lock,
                    # acquire it now; never repair a running second instance.
                    if not locals().get('instance_lock'):
                        instance_lock=QLockFile(str(root/('.'+environment+'.lock')))
                        if not instance_lock.tryLock(100):raise ValueError('Ambiente em uso por outra instância.')
                    from .recovery import run_recovery
                    return run_recovery(root,environment,Path(filename))
                except Exception as error:QMessageBox.critical(None,'Recuperação não concluída',str(error)+'\nOs dados originais foram preservados.')
        return 1

    def handle_error(kind, value, traceback):
        logging.error("Erro não tratado", exc_info=(kind, value, traceback))
        QMessageBox.critical(None, "Operação não concluída", "Não foi possível concluir a operação. Confira os dados, espaço e permissões. Os detalhes técnicos estão na pasta Logs.")
    sys.excepthook = handle_error
    if Login(storage).exec() != Login.Accepted:
        storage.close()
        return 0
    window = Window(storage)
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
