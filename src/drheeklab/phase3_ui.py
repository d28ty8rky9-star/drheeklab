"""Operational desktop product gallery and physical stock management."""
from datetime import datetime, date
from decimal import Decimal
import json
import uuid
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QListWidget, QListWidgetItem, QListView, QTabWidget,
    QFileDialog, QMessageBox, QDialog, QInputDialog, QTableWidget, QTextEdit)
from .catalog import Catalog
from .products import Products, CATEGORIES
from .inventory import Inventory, PIECE_STATES
from .pricing import brl
from .phase2_ui import FormDialog, button, table, fill_table, scroll, date_br, date_iso, decimal_cents, grams


def money_optional(value):
    return '' if value is None else decimal_cents(value)


def selection_combo(dialog, key, label, rows, value, display):
    choices = {None: 'Sem recomendação / vínculo'}
    choices.update({row['id']: display(row) for row in rows})
    return dialog.combo(key, label, choices, value)


class ProductDialog(FormDialog):
    def __init__(self, products, identifier=None, parent=None):
        super().__init__('Editar produto' if identifier else 'Novo produto • código automático', parent)
        self.products, self.identifier = products, identifier
        row = products.get('products', identifier) if identifier is not None else {}
        self.line('name', 'Nome *', row.get('name', ''))
        self.line('description', 'Descrição', row.get('description', ''))
        self.combo('category', 'Categoria', CATEGORIES, row.get('category', 'decorative'))
        catalog = Catalog(products.storage)
        printers = catalog.rows('printers') + [r for r in catalog.rows('printers', True) if r['id'] == row.get('printer_id')]
        filaments = catalog.rows('filaments') + [r for r in catalog.rows('filaments', True) if r['id'] == row.get('filament_id')]
        selection_combo(self, 'printer_id', 'Impressora recomendada', printers, row.get('printer_id'), lambda r: r['identifier'] + ' • ' + r['model'])
        selection_combo(self, 'filament_id', 'Filamento recomendado', filaments, row.get('filament_id'), lambda r: r['name'] + ' • ' + r['material'])
        self.line('settings', 'Configurações recomendadas', row.get('settings', ''), 'Dados manuais do fatiamento: camada, suportes, preenchimento…')
        self.line('estimated_minutes', 'Tempo estimado (minutos)', row.get('estimated_minutes', 0))
        self.line('planned_cost', 'Custo previsto por peça (R$)', money_optional(row.get('planned_cost_cents')), 'Vazio: não informado')
        self.line('suggested_price', 'Preço sugerido por peça (R$)', money_optional(row.get('suggested_price_cents')), 'Vazio: não informado')
        self.line('quality_notes', 'Observações de qualidade', row.get('quality_notes', ''))

    def persist(self):
        self.saved_id = self.products.save(self.values(), self.identifier)


class VariantDialog(FormDialog):
    def __init__(self, products, product_id, identifier=None, parent=None):
        super().__init__('Editar variante' if identifier else 'Nova variante', parent)
        self.products, self.product_id, self.identifier = products, product_id, identifier
        row = products.get('variants', identifier) if identifier is not None else {}
        for key, label in (('name', 'Nome *'), ('size', 'Tamanho'), ('color', 'Cor'), ('material', 'Material')):
            self.line(key, label, row.get(key, ''))
        self.line('planned_cost', 'Custo próprio por peça (R$)', money_optional(row.get('planned_cost_cents')), 'Vazio: herdar do produto')
        self.line('suggested_price', 'Preço próprio por peça (R$)', money_optional(row.get('suggested_price_cents')), 'Vazio: herdar do produto')
        choices = {None: 'Manual / herdar do produto'}
        choices.update({r['id']: f"#{r['id']} • {r['title']}" for r in Catalog(products.storage).calculations()})
        combo = self.combo('calculation_id', 'Copiar valores unitários do cálculo', choices, row.get('calculation_id'))
        combo.currentIndexChanged.connect(self.toggle_costs)
        self.toggle_costs()
        self.form.addRow(QLabel('Vínculo com cálculo copia valores e guarda snapshot; não recalcula históricos.'))

    def toggle_costs(self):
        manual = self.fields['calculation_id'].currentData() is None
        self.fields['planned_cost'].setEnabled(manual)
        self.fields['suggested_price'].setEnabled(manual)

    def persist(self):
        self.saved_id = self.products.save_variant(self.product_id, self.values(), self.identifier)


class ProductsPage(QWidget):
    def __init__(self, storage):
        super().__init__()
        self.products = Products(storage)
        box = QVBoxLayout(self)
        controls = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText('Buscar código, nome, descrição, tamanho, cor ou material…')
        self.search.textChanged.connect(self.refresh)
        controls.addWidget(self.search, 1)
        self.category = QComboBox()
        self.category.addItem('Todas as categorias', None)
        for code, label in CATEGORIES.items():
            self.category.addItem(label, code)
        self.category.currentIndexChanged.connect(self.refresh)
        controls.addWidget(self.category)
        self.trash = QCheckBox('Lixeira')
        self.trash.toggled.connect(self.refresh)
        controls.addWidget(self.trash)
        box.addLayout(controls)
        actions = QHBoxLayout()
        button('Novo produto', self.new, actions)
        button('Editar produto', self.edit, actions)
        button('Arquivar / restaurar', self.archive, actions)
        box.addLayout(actions)
        self.gallery = QListWidget()
        self.gallery.setViewMode(QListView.IconMode)
        self.gallery.setResizeMode(QListView.Adjust)
        self.gallery.setMovement(QListView.Static)
        self.gallery.setIconSize(QSize(140, 100))
        self.gallery.setGridSize(QSize(205, 165))
        self.gallery.setWordWrap(True)
        self.gallery.setMinimumHeight(180)
        self.gallery.itemSelectionChanged.connect(self.show_selection)
        box.addWidget(self.gallery, 1)
        self.info = QLabel('Nenhum produto selecionado. Cadastre modelos e importe suas fotos reais.')
        self.info.setWordWrap(True)
        box.addWidget(self.info)
        self.tabs = QTabWidget()
        box.addWidget(self.tabs, 1)
        self.variant_trash = QCheckBox('Variantes arquivadas')
        self.variant_trash.toggled.connect(self.show_selection)
        self.variants_table = table(['ID', 'Variante', 'Tamanho', 'Cor / material', 'Custo', 'Preço sugerido', 'Cálculo'])
        variants = QWidget(); vb = QVBoxLayout(variants)
        vb.addWidget(self.variant_trash); vb.addWidget(self.variants_table)
        row = QHBoxLayout()
        button('Nova variante', self.variant_new, row)
        button('Editar variante', self.variant_edit, row)
        button('Arquivar / restaurar variante', self.variant_archive, row)
        vb.addLayout(row); self.tabs.addTab(variants, 'Variantes')
        self.photo_table = table(['ID', 'Arquivo original', 'Principal', 'Importado'])
        self.project_table = table(['ID', 'Versão', 'Arquivo original', 'Preferencial', 'Observações'])
        for kind, listing, label in (('photo', self.photo_table, 'Fotos'), ('project', self.project_table, 'STL / 3MF')):
            widget = QWidget(); layout = QVBoxLayout(widget); layout.addWidget(listing)
            row = QHBoxLayout()
            button('Importar foto' if kind == 'photo' else 'Importar nova versão', lambda checked=False, k=kind: self.import_file(k), row)
            button('Definir principal' if kind == 'photo' else 'Definir preferencial', lambda checked=False, k=kind: self.prefer(k), row)
            button('Abrir foto' if kind == 'photo' else 'Abrir no Bambu Studio', lambda checked=False, k=kind: self.open_file(k), row)
            layout.addLayout(row)
            self.tabs.addTab(widget, label)
        self.problem_table = table(['OP', 'Tipo', 'Descrição', 'Responsável', 'Registrado'])
        self.tabs.addTab(self.problem_table, 'Problemas de produção')
        self.refresh()

    def selected_product(self, warn=True):
        item = self.gallery.currentItem()
        if item is None:
            if warn:
                QMessageBox.information(self, 'Selecione um produto', 'Selecione um modelo na galeria.')
            return None
        return item.data(Qt.UserRole)

    def refresh(self, *args):
        selected = self.selected_product(False)
        self.gallery.blockSignals(True)
        self.gallery.clear()
        rows = self.products.search(self.search.text(), self.category.currentData(), self.trash.isChecked())
        for product in rows:
            price = 'Preço não informado' if product['suggested_price_cents'] is None else brl(Decimal(product['suggested_price_cents']) / 100)
            photos = self.products.media(product['id'], 'photo')
            photo = next((p for p in photos if p['is_primary']), None)
            item = QListWidgetItem(f"{product['code']} • {product['name']}\n{CATEGORIES.get(product['category'], product['category'])} • {price}" + ('\nSem foto principal' if not photo else ''))
            if photo:
                try:
                    item.setIcon(QIcon(str(self.products.media_path(photo['id'], 'photo', verify=False))))
                except ValueError:
                    item.setText(item.text() + '\nFoto ausente')
            item.setData(Qt.UserRole, product['id'])
            self.gallery.addItem(item)
            if product['id'] == selected:
                self.gallery.setCurrentItem(item)
        self.gallery.blockSignals(False)
        self.show_selection()

    def select_product(self, identifier):
        for index in range(self.gallery.count()):
            item = self.gallery.item(index)
            if item.data(Qt.UserRole) == identifier:
                self.gallery.setCurrentItem(item)
                self.show_selection()
                return

    def show_selection(self, *args):
        identifier = self.selected_product(False)
        if identifier is None:
            self.info.setText('Nenhum produto selecionado. Fotos, arquivos e variantes são armazenados localmente.')
            self.variant_rows, self.photo_rows, self.project_rows = [], [], []
        else:
            product = self.products.get('products', identifier)
            self.info.setText(f"{product['code']} • {product['name']} • {CATEGORIES[product['category']]}\n{product['description']}\nConfigurações: {product['settings']} • {product['estimated_minutes']} min\nQualidade: {product['quality_notes']}")
            self.variant_rows = self.products.variants(identifier, self.variant_trash.isChecked())
            self.photo_rows = self.products.media(identifier, 'photo')
            self.project_rows = self.products.media(identifier, 'project')
        from .production import Production
        problems=Production(self.products.storage).problems(identifier) if identifier is not None else []
        fill_table(self.problem_table, [[r['code'],r['kind'],r['description'],r['responsible'],r['created_at'][:19]] for r in problems])
        fill_table(self.variants_table, [[r['id'], r['name'], r['size'], r['color'] + ' / ' + r['material'],
            self.variant_money(r, 'planned_cost_cents'),
            self.variant_money(r, 'suggested_price_cents'), r['calculation_id'] or '—'] for r in self.variant_rows])
        fill_table(self.photo_table, [[r['id'], r['original_name'], 'Sim' if r['is_primary'] else 'Não', datetime.fromisoformat(r['created_at']).astimezone().strftime('%d/%m/%Y')] for r in self.photo_rows])
        fill_table(self.project_table, [[r['id'], r['version'], r['original_name'], 'Sim' if r['is_preferred'] else 'Não', r['notes']] for r in self.project_rows])

    def variant_money(self, row, key):
        if row[key] is not None:
            return brl(Decimal(row[key]) / 100)
        product = self.products.get('products', row['product_id'])
        return 'Não informado' if product[key] is None else brl(Decimal(product[key]) / 100) + ' (produto)'

    def new(self):
        dialog = ProductDialog(self.products, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.search.clear(); self.category.setCurrentIndex(0); self.trash.setChecked(False)
            self.refresh(); self.select_product(dialog.saved_id)

    def edit(self):
        identifier = self.selected_product()
        if identifier is not None:
            if self.trash.isChecked():
                QMessageBox.information(self, 'Produto arquivado', 'Restaure antes de editar.'); return
            if ProductDialog(self.products, identifier, self).exec() == QDialog.Accepted:
                self.refresh()

    def archive(self):
        identifier = self.selected_product()
        if identifier is not None:
            self.archive_record('products', identifier, not self.trash.isChecked())

    def archive_record(self, kind, identifier, archived):
        reason, ok = QInputDialog.getText(self, 'Arquivar / restaurar', 'Justificativa obrigatória:')
        if not ok:
            return
        if QMessageBox.question(self, 'Confirmar', 'Confirmar alteração? Arquivos e histórico serão preservados.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        try:
            self.products.archive(kind, identifier, archived, reason)
            self.refresh()
        except ValueError as error:
            QMessageBox.warning(self, 'Verifique os dados', str(error))

    def selected_variant(self):
        row = self.variants_table.currentRow()
        if row < 0:
            QMessageBox.information(self, 'Selecione uma variante', 'Selecione uma linha na tabela.'); return None
        return self.variant_rows[row]['id']

    def variant_new(self):
        product = self.selected_product()
        if product is not None and VariantDialog(self.products, product, parent=self).exec() == QDialog.Accepted:
            self.show_selection()

    def variant_edit(self):
        product = self.selected_product()
        if product is None:
            return
        variant = self.selected_variant()
        if variant is not None and VariantDialog(self.products, product, variant, self).exec() == QDialog.Accepted:
            self.show_selection()

    def variant_archive(self):
        variant = self.selected_variant()
        if variant is not None:
            self.archive_record('variants', variant, not self.variant_trash.isChecked())

    def import_file(self, kind):
        product = self.selected_product()
        if product is None:
            return
        path, _ = QFileDialog.getOpenFileName(self, 'Importar arquivo original', '', 'Fotos (*.png *.jpg *.jpeg)' if kind == 'photo' else 'Projetos (*.stl *.3mf)')
        if not path:
            return
        notes = ''
        if kind == 'project':
            notes, ok = QInputDialog.getText(self, 'Notas da versão', 'Observações (opcional); parâmetros devem ser informados manualmente:')
            if not ok:
                return
        try:
            self.products.import_media(product, path, kind, notes)
            self.refresh()
        except (ValueError, OSError) as error:
            QMessageBox.warning(self, 'Não foi possível importar', str(error))

    def chosen_media(self, kind):
        listing, rows = (self.photo_table, self.photo_rows) if kind == 'photo' else (self.project_table, self.project_rows)
        index = listing.currentRow()
        if index < 0:
            QMessageBox.information(self, 'Selecione um arquivo', 'Selecione uma linha na tabela.'); return None
        return rows[index]['id']

    def prefer(self, kind):
        product, identifier = self.selected_product(), self.chosen_media(kind)
        if product is not None and identifier is not None:
            try:
                self.products.choose_media(product, identifier, kind); self.refresh()
            except ValueError as error:
                QMessageBox.warning(self, 'Verifique os dados', str(error))

    def open_file(self, kind):
        identifier = self.chosen_media(kind)
        if identifier is None:
            return
        try:
            if kind == 'project':
                self.products.open_project(identifier)
            elif not QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.products.media_path(identifier, 'photo')))):
                raise ValueError('Nenhum visualizador de fotos foi encontrado neste sistema.')
        except (ValueError, OSError) as error:
            QMessageBox.warning(self, 'Abrir arquivo', str(error))


class MaterialDialog(FormDialog):
    def __init__(self, inventory, identifier=None, parent=None):
        super().__init__('Material auxiliar • saldo e referência', parent)
        self.inventory, self.identifier = inventory, identifier
        row = inventory.get('materials', identifier) if identifier else {}
        self.line('name', 'Nome *', row.get('name', ''))
        self.line('unit', 'Unidade *', row.get('unit', 'unidade'), 'unidade, g, mL…')
        self.line('balance', 'Saldo físico', grams(row.get('balance_milli', 0)))
        self.line('reference_per_unit', 'Referência (R$/unidade)', row.get('reference_per_unit', '0'))
        self.line('reason', 'Justificativa *', '', 'Origem da entrada ou motivo do ajuste de saldo')

    def persist(self):
        values = self.values()
        self.saved_id = self.inventory.save_material(values, self.identifier, values.pop('reason'))


class ReceiptDialog(FormDialog):
    def __init__(self, inventory, parent=None):
        super().__init__('Entrada de peças físicas • não registra venda', parent)
        self.inventory = inventory
        self.operation_key = uuid.uuid4().hex
        choices = {r['id']: r['code'] + ' • ' + r['product_name'] + ' / ' + r['name'] for r in inventory.products.all_variants()}
        self.combo('variant_id', 'Produto / variante *', choices, next(iter(choices), None))
        calcs = {None: 'Entrada manual (peças já existentes)'}
        for row in Catalog(inventory.storage).calculations():
            if row['actual'] and not inventory.db.execute('SELECT 1 FROM receipts WHERE calculation_id=?', (row['id'],)).fetchone():
                calcs[row['id']] = f"#{row['id']} • {row['title']} (custo confirmado)"
        self.combo('calculation_id', 'Produção para estoque', calcs, None)
        self.line('quantity', 'Quantidade de peças', '1')
        self.line('total_cost', 'Custo TOTAL existente (R$)', '0')
        self.line('source', 'Origem e justificativa *', '', 'Produção para estoque, cadastro inicial ou ajuste documentado')
        self.combo('state', 'Destino inicial', {'quarantine': 'Aguardando verificação', 'personal': 'Uso pessoal', 'available': 'Disponível (verificação prévia registrada)'}, 'quarantine')
        self.line('condition', 'Condição física *', '', 'Registre a condição real das peças')
        self.line('reviewer', 'Responsável pela verificação', '', 'Obrigatório para entrada disponível')
        self.checked = QCheckBox('Confirmo a verificação prévia de cada peça quando marcar disponível')
        self.form.addRow(self.checked)
        self.fields['calculation_id'].currentIndexChanged.connect(self.load_calculation)
        self.form.addRow(QLabel('Não há nova baixa de filamento. Custo existente é rateado sem duplicação.\nPeças vinculadas a OP exigem inspeção formal com três fotos em Produção.'))

    def load_calculation(self):
        identifier = self.fields['calculation_id'].currentData()
        manual = identifier is None
        self.fields['quantity'].setEnabled(manual); self.fields['total_cost'].setEnabled(manual)
        if identifier is not None:
            actual = json.loads(Catalog(self.inventory.storage).get('calculations', identifier)['actual'])
            self.fields['quantity'].setText(str(actual['quantity']))
            self.fields['total_cost'].setText(actual.get('acquisition_production_cost') or actual['total_cost'])

    def persist(self):
        values = self.values()
        if values['variant_id'] is None:
            raise ValueError('Cadastre um produto e uma variante primeiro.')
        if values['state'] == 'available' and not self.checked.isChecked():
            raise ValueError('Confirme a verificação prévia das peças ou use Aguardando verificação.')
        self.receipt_id, self.piece_ids = self.inventory.receive(**values, operation_key=self.operation_key)


class ReserveDialog(FormDialog):
    def __init__(self, inventory, variant_id, parent=None):
        super().__init__('Reservar peças disponíveis', parent)
        self.inventory, self.variant_id = inventory, variant_id
        self.operation_key = uuid.uuid4().hex
        self.line('quantity', 'Quantidade', '1')
        self.line('reference', 'Referência da reserva *', '', 'Referência para futuro pedido; não cria um pedido nesta fase')

    def persist(self):
        values = self.values()
        self.saved_id = self.inventory.reserve(self.variant_id, values['quantity'], values['reference'], self.operation_key)


class ReviewDialog(FormDialog):
    def __init__(self, inventory, ids, parent=None):
        super().__init__('Verificar condição das peças • registro preliminar', parent)
        self.inventory, self.ids = inventory, ids
        self.combo('result', 'Resultado', {'approved': 'Aprovadas para disponibilidade', 'rejected': 'Rejeitadas / manter indisponíveis'}, 'approved')
        self.line('condition', 'Condição / observações *')
        self.line('reviewer', 'Responsável *')
        self.form.addRow(QLabel('Peças de uso pessoal exigem nova verificação antes de ficarem disponíveis.\nEsta é a verificação manual da Fase 3; não é a inspeção formal da Fase 5.'))

    def persist(self):
        self.inventory.review(self.ids, **self.values())


class LossDialog(FormDialog):
    def __init__(self, inventory, entity, identifier, parent=None):
        super().__init__('Registrar perda / descarte • não lança nova despesa em caixa', parent)
        self.inventory, self.entity, self.identifier = inventory, entity, identifier
        self.operation_key = uuid.uuid4().hex
        if entity != 'piece':
            unit = 'g' if entity == 'filament' else inventory.get('materials', identifier)['unit']
            self.line('quantity', 'Quantidade (' + unit + ')', '1')
        self.line('reason', 'Motivo *')
        self.line('occurred_on', 'Data *', date.today().strftime('%d/%m/%Y'))
        self.line('notes', 'Observações')

    def persist(self):
        values = self.values(); values['occurred_on'] = date_iso(values['occurred_on'])
        if not values['occurred_on']:
            raise ValueError('Informe a data do descarte.')
        if QMessageBox.question(self, 'Confirmar descarte', 'Confirmar descarte? Esta perda será preservada no histórico. A mesma peça não poderá ser descartada novamente.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            raise ValueError('Descarte cancelado.')
        if self.entity == 'piece':
            self.saved_id = self.inventory.discard_pieces(self.identifier, **values, operation_key=self.operation_key)
        else:
            self.saved_id = self.inventory.discard_material(self.entity, self.identifier, **values, operation_key=self.operation_key)


class ConsumeMaterialDialog(FormDialog):
    def __init__(self, inventory, identifier, parent=None):
        super().__init__('Consumo de material auxiliar', parent)
        self.inventory, self.identifier = inventory, identifier
        self.operation_key = uuid.uuid4().hex
        self.line('quantity', 'Quantidade consumida', '1')
        self.line('reason', 'Justificativa / destino *')

    def persist(self):
        values = self.values()
        self.inventory.consume_material(self.identifier, **values, operation_key=self.operation_key)


class StockPage(QWidget):
    def __init__(self, storage, filaments_page):
        super().__init__()
        self.inventory = Inventory(storage)
        self.filaments_page = filaments_page
        box = QVBoxLayout(self)
        self.tabs = QTabWidget(); box.addWidget(self.tabs)
        filament_wrapper = QWidget(); fw = QVBoxLayout(filament_wrapper)
        fw.addWidget(filaments_page)
        button('Registrar perda de filamento', self.filament_loss, fw)
        self.tabs.addTab(filament_wrapper, 'Filamentos')
        materials = QWidget(); mb = QVBoxLayout(materials)
        controls = QHBoxLayout()
        button('Novo material', self.material_new, controls); button('Editar / ajustar', self.material_edit, controls)
        button('Consumir', self.material_consume, controls); button('Registrar perda', self.material_loss, controls)
        button('Arquivar / restaurar', self.material_archive, controls)
        self.material_trash = QCheckBox('Lixeira'); self.material_trash.toggled.connect(self.refresh)
        controls.addWidget(self.material_trash); mb.addLayout(controls)
        self.material_table = table(['ID', 'Material', 'Unidade', 'Saldo', 'Referência R$/unidade']); mb.addWidget(self.material_table)
        self.tabs.addTab(materials, 'Auxiliares')
        summary = QWidget(); sb = QVBoxLayout(summary)
        self.stock_table = table(['Variante ID', 'Produto / variante', 'Físico', 'Reservado', 'Disponível', 'Uso pessoal', 'A verificar', 'Descartado'])
        sb.addWidget(self.stock_table)
        controls = QHBoxLayout(); button('Entrada manual / produção para estoque', self.receive, controls)
        button('Reservar disponíveis', self.reserve, controls); sb.addLayout(controls)
        label = QLabel('Reservar não reduz estoque físico. Baixa de reserva e descarte usam o custo já atribuído; não registram venda ou caixa.')
        label.setWordWrap(True); sb.addWidget(label)
        self.tabs.addTab(summary, 'Peças prontas')
        physical = QWidget(); pb = QVBoxLayout(physical)
        self.pieces_table = table(['ID peça', 'Produto / variante', 'Estado', 'Condição', 'Custo atribuído', 'Entrada', 'Reserva'])
        self.pieces_table.setSelectionMode(QTableWidget.ExtendedSelection); pb.addWidget(self.pieces_table)
        controls = QHBoxLayout(); button('Verificar / liberar selecionadas', self.review, controls)
        button('Descartar selecionadas', self.piece_loss, controls); pb.addLayout(controls)
        self.tabs.addTab(physical, 'Peças físicas')
        reservations = QWidget(); rb = QVBoxLayout(reservations)
        self.reservations_table = table(['ID', 'Referência', 'Produto / variante', 'Quantidade', 'Situação']); rb.addWidget(self.reservations_table)
        controls = QHBoxLayout(); button('Liberar reserva', lambda: self.finish_reservation('release'), controls)
        button('Baixar peças reservadas', lambda: self.finish_reservation('issue'), controls); rb.addLayout(controls)
        self.tabs.addTab(reservations, 'Reservas')
        logs = QWidget(); lb = QVBoxLayout(logs)
        self.movements_table = table(['Data / hora', 'Tipo', 'Item', 'Quantidade (+/−)', 'Anterior', 'Novo', 'Justificativa']); lb.addWidget(self.movements_table)
        self.tabs.addTab(logs, 'Movimentos')
        losses = QWidget(); ls = QVBoxLayout(losses)
        self.losses_table = table(['ID', 'Data', 'Tipo', 'Quantidade', 'Custo existente', 'Valoração', 'Motivo', 'Observações']); ls.addWidget(self.losses_table)
        self.tabs.addTab(losses, 'Perdas')
        self.refresh()

    def refresh(self, *args):
        self.filaments_page.refresh()
        self.material_rows = self.inventory.materials(self.material_trash.isChecked())
        fill_table(self.material_table, [[r['id'],r['name'],r['unit'],grams(r['balance_milli']),r['reference_per_unit']] for r in self.material_rows])
        self.stock_rows = self.inventory.summary()
        fill_table(self.stock_table, [[r['id'],r['code']+' • '+r['product_name']+' / '+r['name']+(' (arquivado)' if r['archived'] or r['product_archived'] else ''),r['physical'],r['reserved'],r['available'],r['personal'],r['quarantine'],r['discarded']] for r in self.stock_rows])
        self.piece_rows = self.inventory.pieces()
        fill_table(self.pieces_table, [[r['id'],r['code']+' / '+r['variant_name'],PIECE_STATES[r['state']],r['condition'],brl(Decimal(r['unit_cost_cents'])/100),r['receipt_id'],r['reservation_id'] or '—'] for r in self.piece_rows])
        self.reservation_rows = self.inventory.reservations()
        names = {'reserved':'Reservada','released':'Liberada','issued':'Baixada'}
        fill_table(self.reservations_table, [[r['id'],r['reference'],r['code']+' / '+r['variant_name'],r['quantity'],names[r['state']]] for r in self.reservation_rows])
        moves = self.inventory.movements()
        kinds = {'opening':'Saldo inicial','adjustment':'Ajuste','consumption':'Consumo','receipt':'Entrada','reservation':'Reserva','release':'Liberação','issue':'Baixa','discard':'Descarte','review':'Verificação','return':'Retorno físico'}
        fill_table(self.movements_table, [self.movement_values(r, kinds) for r in moves])
        fill_table(self.losses_table, [[r['id'],date_br(r['occurred_on']),{'piece':'Peças','filament':'Filamento','material':'Material'}[r['entity_kind']],grams(r['quantity_milli'])+' '+r['unit'],brl(Decimal(r['cost_cents'])/100),{'acquisition':'Aquisição','reference':'Referência','existing_piece_cost':'Custo já atribuído'}.get(r['cost_basis'],r['cost_basis']),r['reason'],r['notes']] for r in self.inventory.losses()])

    def movement_values(self, row, kinds):
        if row['piece_id'] is not None:
            name, unit = 'Peça #' + str(row['piece_id']), 'peça'
            before, after = json.loads(row['previous']), json.loads(row['current'])
            previous = PIECE_STATES.get(before, 'Sem entrada')
            current = PIECE_STATES.get(after, 'Sem entrada')
        else:
            if row['filament_id'] is not None:
                item = Catalog(self.inventory.storage).get('filaments', row['filament_id'])
                name, unit = item['name'] + ' • carretel #' + str(item['id']), 'g'
            else:
                item = self.inventory.get('materials', row['material_id'])
                name, unit = item['name'], item['unit']
            before, after = json.loads(row['previous']), json.loads(row['current'])
            previous = 'Desconhecido / não informado' if before is None else grams(before) + ' ' + unit
            current = 'Desconhecido / não informado' if after is None else grams(after) + ' ' + unit
        quantity = 'Desconhecida' if row['quantity_milli'] is None else grams(row['quantity_milli']) + ' ' + unit
        return [datetime.fromisoformat(row['created_at']).astimezone().strftime('%d/%m/%Y %H:%M'),
                kinds.get(row['kind'], row['kind']), name, quantity, previous, current, row['reason']]

    def selected(self, listing, rows):
        index = listing.currentRow()
        if index < 0:
            QMessageBox.information(self, 'Selecione um item', 'Selecione uma linha na tabela.'); return None
        return rows[index]['id']

    def material_new(self):
        if MaterialDialog(self.inventory, parent=self).exec() == QDialog.Accepted:
            self.refresh()

    def material_edit(self):
        identifier = self.selected(self.material_table, self.material_rows)
        if identifier is not None and MaterialDialog(self.inventory, identifier, self).exec() == QDialog.Accepted:
            self.refresh()

    def material_consume(self):
        identifier = self.selected(self.material_table, self.material_rows)
        if identifier is not None and ConsumeMaterialDialog(self.inventory, identifier, self).exec() == QDialog.Accepted:
            self.refresh()

    def material_loss(self):
        identifier = self.selected(self.material_table, self.material_rows)
        if identifier is not None and LossDialog(self.inventory, 'material', identifier, self).exec() == QDialog.Accepted:
            self.refresh()

    def filament_loss(self):
        identifier = self.filaments_page.selected()
        if identifier is not None and LossDialog(self.inventory, 'filament', identifier, self).exec() == QDialog.Accepted:
            self.refresh()

    def material_archive(self):
        identifier = self.selected(self.material_table, self.material_rows)
        if identifier is None:
            return
        reason, ok = QInputDialog.getText(self, 'Arquivar / restaurar material', 'Justificativa obrigatória:')
        if ok and QMessageBox.question(self, 'Confirmar', 'Confirmar arquivamento ou restauração?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            try:
                self.inventory.archive_material(identifier, not self.material_trash.isChecked(), reason); self.refresh()
            except ValueError as error:
                QMessageBox.warning(self, 'Verifique os dados', str(error))

    def receive(self):
        if ReceiptDialog(self.inventory, self).exec() == QDialog.Accepted:
            self.refresh()

    def reserve(self):
        variant = self.selected(self.stock_table, self.stock_rows)
        if variant is not None and ReserveDialog(self.inventory, variant, self).exec() == QDialog.Accepted:
            self.refresh()

    def selected_pieces(self):
        indexes = sorted({item.row() for item in self.pieces_table.selectedItems()})
        if not indexes:
            QMessageBox.information(self, 'Selecione peças', 'Selecione uma ou várias linhas em Peças físicas.'); return []
        return [self.piece_rows[index]['id'] for index in indexes]

    def review(self):
        ids = self.selected_pieces()
        if ids and ReviewDialog(self.inventory, ids, self).exec() == QDialog.Accepted:
            self.refresh()

    def piece_loss(self):
        ids = self.selected_pieces()
        if ids and LossDialog(self.inventory, 'piece', ids, self).exec() == QDialog.Accepted:
            self.refresh()

    def finish_reservation(self, action):
        identifier = self.selected(self.reservations_table, self.reservation_rows)
        if identifier is None:
            return
        reason, ok = QInputDialog.getText(self, 'Liberar / baixar reserva', 'Justificativa obrigatória; esta operação não registra venda nem recebimento:')
        if not ok:
            return
        if QMessageBox.question(self, 'Confirmar movimentação', 'Confirmar operação? Uma reserva baixada não poderá sofrer nova baixa.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        try:
            self.inventory.finish_reservation(identifier, action, reason); self.refresh()
        except ValueError as error:
            QMessageBox.warning(self, 'Verifique os dados', str(error))
