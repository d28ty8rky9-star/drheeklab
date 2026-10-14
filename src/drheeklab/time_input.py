"""Hours in forms, integer minutes in historical records and calculations."""
from decimal import Decimal, ROUND_HALF_UP
from .pricing import number,integer

def hours_to_minutes(value):
    return int((number(value,'Tempo em horas')*60).quantize(Decimal('1'),rounding=ROUND_HALF_UP))

def minutes_to_hours(value):
    value=Decimal(integer(value,'Tempo em minutos'))/60
    return format(value.quantize(Decimal('.000001')), 'f').rstrip('0').rstrip('.') or '0'
