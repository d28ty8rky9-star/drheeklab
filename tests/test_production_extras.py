from decimal import Decimal
import json
import pytest
from PySide6.QtWidgets import QApplication,QDialog
from drheeklab.production_extras import calculate_extras
from drheeklab.recipe_ui import RecipeDialog
from drheeklab.finance import Finance
from test_recipe_flow import system,inspect
APP=QApplication.instance() or QApplication([])

def test_extras_frozen_scaled_and_recognized_only_on_completion(system):
    store,p,spool,product,variant,project,_=system
    p.save_recipe(variant,1,project,60,[(spool,'10')],'1','PLA',extras=[{'name':'Argola','quantity':'2','unit_cost':'0,50'},{'name':'Embalagem','quantity':'1','unit_cost':'2'}])
    saved=p.recipe(variant)['data'];assert saved['auxiliary_base']=='1'
    assert saved['estimate']['auxiliary']=='4.00' and len(saved['extras'])==2
    assert not p.inventory.pieces() and not Finance(store).report()['production']
    op=p.create_from_recipe(variant,2,'Operador')
    assert json.loads(p.entries(op)[0]['planned'])['auxiliary']=='8.00'
    p.save_recipe(variant,1,project,60,[(spool,'10')],'0','PLA',extras=[])
    assert len(p.recipe_order(op)['data']['extras'])==2
    p.start(op);p.confirm_from_recipe(op)
    assert not Finance(store).report()['production']
    inspect(system,op);result=p.complete(op)
    assert result['total_cents']==1220  # 2*(material1 + machine1.1 + base1 + extras3)
    assert Finance(store).report()['metrics']['production_cost_cents']==1220
    assert Finance(store).report()['metrics']['cash_flow_cents']==0

def test_live_cost_without_stl_and_extras_save_reopen_remove(system):
    store,p,spool,product,variant,project,_=system
    form=RecipeDialog(p,variant)
    form.editor.project.setCurrentIndex(-1)
    form.fields['hours'].setText('1,5');form.editor.filaments[0][1].setText('25')
    assert 'R$ 4,15' in form.preview.text()  # no file required to preview
    form.extras.add({'name':'Argola','quantity':'2','unit_cost':'0.5'})
    assert 'R$ 5,15' in form.preview.text()
    form.extras.rows[0][2].setText('3');assert 'R$ 5,65' in form.preview.text()
    form.extras.rows[0][3].setText('1');assert 'R$ 7,15' in form.preview.text()
    form.fields['parameters'].setText('PLA');form.editor.project.setCurrentIndex(form.editor.project.findData(project))
    form.submit();assert form.result()==QDialog.Accepted,form.error.text()
    reopened=RecipeDialog(p,variant)
    assert reopened.extras.rows[0][1].text()=='Argola'
    assert 'R$ 7,15' in reopened.preview.text()
    reopened.extras.remove(reopened.extras.rows[0]);assert 'R$ 4,15' in reopened.preview.text()
    reopened.submit();assert reopened.result()==QDialog.Accepted
    assert p.recipe(variant)['data']['extras']==[]
    assert not Finance(store).report()['production'] and not p.inventory.pieces()

@pytest.mark.parametrize('extra',[{'name':'','quantity':'1','unit_cost':'1'},{'name':'Argola','quantity':'0','unit_cost':'1'},{'name':'Argola','quantity':'1','unit_cost':'-1'}])
def test_invalid_extras_cannot_be_saved(extra):
    with pytest.raises(ValueError):calculate_extras([extra])
