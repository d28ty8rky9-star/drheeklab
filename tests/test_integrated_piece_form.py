import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication,QDialog
import pytest
from drheeklab.storage import Storage
from drheeklab.production import Production
from drheeklab.phase3_ui import ProductDialog
from drheeklab.finance import Finance
from drheeklab.ui import Window
APP=QApplication.instance() or QApplication([])

def setup(tmp_path):
    store=Storage(tmp_path/'data');p=Production(store)
    ids=[p.catalog.save_filament({'name':name,'brand':'Teste','material':'PLA','color':name,'purchase':'100','initial_grams':'1000','remaining_grams':'1000','reference_per_g':'0.2'}) for name in ('Azul','Branco')]
    return store,p,ids

def configure(form,spools):
    form.fields['name'].setText('Dragão');form.fields['printer_id'].setCurrentIndex(form.fields['printer_id'].findData(1))
    form.fields['estimated_hours'].setText('10');form.fields['settings'].setText('0,2 mm / 15%')
    controls=form.production_fields;combo,grams,_=controls.editor.filaments[0]
    combo.setCurrentIndex(combo.findData(spools[0]));grams.setText('100')
    assert 'R$ 21,00' in controls.preview.text()
    controls.editor.add_spool();combo,grams,_=controls.editor.filaments[1]
    combo.setCurrentIndex(combo.findData(spools[1]));grams.setText('50')
    controls.extras.add({'name':'Argola','quantity':'2','unit_cost':'0.5'})
    assert 'R$ 27,00' in controls.preview.text()
    assert form.fields['planned_cost'].text()=='27.00'
    assert form.fields['planned_cost'].isReadOnly()

def test_new_piece_has_cost_materials_extras_saved_without_other_dialog(tmp_path):
    store,p,spools=setup(tmp_path);window=Window(store)
    form=ProductDialog(p.products,parent=window);configure(form,spools)
    form.submit();assert form.result()==QDialog.Accepted,form.error.text()
    variant=p.products.variants(form.saved_id)[0]['id'];recipe=p.recipe(variant)['data']
    assert recipe['minutes']==600 and recipe['project_id'] is None
    assert len(recipe['estimate']['filaments'])==2 and recipe['extras'][0]['name']=='Argola'
    assert not p.inventory.pieces() and not Finance(store).report()['production']
    assert p.catalog.get('filaments',spools[0])['remaining_mg']==1000000
    with pytest.raises(ValueError,match='STL'):p.create_from_recipe(variant,1,'Operador')
    reopened=ProductDialog(p.products,form.saved_id,window)
    assert reopened.fields['estimated_hours'].text()=='10'
    assert reopened.production_fields.extras.rows[0][1].text()=='Argola'
    assert 'R$ 27,00' in reopened.production_fields.preview.text()
    source=tmp_path/'dragao.stl';source.write_text('solid dragon')
    reopened.production_fields.file_path.setText(str(source));reopened.submit()
    assert reopened.result()==QDialog.Accepted,reopened.error.text()
    op=p.create_from_recipe(variant,2,'Operador');assert p.entries(op)[0]['quantity']==2
    assert not Finance(store).report()['production']
    window.close()

def test_existing_edit_form_copies_variant_recipe_and_preserves_other_variant(tmp_path):
    store,p,spools=setup(tmp_path)
    product=p.products.save({'name':'Dragão','category':'decorative'})
    variants=[p.products.variants(product)[0]['id'],p.products.save_variant(product,{'name':'Grande'})]
    path=tmp_path/'model.stl';path.write_text('solid model');project=p.products.import_media(product,path,'project')
    for variant in variants:p.save_recipe(variant,1,project,60,[(spools[0],'10')],'0','PLA',extras=[{'name':'Argola','quantity':'1','unit_cost':'1'}])
    window=Window(store);window.navigate(2);page=window.products_page;page.select_product(product)
    page.variants_table.selectRow(1)
    before=p.recipe(variants[0])
    form=ProductDialog(p.products,product,page)
    assert form.production_fields.variant_id==variants[1]
    form.fields['estimated_hours'].setText('2');form.production_fields.extras.rows[0][3].setText('2')
    assert 'R$ 5,20' in form.production_fields.preview.text()
    form.submit();assert form.result()==QDialog.Accepted,form.error.text()
    assert p.recipe(variants[0])==before
    assert p.recipe(variants[1])['data']['minutes']==120
    window.close()

def test_invalid_file_rolls_back_piece_and_recipe(tmp_path):
    store,p,spools=setup(tmp_path)
    form=ProductDialog(p.products);configure(form,spools)
    path=tmp_path/'invalid.txt';path.write_text('invalid');form.production_fields.file_path.setText(str(path))
    form.submit();assert form.result()!=QDialog.Accepted
    assert not p.products.search() and not store.db.execute('SELECT * FROM production_recipes').fetchall()
    assert not list((store.home/'Projetos STL e 3MF').iterdir())
    store.close()


def test_new_piece_saves_photos_variant_and_stl_in_same_window(tmp_path):
    from PySide6.QtGui import QImage,QColor
    store,p,spools=setup(tmp_path)
    form=ProductDialog(p.products);configure(form,spools)
    controls=form.production_fields;controls.variant_fields['name'].setText('Azul grande');controls.variant_fields['size'].setText('20 cm')
    controls.variant_fields['color'].setText('Azul');controls.variant_fields['material'].setText('PLA')
    source=tmp_path/'dragon.stl';source.write_text('solid dragon');controls.file_path.setText(str(source))
    image=QImage(20,20,QImage.Format_RGB32);image.fill(QColor('blue'));photo=tmp_path/'dragon.png';assert image.save(str(photo));controls.photo_paths.append(str(photo))
    form.fields['description'].setText('Dragão luminoso');form.fields['quality_notes'].setText('Revisar detalhes')
    form.submit();assert form.result()==QDialog.Accepted,form.error.text()
    variant=p.products.variants(form.saved_id)[0]
    assert variant['name']=='Azul grande' and variant['size']=='20 cm'
    assert len(p.products.media(form.saved_id,'photo'))==1
    assert len(p.products.media(form.saved_id,'project'))==1
    assert p.recipe(variant['id'])['data']['project_id'] is not None
    assert not Finance(store).report()['production'] and not p.inventory.pieces()
    store.close()


def test_photo_failure_removes_all_copied_files_and_rolls_back(tmp_path):
    store,p,spools=setup(tmp_path);form=ProductDialog(p.products);configure(form,spools)
    source=tmp_path/'dragon.stl';source.write_text('solid dragon');form.production_fields.file_path.setText(str(source))
    bad=tmp_path/'photo.png';bad.write_text('not an image');form.production_fields.photo_paths.append(str(bad))
    form.submit();assert form.result()!=QDialog.Accepted
    assert not p.products.search()
    assert not list((store.home/'Projetos STL e 3MF').iterdir())
    assert not list((store.home/'Fotos dos Produtos').iterdir())
    store.close()
