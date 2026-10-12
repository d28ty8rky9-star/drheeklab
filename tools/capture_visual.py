"""Capture eight real screens using isolated, explicitly demonstrative data."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
from tempfile import TemporaryDirectory
from PySide6.QtWidgets import QApplication
from drheeklab.storage import Storage
from drheeklab.ui import Window,AREAS
from drheeklab.sales import Sales
from drheeklab.production import Production
from drheeklab.inventory import Inventory
from drheeklab.finance import Finance

app=QApplication.instance() or QApplication([])
output=Path('docs/capturas-modernizacao');output.mkdir(parents=True,exist_ok=True)
with TemporaryDirectory(prefix='drheek-visual-demo-') as temp:
    store=Storage(Path(temp)/'data');sales=Sales(store);prod=Production(store)
    spool=prod.catalog.save_filament(dict(name='PLA azul • demonstração',brand='Material de teste',material='PLA',color='Azul',initial_grams='1000',remaining_grams='80',purchase='100',reference_per_g='0.10'))
    variants=[]
    for i,(name,category,price) in enumerate([('Suporte articulado','functional','45'),('Vaso geométrico','decorative','65'),('Organizador modular','functional','35')]):
        product=prod.products.save(dict(name=name,category=category,suggested_price=price,planned_cost='12',settings='Camada 0,2 mm • preenchimento 15%'))
        variant=prod.products.variants(product)[0]['id'];variants.append(variant)
        project=Path(temp)/f'modelo-{i}.stl';project.write_text('solid demo\nendsolid demo');project_id=prod.products.import_media(product,project,'project')
        op=prod.create(1,90,[dict(variant_id=variant,project_id=project_id,quantity=2,filaments=[(spool,'20')])],'Operador • demonstração','0,2 mm / 15%',priority='high' if i==0 else 'normal')
        if i==1:prod.start(op)
        Inventory(store).receive(variant,5,'Dados de demonstração','available','Nova','demo-'+str(i),total_cost='60',reviewer='Demonstração')
    for i,name in enumerate(['Cliente Aurora • demonstração','Cliente Prisma • demonstração','Cliente Nexus • demonstração']):
        client=sales.save_client({'name':name,'email':f'demo{i}@example.com'})
        order=sales.create_order(client,[{'description':'Peças de demonstração','quantity':4+i,'unit_price':'45','fulfillment':'production'}])
        if i<2:sales.receive_payment(order,'90' if i==0 else '225')
    window=Window(store);window.resize(1440,960);window.show();app.processEvents()
    for i,name in enumerate(AREAS):
        window.navigate(i)
        if i==1:window.sales_page.tabs.setCurrentIndex(2)
        if i==4:window.stock_page.tabs.setCurrentIndex(2)
        app.processEvents();window.grab().save(str(output/f'{i+1:02d}.png'))
    window.close();app.processEvents()
