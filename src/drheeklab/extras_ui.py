"""Accessory details edited entirely in Production."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLineEdit,QLabel,QPushButton
from .production_extras import calculate_extras
from .pricing import brl

class ExtrasEditor(QWidget):
    changed=Signal()
    def __init__(self,entries=(),parent=None):
        super().__init__(parent);self.rows=[];box=QVBoxLayout(self)
        note=QLabel('Extras por peça: argolas, acessórios, montagem ou outros itens. Quantidade × custo unitário entra no valor de produção.');note.setWordWrap(True);box.addWidget(note)
        self.items=QVBoxLayout();box.addLayout(self.items)
        add=QPushButton('Adicionar extra');add.clicked.connect(lambda:self.add());box.addWidget(add)
        self.total_label=QLabel('Total dos extras: R$ 0,00');box.addWidget(self.total_label);box.addStretch()
        for entry in entries:self.add(entry)
        self.changed.connect(self.update_total);self.update_total()

    def add(self,entry=None):
        entry=entry or {};widget=QWidget();row=QHBoxLayout(widget)
        name=QLineEdit(entry.get('name',''));name.setPlaceholderText('Ex.: argola')
        quantity=QLineEdit(str(entry.get('quantity','1')));quantity.setMaximumWidth(80)
        cost=QLineEdit(str(entry.get('unit_cost','0')));cost.setMaximumWidth(100)
        remove=QPushButton('Remover')
        for w in (name,QLabel('Qtd.'),quantity,QLabel('R$/un.'),cost,remove):row.addWidget(w)
        data=(widget,name,quantity,cost);self.rows.append(data);self.items.addWidget(widget)
        for field in (name,quantity,cost):field.textChanged.connect(lambda *_:self.changed.emit())
        remove.clicked.connect(lambda:self.remove(data));self.changed.emit()

    def remove(self,data):
        self.rows.remove(data);self.items.removeWidget(data[0]);data[0].hide();data[0].deleteLater();self.changed.emit()

    def value(self):
        return [{'name':name.text(),'quantity':quantity.text(),'unit_cost':cost.text()} for _,name,quantity,cost in self.rows]

    def update_total(self):
        try:self.total_label.setText('Total dos extras por peça: '+brl(calculate_extras(self.value())[1]))
        except ValueError as error:self.total_label.setText(str(error))
