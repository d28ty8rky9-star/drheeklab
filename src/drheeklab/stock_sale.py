"""Unit pricing uses immutable stock cost, never another production expense."""
from decimal import Decimal,ROUND_HALF_UP
import json,uuid
from .pricing import cents

class StockSales:
    def stock_choice(self,piece_id):
        piece=next((p for p in self.inventory.pieces() if p['id']==piece_id),None)
        if not piece or piece['state']!='available':raise ValueError('A peça não está disponível no Estoque.')
        variant=self.products.active_variant(piece['variant_id']);product=self.products.active_product(variant['product_id'])
        accessory=bool(self.db.execute('SELECT 1 FROM accessory_products WHERE product_id=?',(product['id'],)).fetchone())
        receipt=self.inventory.get('receipts',piece['receipt_id'])
        linked=self.db.execute('SELECT o.*,e.id entry_id FROM production_pieces pp JOIN production_entries e ON e.id=pp.entry_id JOIN production_orders o ON o.id=e.op_id WHERE pp.piece_id=?',(piece_id,)).fetchone()
        purchased=bool(self.db.execute('SELECT 1 FROM purchased_products WHERE product_id=?',(product['id'],)).fetchone()) or (not linked and receipt['calculation_id'] is None)
        kind='accessory' if accessory else 'purchased' if purchased else 'produced'
        markup={'produced':100,'purchased':30,'accessory':0}[kind]
        details={'receipt_source':receipt['source'],'op':None,'attempts':[],'extras':[]}
        if linked:
            details['op']=linked['code']
            for attempt in self.db.execute('SELECT * FROM production_attempts WHERE op_id=? ORDER BY id',(linked['id'],)):
                for actual in json.loads(attempt['actual']):
                    if actual['entry_id']==linked['entry_id']:
                        details['attempts'].append({'minutes_batch':attempt['minutes'],'machine_cents':actual['machine_cents'],'cost':actual['cost'],'quantity':actual['quantity'],'failed':actual['failed']})
            saved=self.db.execute('SELECT recipe FROM recipe_orders WHERE op_id=?',(linked['id'],)).fetchone()
            if saved:details['extras']=json.loads(saved[0])['data'].get('extras',[])
        elif receipt['cost_snapshot']:
            details['receipt_snapshot']=json.loads(receipt['cost_snapshot'])
        embedded=min(piece['unit_cost_cents'],sum(cents(e['total_cost']) for e in details['extras'])) if kind=='produced' else 0
        recommended=int((Decimal(piece['unit_cost_cents']-embedded)*(100+markup)/100+embedded).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
        return {**piece,'kind':kind,'markup_percent':markup,'suggested_cents':recommended,'embedded_accessory_cents':embedded,'details':details}

    def stock_sale_quote(self,piece_ids,accessory_ids=(),*,resale_accessories='cost'):
        ids=list(piece_ids)+list(accessory_ids)
        if not piece_ids:raise ValueError('Selecione uma peça do Estoque.')
        if len(ids)!=len(set(ids)):raise ValueError('Uma unidade não pode aparecer duas vezes na venda.')
        products=[self.stock_choice(i) for i in piece_ids];accessories=[self.stock_choice(i) for i in accessory_ids]
        if any(p['kind']=='accessory' for p in products) or any(p['kind']!='accessory' for p in accessories):raise ValueError('Selecione peças e acessórios em suas listas correspondentes.')
        if resale_accessories!='cost':raise ValueError('Acessórios são cobrados pelo custo, sem acréscimo.')
        rows=[]
        for piece in products+accessories:
            row=dict(piece)
            rows.append(row)
        return {'items':rows,'cost_cents':sum(p['unit_cost_cents'] for p in rows),'suggested_cents':sum(p['suggested_cents'] for p in rows),'resale_accessories':resale_accessories}

    def create_stock_sale(self,client_id,piece_ids,accessory_ids=(),actual_total=None,*,resale_accessories='cost',notes='',operation_key=None):
        from .production import split
        with self.event() as files:
            quote=self.stock_sale_quote(piece_ids,accessory_ids,resale_accessories=resale_accessories)
            total=quote['suggested_cents'] if actual_total is None else cents(actual_total,'Valor realmente vendido')
            accessory_total=sum(p['unit_cost_cents'] for p in quote['items'] if p['kind']=='accessory')
            if total<accessory_total:raise ValueError('O total da venda deve cobrir os acessórios cobrados pelo custo.')
            products=[p for p in quote['items'] if p['kind']!='accessory']
            weights=[p['suggested_cents'] for p in products]
            product_values=iter(split(total-accessory_total,weights if sum(weights) else [1]*len(weights)))
            allocation=[p['unit_cost_cents'] if p['kind']=='accessory' else next(product_values) for p in quote['items']]
            items=[{'variant_id':p['variant_id'],'quantity':1,'unit_price':str(Decimal(value)/100),'fulfillment':'stock','piece_ids':[p['id']]} for p,value in zip(quote['items'],allocation)]
            rows=self.prepare_items(items)
            for row,piece in zip(rows,quote['items']):
                row['snapshot']['pricing']={'piece_id':piece['id'],'kind':piece['kind'],'markup_percent':piece['markup_percent'],'cost_cents':piece['unit_cost_cents'],'suggested_cents':piece['suggested_cents'],'embedded_accessory_cents':piece.get('embedded_accessory_cents',0),'resale_accessories':resale_accessories,'details':piece['details']}
                row['snapshot']['variant']['suggested_price_cents']=piece['suggested_cents']
            order=self._insert_order(self.active_client(client_id),rows,0,None,notes,None,operation_key or uuid.uuid4().hex,files)
            self.storage.audit('venda:estoque e preço',f'orders:{order}',None,{'suggested_cents':quote['suggested_cents'],'actual_cents':total,'piece_ids':list(piece_ids),'accessory_ids':list(accessory_ids)})
        return order

def render_stock_cost(piece):
    from .pricing import brl
    from .time_input import minutes_to_hours
    def money(v):return brl(Decimal(v)/100)
    kind={'produced':'Produzida • +100%','purchased':'Comprada • +30%','accessory':'Acessório • sem acréscimo'}[piece['kind']]
    lines=[f"{piece['product_name']} / {piece['variant_name']} • unidade #{piece['id']}",kind+' • Custo da unidade: '+money(piece['unit_cost_cents'])+' • Sugerido: '+money(piece['suggested_cents'])]
    d=piece['details']
    if d['op']:
        lines.append('Origem: '+d['op']+' • dados do lote/tentativas; custo unitário acima já inclui rateio e perdas.')
        for a in d['attempts']:
            lines.append('Tempo total da tentativa: '+minutes_to_hours(a['minutes_batch'])+' h • Custo de máquina alocado a este modelo: '+money(a['machine_cents']))
            for f in a['cost']['filaments']:
                cost=f.get('acquisition_cost')
                lines.append(f"Filamento {f['name']}: {f['grams']} g no lote • {brl(Decimal(cost if cost is not None else f['cost']))}")
            lines.append('Adicionais totais do lote (incluem extras): '+brl(Decimal(a['cost']['auxiliary'])))
        for e in d['extras']:lines.append(f"Extra por peça: {e['name']} • {e['quantity']} × {brl(Decimal(e['unit_cost']))} = {brl(Decimal(e['total_cost']))} (já incluído)")
    else:
        lines.append('Origem: '+d['receipt_source'])
        snapshot=d.get('receipt_snapshot',{})
        if 'printer' in snapshot:
            lines.append('Tempo do lote: '+minutes_to_hours(snapshot['minutes'])+' h • Máquina: '+brl(Decimal(snapshot['machine_cost'])))
            for f in snapshot['filaments']:lines.append(f"Filamento {f['name']}: {f['grams']} g • {brl(Decimal(f.get('acquisition_cost') or f['cost']))}")
        elif piece['kind']!='accessory':lines.append('Sem horas ou filamentos de impressão registrados nesta entrada. Não são custos adicionais da venda.')
    return '\n'.join(lines)
