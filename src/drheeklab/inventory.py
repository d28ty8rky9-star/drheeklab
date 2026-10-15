"""Physical stock, reservations and one-time losses; no cash/sale side effects."""
from datetime import date
from decimal import Decimal
import json
from .catalog import Catalog, required, optional_date
from .products import Products
from .pricing import number, cents, integer, money, grams_mg
from .storage import now
from .journal import record
from .transactions import transaction

PIECE_STATES = {'available': 'Disponível', 'reserved': 'Reservada', 'personal': 'Uso pessoal',
                'quarantine': 'Aguardando verificação', 'discarded': 'Descartada', 'issued': 'Baixada'}


class Inventory:
    def __init__(self, storage):
        self.storage, self.db = storage, storage.db
        self.products = Products(storage)

    def get(self, table, identifier):
        if table not in ('materials', 'pieces', 'receipts', 'reservations', 'losses'):
            raise ValueError('Registro de estoque inválido.')
        row = self.db.execute(f'SELECT * FROM {table} WHERE id=?', (identifier,)).fetchone()
        if row is None:
            raise ValueError('Registro de estoque não encontrado.')
        return dict(row)

    def materials(self, archived=False):
        return [dict(row) for row in self.db.execute('SELECT * FROM materials WHERE archived=? ORDER BY id', (int(archived),))]

    def save_material(self, data, identifier=None, reason=''):
        name = required(data.get('name', ''), 'Nome')
        unit = required(data.get('unit', ''), 'Unidade')
        balance = grams_mg(data.get('balance', '0'), 'Saldo')
        rate = str(number(data.get('reference_per_unit', '0'), 'Referência por unidade', places=6))
        reason = required(reason, 'Justificativa')
        with transaction(self.db):
            previous = self.get('materials', identifier) if identifier is not None else None
            if previous and previous['archived']:
                raise ValueError('Restaure o material antes de editar.')
            if previous and previous['unit'] != unit and previous['balance_milli']:
                raise ValueError('Unidade não pode ser alterada com saldo; cadastre outro material.')
            if previous is None:
                identifier = self.db.execute('INSERT INTO materials(name,unit,balance_milli,reference_per_unit) VALUES(?,?,?,?)',
                                             (name, unit, balance, rate)).lastrowid
            else:
                self.db.execute('UPDATE materials SET name=?,unit=?,balance_milli=?,reference_per_unit=? WHERE id=?',
                                (name, unit, balance, rate, identifier))
            current = self.get('materials', identifier)
            if previous is None or previous['balance_milli'] != balance:
                record(self.storage, 'opening' if previous is None else 'adjustment', 'material', identifier,
                       balance - (previous['balance_milli'] if previous else 0),
                       previous['balance_milli'] if previous else None, balance, reason)
            self.storage.audit('material:cadastro' if previous is None else 'material:edição', f'materials:{identifier}', previous, current, reason)
        return identifier

    def archive_material(self, identifier, archived, reason):
        required(reason, 'Justificativa')
        with transaction(self.db):
            before = self.get('materials', identifier)
            self.db.execute('UPDATE materials SET archived=? WHERE id=?', (int(archived), identifier))
            self.storage.audit('material:arquivar' if archived else 'material:restaurar', f'materials:{identifier}', before, self.get('materials', identifier), reason)

    def consume_material(self, identifier, quantity, reason, operation_key):
        quantity_milli = grams_mg(quantity, 'Quantidade')
        if quantity_milli <= 0:
            raise ValueError('Informe uma quantidade positiva.')
        required(reason, 'Justificativa'); required(operation_key, 'Identificador da operação')
        with transaction(self.db):
            row = self.get('materials', identifier)
            if row['archived'] or row['balance_milli'] < quantity_milli:
                raise ValueError('Material arquivado ou saldo insuficiente.')
            remaining = row['balance_milli'] - quantity_milli
            cost = cents(str(money(Decimal(quantity_milli) / 1000 * Decimal(row['reference_per_unit']))))
            self.db.execute('UPDATE materials SET balance_milli=? WHERE id=?', (remaining, identifier))
            record(self.storage, 'consumption', 'material', identifier, -quantity_milli, row['balance_milli'], remaining,
                   reason, operation_key, cost)
            self.storage.audit('material:consumo', f'materials:{identifier}', row['balance_milli'], remaining, reason)
        return cost

    def published_piece(self, piece_id):
        return not self.db.execute('SELECT 1 FROM production_pieces pp JOIN production_entries e ON e.id=pp.entry_id JOIN recipe_orders ro ON ro.op_id=e.op_id LEFT JOIN production_completions c ON c.op_id=e.op_id WHERE pp.piece_id=? AND c.op_id IS NULL',(piece_id,)).fetchone()

    def summary(self):
        result = []
        # Archived entries remain visible with stock: physical goods never disappear.
        rows = self.db.execute('SELECT v.*,p.code,p.name AS product_name,p.archived AS product_archived FROM variants v JOIN products p ON p.id=v.product_id ORDER BY p.id,v.id').fetchall()
        for variant in rows:
            row = dict(variant)
            states = {}
            for piece in self.pieces(row['id']):states[piece['state']]=states.get(piece['state'],0)+1
            row.update({state: states.get(state, 0) for state in PIECE_STATES})
            row['physical'] = sum(row[state] for state in ('available', 'reserved', 'personal', 'quarantine'))
            result.append(row)
        return result

    def pieces(self, variant_id=None):
        sql = 'SELECT p.*,v.name AS variant_name,m.code,m.name AS product_name FROM pieces p JOIN variants v ON v.id=p.variant_id JOIN products m ON m.id=v.product_id'
        visible='NOT EXISTS(SELECT 1 FROM production_pieces pp JOIN production_entries e ON e.id=pp.entry_id JOIN recipe_orders ro ON ro.op_id=e.op_id LEFT JOIN production_completions c ON c.op_id=e.op_id WHERE pp.piece_id=p.id AND c.op_id IS NULL)'
        return [dict(row) for row in self.db.execute(sql+' WHERE '+visible+(' AND p.variant_id=?' if variant_id is not None else '')+' ORDER BY p.id',(variant_id,) if variant_id is not None else ())]

    def receive_accessory(self, **values):
        with transaction(self.db):
            receipt,pieces=self.receive_purchased(**values)
            product=self.products.get('variants',self.get('receipts',receipt)['variant_id'])['product_id']
            self.db.execute('INSERT INTO accessory_products VALUES(?)',(product,))
            self.storage.audit('estoque:acessório',f'products:{product}',None,{'receipt':receipt},values['source'])
        return receipt,pieces

    def receive_purchased(self, name, quantity, source, state, condition, operation_key, total_cost='0', reviewer='', description='', suggested_price=''):
        """Create a stock-only saleable item and receipt atomically."""
        with transaction(self.db):
            product=self.products.save({'name':name,'description':description,'category':'decorative','suggested_price':suggested_price})
            self.db.execute('INSERT INTO purchased_products VALUES(?)',(product,))
            variant=self.products.variants(product)[0]['id']
            receipt,pieces=self.receive(variant,quantity,source,state,condition,operation_key,total_cost=total_cost,reviewer=reviewer)
            self.storage.audit('estoque:peça comprada',f'products:{product}',None,{'receipt':receipt,'pieces':pieces},source)
        return receipt,pieces

    def receive(self, variant_id, quantity, source, state, condition, operation_key, total_cost='0', calculation_id=None, reviewer=''):
        quantity = integer(quantity, 'Quantidade', minimum=1)
        if quantity > 10000:
            raise ValueError('Registre no máximo 10.000 peças por entrada.')
        if state not in ('available', 'personal', 'quarantine'):
            raise ValueError('Destino da entrada inválido.')
        condition = required(condition, 'Condição das peças')
        source = required(source, 'Origem e justificativa da entrada')
        required(operation_key, 'Identificador da operação')
        if state == 'available':
            required(reviewer, 'Responsável pela verificação prévia')
        with transaction(self.db):
            self.products.active_variant(variant_id)
            snapshot, basis = None, 'manual'
            total = cents(total_cost, 'Custo total existente')
            if calculation_id is not None:
                calculation = Catalog(self.storage).get('calculations', calculation_id)
                if calculation['actual'] is None:
                    raise ValueError('Confirme o custo real antes de registrar peças produzidas.')
                snapshot = calculation['actual']
                actual = json.loads(snapshot)
                if quantity != actual['quantity']:
                    raise ValueError('A entrada deve corresponder à quantidade confirmada do cálculo. Registre perdas pelas peças físicas sem duplicar o custo.')
                acquisition = actual.get('acquisition_production_cost')
                basis = 'acquisition' if acquisition is not None else 'reference'
                total = cents(acquisition if acquisition is not None else actual['total_cost'])
            receipt_id = self.db.execute('INSERT INTO receipts(variant_id,created_at,quantity,total_cost_cents,source,calculation_id,cost_basis,cost_snapshot,operation_key) VALUES(?,?,?,?,?,?,?,?,?)',
                (variant_id, now(), quantity, total, source, calculation_id, basis, snapshot, operation_key)).lastrowid
            unit, remainder = divmod(total, quantity)
            ids = []
            for index in range(quantity):
                cost = unit + int(index < remainder)
                piece_id = self.db.execute('INSERT INTO pieces(receipt_id,variant_id,state,condition,unit_cost_cents) VALUES(?,?,?,?,?)',
                                          (receipt_id, variant_id, state, condition, cost)).lastrowid
                ids.append(piece_id)
                if state == 'available':
                    self.db.execute('INSERT INTO piece_reviews(piece_id,created_at,reviewer,condition,result) VALUES(?,?,?,?,?)',
                                    (piece_id, now(), reviewer, condition, 'approved'))
                record(self.storage, 'receipt', 'piece', piece_id, 1000, None, state, source,
                       f'receipt:{receipt_id}:{piece_id}', cost)
            self.storage.audit('estoque:entrada', f'receipts:{receipt_id}', None, self.get('receipts', receipt_id), source)
        return receipt_id, ids

    def review(self, piece_ids, result, condition, reviewer):
        if result not in ('approved', 'rejected'):
            raise ValueError('Resultado inválido.')
        required(condition, 'Condição após a verificação'); required(reviewer, 'Responsável')
        ids = self._unique_ids(piece_ids)
        with transaction(self.db):
            for identifier in ids:
                row = self.get('pieces', identifier)
                if self.db.execute('SELECT 1 FROM production_pieces WHERE piece_id=?',(identifier,)).fetchone():
                    raise ValueError('Peça de OP exige inspeção individual com três fotos em Produção.')
                self.products.active_variant(row['variant_id'])
                if row['state'] not in ('personal', 'quarantine', 'available'):
                    raise ValueError('Peça reservada, baixada ou descartada não pode ser liberada por esta verificação.')
                state = 'available' if result == 'approved' else 'quarantine'
                review_id = self.db.execute('INSERT INTO piece_reviews(piece_id,created_at,reviewer,condition,result) VALUES(?,?,?,?,?)',
                                            (identifier, now(), reviewer, condition, result)).lastrowid
                self.db.execute('UPDATE pieces SET state=?,condition=? WHERE id=?', (state, condition, identifier))
                record(self.storage, 'review', 'piece', identifier, 0, row['state'], state, condition, f'review:{review_id}')
                self.storage.audit('estoque:verificação', f'pieces:{identifier}', row, self.get('pieces', identifier), f'{reviewer}: {condition}')

    @staticmethod
    def _unique_ids(piece_ids):
        ids = list(piece_ids)
        if not ids or len(ids) != len(set(ids)):
            raise ValueError('Selecione peças únicas para a operação.')
        return ids

    def reservations(self):
        return [dict(row) for row in self.db.execute('SELECT r.*,v.name AS variant_name,p.code,p.name AS product_name FROM reservations r JOIN variants v ON v.id=r.variant_id JOIN products p ON p.id=v.product_id ORDER BY r.id DESC')]

    def reserve(self, variant_id, quantity, reference, operation_key, *, piece_ids=None):
        quantity = integer(quantity, 'Quantidade', minimum=1)
        required(reference, 'Referência da reserva'); required(operation_key, 'Identificador da operação')
        with transaction(self.db):
            self.products.active_variant(variant_id)
            pieces = self.db.execute("SELECT id FROM pieces WHERE variant_id=? AND state='available' ORDER BY id LIMIT ?", (variant_id, quantity)).fetchall()
            if piece_ids is not None:
                ids=self._unique_ids(piece_ids)
                if len(ids)!=quantity:raise ValueError('Selecione exatamente a quantidade de unidades da venda.')
                pieces=[]
                for identifier in ids:
                    piece=self.get('pieces',identifier)
                    if piece['variant_id']!=variant_id or piece['state']!='available' or not self.published_piece(identifier):raise ValueError('A unidade selecionada não está disponível para venda.')
                    pieces.append(piece)
            if len(pieces) != quantity:
                raise ValueError('Não há quantidade disponível suficiente. Uso pessoal e peças não aprovadas não podem ser reservados.')
            reservation_id = self.db.execute("INSERT INTO reservations(variant_id,reference,quantity,created_at,state,operation_key) VALUES(?,?,?,?,'reserved',?)",
                                             (variant_id, reference, quantity, now(), operation_key)).lastrowid
            from .production import Production
            for row in pieces:
                Production(self.storage).verify_release(row['id'])
                self.db.execute("UPDATE pieces SET state='reserved',reservation_id=? WHERE id=?", (reservation_id, row['id']))
                record(self.storage, 'reservation', 'piece', row['id'], 0, 'available', 'reserved', reference,
                       f'reservation:{reservation_id}:{row["id"]}')
            self.storage.audit('estoque:reserva', f'reservations:{reservation_id}', None, self.get('reservations', reservation_id), reference)
        return reservation_id

    def finish_reservation(self, identifier, action, reason, *, order_id=None):
        if action not in ('release', 'issue'):
            raise ValueError('Ação inválida.')
        required(reason, 'Justificativa')
        with transaction(self.db):
            if self.db.execute('PRAGMA user_version').fetchone()[0] >= 4:
                owner = self.db.execute('SELECT order_id FROM order_items WHERE reservation_id=?', (identifier,)).fetchone()
                if owner and owner[0] != order_id:
                    raise ValueError('Reserva vinculada a pedido: libere, cancele ou entregue pela área Vendas.')
            reservation = self.get('reservations', identifier)
            if reservation['state'] != 'reserved':
                raise ValueError('Esta reserva já foi liberada ou baixada.')
            rows = self.db.execute("SELECT * FROM pieces WHERE reservation_id=? AND state='reserved' ORDER BY id", (identifier,)).fetchall()
            if len(rows) != reservation['quantity']:
                raise ValueError('Quantidade reservada inconsistente; não foi alterado nenhum saldo.')
            state = 'available' if action == 'release' else 'issued'
            for row in rows:
                if action=='issue':
                    from .production import Production
                    Production(self.storage).verify_release(row['id'])
                self.db.execute('UPDATE pieces SET state=?,reservation_id=NULL WHERE id=?', (state, row['id']))
                record(self.storage, 'release' if action == 'release' else 'issue', 'piece', row['id'], 0 if action == 'release' else -1000,
                       'reserved', state, reason, f'{action}:{identifier}:{row["id"]}', row['unit_cost_cents'] if action == 'issue' else None)
            self.db.execute('UPDATE reservations SET state=? WHERE id=?', ('released' if action == 'release' else 'issued', identifier))
            self.storage.audit('estoque:liberar' if action == 'release' else 'estoque:baixa', f'reservations:{identifier}', reservation, self.get('reservations', identifier), reason)
        return sum(row['unit_cost_cents'] for row in rows) if action == 'issue' else 0

    def discard_pieces(self, piece_ids, reason, operation_key, occurred_on=None, notes=''):
        ids = self._unique_ids(piece_ids)
        required(reason, 'Motivo do descarte'); required(operation_key, 'Identificador da operação')
        occurred_on = optional_date(occurred_on or date.today().isoformat())
        with transaction(self.db):
            rows = [self.get('pieces', identifier) for identifier in ids]
            for identifier in ids:
                op=self.db.execute('SELECT o.state FROM production_orders o JOIN production_entries e ON e.op_id=o.id JOIN production_pieces pp ON pp.entry_id=e.id WHERE pp.piece_id=?',(identifier,)).fetchone()
                if op and op[0]!='completed':
                    raise ValueError('Conclua a inspeção e a OP antes de descartar peças, preservando o custo das falhas.')
            if any(row['state'] not in ('available', 'personal', 'quarantine') for row in rows):
                raise ValueError('Peça já descartada, baixada ou reservada. Libere reservas antes de descartar.')
            cost = sum(row['unit_cost_cents'] for row in rows)
            loss_id = self.db.execute('INSERT INTO losses(entity_kind,unit,created_at,occurred_on,reason,notes,quantity_milli,cost_cents,cost_basis,operation_key) VALUES(?,?,?,?,?,?,?,?,?,?)',
                ('piece', 'peça', now(), occurred_on, reason, str(notes), len(rows)*1000, cost, 'existing_piece_cost', operation_key)).lastrowid
            for row in rows:
                self.db.execute("UPDATE pieces SET state='discarded' WHERE id=?", (row['id'],))
                self.db.execute('INSERT INTO loss_pieces VALUES(?,?)', (loss_id, row['id']))
                record(self.storage, 'discard', 'piece', row['id'], -1000, row['state'], 'discarded', reason,
                       f'loss:{loss_id}:{row["id"]}', row['unit_cost_cents'])
            self.storage.audit('estoque:descarte', f'losses:{loss_id}', None, self.get('losses', loss_id), reason)
        return loss_id

    def discard_material(self, entity, identifier, quantity, reason, operation_key, occurred_on=None, notes=''):
        if entity not in ('filament', 'material'):
            raise ValueError('Tipo de material inválido.')
        quantity_milli = grams_mg(quantity, 'Quantidade descartada')
        if quantity_milli <= 0:
            raise ValueError('Informe uma quantidade positiva.')
        required(reason, 'Motivo'); required(operation_key, 'Identificador da operação')
        occurred_on = optional_date(occurred_on or date.today().isoformat())
        with transaction(self.db):
            if entity == 'material':
                row = self.get('materials', identifier)
                previous, rate, basis = row['balance_milli'], Decimal(row['reference_per_unit']), 'reference'
                name, field, table = row['name'], 'balance_milli', 'materials'
            else:
                row = Catalog(self.storage).get('filaments', identifier)
                if row['state'] == 'finished':
                    raise ValueError('Carretel finalizado não pode sofrer novo consumo.')
                previous = row['remaining_mg']
                acquisition = Catalog(self.storage).acquisition_per_g(row)
                rate = acquisition if acquisition is not None else Decimal(row['reference_per_g'])
                basis = 'acquisition' if acquisition is not None else 'reference'
                name, field, table = row['name'], 'remaining_mg', 'filaments'
            if row['archived']:
                raise ValueError('Restaure o material antes de movimentar.')
            remaining = None if previous is None else previous - quantity_milli
            if remaining is not None and remaining < 0:
                raise ValueError(f'Saldo insuficiente de {name}.')
            cost = cents(str(money(Decimal(quantity_milli) / 1000 * rate)))
            loss_id = self.db.execute('INSERT INTO losses(entity_kind,unit,created_at,occurred_on,reason,notes,quantity_milli,cost_cents,cost_basis,operation_key) VALUES(?,?,?,?,?,?,?,?,?,?)',
                (entity, row['unit'] if entity == 'material' else 'g', now(), occurred_on, reason, str(notes), quantity_milli, cost, basis, operation_key)).lastrowid
            self.db.execute(f'UPDATE {table} SET {field}=? WHERE id=?', (remaining, identifier))
            if entity == 'filament':
                self.db.execute('UPDATE filaments SET state=? WHERE id=?', ('finished' if remaining == 0 else 'open', identifier))
            record(self.storage, 'discard', entity, identifier, -quantity_milli, previous, remaining, reason,
                   f'loss:{loss_id}', cost)
            self.storage.audit('estoque:perda de material', f'losses:{loss_id}', None, self.get('losses', loss_id), reason)
        return loss_id

    def movements(self):
        return [dict(row) for row in self.db.execute('SELECT * FROM stock_movements ORDER BY id DESC') if row['piece_id'] is None or self.published_piece(row['piece_id'])]

    def losses(self):
        return [dict(row) for row in self.db.execute('SELECT * FROM losses ORDER BY id DESC')]
