"""Per-piece accessories are planning costs, never stock or cash movements."""
from decimal import Decimal
from .catalog import required
from .pricing import number,money

def calculate_extras(entries):
    if len(entries)>100:raise ValueError('Máximo de 100 extras por peça.')
    rows=[];total=Decimal('0')
    for entry in entries:
        name=required(entry.get('name',''),'Nome do extra')
        quantity=number(entry.get('quantity','1'),'Quantidade do extra',places=3,minimum=Decimal('.001'))
        unit=number(entry.get('unit_cost','0'),'Custo unitário do extra',places=2)
        subtotal=money(quantity*unit);total+=subtotal
        rows.append({'name':name,'quantity':str(quantity),'unit_cost':str(unit),'total_cost':str(subtotal)})
    return rows,money(total)
