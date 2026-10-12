"""Phase 2 desktop forms; values enter the domain as decimal strings."""
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
import json
import sqlite3
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QPushButton, QDialog, QDialogButtonBox, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QTextEdit,
    QScrollArea, QTabWidget)
from .catalog import Catalog, PRINTER_STATES, FILAMENT_STATES
from .pricing import brl, hourly_cost, compare, number


def date_br(value):
    return date.fromisoformat(value).strftime('%d/%m/%Y') if value else ''


def date_iso(value):
    if not value.strip():
        return None
    try:
        return datetime.strptime(value.strip(), '%d/%m/%Y').date().isoformat()
    except ValueError:
        raise ValueError('Data inválida. Use DD/MM/AAAA.') from None


def decimal_cents(value):
    return str(Decimal(value) / 100)


def grams(value):
    return str(Decimal(value) / 1000) if value is not None else ''


def minutes_label(value):
    return f'{value // 60} h {value % 60:02d} min'


def button(label, handler, layout):
    item = QPushButton(label)
    item.clicked.connect(handler)
    layout.addWidget(item)
    return item


def table(headers):
    widget = QTableWidget(0, len(headers))
    widget.setHorizontalHeaderLabels(headers)
    widget.setEditTriggers(QTableWidget.NoEditTriggers)
    widget.setSelectionBehavior(QTableWidget.SelectRows)
    widget.setSelectionMode(QTableWidget.SingleSelection)
    widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    widget.horizontalHeader().setStretchLastSection(True)
    return widget


def fill_table(widget, rows):
    widget.setRowCount(len(rows))
    for i, values in enumerate(rows):
        for j, value in enumerate(values):
            widget.setItem(i, j, QTableWidgetItem(str(value)))


def scroll(widget):
    wrapper = QScrollArea()
    wrapper.setWidgetResizable(True)
    wrapper.setWidget(widget)
    return wrapper


class FormDialog(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(580, 650)
        box = QVBoxLayout(self)
        content = QWidget()
        self.form = QFormLayout(content)
        box.addWidget(scroll(content))
        self.fields = {}
        self.error = QLabel()
        self.error.setWordWrap(True)
        self.error.setStyleSheet('color:#da5876')
        box.addWidget(self.error)
        controls = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        controls.button(QDialogButtonBox.Save).setText('Salvar')
        controls.button(QDialogButtonBox.Cancel).setText('Cancelar')
        controls.accepted.connect(self.submit)
        controls.rejected.connect(self.reject)
        box.addWidget(controls)

    def line(self, key, label, value='', placeholder=''):
        item = QLineEdit(str(value))
        item.setPlaceholderText(placeholder)
        self.fields[key] = item
        self.form.addRow(label, item)
        return item

    def combo(self, key, label, choices, value):
        item = QComboBox()
        for code, name in choices.items():
            item.addItem(name, code)
        item.setCurrentIndex(item.findData(value))
        self.fields[key] = item
        self.form.addRow(label, item)
        return item

    def values(self):
        return {key: item.currentData() if isinstance(item, QComboBox) else item.text().strip()
                for key, item in self.fields.items()}

    def submit(self):
        try:
            self.persist()
            self.accept()
        except (ValueError, OSError, sqlite3.IntegrityError) as error:
            message = str(error)
            if 'UNIQUE constraint' in message:
                message = 'Identificação já utilizada. Escolha uma identificação única.'
            self.error.setText(message)


class PrinterDialog(FormDialog):
    def __init__(self, catalog, identifier=None, parent=None):
        super().__init__('Editar impressora' if identifier else 'Nova impressora', parent)
        self.catalog, self.identifier = catalog, identifier
        row = catalog.get('printers', identifier) if identifier else {}
        for key, label in (('manufacturer', 'Fabricante *'), ('model', 'Modelo *'), ('identifier', 'Identificação *')):
            self.line(key, label, row.get(key, ''))
        self.line('acquired_on', 'Data de aquisição', date_br(row.get('acquired_on')), 'DD/MM/AAAA; opcional')
        self.line('purchase', 'Valor de aquisição (R$)', decimal_cents(row.get('purchase_cents', 0)))
        self.line('accumulated_minutes', 'Tempo acumulado (minutos)', row.get('accumulated_minutes', 0))
        for key, label, default in (('investment_hour', 'Recuperação do investimento (R$/h)', 75),
                                    ('energy_hour', 'Energia elétrica (R$/h)', 10),
                                    ('maintenance_hour', 'Manutenção e desgaste (R$/h)', 25)):
            self.line(key, label, decimal_cents(row.get(key + '_cents', default)))
        self.total = QLabel()
        self.form.addRow('Custo operacional total', self.total)
        for key in ('investment_hour', 'energy_hour', 'maintenance_hour'):
            self.fields[key].textChanged.connect(self.update_total)
        self.update_total()
        self.combo('status', 'Situação', PRINTER_STATES, row.get('status', 'operational'))
        self.line('reason', 'Justificativa de correção de tempo', '', 'Obrigatória quando alterar o tempo acumulado')

    def update_total(self):
        try:
            self.total.setText(brl(sum((number(self.fields[k].text(), places=2) for k in ('investment_hour', 'energy_hour', 'maintenance_hour')), Decimal('0'))) + '/h')
        except ValueError:
            self.total.setText('Verifique os valores.')

    def persist(self):
        values = self.values()
        values['acquired_on'] = date_iso(values['acquired_on'])
        self.saved_id = self.catalog.save_printer(values, self.identifier, values.pop('reason'))


class FilamentDialog(FormDialog):
    def __init__(self, catalog, identifier=None, parent=None):
        super().__init__('Editar filamento' if identifier else 'Novo filamento', parent)
        self.catalog, self.identifier = catalog, identifier
        row = catalog.get('filaments', identifier) if identifier else {}
        self.line('brand', 'Marca *', row.get('brand', ''))
        self.line('material', 'Material *', row.get('material', 'PLA'), 'PLA, PLA Silk, PETG, TPU, ABS ou outro')
        self.line('color', 'Cor *', row.get('color', ''))
        self.line('name', 'Nome comercial *', row.get('name', ''))
        self.line('purchase', 'Preço real de compra (R$)', decimal_cents(row.get('purchase_cents', 0)))
        self.line('initial_grams', 'Peso inicial (g)', grams(row.get('initial_mg', 1000000)), 'Pode ficar vazio se desconhecido')
        self.line('purchased_on', 'Data de compra', date_br(row.get('purchased_on')), 'DD/MM/AAAA; opcional')
        self.line('supplier', 'Fornecedor', row.get('supplier', ''))
        self.reference = self.line('reference_per_g', 'Referência para precificação (R$/g) *', row.get('reference_per_g', ''), 'Até 6 casas decimais; independente da compra')
        self.acquisition = QLabel()
        self.form.addRow('Custo real de aquisição por grama', self.acquisition)
        action = QPushButton('Usar custo de aquisição como referência')
        action.clicked.connect(self.use_acquisition)
        self.form.addRow(action)
        for key in ('purchase', 'initial_grams'):
            self.fields[key].textChanged.connect(self.update_acquisition)
        self.update_acquisition()
        self.unknown = QCheckBox('Saldo desconhecido — usar sem exigir pesagem')
        self.unknown.setChecked(identifier is not None and row['remaining_mg'] is None)
        self.form.addRow(self.unknown)
        self.remaining = self.line('remaining_grams', 'Saldo estimado restante (g)', grams(row.get('remaining_mg', 1000000)))
        self.remaining.setEnabled(not self.unknown.isChecked())
        self.unknown.toggled.connect(lambda checked: self.remaining.setEnabled(not checked))
        self.combo('state', 'Estado', FILAMENT_STATES, row.get('state', 'new'))
        self.line('reason', 'Justificativa de ajuste de saldo', '', 'Obrigatória em correção de saldo ou finalização')
        self.form.addRow(QLabel('Filamento gratuito: compra = 0; a referência de preço pode ser maior que zero.'))

    def acquisition_value(self):
        from .pricing import cost_per_gram
        if not self.fields['initial_grams'].text().strip():
            return None
        return cost_per_gram(self.fields['purchase'].text(), self.fields['initial_grams'].text())

    def update_acquisition(self):
        try:
            value = self.acquisition_value()
            self.acquisition.setText('Desconhecido' if value is None else f'{value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)} R$/g')
        except ValueError:
            self.acquisition.setText('Verifique preço e peso inicial.')

    def use_acquisition(self):
        try:
            value = self.acquisition_value()
            if value is None:
                raise ValueError('Informe um peso inicial conhecido para calcular o custo de aquisição.')
            self.reference.setText(str(value.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)))
        except ValueError as error:
            self.error.setText(str(error))

    def persist(self):
        values = self.values()
        values['purchased_on'] = date_iso(values['purchased_on'])
        if self.unknown.isChecked():
            values['remaining_grams'] = None
            if values['state'] == 'new':
                values['state'] = 'open'
        self.saved_id = self.catalog.save_filament(values, self.identifier, values.pop('reason'))


class MaintenanceDialog(FormDialog):
    def __init__(self, catalog, printer_id, parent):
        super().__init__('Registrar manutenção • não é lançamento de caixa', parent)
        self.catalog, self.printer_id = catalog, printer_id
        self.line('performed_on', 'Data *', date.today().strftime('%d/%m/%Y'))
        self.line('description', 'Descrição *')
        self.line('cost', 'Valor pago (R$)', '0')
        self.line('next_due', 'Próxima manutenção', '', 'DD/MM/AAAA; opcional')

    def persist(self):
        values = self.values()
        self.catalog.add_maintenance(self.printer_id, date_iso(values['performed_on']), values['description'],
                                     values['cost'], date_iso(values['next_due']))


class CatalogPage(QWidget):
    def __init__(self, storage, kind):
        super().__init__()
        self.catalog, self.kind = Catalog(storage), kind
        box = QVBoxLayout(self)
        controls = QHBoxLayout()
        button('Nova impressora' if kind == 'printers' else 'Novo filamento', self.new, controls)
        button('Editar', self.edit, controls)
        button('Arquivar / restaurar', self.archive, controls)
        self.trash = QCheckBox('Mostrar lixeira')
        self.trash.toggled.connect(self.refresh)
        controls.addWidget(self.trash)
        box.addLayout(controls)
        if kind == 'printers':
            self.table = table(['ID', 'Identificação', 'Fabricante / modelo', 'Aquisição', 'Tempo acumulado', 'R$/h', 'Situação'])
            row = QHBoxLayout()
            button('Registrar manutenção', self.maintenance_new, row)
            button('Histórico de manutenção', self.maintenance_history, row)
            box.addLayout(row)
        else:
            self.table = table(['ID', 'Nome / marca', 'Material / cor', 'Compra', 'Referência R$/g', 'Saldo estimado', 'Estado'])
            self.alert = QLabel()
            self.alert.setWordWrap(True)
            box.addWidget(self.alert)
        self.table.doubleClicked.connect(lambda index: self.edit())
        box.addWidget(self.table)
        note = QLabel('Os cadastros são preservados na lixeira. Alterações são auditadas; cálculos antigos mantêm os valores originais.')
        note.setWordWrap(True)
        box.addWidget(note)
        self.refresh()

    def refresh(self):
        self.rows = self.catalog.rows(self.kind, self.trash.isChecked())
        values = []
        for row in self.rows:
            if self.kind == 'printers':
                values.append([row['id'], row['identifier'], row['manufacturer'] + ' ' + row['model'],
                               brl(Decimal(row['purchase_cents']) / 100), minutes_label(row['accumulated_minutes']),
                               brl(hourly_cost(row)), PRINTER_STATES[row['status']]])
            else:
                saldo = 'Desconhecido' if row['remaining_mg'] is None else grams(row['remaining_mg']) + ' g'
                values.append([row['id'], row['name'] + ' / ' + row['brand'], row['material'] + ' / ' + row['color'],
                               brl(Decimal(row['purchase_cents']) / 100), row['reference_per_g'], saldo, FILAMENT_STATES[row['state']]])
        fill_table(self.table, values)
        if self.kind == 'filaments':
            low = self.catalog.low_filaments()
            self.alert.setText('Alerta de saldo baixo (até ' + str(self.catalog.storage.get('low_filament_grams', '100')) + ' g): ' +
                               (', '.join(row['name'] for row in low) if low else 'nenhum carretel conhecido abaixo do limite.') +
                               '\nSaldos desconhecidos não são estimados nem incluídos neste alerta.')

    def selected(self):
        index = self.table.currentRow()
        if index < 0:
            QMessageBox.information(self, 'Selecione um registro', 'Selecione uma linha na tabela.')
            return None
        return self.rows[index]['id']

    def new(self):
        dialog = PrinterDialog(self.catalog, parent=self) if self.kind == 'printers' else FilamentDialog(self.catalog, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh()

    def edit(self):
        identifier = self.selected()
        if identifier is None:
            return
        if self.trash.isChecked():
            QMessageBox.information(self, 'Cadastro arquivado', 'Restaure o registro antes de editar.')
            return
        dialog = PrinterDialog(self.catalog, identifier, self) if self.kind == 'printers' else FilamentDialog(self.catalog, identifier, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh()

    def archive(self):
        identifier = self.selected()
        if identifier is None:
            return
        from PySide6.QtWidgets import QInputDialog
        reason, ok = QInputDialog.getText(self, 'Restaurar' if self.trash.isChecked() else 'Arquivar', 'Justificativa obrigatória:')
        if not ok:
            return
        if QMessageBox.question(self, 'Confirmar', 'Confirmar esta alteração? O histórico será preservado.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        try:
            self.catalog.archive(self.kind, identifier, not self.trash.isChecked(), reason)
            self.refresh()
        except ValueError as error:
            QMessageBox.warning(self, 'Verifique os dados', str(error))

    def maintenance_new(self):
        identifier = self.selected()
        if identifier is not None:
            MaintenanceDialog(self.catalog, identifier, self).exec()

    def maintenance_history(self):
        identifier = self.selected()
        if identifier is None:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle('Histórico de manutenção • separado da reserva por hora')
        dialog.resize(750, 400)
        box = QVBoxLayout(dialog)
        listing = table(['Data', 'Descrição', 'Valor', 'Próxima'])
        fill_table(listing, [[date_br(r['performed_on']), r['description'], brl(Decimal(r['cost_cents']) / 100), date_br(r['next_due'])] for r in self.catalog.maintenance(identifier)])
        box.addWidget(listing)
        dialog.exec()


class PricingDefaults(FormDialog):
    def __init__(self, storage, parent):
        super().__init__('Parâmetros de precificação e alerta', parent)
        self.catalog = Catalog(storage)
        self.line('markup', 'Acréscimo sobre o custo (%)', storage.get('markup_percent', '200'))
        self.line('threshold', 'Alerta de filamento (g)', storage.get('low_filament_grams', '100'))
        self.form.addRow(QLabel('200% significa preço = custo × 3. Não é margem de 200%.'))

    def persist(self):
        values = self.values()
        self.catalog.defaults(values['markup'], values['threshold'])


def summary(snapshot):
    percent = snapshot['adjustment_percent']
    percentage = 'não aplicável (preço sugerido zero)' if percent is None else percent.replace('.', ',') + '%'
    components = '\n'.join(f"  {row['name']} • {row['grams']} g × {row['reference_per_g']} R$/g = {brl(row['cost'])}" for row in snapshot['filaments'])
    printer = snapshot['printer']
    acquisition = snapshot.get('acquisition_production_cost')
    acquisition_text = ('Custo de aquisição do material: desconhecido para ao menos um carretel.\n'
                        if acquisition is None else
                        f"Material pelo custo de aquisição: {brl(snapshot['acquisition_material_cost'])}\n"
                        f"Custo pela aquisição + máquina + auxiliares: {brl(acquisition)}\n"
                        f"Resultado pela aquisição antes de outras despesas: {brl(snapshot['acquisition_commercial_result'])}\n")
    return (f"Impressora: {printer['manufacturer']} {printer['model']} ({printer['identifier']})\n"
            f"Tempo: {minutes_label(snapshot['minutes'])} • {snapshot['quantity']} peça(s)\n"
            f"Máquina: {brl(hourly_cost(printer))}/h → {brl(snapshot['machine_cost'])}\n"
            f"Filamentos:\n{components}\nMateriais auxiliares: {brl(snapshot['auxiliary'])}\n\n"
            f"Custo total à referência: {brl(snapshot['total_cost'])}\nCusto unitário à referência: {brl(snapshot['unit_cost'])}\n"
            f"Acréscimo: {snapshot['markup']}%\nPreço sugerido TOTAL: {brl(snapshot['suggested_total'])}\n"
            f"Preço sugerido unitário: {brl(snapshot['suggested_unit'])}\nPreço final TOTAL: {brl(snapshot['final_total'])}\n"
            f"{snapshot['adjustment_kind'].capitalize()}: {brl(snapshot['adjustment_amount'])} • {percentage}\n"
            f"Resultado à referência antes de outras despesas: {brl(snapshot['commercial_result'])}\n\n"
            + acquisition_text + '\n' +
            'O preço final é usado uma única vez. Este cálculo não registra venda, recebimento ou saída de caixa.')


class ActualDialog(FormDialog):
    def __init__(self, catalog, identifier, parent=None):
        super().__init__('Confirmar tempo e consumo reais', parent)
        self.catalog, self.identifier = catalog, identifier
        self.planned = json.loads(catalog.get('calculations', identifier)['planned'])
        self.form.addRow(QLabel('A confirmação é única e reduz saldos conhecidos.\nReferências de custo permanecem as da previsão.'))
        self.line('minutes', 'Tempo real (minutos)', self.planned['minutes'])
        self.line('quantity', 'Quantidade real de peças', self.planned['quantity'])
        self.line('auxiliary', 'Materiais auxiliares reais (R$)', self.planned['auxiliary'])
        for row in self.planned['filaments']:
            self.line(str(row['id']), row['name'] + ' • consumo real (g)', row['grams'])

    def persist(self):
        values = self.values()
        if QMessageBox.question(self, 'Consolidar custo real', 'Confirmar tempo e consumo? Saldo conhecido será reduzido e o tempo será somado à impressora. Não será possível confirmar novamente.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            raise ValueError('Confirmação cancelada; nenhum dado foi consolidado.')
        self.comparison = self.catalog.confirm_actual(self.identifier, values['minutes'],
            {row['id']: values[str(row['id'])] for row in self.planned['filaments']}, values['auxiliary'], values['quantity'])


class CalculatorPage(QWidget):
    def __init__(self, storage):
        super().__init__()
        self.storage, self.catalog = storage, Catalog(storage)
        self.loading = True
        self.spool_rows = []
        self.filaments = []
        self.last_saved_id = None
        box = QVBoxLayout(self)
        self.tabs = QTabWidget()
        box.addWidget(self.tabs)
        content = QWidget()
        self.tabs.addTab(scroll(content), 'Calculadora')
        layout = QVBoxLayout(content)
        instruction = QLabel('Informe valores do lote inteiro. Salvar previsão não consome filamento nem movimenta caixa. Custo real é confirmado no Histórico.')
        instruction.setWordWrap(True)
        layout.addWidget(instruction)
        form = QFormLayout()
        self.title = QLineEdit()
        self.title.setPlaceholderText('Descrição para identificar o cálculo')
        self.printer = QComboBox()
        self.minutes = QLineEdit('60')
        self.quantity = QLineEdit('1')
        self.markup = QLineEdit(str(storage.get('markup_percent', '200')))
        self.auxiliary = QLineEdit('0')
        self.final = QLineEdit()
        self.final.setPlaceholderText('Vazio: usar preço sugerido; 0: preço final gratuito')
        for label, item in (('Descrição *', self.title), ('Impressora', self.printer), ('Tempo previsto (minutos)', self.minutes),
                            ('Quantidade de peças', self.quantity), ('Acréscimo (%)', self.markup),
                            ('Materiais auxiliares TOTAL (R$)', self.auxiliary), ('Preço final TOTAL (R$)', self.final)):
            form.addRow(label, item)
        layout.addLayout(form)
        self.material_box = QVBoxLayout()
        layout.addLayout(self.material_box)
        buttons = QHBoxLayout()
        button('Adicionar filamento', self.add_filament, buttons)
        button('Calcular', self.preview, buttons)
        button('Salvar previsão', self.save, buttons)
        button('Atualizar parâmetros', self.use_defaults, buttons)
        layout.addLayout(buttons)
        self.result = QTextEdit()
        self.result.setReadOnly(True)
        self.result.setMinimumHeight(230)
        layout.addWidget(self.result)
        self.draft_label = QLabel('Rascunho da calculadora recuperado automaticamente.')
        layout.addWidget(self.draft_label)
        history = QWidget()
        hb = QVBoxLayout(history)
        self.history_table = table(['ID', 'Data', 'Descrição', 'Previsto', 'Real', 'Situação'])
        hb.addWidget(self.history_table)
        controls = QHBoxLayout()
        button('Ver cálculo e comparação', self.details, controls)
        button('Confirmar custo real', self.confirm, controls)
        hb.addLayout(controls)
        self.tabs.addTab(history, 'Histórico')
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(600)
        self.timer.timeout.connect(self.save_draft)
        for item in (self.title, self.minutes, self.quantity, self.markup, self.auxiliary, self.final):
            item.textChanged.connect(self.changed)
        self.printer.currentIndexChanged.connect(self.changed)
        self.refresh()
        self.restore_draft()
        self.loading = False
        self.result.setPlainText('Cadastre filamentos em Estoque e selecione ao menos um para calcular.')

    def refresh(self):
        old_loading = self.loading
        self.loading = True
        current = self.printer.currentData()
        self.printer.clear()
        for row in self.catalog.rows('printers'):
            if row['status'] == 'operational':
                self.printer.addItem(row['identifier'] + ' • ' + row['manufacturer'] + ' ' + row['model'] + ' • ' + brl(hourly_cost(row)) + '/h', row['id'])
        if current is not None:
            self.printer.setCurrentIndex(self.printer.findData(current))
        self.filaments = [row for row in self.catalog.rows('filaments') if row['state'] != 'finished']
        for widget, combo, weight in self.spool_rows:
            self.populate_spools(combo, combo.currentData())
        self.history_rows = self.catalog.calculations()
        values = []
        for row in self.history_rows:
            planned = json.loads(row['planned'])
            actual = json.loads(row['actual']) if row['actual'] else None
            values.append([row['id'], datetime.fromisoformat(row['created_at']).astimezone().strftime('%d/%m/%Y %H:%M'),
                           row['title'], brl(planned['total_cost']), brl(actual['total_cost']) if actual else '—',
                           'Confirmado' if actual else 'Previsto'])
        fill_table(self.history_table, values)
        self.loading = old_loading
        if not self.loading:
            self.result.setPlainText('Cadastros atualizados. Clique em Calcular para usar as referências atuais.')

    def populate_spools(self, combo, identifier=None):
        combo.clear()
        for row in self.filaments:
            saldo = 'saldo desconhecido' if row['remaining_mg'] is None else grams(row['remaining_mg']) + ' g restantes'
            combo.addItem(row['name'] + ' • ' + row['material'] + ' / ' + row['color'] + ' • ' + saldo, row['id'])
        wanted = identifier if identifier is not None else self.storage.get('last_filament_id')
        if wanted is not None:
            index = combo.findData(wanted)
            if identifier is not None or index >= 0:
                combo.setCurrentIndex(index)

    def add_filament(self, identifier=None, weight='10'):
        if isinstance(identifier, bool):
            identifier = None
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        combo = QComboBox()
        self.populate_spools(combo, identifier)
        combo.setMinimumWidth(240)
        consumption = QLineEdit(str(weight))
        consumption.setPlaceholderText('Consumo em gramas')
        layout.addWidget(combo, 1)
        layout.addWidget(QLabel('g:'))
        layout.addWidget(consumption)
        button('Remover', lambda: self.remove_filament(widget), layout)
        self.material_box.addWidget(widget)
        self.spool_rows.append((widget, combo, consumption))
        combo.currentIndexChanged.connect(self.changed)
        consumption.textChanged.connect(self.changed)
        self.changed()

    def remove_filament(self, widget):
        self.spool_rows = [row for row in self.spool_rows if row[0] is not widget]
        self.material_box.removeWidget(widget)
        widget.deleteLater()
        self.changed()

    def changed(self, *args):
        if not self.loading:
            self.result.setPlainText('Valores alterados. Clique em Calcular ou Salvar previsão para atualizar o resultado.')
            self.timer.start()

    def save_draft(self):
        data = {key: getattr(self, key).text() for key in ('title', 'minutes', 'quantity', 'markup', 'auxiliary', 'final')}
        data['printer'] = self.printer.currentData()
        data['filaments'] = [[combo.currentData(), weight.text()] for _, combo, weight in self.spool_rows]
        self.storage.save_draft('calculator', json.dumps(data, ensure_ascii=False))
        self.draft_label.setText('Rascunho salvo automaticamente; nenhuma previsão ou consumo foi confirmado.')

    def restore_draft(self):
        saved = self.storage.load_draft('calculator')
        if saved:
            try:
                data = json.loads(saved)
                for key in ('title', 'minutes', 'quantity', 'markup', 'auxiliary', 'final'):
                    getattr(self, key).setText(str(data[key]))
                self.printer.setCurrentIndex(self.printer.findData(data['printer']))
                for identifier, weight in data['filaments']:
                    self.add_filament(identifier, weight)
            except (ValueError, KeyError, TypeError):
                self.draft_label.setText('Rascunho anterior incompatível; use um novo cálculo.')
        if not self.spool_rows:
            self.add_filament()

    def arguments(self):
        if self.printer.currentData() is None:
            raise ValueError('Selecione uma impressora operacional.')
        selections = [(combo.currentData(), weight.text()) for _, combo, weight in self.spool_rows]
        if any(identifier is None for identifier, weight in selections):
            raise ValueError('Selecione carretéis disponíveis; cadastre filamentos em Estoque.')
        return {'printer_id': self.printer.currentData(), 'minutes': self.minutes.text(), 'selections': selections,
                'auxiliary': self.auxiliary.text(), 'quantity': self.quantity.text(), 'markup': self.markup.text(),
                'final': self.final.text() if self.final.text().strip() else None}

    def preview(self):
        try:
            self.result.setPlainText(summary(self.catalog.estimate(**self.arguments())))
        except ValueError as error:
            self.result.setPlainText(str(error))

    def save(self):
        try:
            self.last_saved_id = self.catalog.save_calculation(self.title.text(), **self.arguments())
            snapshot = json.loads(self.catalog.get('calculations', self.last_saved_id)['planned'])
            self.save_draft()
            self.refresh()
            self.result.setPlainText(f'Previsão #{self.last_saved_id} salva.\n\n' + summary(snapshot))
        except ValueError as error:
            self.result.setPlainText(str(error))

    def use_defaults(self):
        self.markup.setText(str(self.storage.get('markup_percent', '200')))
        self.refresh()

    def selected_history(self):
        index = self.history_table.currentRow()
        if index < 0:
            QMessageBox.information(self, 'Selecione um cálculo', 'Selecione uma linha no histórico.')
            return None
        return self.history_rows[index]['id']

    def details(self):
        identifier = self.selected_history()
        if identifier is None:
            return
        row = self.catalog.get('calculations', identifier)
        dialog = QDialog(self)
        dialog.setWindowTitle(f'Cálculo #{identifier} • {row["title"]}')
        dialog.resize(700, 600)
        box = QVBoxLayout(dialog)
        output = QTextEdit()
        output.setReadOnly(True)
        planned = json.loads(row['planned'])
        text = 'PREVISTO\n' + summary(planned)
        if row['actual']:
            actual = json.loads(row['actual'])
            comparison = compare(planned, actual)
            percent = comparison['percent'] + '%' if comparison['percent'] is not None else 'não aplicável (custo previsto zero)'
            text += '\n\nREAL CONFIRMADO (REFERÊNCIAS DA PREVISÃO)\n' + summary(actual)
            text += f"\n\nDiferença real − previsto: {brl(comparison['difference'])} ({percent})"
        output.setPlainText(text)
        box.addWidget(output)
        dialog.exec()

    def confirm(self):
        identifier = self.selected_history()
        if identifier is None:
            return
        if self.catalog.get('calculations', identifier)['actual']:
            QMessageBox.information(self, 'Já confirmado', 'Este cálculo já foi consolidado; não é possível confirmar novamente.')
            return
        if ActualDialog(self.catalog, identifier, self).exec() == QDialog.Accepted:
            self.refresh()
