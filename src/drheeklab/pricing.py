"""Pricing arithmetic. No binary floats, inventory, cash or sale recognition."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re

CENT = Decimal('0.01')


def number(value, label='Valor', places=None, minimum=Decimal('0')):
    if isinstance(value, (float, bool)):
        raise ValueError(f'{label}: use um número decimal, sem ponto flutuante.')
    try:
        text = str(value).strip()
        if ',' in text:
            if not re.fullmatch(r'[+\-]?(?:[0-9]+|[0-9]{1,3}(?:\.[0-9]{3})+),[0-9]+', text):
                raise ValueError('Formato decimal brasileiro inválido')
            text = text.replace('.', '').replace(',', '.')
        result = Decimal(text)
    except (InvalidOperation, ValueError):
        raise ValueError(f'{label}: número inválido.') from None
    if not result.is_finite() or result < minimum or result > Decimal('1000000000'):
        raise ValueError(f'{label}: valor fora do intervalo permitido.')
    if places is not None and result != result.quantize(Decimal(1).scaleb(-places)):
        raise ValueError(f'{label}: use no máximo {places} casas decimais.')
    return result


def money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def cents(value, label='Valor'):
    return int(number(value, label, places=2) * 100)


def grams_mg(value, label='Peso'):
    return int(number(value, label, places=3) * 1000)


def integer(value, label, minimum=0):
    parsed = number(value, label, places=0, minimum=Decimal(minimum))
    return int(parsed)


def brl(value):
    rendered = f'{money(value):,.2f}'
    return 'R$ ' + rendered.replace(',', '_').replace('.', ',').replace('_', '.')


def cost_per_gram(purchase, weight):
    weight = number(weight, 'Peso inicial', places=3, minimum=Decimal('0.001'))
    return number(purchase, 'Preço de compra', places=2) / weight


def hourly_cost(printer):
    return sum((Decimal(printer[key]) / 100 for key in ('investment_hour_cents', 'energy_hour_cents', 'maintenance_hour_cents')), Decimal('0'))


def calculate(printer, minutes, filaments, auxiliary='0', quantity=1, markup='200', final=None, actual=False):
    minutes = integer(minutes, 'Tempo em minutos')
    quantity = integer(quantity, 'Quantidade de peças', minimum=1)
    markup = number(markup, 'Acréscimo', places=2)
    auxiliary = money(number(auxiliary, 'Materiais auxiliares', places=2))
    machine = money(hourly_cost(printer) * Decimal(minutes) / 60)
    rows = []
    acquisition_total = Decimal('0')
    acquisition_known = True
    for filament in filaments:
        grams = number(filament['grams'], 'Consumo em gramas', places=3,
                       minimum=Decimal('0') if actual else Decimal('0.001'))
        reference = number(filament['reference_per_g'], 'Custo de referência por grama', places=6)
        initial_mg = filament.get('initial_mg')
        if grams == 0:
            acquired = Decimal('0.00')
        elif initial_mg is None:
            acquired = None
        else:
            acquisition_rate = cost_per_gram(Decimal(filament['purchase_cents']) / 100, Decimal(initial_mg) / 1000)
            acquired = money(grams * acquisition_rate)
        if acquired is None:
            acquisition_known = False
        else:
            acquisition_total += acquired
        rows.append({**filament, 'grams': str(grams), 'cost': str(money(grams * reference)),
                     'acquisition_cost': str(acquired) if acquired is not None else None})
    materials = sum((Decimal(row['cost']) for row in rows), Decimal('0'))
    total = money(machine + materials + auxiliary)
    suggested = money(total * (1 + markup / 100))
    final_value = suggested if final is None else money(number(final, 'Preço final total', places=2))
    difference = suggested - final_value
    kind = 'desconto' if difference > 0 else 'acréscimo' if difference < 0 else 'sem alteração'
    percent = money(abs(difference) / suggested * 100) if suggested else None
    acquisition_production = money(machine + auxiliary + acquisition_total) if acquisition_known else None
    return {'confirmed': actual, 'acquisition_material_cost': str(acquisition_total) if acquisition_known else None,
            'acquisition_production_cost': str(acquisition_production) if acquisition_production is not None else None,
            'acquisition_commercial_result': str(money(final_value - acquisition_production)) if acquisition_production is not None else None,
            'printer': dict(printer), 'minutes': minutes, 'filaments': rows,
            'auxiliary': str(auxiliary), 'quantity': quantity, 'markup': str(markup),
            'machine_cost': str(machine), 'material_cost': str(materials),
            'total_cost': str(total), 'unit_cost': str(money(total / quantity)),
            'suggested_total': str(suggested), 'suggested_unit': str(money(suggested / quantity)),
            'final_total': str(final_value), 'adjustment_kind': kind,
            'adjustment_amount': str(abs(difference)),
            'adjustment_percent': str(percent) if percent is not None else None,
            'commercial_result': str(money(final_value - total))}


def compare(planned, actual):
    old = Decimal(planned['total_cost'])
    new = Decimal(actual['total_cost'])
    difference = money(new - old)
    return {'planned': str(old), 'actual': str(new), 'difference': str(difference),
            'percent': str(money(difference / old * 100)) if old else None}
