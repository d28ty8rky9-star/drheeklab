"""Products and immutable owned media; no automatic STL/3MF slicing claims."""
from pathlib import Path
import json
import shutil
import subprocess
import uuid
from decimal import Decimal
from PySide6.QtGui import QImageReader
from .catalog import Catalog, required
from .pricing import cents, integer,brl
from .storage import now
from .transactions import transaction
from .backup import digest

CATEGORIES = {'decorative': 'Decorativo', 'functional': 'Funcional', 'mixed': 'Misto'}


def optional_money(value):
    return None if value in (None, '') else cents(value)


class Products:
    def __init__(self, storage):
        self.storage, self.db = storage, storage.db

    def get(self, table, identifier):
        if table not in ('products', 'variants', 'product_photos', 'project_versions'):
            raise ValueError('Registro de produto inválido.')
        row = self.db.execute(f'SELECT * FROM {table} WHERE id=?', (identifier,)).fetchone()
        if row is None:
            raise ValueError('Registro não encontrado.')
        return dict(row)

    def active_product(self, identifier):
        product = self.get('products', identifier)
        if product['archived']:
            raise ValueError('Restaure o produto antes de alterar seus dados ou estoque.')
        return product

    def active_variant(self, identifier):
        variant = self.get('variants', identifier)
        self.active_product(variant['product_id'])
        if variant['archived']:
            raise ValueError('Restaure a variante antes de movimentar seu estoque.')
        return variant

    def search(self, text='', category=None, archived=False, *, include_stock=False):
        # Literal match, including accented text, avoids SQL LIKE wildcard surprises.
        rows = [dict(row) for row in self.db.execute('SELECT * FROM products WHERE archived=? ORDER BY id', (int(archived),))]
        term = text.casefold().strip()
        result = []
        for row in rows:
            if not include_stock and self.db.execute('SELECT 1 FROM purchased_products WHERE product_id=?',(row['id'],)).fetchone():continue
            variants = self.variants(row['id'])
            searchable = ' '.join(str(row[k]) for k in ('code', 'name', 'description', 'quality_notes'))
            searchable += ' ' + ' '.join(' '.join(str(v[k]) for k in ('name', 'size', 'color', 'material')) for v in variants)
            if (not term or term in searchable.casefold()) and (category is None or row['category'] == category):
                result.append(row)
        return result

    def production_cost_label(self, product_id):
        costs=[]
        for row in self.db.execute('SELECT r.data FROM production_recipes r JOIN variants v ON v.id=r.variant_id WHERE v.product_id=? AND v.archived=0',(product_id,)):
            estimate=json.loads(row[0])['estimate'];value=estimate.get('acquisition_production_cost')
            costs.append(Decimal(value if value is not None else estimate['total_cost']))
        if not costs:return 'Ficha não preenchida'
        lower,upper=min(costs),max(costs)
        return brl(lower) if lower==upper else brl(lower)+' a '+brl(upper)+' (variantes)'

    def save(self, data, identifier=None):
        category = data.get('category', 'decorative')
        if category not in CATEGORIES:
            raise ValueError('Categoria inválida.')
        existing = self.get('products', identifier) if identifier is not None else {}
        for key, table in (('printer_id', 'printers'), ('filament_id', 'filaments')):
            if data.get(key) is not None:
                recommendation = Catalog(self.storage).get(table, data[key])
                if recommendation['archived'] and data[key] != existing.get(key):
                    raise ValueError('Selecione uma recomendação não arquivada.')
        values = {'name': required(data.get('name', ''), 'Nome'), 'description': str(data.get('description', '')).strip(),
                  'category': category, 'printer_id': data.get('printer_id'), 'filament_id': data.get('filament_id'),
                  'settings': str(data.get('settings', '')).strip(),
                  'estimated_minutes': integer(data.get('estimated_minutes', 0), 'Tempo estimado'),
                  'planned_cost_cents': optional_money(data.get('planned_cost')),
                  'suggested_price_cents': optional_money(data.get('suggested_price')),
                  'quality_notes': str(data.get('quality_notes', '')).strip()}
        with transaction(self.db):
            previous = self.active_product(identifier) if identifier is not None else None
            if previous is None:
                identifier = self.db.execute(f"INSERT INTO products({','.join(values)}) VALUES({','.join('?' for _ in values)})", tuple(values.values())).lastrowid
                self.db.execute("INSERT INTO variants(product_id,name) VALUES(?,'Padrão')", (identifier,))
            else:
                self.db.execute(f"UPDATE products SET {','.join(key+'=?' for key in values)} WHERE id=?", (*values.values(), identifier))
            self.storage.audit('produto:cadastro' if previous is None else 'produto:edição', f'products:{identifier}', previous, self.get('products', identifier))
        return identifier

    def variants(self, product_id, archived=False):
        return [dict(row) for row in self.db.execute('SELECT * FROM variants WHERE product_id=? AND archived=? ORDER BY id', (product_id, int(archived)))]

    def all_variants(self):
        return [dict(row) for row in self.db.execute("SELECT v.*,p.code,p.name AS product_name FROM variants v JOIN products p ON p.id=v.product_id WHERE v.archived=0 AND p.archived=0 ORDER BY p.id,v.id")]

    def save_variant(self, product_id, data, identifier=None):
        self.active_product(product_id)
        values = {'product_id': product_id, 'name': required(data.get('name', ''), 'Nome da variante'),
                  'size': str(data.get('size', '')).strip(), 'color': str(data.get('color', '')).strip(),
                  'material': str(data.get('material', '')).strip(),
                  'planned_cost_cents': optional_money(data.get('planned_cost')),
                  'suggested_price_cents': optional_money(data.get('suggested_price')),
                  'calculation_id': data.get('calculation_id'), 'cost_snapshot': None}
        if values['calculation_id'] is not None:
            record = Catalog(self.storage).get('calculations', values['calculation_id'])
            snapshot = json.loads(record['planned'])
            values['planned_cost_cents'] = cents(snapshot['unit_cost'])
            values['suggested_price_cents'] = cents(snapshot['suggested_unit'])
            values['cost_snapshot'] = record['planned']
        with transaction(self.db):
            previous = self.active_variant(identifier) if identifier is not None else None
            if previous and previous['product_id'] != product_id:
                raise ValueError('A variante pertence a outro produto.')
            if previous is None:
                identifier = self.db.execute(f"INSERT INTO variants({','.join(values)}) VALUES({','.join('?' for _ in values)})", tuple(values.values())).lastrowid
            else:
                self.db.execute(f"UPDATE variants SET {','.join(key+'=?' for key in values)} WHERE id=?", (*values.values(), identifier))
            self.storage.audit('variante:cadastro' if previous is None else 'variante:edição', f'variants:{identifier}', previous, self.get('variants', identifier))
        return identifier

    def archive(self, table, identifier, archived, reason):
        if table not in ('products', 'variants'):
            raise ValueError('Cadastro inválido.')
        required(reason, 'Justificativa')
        with transaction(self.db):
            previous = self.get(table, identifier)
            condition = 'p.variant_id=?' if table == 'variants' else 'v.product_id=?'
            if archived and self.db.execute(f"SELECT 1 FROM pieces p JOIN variants v ON v.id=p.variant_id WHERE {condition} AND p.state='reserved' LIMIT 1", (identifier,)).fetchone():
                raise ValueError('Libere as reservas antes de arquivar.')
            self.db.execute(f'UPDATE {table} SET archived=? WHERE id=?', (int(archived), identifier))
            self.storage.audit('produto:arquivar' if archived else 'produto:restaurar', f'{table}:{identifier}', previous, self.get(table, identifier), reason)

    def media(self, product_id, kind, archived=False):
        table = self._media_table(kind)
        return [dict(row) for row in self.db.execute(f'SELECT * FROM {table} WHERE product_id=? AND archived=? ORDER BY id DESC', (product_id,int(archived)))]

    @staticmethod
    def _media_table(kind):
        if kind not in ('photo', 'project'):
            raise ValueError('Tipo de arquivo inválido.')
        return 'product_photos' if kind == 'photo' else 'project_versions'

    def import_media(self, product_id, source, kind, notes=''):
        self.active_product(product_id)
        source = Path(source)
        if not source.is_file() or source.stat().st_size == 0:
            raise ValueError('Selecione um arquivo existente e não vazio.')
        suffix = source.suffix.lower()
        folder = 'Fotos dos Produtos' if kind == 'photo' else 'Projetos STL e 3MF'
        table = self._media_table(kind)
        if kind == 'photo':
            if suffix not in ('.png', '.jpg', '.jpeg') or QImageReader(str(source)).read().isNull():
                raise ValueError('Foto inválida. Use PNG ou JPEG real.')
        elif suffix not in ('.stl', '.3mf'):
            raise ValueError('Projeto deve ser STL ou 3MF. Dados de fatiamento são registrados manualmente.')
        directory = (self.storage.home / folder).resolve()
        if not directory.is_relative_to(self.storage.home.resolve()):
            raise ValueError('Pasta de arquivos fora do armazenamento permitido.')
        target = directory / (uuid.uuid4().hex + suffix)
        created = False
        # Exclusive creation; clean up only this import if its transaction fails.
        try:
            with source.open('rb') as input_file, target.open('xb') as output_file:
                created = True
                shutil.copyfileobj(input_file, output_file)
            checksum = digest(target)
            with transaction(self.db):
                if kind == 'photo':
                    primary = not self.db.execute('SELECT 1 FROM product_photos WHERE product_id=? AND is_primary=1', (product_id,)).fetchone()
                    identifier = self.db.execute('INSERT INTO product_photos(product_id,path,original_name,sha256,created_at,is_primary) VALUES(?,?,?,?,?,?)',
                        (product_id, target.relative_to(self.storage.home.resolve()).as_posix(), source.name, checksum, now(), int(primary))).lastrowid
                else:
                    version = self.db.execute('SELECT COALESCE(MAX(version),0)+1 FROM project_versions WHERE product_id=?', (product_id,)).fetchone()[0]
                    self.db.execute('UPDATE project_versions SET is_preferred=0 WHERE product_id=?', (product_id,))
                    identifier = self.db.execute('INSERT INTO project_versions(product_id,version,path,original_name,sha256,created_at,notes,is_preferred) VALUES(?,?,?,?,?,?,?,1)',
                        (product_id, version, target.relative_to(self.storage.home.resolve()).as_posix(), source.name, checksum, now(), str(notes))).lastrowid
                self.storage.audit('arquivo:importação', f'{table}:{identifier}', None, self.get(table, identifier))
            return identifier
        except Exception:
            if created:
                target.unlink(missing_ok=True)
            raise

    def choose_media(self, product_id, identifier, kind):
        self.active_product(product_id)
        table = self._media_table(kind)
        row = self.get(table, identifier)
        if row['product_id'] != product_id:
            raise ValueError('Arquivo pertence a outro produto.')
        if row['archived']:
            raise ValueError('Restaure o arquivo antes de defini-lo como principal/preferencial.')
        column = 'is_primary' if kind == 'photo' else 'is_preferred'
        with transaction(self.db):
            previous = self.db.execute(f'SELECT id FROM {table} WHERE product_id=? AND {column}=1', (product_id,)).fetchone()
            self.db.execute(f'UPDATE {table} SET {column}=0 WHERE product_id=?', (product_id,))
            self.db.execute(f'UPDATE {table} SET {column}=1 WHERE id=?', (identifier,))
            self.storage.audit('foto principal' if kind == 'photo' else 'versão preferencial', f'{table}:{identifier}', previous[0] if previous else None, self.get(table, identifier))

    def media_path(self, identifier, kind, verify=True):
        row = self.get(self._media_table(kind), identifier)
        folder = 'Fotos dos Produtos' if kind == 'photo' else 'Projetos STL e 3MF'
        relative = Path(row['path'])
        root = self.storage.home.resolve()
        path = (root / relative).resolve()
        if relative.is_absolute() or len(relative.parts) != 2 or relative.parts[0] != folder or not path.is_relative_to(root):
            raise ValueError('Caminho de arquivo fora do armazenamento permitido.')
        if not path.is_file():
            raise ValueError('Arquivo vinculado não encontrado. Restaure um backup completo.')
        if verify and digest(path) != row['sha256']:
            raise ValueError('Arquivo foi alterado fora do aplicativo; importe uma nova versão.')
        return path

    def open_project(self, identifier):
        path = self.media_path(identifier, 'project')
        configured = self.storage.get('bambu_studio_path')
        candidates = [configured] if configured else []
        candidates.extend([r'C:\Program Files\Bambu Studio\bambu-studio.exe', shutil.which('bambu-studio')])
        executable = next((str(Path(candidate)) for candidate in candidates if candidate and Path(candidate).is_file()), None)
        if not executable:
            raise ValueError('Bambu Studio não encontrado. Configure o executável em Configurações; a integração é opcional.')
        subprocess.Popen([executable, str(path)], shell=False)
