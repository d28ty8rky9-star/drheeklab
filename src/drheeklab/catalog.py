"""Validated, audited catalogs and immutable planned/confirmed cost snapshots."""
from datetime import date
from decimal import Decimal
import json
from .storage import now
from .transactions import transaction
from .journal import record as stock_record, supported as stock_supported
from .pricing import number, cents, grams_mg, integer, calculate, compare, cost_per_gram

PRINTER_STATES = {'operational': 'Operacional', 'maintenance': 'Em manutenção', 'inactive': 'Inativa'}
FILAMENT_STATES = {'new': 'Novo', 'open': 'Aberto', 'finished': 'Finalizado'}


def required(value, label):
    value = '' if value is None else str(value).strip()
    if not value:
        raise ValueError(label + ' é obrigatório.')
    return value


def optional_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError:
        raise ValueError('Data inválida. Use DD/MM/AAAA na interface.') from None


class Catalog:
    def __init__(self, storage):
        self.storage = storage
        self.db = storage.db

    def rows(self, table, archived=False):
        if table not in ('printers', 'filaments'):
            raise ValueError('Cadastro inválido.')
        return [dict(row) for row in self.db.execute(f'SELECT * FROM {table} WHERE archived=? ORDER BY id', (int(archived),))]

    def get(self, table, identifier):
        if table not in ('printers', 'filaments', 'calculations'):
            raise ValueError('Cadastro inválido.')
        row = self.db.execute(f'SELECT * FROM {table} WHERE id=?', (identifier,)).fetchone()
        if row is None:
            raise ValueError('Registro não encontrado.')
        return dict(row)

    def _save(self, table, values, identifier=None, reason=None):
        with transaction(self.db):
            previous = self.get(table, identifier) if identifier is not None else None
            if previous and previous['archived']:
                raise ValueError('Restaure o cadastro antes de editar.')
            fields = ','.join(values)
            if identifier is None:
                sql = f"INSERT INTO {table}({fields}) VALUES({','.join('?' for _ in values)})"
                identifier = self.db.execute(sql, tuple(values.values())).lastrowid
            else:
                assignments = ','.join(f'{key}=?' for key in values)
                self.db.execute(f'UPDATE {table} SET {assignments} WHERE id=?', (*values.values(), identifier))
            if table == 'filaments' and stock_supported(self.storage):
                current_balance = values['remaining_mg']
                before_balance = previous['remaining_mg'] if previous else None
                if previous is None or before_balance != current_balance:
                    delta = current_balance if previous is None else (
                        current_balance - before_balance if current_balance is not None and before_balance is not None else None)
                    stock_record(self.storage, 'opening' if previous is None else 'adjustment', 'filament', identifier,
                                 delta, before_balance, current_balance, reason or 'Cadastro inicial do carretel')
            self.storage.audit('cadastro' if previous is None else 'edição', f'{table}:{identifier}', previous, values, reason)
        return identifier

    def save_printer(self, data, identifier=None, reason=None):
        status = data.get('status', 'operational')
        if status not in PRINTER_STATES:
            raise ValueError('Situação da impressora inválida.')
        values = {'manufacturer': required(data.get('manufacturer', ''), 'Fabricante'),
                  'model': required(data.get('model', ''), 'Modelo'),
                  'identifier': required(data.get('identifier', ''), 'Identificação'),
                  'acquired_on': optional_date(data.get('acquired_on')),
                  'purchase_cents': cents(data.get('purchase', '0'), 'Valor de aquisição'),
                  'accumulated_minutes': integer(data.get('accumulated_minutes', 0), 'Minutos acumulados'),
                  'investment_hour_cents': cents(data.get('investment_hour', '0.75')),
                  'energy_hour_cents': cents(data.get('energy_hour', '0.10')),
                  'maintenance_hour_cents': cents(data.get('maintenance_hour', '0.25')),
                  'status': status}
        if identifier is not None and self.get('printers', identifier)['accumulated_minutes'] != values['accumulated_minutes']:
            required(reason or '', 'Justificativa da correção de horas')
        return self._save('printers', values, identifier, reason)

    def save_filament(self, data, identifier=None, reason=None):
        state = data.get('state', 'new')
        if state not in FILAMENT_STATES:
            raise ValueError('Estado do filamento inválido.')
        initial = None if data.get('initial_grams') in (None, '') else grams_mg(data['initial_grams'], 'Peso inicial')
        if initial == 0:
            raise ValueError('O peso inicial deve ser positivo ou desconhecido.')
        remaining = None if data.get('remaining_grams') in (None, '') else grams_mg(data['remaining_grams'], 'Saldo estimado')
        if initial is not None and remaining is not None and remaining > initial:
            raise ValueError('O saldo não pode exceder o peso inicial.')
        if state == 'new' and remaining is None:
            raise ValueError('Carretel com saldo desconhecido deve estar aberto ou finalizado.')
        if state == 'finished' and remaining not in (None, 0):
            raise ValueError('Filamento finalizado não pode ter saldo positivo.')
        values = {'brand': required(data.get('brand', ''), 'Marca'),
                  'material': required(data.get('material', ''), 'Material'),
                  'color': required(data.get('color', ''), 'Cor'),
                  'name': required(data.get('name', ''), 'Nome comercial'),
                  'purchase_cents': cents(data.get('purchase', '0'), 'Preço de compra'),
                  'initial_mg': initial, 'purchased_on': optional_date(data.get('purchased_on')),
                  'supplier': str(data.get('supplier', '')).strip(),
                  'reference_per_g': str(number(data.get('reference_per_g', ''), 'Referência por grama', places=6)),
                  'remaining_mg': remaining, 'state': state}
        if identifier is not None:
            previous = self.get('filaments', identifier)
            if previous['remaining_mg'] != remaining or (previous['state'] != 'finished' and state == 'finished'):
                required(reason or '', 'Justificativa do ajuste de saldo ou finalização')
        return self._save('filaments', values, identifier, reason)

    def acquisition_per_g(self, filament):
        return None if filament['initial_mg'] is None else cost_per_gram(
            Decimal(filament['purchase_cents']) / 100, Decimal(filament['initial_mg']) / 1000)

    def archive(self, table, identifier, archived, reason):
        if table not in ('printers', 'filaments'):
            raise ValueError('Cadastro inválido.')
        required(reason, 'Justificativa')
        with transaction(self.db):
            previous = self.get(table, identifier)
            self.db.execute(f'UPDATE {table} SET archived=? WHERE id=?', (int(archived), identifier))
            self.storage.audit('arquivar' if archived else 'restaurar', f'{table}:{identifier}', previous, self.get(table, identifier), reason)

    def add_maintenance(self, printer_id, performed_on, description, cost='0', next_due=None):
        self.get('printers', printer_id)
        values = (printer_id, optional_date(required(performed_on, 'Data')), required(description, 'Descrição'),
                  cents(cost), optional_date(next_due))
        with transaction(self.db):
            result = self.db.execute('INSERT INTO maintenance(printer_id,performed_on,description,cost_cents,next_due) VALUES(?,?,?,?,?)', values).lastrowid
            self.storage.audit('manutenção', f'printers:{printer_id}', None, dict(zip(('printer_id', 'performed_on', 'description', 'cost_cents', 'next_due'), values)))
        return result

    def maintenance(self, printer_id):
        return [dict(row) for row in self.db.execute('SELECT * FROM maintenance WHERE printer_id=? ORDER BY performed_on DESC,id DESC', (printer_id,))]

    def defaults(self, markup, threshold):
        markup = str(number(markup, 'Acréscimo padrão', places=2))
        threshold = str(number(threshold, 'Alerta de saldo baixo', places=3))
        with transaction(self.db):
            for key, value in (('markup_percent', markup), ('low_filament_grams', threshold)):
                previous = self.storage.get(key)
                self.db.execute('UPDATE settings SET value=? WHERE key=?', (json.dumps(value), key))
                self.storage.audit('configuração', key, previous, value)

    def low_filaments(self):
        threshold = grams_mg(self.storage.get('low_filament_grams', '100'))
        return [row for row in self.rows('filaments') if row['state'] != 'finished' and row['remaining_mg'] is not None and row['remaining_mg'] <= threshold]

    def estimate(self, printer_id, minutes, selections, auxiliary='0', quantity=1, markup=None, final=None):
        printer = self.get('printers', printer_id)
        if printer['archived'] or printer['status'] != 'operational':
            raise ValueError('Selecione uma impressora operacional e não arquivada.')
        filaments = []
        seen = set()
        for filament_id, grams in selections:
            if filament_id in seen:
                raise ValueError('O mesmo carretel foi adicionado duas vezes. Some o consumo em uma linha.')
            seen.add(filament_id)
            spool = self.get('filaments', filament_id)
            if spool['archived'] or spool['state'] == 'finished':
                raise ValueError('Filamento finalizado ou arquivado não pode ser selecionado.')
            filaments.append({**spool, 'grams': grams})
        if not filaments:
            raise ValueError('Adicione pelo menos um filamento.')
        return calculate(printer, minutes, filaments, auxiliary, quantity,
                         self.storage.get('markup_percent', '200') if markup is None else markup, final)

    def save_calculation(self, title, printer_id, minutes, selections, auxiliary='0', quantity=1, markup=None, final=None):
        title = required(title, 'Descrição do cálculo')
        snapshot = self.estimate(printer_id, minutes, selections, auxiliary, quantity, markup, final)
        with transaction(self.db):
            result = self.db.execute('INSERT INTO calculations(created_at,title,printer_id,planned) VALUES(?,?,?,?)',
                                    (now(), title, printer_id, json.dumps(snapshot, ensure_ascii=False))).lastrowid
            if selections:
                self.db.execute("INSERT INTO settings VALUES('last_filament_id',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (json.dumps(selections[-1][0]),))
            self.storage.audit('custo previsto', f'calculations:{result}', None, snapshot)
        return result

    def calculations(self):
        return [dict(row) for row in self.db.execute('SELECT * FROM calculations ORDER BY id DESC')]

    def confirm_actual(self, identifier, minutes, consumptions, auxiliary='0', quantity=None):
        # Atomic and one-time: never reduce balances twice or edit frozen snapshots.
        with transaction(self.db):
            record = self.get('calculations', identifier)
            if record['actual'] is not None:
                raise ValueError('O custo real já foi confirmado. Não é possível consolidar duas vezes.')
            planned = json.loads(record['planned'])
            expected_ids = {row['id'] for row in planned['filaments']}
            if set(consumptions) != expected_ids:
                raise ValueError('Informe o consumo confirmado de cada carretel previsto.')
            rows = [{**row, 'grams': consumptions[row['id']]} for row in planned['filaments']]
            actual = calculate(planned['printer'], minutes, rows, auxiliary,
                               planned['quantity'] if quantity is None else quantity,
                               planned['markup'], planned['final_total'], actual=True)
            # Saved reference rates preserve comparison; quantities/time are actual.
            for row in actual['filaments']:
                spool = self.get('filaments', row['id'])
                consumed = grams_mg(row['grams'])
                if consumed and (spool['archived'] or spool['state'] == 'finished'):
                    raise ValueError('Restaure/reabra o carretel antes de confirmar consumo.')
                previous = spool['remaining_mg']
                remaining = None if previous is None else previous - consumed
                if remaining is not None and remaining < 0:
                    raise ValueError(f"Saldo insuficiente para {spool['name']}. Corrija o saldo com justificativa, se necessário.")
                self.db.execute('UPDATE filaments SET remaining_mg=?,state=? WHERE id=?',
                                (remaining, 'finished' if remaining == 0 else 'open' if consumed else spool['state'], row['id']))
                self.db.execute('INSERT INTO filament_consumption(calculation_id,filament_id,consumed_mg,previous_mg,remaining_mg) VALUES(?,?,?,?,?)',
                                (identifier, row['id'], consumed, previous, remaining))
                if stock_supported(self.storage):
                    stock_record(self.storage, 'consumption', 'filament', row['id'], -consumed, previous, remaining,
                                 f'Cálculo confirmado {identifier}', f'calculation:{identifier}:{row["id"]}', cents(row['cost']))
                self.storage.audit('consumo confirmado', f"filaments:{row['id']}", previous, remaining,
                                   f'Cálculo {identifier}: {row["grams"]} g' + ('; saldo desconhecido preservado' if previous is None else ''))
            previous_minutes = self.get('printers', record['printer_id'])['accumulated_minutes']
            self.storage.audit('tempo confirmado', f"printers:{record['printer_id']}", previous_minutes, previous_minutes + actual['minutes'], f'Cálculo {identifier}')
            self.db.execute('UPDATE printers SET accumulated_minutes=accumulated_minutes+? WHERE id=?',
                            (actual['minutes'], record['printer_id']))
            self.db.execute('UPDATE calculations SET actual=?,confirmed_at=? WHERE id=?',
                            (json.dumps(actual, ensure_ascii=False), now(), identifier))
            self.storage.audit('custo real confirmado', f'calculations:{identifier}', planned, actual)
        return compare(planned, actual)
