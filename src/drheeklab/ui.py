from pathlib import Path
import os
import shutil
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QLineEdit, QDialog, QFormLayout, QMessageBox,
    QTextEdit, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QApplication, QScrollArea, QTabWidget)
from . import __version__
from .security import Auth
from .storage import ENVIRONMENTS
from .backup import create_backup, daily_backup, restore_backup
from .phase2_ui import CatalogPage, CalculatorPage, PricingDefaults
from .phase3_ui import ProductsPage, StockPage
from .phase4_ui import SalesPage
from .phase5_ui import ProductionPage
from .phase6_ui import FinancePage
from .phase7_ui import DocumentCenter,NotificationDialog
from .notifications import Notifications
from .sales import Sales

AREAS = ("Início", "Vendas", "Produção", "Produtos", "Estoque", "Financeiro", "Impressoras", "Configurações")
SYMBOLS = ("⌂", "$", "⚙", "◇", "▤", "↗", "▣", "☷")

class Login(QDialog):
    def __init__(self, storage):
        super().__init__()
        self.auth = Auth(storage)
        self.setWindowTitle("Dr. Heek Lab • Acesso")
        self.setMinimumWidth(390)
        box = QVBoxLayout(self)
        title = QLabel("DR. HEEK LAB 2.0")
        title.setStyleSheet("font-size:24px; font-weight:bold; color:#8757ef")
        box.addWidget(title)
        box.addWidget(QLabel("Ambiente: " + ENVIRONMENTS[storage.environment]))
        box.addWidget(QLabel("Digite sua senha." if self.auth.configured else "Primeiro acesso: cadastre sua senha (mínimo 8 caracteres)."))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Senha")
        box.addWidget(self.password)
        self.confirm = QLineEdit()
        self.confirm.setEchoMode(QLineEdit.Password)
        self.confirm.setPlaceholderText("Confirme a senha")
        if not self.auth.configured:
            box.addWidget(self.confirm)
        self.message = QLabel()
        self.message.setWordWrap(True)
        box.addWidget(self.message)
        enter = QPushButton("Entrar" if self.auth.configured else "Cadastrar e entrar")
        enter.clicked.connect(self.submit)
        self.password.returnPressed.connect(self.submit)
        self.confirm.returnPressed.connect(self.submit)
        box.addWidget(enter)

    def submit(self):
        try:
            if not self.auth.configured:
                if self.password.text() != self.confirm.text():
                    raise ValueError("As senhas não coincidem.")
                self.auth.create(self.password.text())
            elif not self.auth.verify(self.password.text()):
                raise ValueError("Senha incorreta.")
            with self.auth.storage.db:
                self.auth.storage.audit("login", "usuário principal")
            self.password.clear()
            self.confirm.clear()
            self.accept()
        except ValueError as error:
            self.message.setText(str(error))

class PasswordDialog(QDialog):
    def __init__(self, storage, parent):
        super().__init__(parent)
        self.setWindowTitle("Alterar senha")
        form = QFormLayout(self)
        self.fields = []
        for name in ("Senha atual", "Nova senha", "Confirmar nova senha"):
            field = QLineEdit()
            field.setEchoMode(QLineEdit.Password)
            form.addRow(name, field)
            self.fields.append(field)
        button = QPushButton("Salvar nova senha")
        form.addRow(button)
        button.clicked.connect(lambda: self.save(storage))

    def save(self, storage):
        try:
            old, new, confirmation = [f.text() for f in self.fields]
            if new != confirmation:
                raise ValueError("As novas senhas não coincidem.")
            Auth(storage).change(old, new)
            self.accept()
        except ValueError as error:
            QMessageBox.warning(self, "Verifique a senha", str(error))

class Window(QMainWindow):
    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self._closed = False
        self.theme = storage.get("theme", "dark")
        self.collapsed = storage.get("sidebar_collapsed", False)
        self.setWindowTitle(f"Dr. Heek Lab 2.0 • {ENVIRONMENTS[storage.environment]}")
        self.resize(1180, 800)
        self.setMinimumSize(780, 560)
        root = QWidget()
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        side = QVBoxLayout(self.sidebar)
        self.brand = QLabel("DR. HEEK\nLAB 2.0")
        self.brand.setObjectName("brand")
        side.addWidget(self.brand)
        collapse = QPushButton("☰")
        collapse.setAccessibleName("Recolher ou expandir menu")
        collapse.clicked.connect(self.toggle_sidebar)
        side.addWidget(collapse)
        self.buttons = []
        for index, area in enumerate(AREAS):
            button = QPushButton()
            button.setCheckable(True)
            button.setToolTip(area)
            button.setAccessibleName(area)
            button.clicked.connect(lambda checked=False, i=index: self.navigate(i))
            self.buttons.append(button)
            side.addWidget(button)
        side.addStretch()
        self.phase_label = QLabel("FASE 8\nValidação e finalização")
        side.addWidget(self.phase_label)
        outer.addWidget(self.sidebar)
        content = QVBoxLayout()
        content.setContentsMargins(28, 24, 28, 20)
        header = QHBoxLayout()
        self.page_title = QLabel("Início")
        self.page_title.setObjectName("title")
        header.addWidget(self.page_title)
        header.addStretch()
        environment = QLabel("● " + ENVIRONMENTS[storage.environment])
        environment.setStyleSheet("color:#28b8d9; font-weight:bold")
        header.addWidget(environment)
        theme_button = QPushButton("◐ Tema")
        theme_button.clicked.connect(self.toggle_theme)
        header.addWidget(theme_button)
        self.search_button = QPushButton('Buscar')
        self.search_button.clicked.connect(self.open_search)
        header.addWidget(self.search_button)
        self.notification_button=QPushButton("Notificações")
        self.notification_button.clicked.connect(self.open_notifications)
        header.addWidget(self.notification_button)
        content.addLayout(header)
        self.pages = QStackedWidget()
        self.pages.addWidget(self.home_page())
        self.calculator = CalculatorPage(storage)
        self.printers_page = CatalogPage(storage, 'printers')
        self.filaments_page = CatalogPage(storage, 'filaments')
        self.products_page = ProductsPage(storage)
        self.stock_page = StockPage(storage, self.filaments_page)
        self.sales_page = SalesPage(storage, self.calculator)
        self.production_page = ProductionPage(storage)
        self.finance_page = FinancePage(storage)
        for area in AREAS[1:-1]:
            if area == 'Vendas':
                self.pages.addWidget(self.sales_page)
            elif area == 'Produção':
                self.pages.addWidget(self.production_page)
            elif area == 'Estoque':
                self.pages.addWidget(self.stock_page)
            elif area == 'Produtos':
                self.pages.addWidget(self.products_page)
            elif area == 'Financeiro':
                self.pages.addWidget(self.finance_page)
            elif area == 'Impressoras':
                self.pages.addWidget(self.printers_page)
            else:
                self.pages.addWidget(self.pending_page(area))
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setWidget(self.settings_page())
        self.pages.addWidget(settings_scroll)
        content.addWidget(self.pages)
        content.addWidget(QLabel("Offline • Dados locais • v" + __version__ + " • Fase 8"))
        outer.addLayout(content, 1)
        self.render_sidebar()
        self.apply_theme()
        self.navigate(0)
        self.notification_timer=QTimer(self)
        self.notification_timer.setInterval(60000)
        self.notification_timer.timeout.connect(self.refresh_notifications)
        self.notification_timer.start()
        self.refresh_notifications()
        self.draft_timer = QTimer(self)
        self.draft_timer.setInterval(600)
        self.draft_timer.setSingleShot(True)
        self.draft_timer.timeout.connect(self.save_draft)
        self.notes.textChanged.connect(self.draft_timer.start)
        self.daily_timer = QTimer(self)
        self.daily_timer.setInterval(60 * 60 * 1000)
        self.daily_timer.timeout.connect(self.run_daily_backup)
        self.daily_timer.start()
        QTimer.singleShot(0, self.run_daily_backup)

    def home_page(self):
        page = QWidget()
        box = QVBoxLayout(page)
        heading = QLabel("Seu laboratório, organizado.")
        heading.setObjectName("hero")
        box.addWidget(heading)
        intro = QLabel("Clientes, orçamentos, pedidos, pagamentos e entregas disponíveis. Produção e inspeção individual disponíveis. Financeiro com caixa, contas e relatórios disponível. Documentos, catálogo, auditoria e lixeira em Configurações; alertas no botão Notificações.")
        intro.setWordWrap(True)
        box.addWidget(intro)
        self.low_alert = QLabel()
        self.low_alert.setWordWrap(True)
        box.addWidget(self.low_alert)
        self.business_summary = QLabel()
        self.business_summary.setWordWrap(True)
        box.addWidget(self.business_summary)
        sale_button = QPushButton("Nova venda")
        sale_button.clicked.connect(self.open_new_sale)
        box.addWidget(sale_button)
        production_button=QPushButton('Nova produção')
        production_button.clicked.connect(self.open_new_production)
        box.addWidget(production_button)
        price_button = QPushButton('Calcular preço')
        price_button.clicked.connect(self.open_calculator)
        box.addWidget(price_button)
        cards = QHBoxLayout()
        for title, detail in (("ACESSO PROTEGIDO", "Senha local com hash seguro"), ("DADOS ISOLADOS", ENVIRONMENTS[self.storage.environment]), ("BACKUP LOCAL", "Banco e arquivos vinculados")):
            card = QFrame()
            card.setMinimumHeight(100)
            card.setObjectName("card")
            layout = QVBoxLayout(card)
            layout.addWidget(QLabel(title))
            text = QLabel(detail)
            text.setWordWrap(True)
            layout.addWidget(text)
            cards.addWidget(card)
        box.addLayout(cards)
        self.logo = QLabel()
        self.logo.setAlignment(Qt.AlignCenter)
        self.logo.setMinimumHeight(120)
        self.update_logo()
        box.addWidget(self.logo)
        box.addWidget(QLabel("Anotações do laboratório • rascunho recuperado automaticamente"))
        self.notes = QTextEdit()
        self.notes.setMinimumHeight(110)
        self.notes.setPlaceholderText("Anote aqui suas informações. Salvamento automático após 0,6 segundo e ao fechar.")
        self.notes.setPlainText(self.storage.load_draft("home_notes"))
        box.addWidget(self.notes, 1)
        self.draft_status = QLabel("Rascunho carregado do ambiente ativo.")
        box.addWidget(self.draft_status)
        from .phase2_ui import scroll
        return scroll(page)

    def update_logo(self):
        path = self.storage.get("logo")
        full = self.storage.home / path if path else None
        pixmap = QPixmap(str(full)) if full and full.is_file() else QPixmap()
        if not pixmap.isNull():
            self.logo.setPixmap(pixmap.scaled(220, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo.setText("LOGOTIPO OFICIAL\nImporte a imagem original em Configurações → Marca.")
            self.logo.setObjectName("card")

    def pending_page(self, area):
        page = QWidget()
        box = QVBoxLayout(page)
        box.addStretch()
        title = QLabel(area + " • implementação pendente")
        title.setObjectName("hero")
        title.setWordWrap(True)
        box.addWidget(title)
        label = QLabel("Esta área está prevista no planejamento. Os fluxos desta área ainda não estão disponíveis. As Fases 1–8 estão disponíveis; o financeiro completo pertence à Fase 6.")
        label.setWordWrap(True)
        box.addWidget(label)
        box.addStretch()
        return page

    def settings_page(self):
        page = QWidget()
        box = QVBoxLayout(page)
        text = QLabel("Configurações do ambiente " + ENVIRONMENTS[self.storage.environment] + "\n" + str(self.storage.home))
        text.setWordWrap(True)
        box.addWidget(text)
        for label, handler in (("Abrir pasta de armazenamento", self.open_folder),
                               ("Alterar senha", lambda: PasswordDialog(self.storage, self).exec()),
                               ("Precificação e alerta de filamento", lambda: PricingDefaults(self.storage, self).exec()),
                               ("Configurar Bambu Studio (opcional)", self.configure_bambu),
                               ("Marca • importar logotipo oficial", self.import_logo),
                               ("Criar backup completo (local ou externo)", self.manual_backup),
                               ("Agendar backup diário no Windows", self.backup_schedule),
                               ("Restaurar backup deste ambiente", self.restore),
                               ("Documentos, catálogo, auditoria e lixeira", lambda: DocumentCenter(self.storage,self).exec()),
                               ("Consultar auditoria", self.show_audit),
                               ("Sobre o programa", self.about)):
            button = QPushButton(label)
            button.clicked.connect(handler)
            box.addWidget(button)
        label = QLabel("Para trocar de ambiente, encerre o aplicativo e selecione Testes ou Produção na próxima abertura. Cada ambiente possui senha, banco, arquivos e preferências próprios.")
        label.setWordWrap(True)
        box.addWidget(label)
        box.addStretch()
        return page

    def navigate(self, index):
        if index == 0:
            low = self.filaments_page.catalog.low_filaments()
            self.low_alert.setText('Filamento baixo: ' + (', '.join(row['name'] for row in low) if low else 'nenhum saldo conhecido abaixo do limite.'))
            from .phase4_ui import currency
            indicators=self.sales_page.sales.indicators()
            self.business_summary.setText('Vendas aprovadas no mês: '+currency(indicators['sold'])+' • Recebido líquido menos reembolsos no mês: '+currency(indicators['net_received'])+'\nA receber (todos os pedidos): '+currency(indicators['receivable'])+' • Pedidos em andamento: '+str(indicators['active_orders'])+' • Parcelas atrasadas: '+str(indicators['overdue_installments']))
        elif index == 1:
            self.calculator.refresh()
            self.sales_page.refresh()
        elif index == 2:
            self.production_page.refresh()
        elif index == 3:
            self.products_page.refresh()
        elif index == 4:
            self.stock_page.refresh()
        elif index == 5:
            self.finance_page.refresh()
        elif index == 6:
            self.printers_page.refresh()
        self.pages.setCurrentIndex(index)
        self.page_title.setText(AREAS[index])
        for i, button in enumerate(self.buttons):
            button.setChecked(i == index)

    def open_calculator(self):
        self.navigate(1)
        self.sales_page.tabs.setCurrentIndex(4)

    def open_new_sale(self):
        self.navigate(1)
        self.sales_page.tabs.setCurrentIndex(2)
        self.sales_page.order_new()

    def render_sidebar(self):
        self.sidebar.setFixedWidth(76 if self.collapsed else 216)
        self.brand.setText("HL" if self.collapsed else "DR. HEEK\nLAB 2.0")
        self.phase_label.setVisible(not self.collapsed)
        for i, button in enumerate(self.buttons):
            button.setText(SYMBOLS[i] if self.collapsed else SYMBOLS[i] + "   " + AREAS[i])

    def toggle_sidebar(self):
        self.collapsed = not self.collapsed
        self.storage.set("sidebar_collapsed", self.collapsed)
        self.render_sidebar()

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.storage.set("theme", self.theme)
        self.apply_theme()

    def apply_theme(self):
        dark = self.theme == "dark"
        bg, panel, fg, border = ("#10131f", "#1b2033", "#edf0fa", "#333c58") if dark else ("#f1f3fa", "#ffffff", "#20243a", "#d2d8e8")
        QApplication.instance().setStyleSheet(f"""
            QWidget {{ background:{bg}; color:{fg}; font-family:'Segoe UI'; font-size:14px; }}
            QFrame#sidebar, QFrame#sidebar QLabel {{ background:{panel}; }}
            QFrame#card {{ background:{panel}; border:1px solid {border}; border-radius:10px; padding:14px; }}
            QFrame#card QLabel {{ background:transparent; }}
            QLabel#brand {{ color:#a880ff; font-size:23px; font-weight:800; padding:16px 0; }}
            QLabel#title {{ font-size:26px; font-weight:700; }}
            QLabel#hero {{ font-size:28px; font-weight:700; padding:16px 0; }}
            QPushButton {{ background:{panel}; border:1px solid {border}; border-radius:7px; padding:11px; text-align:left; }}
            QPushButton:hover {{ border:1px solid #8e5ded; }}
            QPushButton:checked {{ background:#6d41c7; color:white; border-color:#a780f3; }}
            QLineEdit, QTextEdit, QTableWidget, QComboBox {{ background:{panel}; border:1px solid {border}; border-radius:6px; padding:8px; }}
            QHeaderView::section {{ background:{panel}; color:{fg}; padding:8px; }}
        """)

    def save_draft(self):
        self.storage.save_draft("home_notes", self.notes.toPlainText())
        self.draft_status.setText("Rascunho salvo automaticamente.")

    def run_daily_backup(self):
        if self._closed or getattr(self, "restored", False):
            return
        try:
            daily_backup(self.storage)
        except Exception:
            import logging
            logging.exception("Falha no backup diário")
            QMessageBox.warning(self, "Backup diário", "Não foi possível criar o backup. Confira espaço e permissão na pasta; consulte os logs.")

    def open_folder(self):
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.storage.home))):
            QMessageBox.information(self, "Pasta", str(self.storage.home))

    def configure_bambu(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Selecionar executável instalado do Bambu Studio', '', 'Executável (*.exe)' if os.name == 'nt' else 'Todos os arquivos (*)')
        if filename:
            self.storage.set('bambu_studio_path', filename)
            QMessageBox.information(self, 'Bambu Studio', 'Caminho salvo. Os parâmetros de fatiamento continuam sendo registrados manualmente no produto.')

    def import_logo(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Logotipo oficial", "", "Imagens (*.png *.jpg *.jpeg)")
        if not filename:
            return
        if QPixmap(filename).isNull():
            raise ValueError("Arquivo de imagem inválido.")
        import uuid
        target = self.storage.home / "Marca" / (uuid.uuid4().hex + Path(filename).suffix.lower())
        shutil.copy2(filename, target)
        self.storage.set("logo", target.relative_to(self.storage.home).as_posix())
        self.update_logo()

    def manual_backup(self):
        directory = QFileDialog.getExistingDirectory(self, "Destino do backup (pasta, pendrive ou HD)", str(self.storage.home / "Backups"))
        if directory:
            from .backup_ui import choose_encryption
            password,ok=choose_encryption(self)
            if not ok:return
            self.save_draft()
            self.calculator.save_draft()
            result = create_backup(self.storage, directory,password=password)
            QMessageBox.information(self, "Backup verificado", str(result))

    def restore(self):
        path, _ = QFileDialog.getOpenFileName(self, "Restaurar backup", str(self.storage.home / "Backups"), "Backup (*.zip *.hbk)")
        if not path:
            return
        from .backup_ui import backup_password
        from .backup import verify_backup
        try:
            password,ok=backup_password(path,self)
            if not ok:return
            verify_backup(path,self.storage.environment,password=password)
        except Exception as error:
            QMessageBox.warning(self,'Backup não validado',str(error));return
        if QMessageBox.question(self, "Confirmar restauração", "Substituir os dados do ambiente ativo? Um backup do estado atual será criado. O programa será encerrado; abra novamente e use a senha do backup.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        self.save_draft()
        self.calculator.save_draft()
        try:
            rollback = restore_backup(self.storage, path,password=password)
        except Exception:
            self.restored = True
            # Restoration may close the connection. Quit safely, preserving disk data.
            QMessageBox.critical(self, "Restauração não concluída", "Os dados anteriores foram preservados. Reinicie o programa e consulte os logs.")
            import logging
            logging.exception("Falha na restauração")
            self.restored = True
            self.close()
            return
        self.restored = True
        QMessageBox.information(self, "Restauração concluída", "Reabra o programa. Estado anterior preservado em:\n" + str(rollback))
        self.close()

    def refresh_notifications(self):
        if self._closed or getattr(self,'restored',False):return
        rows=Notifications(self.storage).refresh()
        self.notification_button.setText('Notificações ('+str(sum(not r['read'] and not r['snoozed'] for r in rows))+')')

    def open_notifications(self):
        NotificationDialog(self.storage,self).exec()
        self.refresh_notifications()

    def show_audit(self):
        from .phase7_ui import AuditPage
        dialog=QDialog(self);dialog.setWindowTitle('Auditoria');dialog.resize(1100,650)
        QVBoxLayout(dialog).addWidget(AuditPage(self.storage,dialog));dialog.exec()

    def about(self):
        from importlib.resources import files
        dialog=QDialog(self);dialog.setWindowTitle('Sobre Dr. Heek Lab');dialog.resize(800,600)
        box=QVBoxLayout(dialog)
        box.addWidget(QLabel('Dr. Heek Lab '+__version__+' • Fases 1–8\nAplicativo offline; não é sistema fiscal nem certificação ISO.\nCandidato à homologação: instalador Windows e ícone oficial pendentes.'))
        history=QTextEdit();history.setReadOnly(True);history.setMarkdown(files('drheeklab').joinpath('CHANGELOG.md').read_text(encoding='utf-8'));box.addWidget(history)
        close=QPushButton('Fechar');close.clicked.connect(dialog.accept);box.addWidget(close);dialog.exec()

    def open_search(self):
        from .search import SearchDialog
        SearchDialog(self.storage,self).exec()

    def open_new_production(self):
        from .phase5_ui import OrderDialog
        self.navigate(2)
        self.production_page.dialog(OrderDialog(self.production_page.production,self.production_page))

    def backup_schedule(self):
        from .backup_ui import ScheduleDialog
        ScheduleDialog(self.storage,self).exec()

    def closeEvent(self, event):
        self.draft_timer.stop()
        self.calculator.timer.stop()
        self.production_page.timer.stop()
        self.daily_timer.stop()
        self.notification_timer.stop()
        if not getattr(self, "restored", False):
            try:
                self.save_draft()
                self.calculator.save_draft()
                self.storage.close()
            except Exception:
                event.ignore()
                raise
        self._closed = True
        event.accept()
