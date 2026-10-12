"""Stock journal writes share the caller's transaction; never recognize cash."""
import json
import uuid
from .storage import now


def record(storage, kind, entity, identifier, quantity, previous, current, reason,
           operation_key=None, cost_cents=None):
    columns = {'filament': 'filament_id', 'material': 'material_id', 'piece': 'piece_id'}
    if entity not in columns:
        raise ValueError('Tipo de estoque inválido.')
    storage.db.execute(
        f'INSERT INTO stock_movements(created_at,kind,{columns[entity]},quantity_milli,previous,current,reason,operation_key,cost_cents) VALUES(?,?,?,?,?,?,?,?,?)',
        (now(), kind, identifier, quantity, json.dumps(previous, ensure_ascii=False),
         json.dumps(current, ensure_ascii=False), reason, operation_key or uuid.uuid4().hex, cost_cents))


def supported(storage):
    return storage.db.execute('PRAGMA user_version').fetchone()[0] >= 3
