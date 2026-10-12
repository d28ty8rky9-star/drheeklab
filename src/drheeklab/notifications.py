"""Derived operational alerts; reading/snoozing never settles an obligation."""
from datetime import date,timedelta
import hashlib
import json
from .storage import now
from .transactions import transaction
from .catalog import Catalog
from .sales import Sales
from .finance import Finance
from .pricing import grams_mg,integer,brl
from decimal import Decimal

class Notifications:
    def __init__(self,storage):self.storage,self.db=storage,storage.db

    def refresh(self,as_of=None):
        today=date.fromisoformat(as_of) if as_of else date.today();horizon=integer(self.storage.get('notification_days',7),'Dias de alerta')
        if horizon>90:raise ValueError('Use no máximo 90 dias para próximos vencimentos.')
        limit=(today+timedelta(days=horizon)).isoformat();day=today.isoformat();alerts=[]
        def add(key,kind,title,detail,area,severity='info'):
            alerts.append({'key':key,'kind':kind,'title':title,'detail':detail,'area':area,'severity':severity})
        catalog=Catalog(self.storage);threshold=grams_mg(self.storage.get('low_filament_grams','100'))
        for f in catalog.rows('filaments'):
            if f['state']!='finished' and f['remaining_mg'] is not None and f['remaining_mg']<=threshold:
                add(f'filament:{f["id"]}','filament','Filamento baixo',f'{f["name"]} / {f["color"]}: {f["remaining_mg"]/1000:g} g',4,'warning')
        finance=Finance(self.storage)
        for kind,rows,area in [('receivable',finance.receivables(day),1),('payable',finance.payables(day),5)]:
            for r in rows:
                if r['balance_cents']>0 and r['due_on'] and r['due_on']<=limit:
                    overdue=r['due_on']<day;title=('Recebimento' if kind=='receivable' else 'Pagamento')+(' vencido' if overdue else ' próximo do vencimento')
                    add(f'{kind}:{r["id"]}',kind,title,(r.get('code') or r['description'])+' • vence '+r['due_on']+' • saldo '+brl(Decimal(r['balance_cents'])/100),area,'urgent' if overdue else 'warning')
        sales=Sales(self.storage)
        for o in sales.orders():
            delivery=sales.delivery(o['id'])
            if o['state']=='approved' and delivery['state']!='delivered':
                add(f'delivery:{o["id"]}','delivery','Entrega pendente',o['code']+' • '+('enviado, aguardando entrega' if delivery['state']=='sent' else 'aguardando saída')+' • prazo '+(o['due_on'] or 'não definido'),1,'urgent' if o['due_on'] and o['due_on']<day else 'info')
        for q in sales.quotes():
            if q['state']=='pending' and q['valid_until'] and q['valid_until']<=limit:
                overdue=q['valid_until']<day
                add(f'quote:{q["id"]}','quote','Orçamento vencido' if overdue else 'Orçamento próximo do vencimento',q['code']+' • validade '+q['valid_until'],1,'urgent' if overdue else 'warning')
        for printer in catalog.rows('printers'):
            maintenance=catalog.maintenance(printer['id']);latest=maintenance[0] if maintenance else None;due=latest['next_due'] if latest else None
            if printer['status']=='maintenance' or due and due<=limit:
                add(f'maintenance:{printer["id"]}','maintenance','Manutenção necessária',printer['identifier']+' • '+('em manutenção' if printer['status']=='maintenance' else 'programada para '+due),6,'urgent' if printer['status']=='maintenance' or due and due<day else 'warning')
        with transaction(self.db):
            keys={r['key'] for r in alerts}
            for state in self.db.execute('SELECT * FROM notification_states WHERE active=1').fetchall():
                if state['key'] not in keys:self.db.execute('UPDATE notification_states SET active=0,seen_at=NULL,snoozed_until=NULL WHERE key=?',(state['key'],))
            for alert in alerts:
                fingerprint=hashlib.sha256(json.dumps(alert,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
                old=self.db.execute('SELECT * FROM notification_states WHERE key=?',(alert['key'],)).fetchone()
                if not old or not old['active'] or old['fingerprint']!=fingerprint:
                    self.db.execute('INSERT INTO notification_states(key,fingerprint,active) VALUES(?,?,1) ON CONFLICT(key) DO UPDATE SET fingerprint=excluded.fingerprint,active=1,seen_at=NULL,snoozed_until=NULL',(alert['key'],fingerprint))
                    self.storage.audit('notificação ativa',alert['key'],dict(old) if old else None,{'fingerprint':fingerprint,'title':alert['title']})
                state=self.db.execute('SELECT * FROM notification_states WHERE key=?',(alert['key'],)).fetchone()
                alert['read']=bool(state['seen_at']);alert['snoozed']=bool(state['snoozed_until'] and state['snoozed_until']>day)
        return sorted(alerts,key=lambda r:({'urgent':0,'warning':1,'info':2}[r['severity']],r['key']))

    def mark(self,key,snooze_days=None):
        with transaction(self.db):
            old=self.db.execute('SELECT * FROM notification_states WHERE key=? AND active=1',(key,)).fetchone()
            if not old:raise ValueError('Alerta não está mais ativo. Atualize a lista.')
            until=None
            if snooze_days is not None:
                days=integer(snooze_days,'Dias',minimum=1)
                if days>90:raise ValueError('Use até 90 dias para adiar.')
                until=(date.today()+timedelta(days=days)).isoformat()
            self.db.execute('UPDATE notification_states SET seen_at=?,snoozed_until=? WHERE key=?',(now(),until,key))
            self.storage.audit('notificação adiada' if until else 'notificação lida',key,dict(old),{'snoozed_until':until})
