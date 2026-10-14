"""Read-only, literal search across local records, including archived history."""
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit
from .phase2_ui import table,fill_table,button

SOURCES = (
    ('Cliente',1,"SELECT id,name AS title,phone||' '||email||' '||notes AS detail,CASE archived WHEN 1 THEN 'Arquivado' ELSE 'Ativo' END AS state FROM clients"),
    ('Pedido',1,"SELECT id,code AS title,client_snapshot||' '||notes AS detail,state FROM orders"),
    ('Orçamento',1,"SELECT id,code AS title,client_snapshot||' '||notes AS detail,state FROM quotes"),
    ('Produto',2,"SELECT id,code||' — '||name AS title,description AS detail,CASE archived WHEN 1 THEN 'Arquivado' ELSE 'Ativo' END AS state FROM products WHERE id NOT IN (SELECT product_id FROM purchased_products)"),
    ('Peça comprada',3,"SELECT id,code||' — '||name AS title,description AS detail,CASE archived WHEN 1 THEN 'Arquivado' ELSE 'Ativo' END AS state FROM products WHERE id IN (SELECT product_id FROM purchased_products)"),
    ('Projeto',2,"SELECT v.id,p.code||' — '||v.original_name AS title,p.name||' / versão '||v.version||' / '||v.notes AS detail,CASE v.archived WHEN 1 THEN 'Arquivado' ELSE 'Ativo' END AS state FROM project_versions v JOIN products p ON p.id=v.product_id"),
    ('Filamento',3,"SELECT id,brand||' / '||name AS title,material||' '||color AS detail,CASE archived WHEN 1 THEN 'Arquivado' ELSE state END AS state FROM filaments"),
    ('Produção',2,"SELECT o.id,o.code AS title,o.responsible||' '||o.parameters||' '||COALESCE((SELECT group_concat(p.name,' ') FROM production_entries e JOIN variants v ON v.id=e.variant_id JOIN products p ON p.id=v.product_id WHERE e.op_id=o.id),'') AS detail,o.state FROM production_orders o"),
)

def search(storage,term,limit=200):
    term=term.strip().casefold()
    if not term:return []
    if not 1<=limit<=1000:raise ValueError('Limite de busca inválido')
    storage.db.create_function('search_casefold',1,lambda v:str(v or '').casefold(),deterministic=True)
    rows=[]
    for kind,area,query in SOURCES:
        results=storage.db.execute('SELECT * FROM ('+query+') WHERE instr(search_casefold(title||\' \'||detail),?)>0 ORDER BY id DESC LIMIT ?', (term,limit-len(rows)))
        rows.extend(dict(r,kind=kind,area=area) for r in results)
        if len(rows)>=limit:break
    return rows

class SearchDialog(QDialog):
    def __init__(self,storage,parent=None):
        super().__init__(parent);self.storage=storage;self.setWindowTitle('Busca global');self.resize(1000,600)
        box=QVBoxLayout(self);self.term=QLineEdit();self.term.setPlaceholderText('Nome, código, telefone ou arquivo — busca literal')
        row=QHBoxLayout();box.addLayout(row);row.addWidget(self.term);button('Pesquisar',self.refresh,row);self.term.returnPressed.connect(self.refresh)
        self.listing=table(['Tipo','ID','Registro','Detalhes','Estado']);box.addWidget(self.listing)
        box.addWidget(QLabel('Até 200 resultados. Refine o texto para localizar outros registros. Arquivados permanecem identificados.'))
        button('Abrir área do selecionado',self.open_area,box);self.rows=[]
    def refresh(self):
        self.rows=search(self.storage,self.term.text());fill_table(self.listing,[[r[k] for k in ('kind','id','title','detail','state')] for r in self.rows])
    def open_area(self):
        index=self.listing.currentRow()
        if index<0:return
        self.parent().navigate(self.rows[index]['area']);self.accept()
