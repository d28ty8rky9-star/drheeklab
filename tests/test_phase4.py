from datetime import date,timedelta
from decimal import Decimal
import json
import sqlite3
import pytest
from pypdf import PdfReader
from PySide6.QtGui import QImage,QColor
from drheeklab.storage import Storage,SCHEMA_VERSION
from drheeklab.sales import Sales
from drheeklab.products import Products
from drheeklab.inventory import Inventory
from drheeklab.catalog import Catalog
from drheeklab.backup import create_backup,restore_backup,verify_backup
from drheeklab.transactions import transaction

@pytest.fixture
def system(tmp_path):
    store=Storage(tmp_path/'data'); sales=Sales(store)
    client=sales.save_client({'name':'Cliente Árvore','phone':'(11) 99999-0000','email':'cliente@example.com'})
    yield store,sales,client
    try:store.close()
    except sqlite3.ProgrammingError:pass


def custom(price='90',quantity=1,**extra):
    return {'description':'Peça personalizada','quantity':quantity,'unit_price':price,'fulfillment':'production',**extra}


def stock(system,count=5):
    store,sales,client=system
    product=sales.products.save({'name':'Suporte','category':'functional','planned_cost':'12.34','suggested_price':'35'})
    variant=sales.products.variants(product)[0]['id']
    _,ids=sales.inventory.receive(variant,count,'Estoque inicial','available','Nova','initial',total_cost='50',reviewer='Responsável')
    return variant,ids


def pdf_text(sales,document):
    return '\n'.join(page.extract_text() for page in PdfReader(sales.document_path(document)).pages)


def test_clients_validation_archival_and_historical_snapshot(system):
    store,sales,client=system
    for data in ({'name':''},{'name':None},{'name':'Nome','email':'invalid'}):
        with pytest.raises(ValueError):sales.save_client(data)
    order=sales.create_order(client,[custom()])
    sales.save_client({'name':'Nome alterado','phone':'123'},client)
    assert json.loads(sales.get('orders',order)['client_snapshot'])['name']=='Cliente Árvore'
    sales.archive_client(client,True,'Sem novas vendas')
    with pytest.raises(ValueError):sales.create_order(client,[custom()])
    assert sales.orders(client)[0]['id']==order
    sales.archive_client(client,False,'Restaurar')
    assert sales.clients()[0]['name']=='Nome alterado'


def test_quote_has_no_revenue_payment_or_stock_effect_and_default_validity(system):
    store,sales,client=system
    variant,ids=stock(system)
    quote=sales.create_quote(client,[custom('35',2,variant_id=variant,fulfillment='stock')],freight='5')
    row=sales.get('quotes',quote)
    assert row['valid_until']==(date.today()+timedelta(days=7)).isoformat()
    assert row['total_cents']==7500
    assert sales.orders()==[]
    assert store.db.execute('SELECT count(*) FROM payments').fetchone()[0]==0
    assert sales.inventory.summary()[0]['available']==5
    assert sales.indicators()['sold']==0
    assert sales.indicators()['net_received']==0
    text=pdf_text(sales,sales.documents(quote_id=quote)[0]['id'])
    assert 'Cliente Árvore' in text and 'R$ 75,00' in text
    assert '12,34' not in text and 'Custo' not in text and 'Desconto' not in text


def test_quote_approval_copies_snapshots_reserves_once_and_rolls_back_if_unavailable(system):
    store,sales,client=system
    variant,ids=stock(system)
    quote=sales.create_quote(client,[custom('35',2,variant_id=variant,fulfillment='stock')],freight='5')
    order=sales.approve_quote(quote)
    assert sales.get('quotes',quote)['state']=='approved'
    assert sales.get('orders',order)['quote_id']==quote
    assert sales.items(order)[0]['quantity']==2
    assert sales.inventory.summary()[0]['physical']==5
    assert sales.inventory.summary()[0]['available']==3
    with pytest.raises(ValueError):sales.approve_quote(quote)
    too_many=sales.create_quote(client,[custom('35',4,variant_id=variant,fulfillment='stock')])
    with pytest.raises(ValueError):sales.approve_quote(too_many)
    assert sales.get('quotes',too_many)['state']=='pending'
    assert len(sales.orders())==1
    assert sales.inventory.summary()[0]['reserved']==2


def test_expiry_rejection_and_blank_validity(system):
    store,sales,client=system
    expired=sales.create_quote(client,[custom()],valid_until=(date.today()-timedelta(days=1)).isoformat())
    assert sales.quotes()[0]['display_state']=='expired'
    with pytest.raises(ValueError):sales.approve_quote(expired)
    unlimited=sales.create_quote(client,[custom()],valid_until=None)
    assert sales.get('quotes',unlimited)['valid_until'] is None
    sales.reject_quote(unlimited,'Cliente recusou')
    with pytest.raises(ValueError):sales.approve_quote(unlimited)
    assert sales.get('quotes',unlimited)['reason']=='Cliente recusou'


def test_partial_payments_fees_fifo_freight_and_installments_reconcile(system):
    store,sales,client=system
    order=sales.create_order(client,[custom('30'),custom('20',2)],freight='10',installments=[{'amount':'40','due_on':None},{'amount':'40','due_on':None}])
    first=sales.receive_payment(order,'35','credit_card','1.05')
    assert sales.financial(order)=={'total':8000,'paid':3500,'cash_received':3500,'credit_applied':0,'fees':105,'net_received':3395,'balance':4500,'refunded':0,'credited':0,'retained':0}
    items=sales.items(order)
    allocations=store.db.execute('SELECT item_id,amount_cents FROM payment_allocations WHERE payment_id=? ORDER BY id',(first,)).fetchall()
    assert [(r[0],r[1]) for r in allocations]==[(items[0]['id'],3000),(items[1]['id'],500)]
    assert [r['received_cents'] for r in sales.installment_status(order)]==[3500,0]
    second=sales.receive_payment(order,'45','pix')
    assert sales.financial(order)['balance']==0
    allocations=store.db.execute('SELECT item_id,amount_cents FROM payment_allocations WHERE payment_id=? ORDER BY id',(second,)).fetchall()
    assert [(r[0],r[1]) for r in allocations]==[(items[1]['id'],3500),(None,1000)]
    assert all(r['status']=='paid' for r in sales.installment_status(order))
    assert store.db.execute('SELECT sum(amount_cents) FROM installment_allocations').fetchone()[0]==8000
    with pytest.raises(ValueError):sales.receive_payment(order,'1')


def test_installments_rounding_month_ends_and_overdue_partial_status(system):
    store,sales,client=system
    rows=sales.split_installments(10001,3,'2026-01-31')
    assert [r['amount'] for r in rows]==['33.34','33.34','33.33']
    assert [r['due_on'] for r in rows]==['2026-01-31','2026-02-28','2026-03-31']
    order=sales.create_order(client,[custom('100.01')],installments=rows)
    sales.receive_payment(order,'10')
    assert sales.installment_status(order)[0]['status']=='overdue'
    assert sales.installment_status(order)[0]['balance_cents']==2334
    assert sales.indicators()['overdue_installments']==3
    with pytest.raises(ValueError):sales.create_order(client,[custom('100')],installments=[{'amount':'99','due_on':None}])
    assert len(sales.orders())==1


@pytest.mark.parametrize('amount,fee,method', [('0','0','pix'),('-1','0','pix'),('1','2','credit_card'),('1.001','0','pix'),('1','0','unknown')])
def test_invalid_payments_have_no_effect(system,amount,fee,method):
    store,sales,client=system
    order=sales.create_order(client,[custom()])
    with pytest.raises(ValueError):sales.receive_payment(order,amount,method,fee)
    assert sales.payments(order)==[]
    assert len(sales.documents(order_id=order))==1


def test_future_receipt_date_and_duplicate_key_are_rejected(system):
    store,sales,client=system
    order=sales.create_order(client,[custom()])
    with pytest.raises(ValueError):sales.receive_payment(order,'10',paid_on=(date.today()+timedelta(days=1)).isoformat())
    sales.receive_payment(order,'10',operation_key='unique-payment')
    with pytest.raises(sqlite3.IntegrityError):sales.receive_payment(order,'10',operation_key='unique-payment')
    assert sales.financial(order)['paid']==1000
    assert len(sales.documents(order_id=order))==2


def test_new_receipt_version_preserves_old_pdf_and_customer_prices(system):
    store,sales,client=system
    order=sales.create_order(client,[custom('90')])
    original=sales.documents(order_id=order)[0]
    content=sales.document_path(original['id']).read_bytes()
    sales.receive_payment(order,'35')
    partial=sales.documents(order_id=order)[0]
    assert partial['version']==2
    text=pdf_text(sales,partial['id'])
    assert 'R$ 55,00' in text and 'R$ 35,00' in text
    assert 'QUITADO' not in text
    sales.receive_payment(order,'55')
    latest=sales.documents(order_id=order)[0]
    assert latest['version']==3 and 'QUITADO' in pdf_text(sales,latest['id'])
    assert 'Não é nota fiscal' in pdf_text(sales,latest['id'])
    assert sales.document_path(original['id']).read_bytes()==content


def test_pdf_failure_rolls_back_payments_installments_and_new_files(system,monkeypatch):
    store,sales,client=system
    order=sales.create_order(client,[custom()])
    files=set((store.home/'Pedidos e Comprovantes').iterdir())
    def fail(*args):raise RuntimeError('PDF failed')
    monkeypatch.setattr('drheeklab.sales_documents.render_pdf',fail)
    with pytest.raises(RuntimeError):sales.receive_payment(order,'10')
    assert sales.payments(order)==[]
    assert sales.financial(order)['balance']==9000
    assert sales.installment_status(order)[0]['received_cents']==0
    assert set((store.home/'Pedidos e Comprovantes').iterdir())==files


def test_initial_deposit_nested_event_failure_leaves_no_order_reservation_or_pdf(system):
    store,sales,client=system
    variant,ids=stock(system)
    files=set((store.home/'Pedidos e Comprovantes').iterdir())
    with pytest.raises(ValueError):
        with sales.event():
            order=sales.create_order(client,[custom('35',variant_id=variant,fulfillment='stock')])
            sales.receive_payment(order,'99')
    assert sales.orders()==[]
    assert sales.inventory.summary()[0]['available']==5
    assert sales.inventory.reservations()==[]
    assert set((store.home/'Pedidos e Comprovantes').iterdir())==files


def test_cancellation_refund_credit_retention_releases_stock_and_preserves_cost(system):
    store,sales,client=system
    variant,ids=stock(system)
    order=sales.create_order(client,[custom('100',variant_id=variant,fulfillment='stock')])
    sales.receive_payment(order,'50','credit_card','1.50')
    before=[p['unit_cost_cents'] for p in sales.inventory.pieces()]
    cancelled=sales.cancel(order,'Cliente desistiu; retenção justificada pelo acordo','20','20','10')
    f=sales.financial(order)
    assert (f['balance'],f['refunded'],f['credited'],f['retained'])==(0,2000,2000,1000)
    assert sales.credit_balance(client)==2000
    assert sales.inventory.summary()[0]['available']==5
    assert [p['unit_cost_cents'] for p in sales.inventory.pieces()]==before
    assert sales.get('orders',order)['state']=='cancelled'
    assert 'PEDIDO CANCELADO' in pdf_text(sales,sales.documents(order_id=order)[0]['id'])
    assert 'QUITADO' not in pdf_text(sales,sales.documents(order_id=order)[0]['id'])
    with pytest.raises(ValueError):sales.cancel(order,'Repetir','20','20','10')
    with pytest.raises(ValueError):sales.receive_payment(order,'1')
    assert store.db.execute('SELECT count(*) FROM refunds').fetchone()[0]==1


def test_customer_credit_can_be_used_without_fake_cash_and_cannot_be_cashed_out(system):
    store,sales,client=system
    first=sales.create_order(client,[custom('50')]);sales.receive_payment(first,'50');sales.cancel(first,'Crédito acordado',future_credit='50')
    order=sales.create_order(client,[custom('30')]);sales.receive_payment(order,'20','customer_credit')
    assert sales.credit_balance(client)==3000
    assert sales.financial(order)['net_received']==0
    assert sales.financial(order)['cash_received']==0
    assert sales.financial(order)['credit_applied']==2000
    assert sales.financial(order)['balance']==1000
    with pytest.raises(ValueError):sales.cancel(order,'Não criar dinheiro',refund='20')
    sales.cancel(order,'Devolver crédito',future_credit='20')
    assert sales.credit_balance(client)==5000
    assert sales.indicators()['net_received']==5000


def test_invalid_cancellation_and_failure_restore_stock_and_payment_history(system,monkeypatch):
    store,sales,client=system
    variant,ids=stock(system)
    order=sales.create_order(client,[custom('100',variant_id=variant,fulfillment='stock')]);sales.receive_payment(order,'30')
    with pytest.raises(ValueError):sales.cancel(order,'Valor insuficiente',refund='10')
    assert sales.get('orders',order)['state']=='approved'
    original=sales.storage.audit
    def fail(operation,*args):
        if operation=='pedido cancelado':raise RuntimeError('Audit failed')
        return original(operation,*args)
    monkeypatch.setattr(sales.storage,'audit',fail)
    with pytest.raises(RuntimeError):sales.cancel(order,'Falha',refund='30')
    assert sales.get('orders',order)['state']=='approved'
    assert sales.inventory.summary()[0]['reserved']==1
    assert store.db.execute('SELECT count(*) FROM refunds').fetchone()[0]==0


def test_delivery_and_pickup_issue_stock_once_and_owned_reserves_are_protected(system):
    store,sales,client=system
    variant,ids=stock(system)
    order=sales.create_order(client,[custom('35',2,variant_id=variant,fulfillment='stock')])
    reserve=sales.items(order)[0]['reservation_id']
    with pytest.raises(ValueError,match='Vendas'):sales.inventory.finish_reservation(reserve,'issue','Tentativa externa')
    sales.deliver(order,'send','shipping','Transportadora','TRACK-123')
    assert sales.delivery(order)['state']=='sent'
    assert sales.inventory.summary()[0]['physical']==3
    sales.deliver(order,'deliver','shipping')
    assert sales.delivery(order)['state']=='delivered'
    assert sales.inventory.summary()[0]['physical']==3
    assert sales.delivery(order)['tracking']=='TRACK-123'
    with pytest.raises(ValueError):sales.deliver(order,'deliver')
    assert sales.financial(order)['balance']==7000
    pickup=sales.create_order(client,[custom('35',variant_id=variant,fulfillment='stock')]);sales.deliver(pickup,'deliver','pickup')
    assert sales.inventory.summary()[0]['physical']==2


def test_custom_production_attachment_mapping_and_no_delivery_before_ready(system,tmp_path):
    store,sales,client=system
    source=tmp_path/'model.stl';source.write_text('solid original\nendsolid original\n')
    quote=sales.create_quote(client,[custom(files=[str(source)])]);order=sales.approve_quote(quote)
    assets=sales.attachments(order);assert len(assets)==1
    assert assets[0]['original_name']=='model.stl'
    source.unlink()
    assert (store.home/assets[0]['path']).exists()
    with pytest.raises(ValueError):sales.deliver(order,'deliver','pickup')
    variant,ids=stock(system)
    item=sales.items(order)[0]['id'];sales.reserve_item(item,variant)
    original=sales.get('order_items',item)
    assert original['variant_id'] is None and original['description']=='Peça personalizada'
    sales.deliver(order,'deliver','pickup')
    assert sales.inventory.summary()[0]['physical']==4


def test_shipping_pdf_proof_and_return_after_cancel_preserve_cost_and_require_reinspection(system,tmp_path):
    store,sales,client=system
    variant,ids=stock(system)
    order=sales.create_order(client,[custom('35',variant_id=variant,fulfillment='stock')]);sales.receive_payment(order,'35')
    proof=sales.document_path(sales.documents(order_id=order)[0]['id'])
    sales.deliver(order,'send','shipping','Correios','ABC',proof=str(proof))
    assert sales.delivery(order)['proof_id']
    sales.cancel(order,'Cancelamento durante transporte',refund='35')
    assert sales.inventory.summary()[0]['physical']==4
    returnable=sales.returnable_pieces(order); assert len(returnable)==1
    key=returnable[0]['id'];cost=returnable[0]['unit_cost_cents']
    sales.return_cancelled_pieces(order,[key],'Recebida fisicamente; embalagem danificada','return')
    assert sales.inventory.get('pieces',key)['state']=='quarantine'
    assert sales.inventory.get('pieces',key)['unit_cost_cents']==cost
    assert sales.inventory.summary()[0]['physical']==5
    assert sales.inventory.summary()[0]['available']==4
    with pytest.raises(ValueError):sales.return_cancelled_pieces(order,[key],'Não duplicar')
    sales.inventory.review([key],'approved','Peça íntegra após verificação','Responsável')
    assert sales.inventory.summary()[0]['available']==5


def test_incurred_calculation_survives_cancel_and_can_enter_stock_without_new_consumption(system):
    store,sales,client=system
    variant,ids=stock(system)
    catalog=Catalog(store)
    filament=catalog.save_filament({'name':'PLA','brand':'Marca','material':'PLA','color':'Azul','purchase':'100','initial_grams':'1000','remaining_grams':'1000','reference_per_g':'0.1'})
    calc=catalog.save_calculation('Produção iniciada',1,60,[(filament,'100')]);catalog.confirm_actual(calc,60,{filament:'100'})
    order=sales.create_order(client,[custom(variant_id=variant)]);item=sales.items(order)[0]['id'];sales.link_calculation(item,calc)
    sales.cancel(order,'Cliente cancelou antes de receber')
    assert catalog.get('calculations',calc)['actual']
    sales.inventory.receive(variant,1,'Peça concluída após cancelamento','quarantine','Nova','stock-from-cancel',calculation_id=calc)
    assert catalog.get('filaments',filament)['remaining_mg']==900000
    assert catalog.get('printers',1)['accumulated_minutes']==60
    assert sales.inventory.summary()[0]['physical']==6


def test_backup_restores_sales_payments_credit_pdfs_and_attachments(system,tmp_path):
    store,sales,client=system
    variant,ids=stock(system)
    image=QImage(40,40,QImage.Format_RGB32);image.fill(QColor('#662299'));photo=tmp_path/'reference.png';assert image.save(str(photo))
    order=sales.create_order(client,[custom('35',variant_id=variant,fulfillment='stock',files=[str(photo)])])
    sales.receive_payment(order,'10')
    original=sales.financial(order);docs=sales.documents(order_id=order)
    snapshot=create_backup(store);assert verify_backup(snapshot,'test')
    sales.receive_payment(order,'25')
    restore_backup(store,snapshot)
    reopened=Storage(store.root);restored=Sales(reopened)
    assert restored.financial(order)==original
    assert len(restored.documents(order_id=order))==2
    assert restored.document_path(docs[0]['id']).is_file()
    assert (reopened.home/restored.attachments(order)[0]['path']).exists()
    assert Inventory(reopened).summary()[0]['reserved']==1
    assert reopened.db.execute('PRAGMA foreign_key_check').fetchall()==[]
    reopened.close()


def test_real_phase3_upgrade_preserves_stock_password_and_old_backups(tmp_path,monkeypatch):
    import drheeklab.storage as module
    from drheeklab.security import Auth
    with monkeypatch.context() as patch:
        patch.setattr(module,'SCHEMA_VERSION',3)
        old=Storage(tmp_path);Auth(old).create('senha preservada')
        products=Products(old);product=products.save({'name':'Antigo','category':'decorative'});variant=products.variants(product)[0]['id']
        inventory=Inventory(old);inventory.receive(variant,2,'Anterior','available','Nova','old',total_cost='10',reviewer='Responsável')
        snapshot=create_backup(old);old.close()
    updated=Storage(tmp_path)
    assert updated.db.execute('PRAGMA user_version').fetchone()[0]==SCHEMA_VERSION
    assert Auth(updated).verify('senha preservada')
    assert Inventory(updated).summary()[0]['physical']==2
    assert Sales(updated).clients()==[]
    restore_backup(updated,snapshot)
    reopened=Storage(tmp_path)
    assert Auth(reopened).verify('senha preservada')
    assert Inventory(reopened).summary()[0]['physical']==2
    assert Sales(reopened).orders()==[]
    reopened.close()

def test_long_custom_descriptions_produce_valid_multipage_pdf(system):
    store,sales,client=system
    description='Descrição personalizada longa para o cliente. '*400
    quote=sales.create_quote(client,[custom(description=description)])
    path=sales.document_path(sales.documents(quote_id=quote)[0]['id'])
    reader=PdfReader(path)
    assert len(reader.pages)>1
    text='\n'.join(page.extract_text() for page in reader.pages)
    assert 'R$ 90,00' in text and 'Validade:' in text


def test_approved_and_rejected_quote_pdfs_get_new_versions_without_overwriting(system):
    store,sales,client=system
    quote=sales.create_quote(client,[custom()])
    original=sales.documents(quote_id=quote)[0]
    content=sales.document_path(original['id']).read_bytes()
    sales.approve_quote(quote)
    approved=sales.documents(quote_id=quote)[0]
    assert approved['version']==2 and 'Aprovado' in pdf_text(sales,approved['id'])
    assert sales.document_path(original['id']).read_bytes()==content
    other=sales.create_quote(client,[custom()]);sales.reject_quote(other,'Não aprovado')
    assert 'Rejeitado' in pdf_text(sales,sales.documents(quote_id=other)[0]['id'])
