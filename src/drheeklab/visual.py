"""Shared presentation components. No business writes or financial calculations."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap, QIcon, QPen
from PySide6.QtWidgets import QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QTableWidget, QPushButton, QStyle

COLORS = {'purple':'#9565fa', 'blue':'#38bdf8', 'magenta':'#e879f9', 'green':'#34d399', 'amber':'#fbbf24', 'red':'#fb7185'}
SPACING = 12

def stylesheet(dark=True):
    bg, panel, text, muted, edge = ('#090f20','#121d34','#edf3ff','#a8b8d3','#293b58') if dark else ('#eef3fb','#ffffff','#182841','#526582','#c8d4e5')
    return f"""
    QWidget {{background:{bg};color:{text};font-family:'Segoe UI';font-size:13px;}}
    QLabel {{background:transparent;}}
    QFrame#sidebar,QFrame#card,QGroupBox {{background:{panel};border:1px solid {edge};border-radius:12px;}}
    QFrame#card {{padding:8px;}} QFrame#sidebar {{border-radius:0;}}
    QLabel#brand {{color:#9565fa;font-size:24px;font-weight:800;padding:16px 0;}}
    QLabel#title,QLabel#hero {{font-size:26px;font-weight:700;}}
    QLabel#alert {{color:#fbbf24;padding:10px;border:1px solid #745a2b;border-radius:7px;}}
    QLabel#muted {{color:{muted};}} QLabel#metric {{font-size:23px;font-weight:700;}}
    QPushButton {{background:{panel};border:1px solid {edge};border-radius:7px;padding:7px 11px;min-height:20px;}}
    QPushButton[nav="expanded"] {{text-align:left;}}
    QPushButton:hover {{border-color:#9565fa;background:#293b58;color:white;}}
    QPushButton:checked,QPushButton[role="primary"] {{background:#7044cf;color:white;border-color:#9565fa;}}
    QPushButton[role="danger"] {{color:#fb7185;}} QPushButton[role="export"] {{color:#38bdf8;}}
    QPushButton:disabled {{color:{muted};}}
    QLineEdit,QTextEdit,QPlainTextEdit,QComboBox,QSpinBox,QDoubleSpinBox,QDateEdit {{background:{panel};border:1px solid {edge};border-radius:6px;padding:7px;min-height:20px;}}
    QLineEdit:focus,QTextEdit:focus,QComboBox:focus {{border-color:#9565fa;}}
    QTableWidget,QListWidget {{background:{panel};alternate-background-color:{bg};border:1px solid {edge};border-radius:8px;selection-background-color:#6543ad;selection-color:white;}}
    QTableWidget::item {{padding:7px;border-bottom:1px solid {edge};}}
    QHeaderView::section {{background:{panel};color:{muted};border:0;border-bottom:1px solid {edge};padding:10px;font-weight:600;}}
    QTabWidget::pane {{border:1px solid {edge};border-radius:8px;}}
    QTabBar::tab {{background:{panel};padding:9px 14px;color:{muted};border-bottom:2px solid transparent;}}
    QTabBar::tab:selected {{color:{text};border-bottom:2px solid #9565fa;}}
    QListWidget::item {{border:1px solid {edge};border-radius:9px;margin:5px;padding:8px;}}
    QListWidget::item:selected {{background:#6543ad;color:white;}}
    QProgressBar {{border:1px solid {edge};border-radius:6px;text-align:center;min-height:20px;}} QProgressBar::chunk {{background:#7044cf;border-radius:5px;}}
    QScrollArea {{border:0;}} QToolTip {{background:{panel};color:{text};border:1px solid {edge};}}
    """

class MetricCard(QFrame):
    def __init__(self, title, value='—', detail='', accent='purple'):
        super().__init__(); self.setObjectName('card'); self.setMinimumHeight(100); box=QVBoxLayout(self)
        label=QLabel(title);label.setObjectName('muted');box.addWidget(label)
        self.value=QLabel(str(value));self.value.setObjectName('metric');self.value.setStyleSheet('color:'+COLORS[accent]);box.addWidget(self.value)
        self.detail=QLabel(detail);self.detail.setWordWrap(True);self.detail.setObjectName('muted');box.addWidget(self.detail)
    def update_value(self, value):self.value.setText(str(value))

class MetricStrip(QWidget):
    def __init__(self, titles):
        super().__init__();box=QHBoxLayout(self);box.setContentsMargins(0,0,0,0);box.setSpacing(SPACING)
        self.cards=[MetricCard(t, accent=a) for t,a in zip(titles,('purple','blue','magenta','green'))]
        for card in self.cards:box.addWidget(card,1)
    def set_values(self,values):
        for card,value in zip(self.cards,values):card.update_value(value)

class BarChart(QWidget):
    """Signed values with a shared scale; labels retain exact values."""
    def __init__(self,title):
        super().__init__();self.title=title;self.values=[];self.setMinimumHeight(150)
    def set_values(self, values):self.values=values;self.update()
    def paintEvent(self,event):
        painter=QPainter(self);painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.palette().windowText().color());painter.drawText(12,23,self.title)
        if not self.values or not any(v for _,v,_ in self.values):
            painter.drawText(12,60,'Sem movimentações no período');return
        maximum=max(abs(v) for _,v,_ in self.values) or 1
        for i,(label,value,display) in enumerate(self.values):
            y=48+i*30;painter.setPen(self.palette().windowText().color());painter.drawText(12,y+15,label+'  '+display)
            painter.setBrush(QColor(list(COLORS.values())[i%6]));painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(self.width()//2,y,max(2,int((self.width()/2-20)*abs(value)/maximum)),18,4,4)

def action_style(button):
    text=button.text().lower()
    role='primary' if text.startswith(('nov','criar','iniciar','confirmar','registrar recebimento')) else 'danger' if text.startswith(('descartar','cancelar','estornar','rejeitar')) else 'export' if any(x in text for x in ('exportar','pdf','backup')) else 'secondary'
    button.setProperty('role',role)
    icon=QStyle.SP_FileDialogNewFolder if role=='primary' else QStyle.SP_DialogSaveButton if role=='export' else QStyle.SP_DialogCancelButton if role=='danger' else QStyle.SP_ArrowRight
    # Draw a consistent small line icon instead of platform-dependent clip art.
    pixmap=QPixmap(18,18);pixmap.fill(Qt.transparent);painter=QPainter(pixmap);painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor(COLORS['blue'] if role=='export' else COLORS['red'] if role=='danger' else '#bfa4ff'),2))
    if role=='primary':painter.drawLine(4,9,14,9);painter.drawLine(9,4,9,14)
    elif role=='danger':painter.drawLine(5,5,13,13);painter.drawLine(13,5,5,13)
    elif role=='export':painter.drawLine(9,3,9,12);painter.drawLine(5,8,9,12);painter.drawLine(13,8,9,12);painter.drawLine(3,15,15,15)
    else:painter.drawEllipse(4,4,10,10)
    painter.end();button.setIcon(QIcon(pixmap))

def modern_table(widget):
    widget.setAlternatingRowColors(True);widget.setShowGrid(False);widget.verticalHeader().hide();widget.verticalHeader().setDefaultSectionSize(36)

def status_color(text):
    text=text.lower()
    if any(x in text for x in ('cancelad','descart','atrasad','rejeitad')):return COLORS['red']
    if any(x in text for x in ('parcial','aguardando inspe','manutenção','alta')):return COLORS['amber']
    if any(x in text for x in ('conclu','pago','quitado','recebido','entregue','disponível')):return COLORS['green']
    if 'imprimindo' in text:return COLORS['blue']
    if any(x in text for x in ('aguardando','pendente','reservad')):return COLORS['magenta']
    return None

class Alert(QFrame):
    def __init__(self,text,accent='amber'):
        super().__init__();self.setObjectName('card');box=QHBoxLayout(self)
        label=QLabel(text);label.setWordWrap(True);label.setStyleSheet('color:'+COLORS[accent]);box.addWidget(label)
