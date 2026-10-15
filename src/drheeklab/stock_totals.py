"""Read-only acquisition valuation; unknown filament balances are never guessed."""
from decimal import Decimal,ROUND_HALF_UP
from .catalog import Catalog

def filament_value(row):
    if row['state']=='finished':return 0
    if row['remaining_mg'] is None or not row['initial_mg']:return None
    return int((Decimal(row['purchase_cents'])*row['remaining_mg']/row['initial_mg']).quantize(Decimal('1'),rounding=ROUND_HALF_UP))

def stock_totals(inventory):
    spools=[r for r in Catalog(inventory.storage).rows('filaments') if r['state']!='finished']
    known=[r for r in spools if filament_value(r) is not None]
    filament_cents=sum(filament_value(r) for r in known)
    accessories={r[0] for r in inventory.db.execute('SELECT v.id FROM variants v JOIN accessory_products a ON a.product_id=v.product_id')}
    held=[r for r in inventory.pieces() if r['state'] in ('available','reserved','quarantine','personal')]
    pieces=[r for r in held if r['variant_id'] not in accessories];extra=[r for r in held if r['variant_id'] in accessories]
    return {'filament_cents':filament_cents,'filament_mg':sum(r['remaining_mg'] for r in spools if r['remaining_mg'] is not None),'filament_unknown':sum(r['remaining_mg'] is None for r in spools),'filament_unvalued':len(spools)-len(known),'piece_count':len(pieces),'piece_cents':sum(r['unit_cost_cents'] for r in pieces),'accessory_count':len(extra),'accessory_cents':sum(r['unit_cost_cents'] for r in extra)}
