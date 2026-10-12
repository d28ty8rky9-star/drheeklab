"""Logical archive/recovery and queryable audit, preserving historical links."""
from .catalog import Catalog,required
from .products import Products
from .inventory import Inventory
from .sales import Sales
from .finance import Finance
from .documents import Documents
from .transactions import transaction

TABLES={'products':('Produtos','name'),'variants':('Variantes','name'),'printers':('Impressoras','identifier'),'filaments':('Filamentos','name'),'materials':('Materiais auxiliares','name'),'clients':('Clientes','name'),'expense_categories':('Categorias de despesas','name'),'product_photos':('Fotos de produto','original_name'),'project_versions':('Versões STL/3MF','original_name'),'generated_documents':('PDFs emitidos','title')}

class Lifecycle:
    def __init__(self,storage):self.storage,self.db=storage,storage.db
    def rows(self,archived=True):
        rows=[]
        for table,(label,column) in TABLES.items():
            for r in self.db.execute(f'SELECT * FROM {table} WHERE archived=?',(int(archived),)):
                rows.append({'table':table,'type':label,'id':r['id'],'name':r[column]})
        return rows
    def archive(self,table,identifier,archived,reason):
        if table not in TABLES:raise ValueError('Tipo de recuperação inválido.')
        required(reason,'Justificativa')
        with transaction(self.db):
            old=self.db.execute(f'SELECT * FROM {table} WHERE id=?',(identifier,)).fetchone()
            if not old:raise ValueError('Registro não encontrado.')
            if bool(old['archived'])==bool(archived):raise ValueError('Registro já está nesta condição.')
            if table=='variants' and not archived:Products(self.storage).active_product(old['product_id'])
            if table in ('products','variants'):Products(self.storage).archive(table,identifier,archived,reason)
            elif table in ('printers','filaments'):Catalog(self.storage).archive(table,identifier,archived,reason)
            elif table=='materials':Inventory(self.storage).archive_material(identifier,archived,reason)
            elif table=='clients':Sales(self.storage).archive_client(identifier,archived,reason)
            elif table=='expense_categories':Finance(self.storage).archive_category(identifier,archived,reason)
            elif table=='generated_documents':Documents(self.storage).archive(identifier,archived,reason)
            else:
                Products(self.storage).active_product(old['product_id'])
                if not archived:Products(self.storage).media_path(identifier,'photo' if table=='product_photos' else 'project')
                if table=='project_versions' and archived and self.db.execute("SELECT 1 FROM production_entries e JOIN production_orders o ON o.id=e.op_id WHERE e.project_id=? AND o.state!='completed'",(identifier,)).fetchone():raise ValueError('Versão usada por OP ativa não pode ser arquivada.')
                self.db.execute(f'UPDATE {table} SET archived=? WHERE id=?',(int(archived),identifier))
                self.storage.audit('mídia arquivada' if archived else 'mídia restaurada',f'{table}:{identifier}',dict(old),dict(self.db.execute(f'SELECT * FROM {table} WHERE id=?',(identifier,)).fetchone()),reason)

    def audit(self,start=None,end=None,operation='',record='',reason='',limit=1000):
        from .finance import period
        start,end=period(start,end)
        if not isinstance(limit,int) or not 1<=limit<=10000:raise ValueError('Limite de auditoria inválido.')
        rows=self.db.execute('SELECT * FROM audit WHERE substr(created_at,1,10) BETWEEN ? AND ? ORDER BY id DESC',(start,end))
        result=[]
        for row in rows:
            r=dict(row)
            if operation.casefold() in r['operation'].casefold() and record.casefold() in r['record'].casefold() and reason.casefold() in (r['reason'] or '').casefold():result.append(r)
            if len(result)>=limit:break
        return result
