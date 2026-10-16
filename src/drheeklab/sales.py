"""Offline commercial workflow. Every financial value is an integer cent amount."""
from contextlib import contextmanager
from datetime import date, timedelta
from calendar import monthrange
from decimal import Decimal
import json
import re
import uuid
from .catalog import Catalog,required,optional_date
from .products import Products
from .inventory import Inventory
from .pricing import cents,integer
from .storage import now
from .transactions import transaction
from .sales_documents import emit,import_attachment,owned_path

PAYMENT_METHODS={'pix':'Pix','cash':'Dinheiro','debit':'Débito','credit_card':'Crédito','transfer':'Transferência','other':'Outros','customer_credit':'Crédito do cliente'}

from .stock_sale import StockSales

class Sales(StockSales):
    def __init__(self,storage):
        self.storage,self.db=storage,storage.db
        self.inventory=Inventory(storage)
        self.products=Products(storage)

    @contextmanager
    def event(self):
        parent=getattr(self,'_event_files',None)
        files=parent if parent is not None else []
        offset=len(files)
        self._event_files=files
        try:
            with transaction(self.db):
                yield files
        except BaseException:
            for path in files[offset:]: path.unlink(missing_ok=True)
            del files[offset:]
            raise
        finally:
            self._event_files=parent

    def get(self,table,identifier):
        if table not in ('clients','quotes','orders','order_items','payments','sales_documents'):
            raise ValueError('Registro comercial inválido.')
        row=self.db.execute(f'SELECT * FROM {table} WHERE id=?',(identifier,)).fetchone()
        if row is None: raise ValueError('Registro comercial não encontrado.')
        return dict(row)

    def clients(self,archived=False):
        return [dict(r) for r in self.db.execute('SELECT * FROM clients WHERE archived=? ORDER BY name,id',(int(archived),))]

    def save_client(self,data,identifier=None):
        name=required(data.get('name'),'Nome')
        email=str(data.get('email','')).strip()
        if email and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):
            raise ValueError('E-mail inválido.')
        values=(name,str(data.get('phone','')).strip(),email,str(data.get('notes','')).strip())
        with transaction(self.db):
            previous=self.get('clients',identifier) if identifier is not None else None
            if previous and previous['archived']: raise ValueError('Restaure o cliente antes de editar.')
            if previous is None:
                identifier=self.db.execute('INSERT INTO clients(name,phone,email,notes) VALUES(?,?,?,?)',values).lastrowid
            else:
                self.db.execute('UPDATE clients SET name=?,phone=?,email=?,notes=? WHERE id=?',(*values,identifier))
            self.storage.audit('cliente:cadastro' if previous is None else 'cliente:edição',f'clients:{identifier}',previous,self.get('clients',identifier))
        return identifier

    def archive_client(self,identifier,archived,reason):
        required(reason,'Justificativa')
        with transaction(self.db):
            previous=self.get('clients',identifier)
            self.db.execute('UPDATE clients SET archived=? WHERE id=?',(int(archived),identifier))
            self.storage.audit('cliente:arquivar' if archived else 'cliente:restaurar',f'clients:{identifier}',previous,self.get('clients',identifier),reason)

    def active_client(self,identifier):
        row=self.get('clients',identifier)
        if row['archived']: raise ValueError('Restaure o cliente para novos registros comerciais.')
        return row

    def code(self,kind):
        year=date.today().year
        self.db.execute('INSERT INTO document_sequences VALUES(?,?,1) ON CONFLICT(kind,year) DO UPDATE SET value=value+1',(kind,year))
        value=self.db.execute('SELECT value FROM document_sequences WHERE kind=? AND year=?',(kind,year)).fetchone()[0]
        return f'{kind}-{year}-{value:04d}'

    def prepare_items(self,items):
        if not items: raise ValueError('Adicione pelo menos um item.')
        result=[]
        for item in items:
            variant_id=item.get('variant_id')
            variant=self.products.active_variant(variant_id) if variant_id is not None else None
            product=self.products.active_product(variant['product_id']) if variant else None
            description=str(item.get('description') or '').strip()
            if not description and product: description=product['name']+' / '+variant['name']
            description=required(description,'Descrição do item personalizado')
            quantity=integer(item.get('quantity',1),'Quantidade',minimum=1)
            unit=cents(item.get('unit_price',''),'Preço final unitário')
            if unit*quantity>9_000_000_000_000_000_000: raise ValueError('Total do item fora do limite de armazenamento.')
            fulfillment=item.get('fulfillment','production')
            if fulfillment not in ('stock','production'): raise ValueError('Origem do item inválida.')
            if fulfillment=='stock' and variant is None: raise ValueError('Item de estoque precisa de variante cadastrada.')
            result.append({'variant_id':variant_id,'description':description,'quantity':quantity,'unit_price_cents':unit,
                'total_cents':unit*quantity,'fulfillment':fulfillment,'snapshot':{'product':product,'variant':variant},'files':list(item.get('files',[])),'piece_ids':item.get('piece_ids')})
        return result

    def quote_state(self,row):
        return 'expired' if row['state']=='pending' and row['valid_until'] and row['valid_until']<date.today().isoformat() else row['state']

    def quotes(self):
        rows=[dict(r) for r in self.db.execute('SELECT * FROM quotes ORDER BY id DESC')]
        for row in rows: row['display_state']=self.quote_state(row)
        return rows

    def create_quote(self,client_id,items,freight='0',valid_until='default',notes='',operation_key=None):
        with self.event() as files:
            client=self.active_client(client_id)
            rows=self.prepare_items(items)
            shipping=cents(freight,'Frete')
            validity=(date.today()+timedelta(days=7)).isoformat() if valid_until=='default' else optional_date(valid_until)
            if shipping+sum(r['total_cents'] for r in rows)>9_000_000_000_000_000_000: raise ValueError('Total fora do limite de armazenamento.')
            clean=[{k:v for k,v in row.items() if k!='files'} for row in rows]
            quote=self.db.execute("INSERT INTO quotes(code,client_id,client_snapshot,items,freight_cents,total_cents,valid_until,notes,created_at,state,operation_key) VALUES(?,?,?,?,?,?,?,?,?,'pending',?)",
                (self.code('ORC'),client_id,json.dumps(client,ensure_ascii=False),json.dumps(clean,ensure_ascii=False),shipping,shipping+sum(r['total_cents'] for r in rows),validity,str(notes),now(),operation_key or uuid.uuid4().hex)).lastrowid
            for index,row in enumerate(rows):
                for source in row['files']: import_attachment(self.storage,source,quote_id=quote,item_index=index,created=files)
            self.storage.audit('orçamento criado',f'quotes:{quote}',None,self.get('quotes',quote))
            self.emit_quote(quote,files)
            return quote

    def reject_quote(self,identifier,reason):
        required(reason,'Motivo')
        with self.event() as files:
            row=self.get('quotes',identifier)
            if row['state']!='pending': raise ValueError('Orçamento já aprovado ou rejeitado.')
            self.db.execute("UPDATE quotes SET state='rejected',reason=? WHERE id=?",(reason,identifier))
            self.storage.audit('orçamento rejeitado',f'quotes:{identifier}',row,self.get('quotes',identifier),reason)
            self.emit_quote(identifier,files)

    def create_order(self,client_id,items,freight='0',due_on=None,notes='',installments=None,operation_key=None):
        with self.event() as files:
            client=self.active_client(client_id)
            rows=self.prepare_items(items)
            return self._insert_order(client,rows,cents(freight,'Frete'),optional_date(due_on),str(notes),installments,
                                      operation_key or uuid.uuid4().hex,files)

    def approve_quote(self,identifier,due_on=None,installments=None):
        with self.event() as files:
            quote=self.get('quotes',identifier)
            if self.quote_state(quote)!='pending': raise ValueError('Orçamento já processado ou vencido; crie um novo registro se necessário.')
            rows=json.loads(quote['items'])
            for row in rows:
                if row['variant_id'] is not None: self.products.active_variant(row['variant_id'])
                row['files']=[]
            order=self._insert_order(json.loads(quote['client_snapshot']),rows,quote['freight_cents'],optional_date(due_on),quote['notes'],installments,
                                     'quote-conversion-'+str(identifier),files,quote_id=identifier)
            self.db.execute("UPDATE quotes SET state='approved' WHERE id=?",(identifier,))
            attachments=self.db.execute('SELECT * FROM sales_attachments WHERE quote_id=?',(identifier,)).fetchall()
            items=self.items(order)
            for asset in attachments:
                owned_path(self.storage,asset['path'],asset['sha256'])
                self.db.execute('INSERT INTO sales_attachments(order_id,item_id,item_index,kind,path,original_name,sha256,created_at) VALUES(?,?,?,?,?,?,?,?)',
                    (order,items[asset['item_index']]['id'],asset['item_index'],asset['kind'],asset['path'],asset['original_name'],asset['sha256'],now()))
            self.storage.audit('orçamento aprovado',f'quotes:{identifier}',quote,{'order_id':order})
            self.emit_quote(identifier,files)
            return order

    def _insert_order(self,client,rows,freight,due_on,notes,installments,key,files,quote_id=None):
        total=freight+sum(row['total_cents'] for row in rows)
        if total>9_000_000_000_000_000_000: raise ValueError('Total fora do limite de armazenamento.')
        identifier=self.db.execute("INSERT INTO orders(code,quote_id,client_id,client_snapshot,freight_cents,total_cents,notes,due_on,created_at,state,operation_key) VALUES(?,?,?,?,?,?,?,?,?,'approved',?)",
            (self.code('PED'),quote_id,client['id'],json.dumps(client,ensure_ascii=False),freight,total,notes,due_on,now(),key)).lastrowid
        for index,row in enumerate(rows):
            item=self.db.execute('INSERT INTO order_items(order_id,variant_id,description,quantity,unit_price_cents,total_cents,snapshot,fulfillment) VALUES(?,?,?,?,?,?,?,?)',
                (identifier,row['variant_id'],row['description'],row['quantity'],row['unit_price_cents'],row['total_cents'],json.dumps(row['snapshot'],ensure_ascii=False),row['fulfillment'])).lastrowid
            if row['fulfillment']=='stock': self.reserve_item(item,piece_ids=row.get('piece_ids'))
            for source in row.get('files',[]): import_attachment(self.storage,source,order_id=identifier,item_id=item,item_index=index,created=files)
        planned=installments if installments is not None else ([{'amount':str(Decimal(total)/100),'due_on':due_on}] if total else [])
        self._installments(identifier,planned,total)
        self.db.execute("INSERT INTO deliveries(order_id,state,mode) VALUES(?,'waiting','pickup')",(identifier,))
        self.storage.audit('pedido aprovado',f'orders:{identifier}',None,self.get('orders',identifier))
        self.emit_order(identifier,files)
        return identifier

    def _installments(self,order_id,rows,total):
        converted=[(cents(row['amount'],'Parcela'),optional_date(row.get('due_on'))) for row in rows]
        if any(amount<=0 for amount,due in converted) or sum(amount for amount,due in converted)!=total:
            raise ValueError('Parcelas positivas devem somar exatamente o total do pedido.')
        for amount,due in converted:
            self.db.execute('INSERT INTO installments(order_id,amount_cents,due_on) VALUES(?,?,?)',(order_id,amount,due))

    @staticmethod
    def split_installments(total_cents,count,first_due=None):
        count=integer(count,'Quantidade de parcelas',minimum=1)
        if count>120: raise ValueError('Use no máximo 120 parcelas.')
        if total_cents==0: return []
        if total_cents<count: raise ValueError('Cada parcela deve ter ao menos um centavo.')
        first=date.fromisoformat(first_due) if first_due else None
        base,extra=divmod(total_cents,count)
        rows=[]
        for i in range(count):
            due=None
            if first:
                month=first.month-1+i; year=first.year+month//12; month=month%12+1
                due=date(year,month,min(first.day,monthrange(year,month)[1])).isoformat()
            rows.append({'amount':str(Decimal(base+int(i<extra))/100),'due_on':due})
        return rows

    def items(self,order_id):
        return [dict(r) for r in self.db.execute('SELECT * FROM order_items WHERE order_id=? ORDER BY id',(order_id,))]

    def payments(self,order_id):
        return [dict(r) for r in self.db.execute('SELECT * FROM payments WHERE order_id=? ORDER BY paid_on,id',(order_id,))]

    def credit_balance(self,client_id):
        return self.db.execute("SELECT COALESCE(SUM(CASE direction WHEN 'in' THEN amount_cents ELSE -amount_cents END),0) FROM client_credit WHERE client_id=?",(client_id,)).fetchone()[0]

    def client_totals(self,client_id):
        rows=self.orders(client_id)
        amounts=[self.financial(r['id']) for r in rows]
        return {'sold':sum(r['total_cents'] for r in rows if r['state']!='cancelled'),
                'received':sum(r['cash_received']-r['refunded'] for r in amounts),
                'receivable':sum(r['balance'] for r in amounts)}

    def financial(self,order_id):
        order=self.get('orders',order_id)
        row=self.db.execute("SELECT COALESCE(SUM(amount_cents),0),COALESCE(SUM(fee_cents),0),COALESCE(SUM(net_cents),0),COALESCE(SUM(CASE kind WHEN 'cash' THEN amount_cents ELSE 0 END),0) FROM payments WHERE order_id=?",(order_id,)).fetchone()
        applied,fees,net,cash=row
        cancellation=self.db.execute('SELECT * FROM cancellations WHERE order_id=?',(order_id,)).fetchone()
        balance=0 if order['state']=='cancelled' else order['total_cents']-applied
        return {'total':order['total_cents'],'paid':applied,'cash_received':cash,'credit_applied':applied-cash,
                'fees':fees,'net_received':net,'balance':balance,
                'refunded':cancellation['refund_cents'] if cancellation else 0,
                'credited':cancellation['credit_cents'] if cancellation else 0,'retained':cancellation['retained_cents'] if cancellation else 0}

    def installment_status(self,order_id):
        cancelled=self.get('orders',order_id)['state']=='cancelled'
        rows=[dict(r) for r in self.db.execute('SELECT * FROM installments WHERE order_id=? ORDER BY COALESCE(due_on,\'9999-12-31\'),id',(order_id,))]
        for row in rows:
            row['balance_cents']=0 if cancelled else row['amount_cents']-row['received_cents']
            row['status']='cancelled' if cancelled else 'paid' if not row['balance_cents'] else 'overdue' if row['due_on'] and row['due_on']<date.today().isoformat() else 'partial' if row['received_cents'] else 'pending'
        return rows

    def orders(self,client_id=None):
        return [dict(r) for r in self.db.execute('SELECT * FROM orders'+(' WHERE client_id=?' if client_id is not None else '')+' ORDER BY id DESC',(client_id,) if client_id is not None else ())]

    def receive_payment(self,order_id,amount,method='pix',fee='0',paid_on=None,operation_key=None):
        amount=cents(amount,'Pagamento'); fee=cents(fee,'Taxa')
        if amount<=0 or fee>amount: raise ValueError('Pagamento deve ser positivo e a taxa não pode excedê-lo.')
        if method not in PAYMENT_METHODS: raise ValueError('Forma de pagamento inválida.')
        paid_on=optional_date(paid_on or date.today().isoformat())
        if paid_on>date.today().isoformat(): raise ValueError('Data efetiva de recebimento não pode ser futura; use parcelas previstas.')
        key=operation_key or uuid.uuid4().hex
        with self.event() as files:
            order=self.get('orders',order_id)
            if order['state']=='cancelled': raise ValueError('Pedido cancelado não recebe pagamentos.')
            finance=self.financial(order_id)
            if amount>finance['balance']: raise ValueError('Pagamento excede o saldo do pedido.')
            credit_id=None
            if method=='customer_credit':
                if fee: raise ValueError('Crédito do cliente não possui taxa nem recebimento em caixa.')
                if self.credit_balance(order['client_id'])<amount: raise ValueError('Crédito do cliente insuficiente.')
                credit_id=self.db.execute("INSERT INTO client_credit(client_id,order_id,direction,amount_cents,created_at,reason,operation_key) VALUES(?,?,'out',?,?,?,?)",
                    (order['client_id'],order_id,amount,now(),'Crédito aplicado ao pedido',key)).lastrowid
            payment=self.db.execute('INSERT INTO payments(order_id,amount_cents,fee_cents,net_cents,paid_on,method,kind,credit_id,created_at,operation_key) VALUES(?,?,?,?,?,?,?,?,?,?)',
                (order_id,amount,fee,0 if method=='customer_credit' else amount-fee,paid_on,method,'credit' if method=='customer_credit' else 'cash',credit_id,now(),key)).lastrowid
            remaining=amount
            for item in self.items(order_id):
                already=self.db.execute('SELECT COALESCE(SUM(a.amount_cents),0) FROM payment_allocations a WHERE a.item_id=?',(item['id'],)).fetchone()[0]
                assigned=min(remaining,item['total_cents']-already)
                if assigned:
                    self.db.execute('INSERT INTO payment_allocations(payment_id,item_id,amount_cents) VALUES(?,?,?)',(payment,item['id'],assigned)); remaining-=assigned
                if not remaining: break
            if remaining: self.db.execute('INSERT INTO payment_allocations(payment_id,item_id,amount_cents) VALUES(?,NULL,?)',(payment,remaining))
            remaining=amount
            for installment in self.installment_status(order_id):
                assigned=min(remaining,installment['balance_cents'])
                if assigned:
                    self.db.execute('INSERT INTO installment_allocations VALUES(?,?,?)',(payment,installment['id'],assigned))
                    self.db.execute('UPDATE installments SET received_cents=received_cents+? WHERE id=?',(assigned,installment['id'])); remaining-=assigned
                if not remaining: break
            if remaining: raise ValueError('Parcelamento inconsistente; nenhum pagamento foi consolidado.')
            self.storage.audit('pagamento recebido',f'payments:{payment}',None,self.get('payments',payment))
            self.emit_order(order_id,files)
            return payment

    def reserve_item(self,item_id,variant_id=None,*,piece_ids=None):
        with transaction(self.db):
            item=self.get('order_items',item_id); order=self.get('orders',item['order_id'])
            if order['state']=='cancelled': raise ValueError('Pedido cancelado não reserva peças.')
            if item['reservation_id'] is not None: raise ValueError('Este item já tem reserva vinculada.')
            existing=self.db.execute('SELECT variant_id FROM order_fulfillment WHERE item_id=?',(item_id,)).fetchone()
            expected=item['variant_id'] if item['variant_id'] is not None else existing[0] if existing else variant_id
            if expected is None: raise ValueError('Cadastre uma variante para as peças personalizadas e selecione-a para atendimento.')
            if variant_id is not None and variant_id!=expected: raise ValueError('Não é possível trocar a variante de um item aprovado.')
            if item['variant_id'] is None and existing is None:
                self.db.execute('INSERT INTO order_fulfillment VALUES(?,?)',(item_id,expected))
            reserved=self.inventory.reserve(expected,item['quantity'],order['code'],'order-item-'+str(item_id)+'-'+uuid.uuid4().hex,piece_ids=piece_ids)
            self.db.execute('UPDATE order_items SET reservation_id=? WHERE id=?',(reserved,item_id))
            self.storage.audit('pedido:peças reservadas',f'order_items:{item_id}',None,{'reservation_id':reserved})
            return reserved

    def release_item(self,item_id,reason):
        with transaction(self.db):
            item=self.get('order_items',item_id)
            order=self.get('orders',item['order_id'])
            if order['state']=='cancelled': raise ValueError('Pedido já cancelado.')
            if item['reservation_id'] is None: raise ValueError('Item não possui reserva.')
            self.inventory.finish_reservation(item['reservation_id'],'release',reason,order_id=order['id'])
            self.db.execute('UPDATE order_items SET reservation_id=NULL WHERE id=?',(item_id,))
            self.storage.audit('pedido:reserva liberada',f'order_items:{item_id}',item,None,reason)

    def link_calculation(self,item_id,calculation_id):
        with transaction(self.db):
            item=self.get('order_items',item_id)
            if self.get('orders',item['order_id'])['state']=='cancelled': raise ValueError('Pedido cancelado: vínculos existentes são preservados; produção adicional deve ser para estoque.')
            Catalog(self.storage).get('calculations',calculation_id)
            self.db.execute('INSERT INTO order_item_calculations VALUES(?,?,?)',(item_id,calculation_id,now()))
            self.storage.audit('pedido:cálculo vinculado',f'order_items:{item_id}',None,{'calculation_id':calculation_id})

    def cancel(self,order_id,reason,refund='0',future_credit='0',retained='0',refund_method='pix',refund_on=None,operation_key=None):
        required(reason,'Motivo e justificativa financeira')
        refund,credit,retained=cents(refund),cents(future_credit),cents(retained)
        refund_on=optional_date(refund_on or date.today().isoformat())
        if refund_on>date.today().isoformat(): raise ValueError('Reembolso efetivo não pode ter data futura.')
        if refund_method not in PAYMENT_METHODS or refund_method=='customer_credit': raise ValueError('Meio de reembolso inválido.')
        with self.event() as files:
            order=self.get('orders',order_id)
            if order['state']=='cancelled': raise ValueError('Pedido já cancelado.')
            delivery=self.delivery(order_id)
            # Cancellation never invents physical returns for already issued goods.
            finance=self.financial(order_id)
            if refund+credit+retained!=finance['paid']: raise ValueError('Reembolso + crédito futuro + retenção devem somar os pagamentos/créditos já aplicados.')
            if refund>finance['cash_received']: raise ValueError('Crédito aplicado não pode ser convertido em reembolso de dinheiro não recebido.')
            if refund and any(p['paid_on']>refund_on for p in self.payments(order_id)): raise ValueError('Reembolso não pode preceder os pagamentos do pedido.')
            key=operation_key or uuid.uuid4().hex
            cancellation=self.db.execute('INSERT INTO cancellations(order_id,reason,refund_cents,credit_cents,retained_cents,created_at,operation_key) VALUES(?,?,?,?,?,?,?)',
                (order_id,reason,refund,credit,retained,now(),key)).lastrowid
            if refund: self.db.execute('INSERT INTO refunds(cancellation_id,amount_cents,paid_on,method,reason) VALUES(?,?,?,?,?)',(cancellation,refund,refund_on,refund_method,reason))
            if credit: self.db.execute("INSERT INTO client_credit(client_id,order_id,direction,amount_cents,created_at,reason,operation_key) VALUES(?,?,'in',?,?,?,?)",(order['client_id'],order_id,credit,now(),reason,'cancel-credit-'+str(cancellation)))
            for item in self.items(order_id):
                if item['reservation_id'] and self.inventory.get('reservations',item['reservation_id'])['state']=='reserved':
                    self.inventory.finish_reservation(item['reservation_id'],'release',reason,order_id=order_id)
            self.db.execute("UPDATE orders SET state='cancelled' WHERE id=?",(order_id,))
            self.storage.audit('pedido cancelado',f'orders:{order_id}',order,{'cancellation_id':cancellation},reason)
            self.emit_order(order_id,files)
            return cancellation

    def delivery(self,order_id):
        self.get('orders',order_id)
        return dict(self.db.execute('SELECT * FROM deliveries WHERE order_id=?',(order_id,)).fetchone())

    def deliver(self,order_id,action,mode='pickup',carrier='',tracking='',occurred_on=None,proof=None):
        if action not in ('send','deliver') or mode not in ('pickup','shipping'): raise ValueError('Etapa de entrega inválida.')
        occurred_on=optional_date(occurred_on or date.today().isoformat())
        if occurred_on>date.today().isoformat(): raise ValueError('Data efetiva de entrega não pode ser futura.')
        with self.event() as files:
            order=self.get('orders',order_id); previous=self.delivery(order_id)
            if order['state']=='cancelled': raise ValueError('Pedido cancelado não pode ser entregue.')
            if previous['state']=='delivered' or action=='send' and previous['state']!='waiting': raise ValueError('Esta etapa de entrega já foi registrada.')
            if previous['state']=='waiting':
                if mode=='shipping' and action=='deliver': raise ValueError('Registre o envio antes da entrega pela transportadora.')
                for item in self.items(order_id):
                    if item['reservation_id'] is None: raise ValueError('Todos os itens devem ter peças disponíveis reservadas antes da saída.')
                    self.inventory.finish_reservation(item['reservation_id'],'issue','Entrega do pedido '+order['code'],order_id=order_id)
                proof_id=import_attachment(self.storage,proof,order_id=order_id,kind='delivery',created=files) if proof else None
                self.db.execute('UPDATE deliveries SET state=?,mode=?,carrier=?,tracking=?,sent_on=?,delivered_on=?,proof_id=? WHERE order_id=?',
                    ('sent' if action=='send' else 'delivered',mode,str(carrier),str(tracking),occurred_on,occurred_on if action=='deliver' else None,proof_id,order_id))
            else:
                if occurred_on<previous['sent_on']: raise ValueError('Entrega não pode preceder o envio.')
                proof_id=import_attachment(self.storage,proof,order_id=order_id,kind='delivery',created=files) if proof else previous['proof_id']
                self.db.execute("UPDATE deliveries SET state='delivered',delivered_on=?,proof_id=? WHERE order_id=?",(occurred_on,proof_id,order_id))
            if self.db.execute('PRAGMA user_version').fetchone()[0]>=6:
                from .finance import Finance
                Finance(self.storage).capture_costs()
            self.storage.audit('pedido:entrega',f'orders:{order_id}',previous,self.delivery(order_id))
            self.emit_order(order_id,files)

    def returnable_pieces(self,order_id):
        ids=[]
        for item in self.items(order_id):
            if item['reservation_id'] is None: continue
            for row in self.db.execute("SELECT piece_id FROM stock_movements WHERE kind='issue' AND operation_key LIKE ?",(f"issue:{item['reservation_id']}:%",)):
                if not self.db.execute('SELECT 1 FROM order_returns WHERE order_id=? AND piece_id=?',(order_id,row[0])).fetchone(): ids.append(row[0])
        return [self.inventory.get('pieces',key) for key in ids]

    def return_cancelled_pieces(self,order_id,piece_ids,condition,operation_key=None):
        from .journal import record
        required(condition,'Condição e confirmação do retorno físico')
        ids=self.inventory._unique_ids(piece_ids)
        key=operation_key or uuid.uuid4().hex
        with transaction(self.db):
            if self.get('orders',order_id)['state']!='cancelled': raise ValueError('Este fluxo é para peças de pedido cancelado.')
            allowed={p['id'] for p in self.returnable_pieces(order_id)}
            for identifier in ids:
                piece=self.inventory.get('pieces',identifier)
                if identifier not in allowed or piece['state']!='issued': raise ValueError('Peça não pertence à saída do pedido, já retornou ou não está baixada.')
                self.db.execute('INSERT INTO order_returns(order_id,piece_id,created_at,condition,operation_key) VALUES(?,?,?,?,?)',(order_id,identifier,now(),condition,key+'-'+str(identifier)))
                self.db.execute("UPDATE pieces SET state='quarantine',condition=? WHERE id=?",(condition,identifier))
                self.db.execute('UPDATE inspections SET valid=0 WHERE piece_id=?',(identifier,))
                self.db.execute("UPDATE production_orders SET state='inspection' WHERE id IN (SELECT e.op_id FROM production_entries e JOIN production_pieces pp ON pp.entry_id=e.id WHERE pp.piece_id=?)",(identifier,))
                record(self.storage,'return','piece',identifier,1000,'issued','quarantine',condition,'return-'+key+'-'+str(identifier),piece['unit_cost_cents'])
                self.storage.audit('pedido:retorno físico',f'pieces:{identifier}',piece,self.inventory.get('pieces',identifier),condition)

            if self.db.execute('PRAGMA user_version').fetchone()[0]>=6:
                from .finance import Finance
                Finance(self.storage).capture_costs()

    def documents(self,order_id=None,quote_id=None):
        column,identifier=('order_id',order_id) if order_id is not None else ('quote_id',quote_id)
        return [dict(r) for r in self.db.execute(f'SELECT * FROM sales_documents WHERE {column}=? ORDER BY version DESC',(identifier,))]

    def attachments(self,order_id):
        return [dict(r) for r in self.db.execute('SELECT * FROM sales_attachments WHERE order_id=? ORDER BY id',(order_id,))]

    def public_order(self,identifier):
        row=self.get('orders',identifier); financial=self.financial(identifier)
        cancellation=self.db.execute('SELECT * FROM cancellations WHERE order_id=?',(identifier,)).fetchone()
        return {'kind':'order','title':'Comprovante comercial '+row['code'],'code':row['code'],'client':json.loads(row['client_snapshot']),
            'items':[{k:item[k] for k in ('description','quantity','unit_price_cents','total_cents')} for item in self.items(identifier)],
            'freight_cents':row['freight_cents'],'total_cents':row['total_cents'],'notes':row['notes'],'due_on':self.date_br(row['due_on']),
            'payments':[{'paid_on':self.date_br(p['paid_on']),'method':PAYMENT_METHODS[p['method']],'amount_cents':p['amount_cents']} for p in self.payments(identifier)],
            'cash_received_cents':financial['cash_received'],'credit_applied_cents':financial['credit_applied'],
            'balance_cents':financial['balance'],'state':row['state'],'cancellation':dict(cancellation) if cancellation else None,
            'emitted_date':date.today().strftime('%d/%m/%Y')}

    @staticmethod
    def date_br(value):
        return date.fromisoformat(value).strftime('%d/%m/%Y') if value else ''

    def emit_order(self,identifier,files=None):
        return emit(self.storage,self.public_order(identifier),order_id=identifier,created=files)

    def emit_quote(self,identifier,files=None):
        row=self.get('quotes',identifier)
        public={'kind':'quote','title':'Orçamento '+row['code'],'code':row['code'],'client':json.loads(row['client_snapshot']),
            'items':[{k:item[k] for k in ('description','quantity','unit_price_cents','total_cents')} for item in json.loads(row['items'])],
            'freight_cents':row['freight_cents'],'total_cents':row['total_cents'],'notes':row['notes'],'valid_until':self.date_br(row['valid_until']),
            'emitted_date':date.today().strftime('%d/%m/%Y'),'state':self.quote_state(row)}
        return emit(self.storage,public,quote_id=identifier,created=files)

    def document_path(self,identifier):
        row=self.get('sales_documents',identifier)
        return owned_path(self.storage,row['path'],row['sha256'])

    def indicators(self):
        first=date.today().replace(day=1).isoformat()
        sold=self.db.execute("SELECT COALESCE(SUM(total_cents),0) FROM orders WHERE state='approved' AND substr(created_at,1,10)>=?",(first,)).fetchone()[0]
        received=self.db.execute("SELECT COALESCE(SUM(net_cents),0) FROM payments WHERE kind='cash' AND paid_on>=?",(first,)).fetchone()[0]
        refund=self.db.execute('SELECT COALESCE(SUM(amount_cents),0) FROM refunds WHERE paid_on>=?',(first,)).fetchone()[0]
        receivable=sum(self.financial(row['id'])['balance'] for row in self.orders() if row['state']=='approved')
        active=self.db.execute("SELECT count(*) FROM orders o JOIN deliveries d ON d.order_id=o.id WHERE o.state='approved' AND d.state!='delivered'").fetchone()[0]
        overdue=sum(1 for o in self.orders() for i in self.installment_status(o['id']) if i['status']=='overdue')
        return {'sold':sold,'net_received':received-refund,'receivable':receivable,'active_orders':active,'overdue_installments':overdue}
