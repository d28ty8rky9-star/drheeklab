"""Desktop production queue, mixed batches and photographic piece inspection."""
from decimal import Decimal
import json
from pathlib import Path
from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QComboBox,QLineEdit,QPushButton,QFileDialog,QMessageBox,QTabWidget,QDialog,QTextEdit,QProgressBar
from .phase2_ui import FormDialog, table, fill_table, button, scroll
from .production import Production, STATES, PRIORITIES, CHECKS, CHECK_LABELS, VIEWS
from .pricing import brl
from .time_input import hours_to_minutes,minutes_to_hours


class EntryEditor(QWidget):
    def __init__(self, production, parent=None, *, recipe=False):
        super().__init__(parent); self.production=production;self.recipe_editor=recipe
        layout=QVBoxLayout(self); row=QHBoxLayout(); layout.addLayout(row)
        self.variant=QComboBox(); self.project=QComboBox(); self.quantity=QLineEdit('1');self.quantity.setMaximumWidth(70)
        if not recipe:
            row.addWidget(QLabel('Modelo/variante'));row.addWidget(self.variant,1);row.addWidget(QLabel('Quantidade'));row.addWidget(self.quantity)
        for p in production.products.search():
            for v in production.products.variants(p['id']):
                if not v['archived']: self.variant.addItem(p['name']+' / '+v['name'],(v['id'],p['id']))
        layout.addWidget(QLabel('Arquivo e versão'));layout.addWidget(self.project)
        self.variant.currentIndexChanged.connect(self.projects);self.projects()
        self.filaments=[];self.filament_layout=QVBoxLayout();layout.addLayout(self.filament_layout)
        button('Adicionar filamento' if recipe else 'Adicionar carretel deste modelo',self.add_spool,layout);self.add_spool()
        aux=QHBoxLayout();layout.addLayout(aux);aux.addWidget(QLabel('Outros custos adicionais (R$ por peça)' if recipe else 'Auxiliares (R$)'));self.aux=QLineEdit('0');aux.addWidget(self.aux)
        self.weight=QLineEdit()
        if not recipe:
            aux.addWidget(QLabel('Peso manual de rateio (opcional)'));aux.addWidget(self.weight)

    def projects(self):
        self.project.clear(); choice=self.variant.currentData()
        if choice:
            for p in self.production.db.execute('SELECT * FROM project_versions WHERE product_id=? AND archived=0 ORDER BY version DESC',(choice[1],)):
                self.project.addItem(f'v{p["version"]} • {p["original_name"]}',p['id'])

    def add_spool(self):
        row=QHBoxLayout();combo=QComboBox();grams=QLineEdit('10');grams.setMaximumWidth(100)
        for f in self.production.catalog.rows('filaments'):
            if f['state']!='finished':combo.addItem(f'{f["id"]} • {f["name"]} / {f["color"]}',f['id'])
        row.addWidget(combo,1);row.addWidget(QLabel('g por peça' if self.recipe_editor else 'g totais'));row.addWidget(grams)
        remove=QPushButton('Remover');row.addWidget(remove);self.filament_layout.addLayout(row)
        data=(combo,grams,row);self.filaments.append(data)
        remove.clicked.connect(lambda:self.remove_spool(data))
        if getattr(self,'changed',None):
            combo.currentIndexChanged.connect(self.changed);grams.textChanged.connect(self.changed);self.changed()

    def remove_spool(self,data):
        self.filaments.remove(data)
        while data[2].count():
            widget=data[2].takeAt(0).widget();widget.hide();widget.deleteLater()
        self.filament_layout.removeItem(data[2])
        if getattr(self,'changed',None):self.changed()

    def value(self):
        if not self.variant.currentData() or not self.project.currentData():raise ValueError('Cadastre um modelo, variante e arquivo STL/3MF em Produtos.')
        return {'variant_id':self.variant.currentData()[0],'project_id':self.project.currentData(),'quantity':self.quantity.text(),'auxiliary':self.aux.text(),'filaments':[(c.currentData(),g.text()) for c,g,_ in self.filaments]}


class OrderDialog(FormDialog):
    def __init__(self, production,parent=None):
        super().__init__('Nova OP — lote simples ou misto',parent);self.production=production;self.resize(850,750)
        self.combo('printer','Impressora',{p['id']:p['identifier'] for p in production.catalog.rows('printers') if p['status']=='operational'},1)
        self.line('hours','Tempo previsto total do lote (horas)','1','Ex.: 1,5 = 1 hora e 30 minutos')
        self.line('responsible','Responsável *');self.line('parameters','Camada, preenchimento, temperaturas, suportes *')
        self.combo('priority','Prioridade',PRIORITIES,'normal')
        choices={None:'Para estoque'}
        for r in production.db.execute("SELECT i.*,o.code FROM order_items i JOIN orders o ON o.id=i.order_id WHERE o.state='approved' ORDER BY i.id DESC"):
            choices[r['id']]=f'{r["code"]} • {r["description"]} • {r["quantity"]} un.'
        self.combo('item','Pedido/item vinculado',choices,None)
        self.line('allocation_reason','Justificativa do rateio manual')
        self.editors=[];self.models=QVBoxLayout();self.form.addRow(self.models)
        add=QPushButton('Adicionar modelo ao lote');add.clicked.connect(self.add);self.form.addRow(add);self.add()

    def add(self):
        editor=EntryEditor(self.production);self.editors.append(editor);self.models.addWidget(editor)
        remove=QPushButton('Remover este modelo');self.models.addWidget(remove)
        def discard():
            self.editors.remove(editor);editor.deleteLater();remove.deleteLater()
        remove.clicked.connect(discard)

    def persist(self):
        v=self.values(); weights=[e.weight.text().strip() for e in self.editors]
        self.saved_id=self.production.create(v['printer'],hours_to_minutes(v['hours']),[e.value() for e in self.editors],v['responsible'],v['parameters'],v['priority'],v['item'],weights if any(weights) else None,v['allocation_reason'])


class ConfirmDialog(FormDialog):
    def __init__(self,production,identifier,parent=None):
        super().__init__('Confirmar tentativa: tempo, consumo e falhas',parent);self.production=production;self.identifier=identifier
        self.line('hours','Tempo real confirmado (horas)',minutes_to_hours(production.elapsed_minutes(identifier)),'Ex.: 1,5 = 1 hora e 30 minutos')
        self.line('progress','Progresso estimado (%)',100);self.line('reason','Motivo das falhas / interrupção')
        self.inputs=[]
        for e in production.entries(identifier):
            self.form.addRow(QLabel(f'{e["product_name"]} / {e["variant_name"]} • {e["quantity"]} planejadas'))
            snap=json.loads(e['planned']);fs={}
            for f in snap['filaments']:
                field=QLineEdit(f['grams']);self.form.addRow(f'{f["name"]} • g reais totais',field);fs[f['id']]=field
            failed=QLineEdit('0');aux=QLineEdit(snap['auxiliary']);loss=QLineEdit()
            self.form.addRow('Peças perdidas sem unidade aproveitável',failed);self.form.addRow('Auxiliares reais (R$)',aux);self.form.addRow('Perda do custo (%) — vazio = proporcional',loss)
            self.inputs.append((e,fs,failed,aux,loss))
        suggest=QPushButton('Sugerir gramas pelo progresso (revisar antes de salvar)');self.form.addRow(suggest);suggest.clicked.connect(self.suggest)
        note=QLabel('Peças com defeito ainda existentes devem seguir para inspeção e reprovação individual. Tempo e consumo incluem falhas; salvar consolida uma única vez.');note.setWordWrap(True);self.form.addRow(note)

    def suggest(self):
        try:
            for (_,fs,_,_,_),values in zip(self.inputs,self.production.suggested_consumption(self.identifier,self.fields['progress'].text())):
                for key,value in values.items():fs[key].setText(value)
        except ValueError as err:self.error.setText(str(err))

    def persist(self):
        v=self.values();entries=[]
        for e,fs,failed,aux,loss in self.inputs:
            value={'entry_id':e['id'],'consumptions':{key:field.text() for key,field in fs.items()},'failed':failed.text(),'auxiliary':aux.text()}
            if loss.text().strip():value['loss_percent']=loss.text()
            entries.append(value)
        self.production.confirm(self.identifier,hours_to_minutes(v['hours']),entries,v['progress'],v['reason'])


class InspectionDialog(FormDialog):
    def __init__(self,production,identifier,piece,parent=None):
        super().__init__(f'FR-001 • Inspeção da peça {piece["id"]}',parent);self.production=production;self.identifier=identifier;self.piece=piece
        self.line('responsible','Responsável *');self.combo('result','Resultado',{'approved':'Aprovada','notes':'Aprovada com observações leves','rejected':'Reprovada'},'approved');self.line('notes','Observações / defeitos')
        self.checks={};self.photos={}
        for key in CHECKS[piece['category']]:
            combo=QComboBox();combo.addItem('Selecione',None)
            for code,label in (('ok','Conforme'),('fail','Reprovado'),('na','Não aplicável')):combo.addItem(label,code)
            reason=QLineEdit();reason.setPlaceholderText('Justificativa para não aplicável/reprovado')
            row=QHBoxLayout();row.addWidget(combo);row.addWidget(reason);self.form.addRow(CHECK_LABELS[key],row);self.checks[key]=(combo,reason)
        for view,label in VIEWS.items():
            field=QLineEdit();field.setReadOnly(True);choose=QPushButton('Selecionar foto');row=QHBoxLayout();row.addWidget(field);row.addWidget(choose)
            choose.clicked.connect(lambda checked=False,k=view:self.choose(k));self.form.addRow(label+' *',row);self.photos[view]=field
        self.form.addRow(QLabel('Três fotos distintas por peça. A disponibilidade será liberada ao concluir a OP.'))

    def choose(self,key):
        path,_=QFileDialog.getOpenFileName(self,'Foto da peça','','Fotos (*.png *.jpg *.jpeg)')
        if path:self.photos[key].setText(path)

    def persist(self):
        v=self.values();checklist={key:{'result':c.currentData(),'reason':r.text()} for key,(c,r) in self.checks.items()}
        self.production.inspect(self.identifier,self.piece['id'],v['result'],checklist,{key:p.text() for key,p in self.photos.items()},v['responsible'],v['notes'])


class ProductionPage(QWidget):
    def __init__(self,storage,parent=None):
        super().__init__(parent);self.production=Production(storage)
        layout=QVBoxLayout(self);bar=QHBoxLayout();layout.addLayout(bar)
        self.new_order_button=button('Nova OP da peça selecionada',lambda:self.dialog(OrderDialog(self.production,self)),bar)
        button('Atualizar',self.refresh,bar)
        self.tabs=QTabWidget();layout.addWidget(self.tabs)
        queue=QWidget();q=QVBoxLayout(queue);self.queue_table=table(['OP','Prioridade','Estado','Criada','Responsável','Pedido/item']);q.addWidget(self.queue_table)
        actions=QHBoxLayout();q.addLayout(actions)
        for label,handler in [('Iniciar',self.start),('Impressão terminada',self.confirm),('Inspecionar',self.inspect),('Concluir OP',self.complete),('Reimprimir',self.reprint)]:button(label,handler,actions)
        bar2=QHBoxLayout();q.addLayout(bar2)
        self.priority_box=QComboBox()
        for key,label in PRIORITIES.items():self.priority_box.addItem(label,key)
        bar2.addWidget(self.priority_box);button('Alterar prioridade',self.set_priority,bar2);button('↑',lambda:self.move(-1),bar2);button('↓',lambda:self.move(1),bar2);button('Parâmetros / revalidação',self.revalidate,bar2);button('Registrar problema',self.problem,bar2)
        self.inspection_progress=QProgressBar();self.inspection_progress.setFormat("Peças aprovadas / planejadas: %v / %m");q.addWidget(self.inspection_progress)
        self.summary_label=QLabel();self.summary_label.setWordWrap(True);q.addWidget(self.summary_label)
        self.piece_table=table(['Peça','Variante','Estado','Inspeção','Custo alocado']);self.piece_table.setColumnHidden(4,True);q.addWidget(self.piece_table)
        self.history=QTextEdit();self.history.setReadOnly(True);q.addWidget(self.history)
        button('Histórico e fotos da peça',self.inspection_history,q)
        button('Emitir relatório PDF da OP',self.pdf,q)
        self.tabs.addTab(queue,'Fila e inspeção')
        procedures=QTextEdit();procedures.setReadOnly(True)
        from .procedures import TEXT
        procedures.setPlainText(TEXT);self.tabs.addTab(procedures,'Procedimentos PO-001 a PO-012 / FR-001')
        self.queue_table.itemSelectionChanged.connect(self.details)
        self.timer=QTimer(self);self.timer.setInterval(30000);self.timer.timeout.connect(self.details);self.timer.start();self.refresh()

    def selected(self):
        index=self.queue_table.currentRow()
        if index<0 or index>=len(self.rows):raise ValueError('Selecione uma OP.')
        return self.rows[index]['id']

    def act(self,fn):
        try:fn();self.refresh()
        except (ValueError,OSError) as err:QMessageBox.warning(self,'Verifique a produção',str(err))

    def dialog(self,item):
        if item.exec():self.refresh()

    def refresh(self):
        try:selected=self.selected()
        except ValueError:selected=None
        self.queue_table.blockSignals(True)
        self.rows=self.production.queue()
        fill_table(self.queue_table,[(r['code'],PRIORITIES[r['priority']],STATES[r['state']],r['created_at'][:19],r['responsible'],r['item_id'] or 'Estoque') for r in self.rows])
        self.queue_table.blockSignals(False)
        if self.rows:self.queue_table.selectRow(next((i for i,r in enumerate(self.rows) if r['id']==selected),0))
        self.details()
        if getattr(self, '_after_refresh', None): self._after_refresh()

    def details(self):
        try:identifier=self.selected()
        except ValueError:return
        self.parts=self.production.pieces(identifier);s=self.production.summary(identifier);op=self.production.get(identifier)
        self.inspection_progress.setRange(0,max(s['planned'],s['good'],1));self.inspection_progress.setValue(s['good'])
        effective=brl(s['effective_unit']) if s['effective_unit'] else 'sem aprovadas'
        self.summary_label.setText(f'Planejadas {s["planned"]} • Produzidas {s["produced"]} • Perdidas {s["failed"]} • Reprovadas {s["rejected"]} • Boas {s["good"]} • Tentativas {s["attempts"]}')
        self.piece_table.setColumnHidden(4,True)
        selected_piece=self.piece_table.currentRow()
        fill_table(self.piece_table,[(p['id'],p['variant_id'],p['state'],p['inspection_result'] or 'Pendente',brl(Decimal(p['unit_cost_cents'])/100)) for p in self.parts])
        if self.parts:self.piece_table.selectRow(min(max(selected_piece,0),len(self.parts)-1))
        lines=[f'Parâmetros (revisão {op["revision"]}): {op["parameters"]}']
        for e in self.production.entries(identifier):
            snap=json.loads(e['planned']);lines.append(f'{e["product_name"]} / {e["variant_name"]} — {e["quantity"]} un. — arquivo v{snap["project"]["version"]}: {snap["project"]["original_name"]}')
        for r in self.production.db.execute('SELECT * FROM production_attempts WHERE op_id=?',(identifier,)):lines.append(f'Tentativa {r["id"]}: {r["minutes"]} min, progresso {r["progress"]}%, {r["reason"]}')
        for r in self.production.db.execute('SELECT * FROM production_problems WHERE op_id=?',(identifier,)):lines.append(f'Problema do produto {r["product_id"]}: {r["kind"]} — {r["description"]}')
        self.history.setPlainText('\n'.join(lines))

    def start(self):self.act(lambda:self.production.start(self.selected()))
    def confirm(self):
        def run():
            from .recipe_ui import RecipeConfirmDialog
            identifier=self.selected()
            dialog=RecipeConfirmDialog if self.production.recipe_order(identifier) else ConfirmDialog
            self.dialog(dialog(self.production,identifier,self))
        self.act(run)
    def complete(self):self.act(lambda:self.production.complete(self.selected()))
    def inspect(self):
        def run():
            index=self.piece_table.currentRow()
            if index<0:raise ValueError('Selecione uma peça para inspeção individual.')
            self.dialog(InspectionDialog(self.production,self.selected(),self.parts[index],self))
        self.act(run)
    def reprint(self):
        def run():
            d=FormDialog('Nova OP de reimpressão',self);d.line('responsible','Responsável *')
            op=self.selected();old_spools={f['id'] for e in self.production.entries(op) for f in json.loads(e['planned'])['filaments']}
            choices={f['id']:f'{f["id"]} • {f["name"]} / {f["color"]}' for f in self.production.catalog.rows('filaments') if f['state']!='finished'}
            for key in sorted(old_spools):d.combo('spool_'+str(key),f'Substituir carretel #{key}',choices,key if key in choices else next(iter(choices),None))
            d.persist=lambda:self.production.reprint(op,d.values()['responsible'],{key:d.values()['spool_'+str(key)] for key in old_spools})
            self.dialog(d)
        self.act(run)
    def set_priority(self):self.act(lambda:self.production.priority(self.selected(),self.priority_box.currentData()))
    def move(self,direction):
        def run():
            selected=self.production.get(self.selected());group=[r['id'] for r in self.rows if r['priority']==selected['priority'] and r['state']!='completed'];index=group.index(selected['id']);target=index+direction
            if 0<=target<len(group):group[index],group[target]=group[target],group[index];self.production.reorder(group,selected['priority'])
        self.act(run)
    def revalidate(self):
        def run():
            op=self.production.get(self.selected());d=FormDialog('Alterar parâmetros e exigir revalidação',self);d.line('parameters','Parâmetros',op['parameters']);d.line('reason','Justificativa *')
            d.persist=lambda:self.production.revalidate(op['id'],d.values()['parameters'],d.values()['reason']);self.dialog(d)
        self.act(run)
    def problem(self):
        def run():
            identifier=self.selected();d=FormDialog('Histórico de problema',self)
            d.combo('product','Produto',{e['product_id']:e['product_name'] for e in self.production.entries(identifier)},self.production.entries(identifier)[0]['product_id'])
            d.combo('kind','Tipo',{k:CHECK_LABELS[k] for k in ('surface','supports','adhesion','detail')},'surface');d.line('description','Descrição *');d.line('responsible','Responsável *')
            d.persist=lambda:self.production.problem(identifier,d.values()['product'],d.values()['kind'],d.values()['description'],d.values()['responsible']);self.dialog(d)
        self.act(run)

    def inspection_history(self):
        def run():
            index=self.piece_table.currentRow()
            if index<0:raise ValueError('Selecione uma peça.')
            piece=self.parts[index];d=QDialog(self);d.setWindowTitle(f'Inspeções da peça {piece["id"]}');d.resize(740,600);layout=QVBoxLayout(d);content=QWidget();body=QVBoxLayout(content);layout.addWidget(scroll(content))
            for inspection in self.production.db.execute('SELECT * FROM inspections WHERE piece_id=? ORDER BY id DESC',(piece['id'],)):
                label=QLabel(f'Revisão {inspection["revision"]} • {inspection["created_at"]} • {inspection["responsible"]} • {inspection["result"]} • '+('Válida' if inspection['valid'] else 'Histórico')+'\n'+inspection['notes']);label.setWordWrap(True);body.addWidget(label)
                for key,value in json.loads(inspection['checklist']).items():body.addWidget(QLabel(CHECK_LABELS[key]+': '+value['result']+' — '+value.get('reason','')))
                for photo in self.production.db.execute('SELECT * FROM inspection_photos WHERE inspection_id=?',(inspection['id'],)):
                    button('Abrir foto: '+VIEWS[photo['view']],lambda checked=False,k=photo['id']:self.act(lambda:QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.production.photo_path(k))))),body)
            button('Fechar',d.accept,layout);d.exec()
        self.act(run)

    def pdf(self):
        def run():
            from .documents import Documents
            from .phase4_ui import open_local
            documents=Documents(self.production.storage);identifier=documents.emit_production(self.selected());open_local(self,documents.path(identifier))
        self.act(run)
