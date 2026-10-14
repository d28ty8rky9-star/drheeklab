"""Reusable per-variant recipes; planning never consumes stock or creates cash."""
import json
from decimal import Decimal
from .catalog import required
from .pricing import integer, number, calculate, cents
from .storage import now
from .transactions import transaction

class RecipeProduction:
    def recipe(self, variant_id):
        row=self.db.execute('SELECT * FROM production_recipes WHERE variant_id=?',(variant_id,)).fetchone()
        return {**dict(row),'data':json.loads(row['data'])} if row else None

    def recipe_order(self, identifier):
        row=self.db.execute('SELECT recipe FROM recipe_orders WHERE op_id=?',(identifier,)).fetchone()
        return json.loads(row[0]) if row else None

    def save_recipe(self, variant_id, printer_id, project_id, minutes, filaments, auxiliary='0', parameters=''):
        """Amounts and duration describe ONE unit. Save a revision, not an expense."""
        variant=self.products.active_variant(variant_id)
        if self.db.execute('SELECT 1 FROM purchased_products WHERE product_id=?',(variant['product_id'],)).fetchone():
            raise ValueError('Peça comprada pertence ao Estoque; cadastre um modelo próprio em Produção para imprimir.')
        self.products.active_product(variant['product_id'])
        project=self.products.get('project_versions',project_id)
        if project['archived'] or project['product_id']!=variant['product_id']:
            raise ValueError('Selecione um STL/3MF ativo desta peça.')
        self.products.media_path(project_id,'project')
        minutes=integer(minutes,'Tempo por peça',minimum=1)
        parameters=required(parameters,'Parâmetros de impressão')
        estimate=self.catalog.estimate(printer_id,minutes,filaments,auxiliary,1)
        if not sum(number(f['grams']) for f in estimate['filaments']):
            raise ValueError('Informe o consumo de filamento por peça.')
        data={'printer_id':printer_id,'project_id':project_id,'minutes':minutes,
              'parameters':parameters,'estimate':estimate}
        with transaction(self.db):
            previous=self.recipe(variant_id);revision=previous['revision']+1 if previous else 1
            self.db.execute('INSERT INTO production_recipes VALUES(?,?,?,?) ON CONFLICT(variant_id) DO UPDATE SET revision=excluded.revision,data=excluded.data,updated_at=excluded.updated_at',
                            (variant_id,revision,json.dumps(data,ensure_ascii=False),now()))
            self.storage.audit('produção:ficha',f'variants:{variant_id}',previous,self.recipe(variant_id))
        return self.recipe(variant_id)

    def create_from_recipe(self, variant_id, quantity, responsible, priority='normal', item_id=None):
        recipe=self.recipe(variant_id)
        if not recipe:raise ValueError('Salve a ficha de produção desta variante antes de criar a OP.')
        qty=integer(quantity,'Quantidade',minimum=1);data=recipe['data'];estimate=data['estimate']
        filaments=[(f['id'],str(number(f['grams'])*qty)) for f in estimate['filaments']]
        auxiliary=str(number(estimate['auxiliary'])*qty);minutes=data['minutes']*qty
        with transaction(self.db):
            identifier=self.create(data['printer_id'],minutes,[{'variant_id':variant_id,'project_id':data['project_id'],'quantity':qty,'filaments':filaments,'auxiliary':auxiliary}],responsible,data['parameters'],priority,item_id)
            # Freeze the recipe's cost parameters as well as quantities. Later
            # catalog price edits cannot rewrite an already queued order.
            scaled=calculate(estimate['printer'],minutes,[{**f,'grams':grams} for f,(_,grams) in zip(estimate['filaments'],filaments)],auxiliary,qty)
            entry=self.entries(identifier)[0];snapshot=json.loads(entry['planned'])
            snapshot.update(scaled)
            planned=json.loads(self.get(identifier)['planned']);planned.update(printer=estimate['printer'],machine_cents=cents(scaled['machine_cost']),reference_cents=cents(scaled['total_cost']))
            self.db.execute('UPDATE production_entries SET planned=? WHERE id=?',(json.dumps(snapshot,ensure_ascii=False),entry['id']))
            self.db.execute('UPDATE production_orders SET planned=? WHERE id=?',(json.dumps(planned),identifier))
            self.db.execute('INSERT INTO recipe_orders VALUES(?,?)',(identifier,json.dumps(recipe,ensure_ascii=False)))
            self.storage.audit('produção:OP da ficha',f'OP:{identifier}',None,recipe)
        return identifier

    def confirm_from_recipe(self, identifier, failed=0, reason=''):
        if not self.recipe_order(identifier):raise ValueError('Esta OP usa confirmação técnica do fluxo anterior.')
        entries=[]
        for entry in self.entries(identifier):
            snap=json.loads(entry['planned'])
            entries.append({'entry_id':entry['id'],'consumptions':{f['id']:f['grams'] for f in snap['filaments']},'auxiliary':snap['auxiliary'],'failed':failed})
        return self.confirm(identifier,json.loads(self.get(identifier)['planned'])['minutes'],entries,reason=reason)
