"""CSV and Excel exports with explicit money columns and literal user text."""
import csv
from pathlib import Path
from openpyxl import Workbook
from .storage import now

DATASETS=('metrics','sales','cash','payables','receivables','production','products','printers','stock_losses','production_adjustments','reconciliation')
NAMES={'metrics':'Indicadores','sales':'Vendas','cash':'Caixa','payables':'Contas a pagar','receivables':'Contas a receber','production':'Produção','products':'Produtos','printers':'Impressoras','stock_losses':'Perdas de estoque','production_adjustments':'Perdas e absorção','reconciliation':'Reconciliação'}


def rows(report,dataset):
    if dataset not in DATASETS:raise ValueError('Relatório inválido.')
    value=report['metrics'] if dataset=='metrics' else report[dataset]
    if isinstance(value,dict):return [{'indicador':k,'valor':v} for k,v in value.items()]
    return value


def printable(value):
    if isinstance(value,(dict,list)):return str(value)
    return '' if value is None else value


def csv_safe(value):
    if isinstance(value,str) and value.lstrip().startswith(('=','+','-','@')):return "'"+value
    return value


def export_csv(report,path,dataset='cash'):
    path=Path(path)
    if path.suffix.lower()!='.csv':raise ValueError('Escolha arquivo .csv.')
    data=rows(report,dataset);headers=list(dict.fromkeys(k for r in data for k in r))
    with path.open('w',encoding='utf-8-sig',newline='') as file:
        writer=csv.writer(file,delimiter=';');writer.writerow(headers)
        for row in data:writer.writerow([csv_safe(printable(row.get(k))) for k in headers])
    return path


def export_excel(report,path):
    path=Path(path)
    if path.suffix.lower()!='.xlsx':raise ValueError('Escolha arquivo .xlsx.')
    wb=Workbook();info=wb.active;info.title='Informações'
    for row in [('Dr. Heek Lab — relatório gerencial',),('Exportado em',now()),('Início',report['start']),('Final',report['end']),('Valores *_cents','Inteiros em centavos; nenhum arredondamento de cálculo em ponto flutuante')]:info.append(row)
    for note in report['notes']:info.append((note,))
    for dataset in DATASETS:
        ws=wb.create_sheet(NAMES[dataset]);data=rows(report,dataset);headers=list(dict.fromkeys(k for r in data for k in r));ws.append(headers)
        for r in data:ws.append([printable(r.get(k)) for k in headers])
        ws.freeze_panes='A2'
        if headers:ws.auto_filter.ref=ws.dimensions
        for column in ws.columns:
            ws.column_dimensions[column[0].column_letter].width=min(60,max(14,max(len(str(c.value or '')) for c in column)+2))
    # An arbitrary description beginning '=' must remain text, never a formula.
    for ws in wb.worksheets:
        for row in ws:
            for cell in row:
                if isinstance(cell.value,str):cell.data_type='s'
                elif isinstance(cell.value,int) and abs(cell.value)>999999999999999:cell.value=str(cell.value);cell.data_type='s'
    wb.save(path);wb.close();return path
