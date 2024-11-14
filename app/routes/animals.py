from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.animal import Animal, HealthRecord
from app import db
from datetime import datetime

# Define valid species constants
VALID_SPECIES = ['Sheep', 'Cattle', 'Chicken', 'Other']
VALID_TYPES = ['sheep', 'cattle', 'chicken', 'other']

bp = Blueprint('animals', __name__, url_prefix='/animals')

@bp.route('/')
@login_required
def index():
    # Get separate lists for each animal type
    sheep_list = Animal.query.filter_by(species='Sheep').all()
    cattle_list = Animal.query.filter_by(species='Cattle').all()
    chicken_list = Animal.query.filter_by(species='Chicken').all()
    other_list = Animal.query.filter(Animal.species.notin_(['Sheep', 'Cattle', 'Chicken'])).all()
    
    return render_template('animals/index.html', 
                         sheep_list=sheep_list, 
                         cattle_list=cattle_list,
                         chicken_list=chicken_list,
                         other_list=other_list)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    animal_type = request.args.get('type', 'sheep').lower()
    
    # Validate animal type
    if animal_type not in VALID_TYPES:
        flash('Invalid animal type selected', 'danger')
        return redirect(url_for('animals.index'))
    
    if request.method == 'POST':
        try:
            # Determine species based on animal type
            if animal_type == 'other':
                species = request.form.get('category', 'Other')
            else:
                species = animal_type.capitalize()
                
            # Validate species if not 'other'
            if animal_type != 'other' and species not in VALID_SPECIES:
                flash('Invalid species selected', 'danger')
                return redirect(url_for('animals.add', type=animal_type))
            
            animal = Animal(
                tag_number=request.form.get('tag_number'),
                name=request.form.get('name'),
                species=species,
                breed=request.form.get('breed'),
                date_of_birth=datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date() if request.form.get('date_of_birth') else None,
                gender=request.form.get('gender'),
                weight=float(request.form.get('weight')) if request.form.get('weight') else None,
                status='active',
                purchase_date=datetime.strptime(request.form.get('purchase_date'), '%Y-%m-%d').date() if request.form.get('purchase_date') else None,
                purchase_price=float(request.form.get('purchase_price')) if request.form.get('purchase_price') else None,
                notes=request.form.get('notes')
            )

            # Add type-specific fields
            if animal_type == 'sheep':
                animal.wool_type = request.form.get('wool_type')
                animal.last_shearing = datetime.strptime(request.form.get('last_shearing'), '%Y-%m-%d').date() if request.form.get('last_shearing') else None
                animal.fleece_weight = float(request.form.get('fleece_weight')) if request.form.get('fleece_weight') else None
                animal.wool_grade = request.form.get('wool_grade')
                animal.lambing_status = request.form.get('lambing_status')
                animal.lambing_date = datetime.strptime(request.form.get('lambing_date'), '%Y-%m-%d').date() if request.form.get('lambing_date') else None

            elif animal_type == 'cattle':
                animal.milk_production = float(request.form.get('milk_production')) if request.form.get('milk_production') else None
                animal.last_milking = datetime.strptime(request.form.get('last_milking'), '%Y-%m-%d').date() if request.form.get('last_milking') else None
                animal.milk_quality = request.form.get('milk_quality')
                animal.calving_status = request.form.get('calving_status')
                animal.calving_date = datetime.strptime(request.form.get('calving_date'), '%Y-%m-%d').date() if request.form.get('calving_date') else None
                animal.milk_fat_content = float(request.form.get('milk_fat_content')) if request.form.get('milk_fat_content') else None

            elif animal_type == 'chicken':
                animal.egg_production = int(request.form.get('egg_production')) if request.form.get('egg_production') else None
                animal.egg_color = request.form.get('egg_color')
                animal.comb_type = request.form.get('comb_type')
                animal.laying_status = request.form.get('laying_status')
                animal.last_laying_date = datetime.strptime(request.form.get('last_laying_date'), '%Y-%m-%d').date() if request.form.get('last_laying_date') else None
                animal.egg_size = request.form.get('egg_size')

            elif animal_type == 'other':
                animal.category = request.form.get('category')
                animal.special_needs = request.form.get('special_needs')
                animal.diet_requirements = request.form.get('diet_requirements')
                animal.habitat = request.form.get('habitat')

            # Validate required fields
            if not animal.tag_number:
                flash('Tag number is required', 'danger')
                return redirect(url_for('animals.add', type=animal_type))

            db.session.add(animal)
            db.session.commit()
            flash(f'New {species.lower()} added successfully!', 'success')
            return redirect(url_for('animals.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding animal: {str(e)}', 'danger')
            return redirect(url_for('animals.add', type=animal_type))
            
    return render_template('animals/add.html', animal_type=animal_type)

@bp.route('/<int:id>')
@login_required
def view(id):
    animal = Animal.query.get_or_404(id)
    return render_template('animals/view.html', animal=animal)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    animal = Animal.query.get_or_404(id)
    if request.method == 'POST':
        try:
            animal.tag_number = request.form.get('tag_number')
            animal.name = request.form.get('name')
            animal.breed = request.form.get('breed')
            animal.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date() if request.form.get('date_of_birth') else None
            animal.gender = request.form.get('gender')
            animal.weight = float(request.form.get('weight')) if request.form.get('weight') else None
            animal.status = request.form.get('status')
            animal.notes = request.form.get('notes')
            
            # Add type-specific fields here
            if animal.species == 'Sheep':
                animal.wool_type = request.form.get('wool_type')
                animal.last_shearing = datetime.strptime(request.form.get('last_shearing'), '%Y-%m-%d').date() if request.form.get('last_shearing') else None
                animal.fleece_weight = float(request.form.get('fleece_weight')) if request.form.get('fleece_weight') else None
                animal.wool_grade = request.form.get('wool_grade')
                animal.lambing_status = request.form.get('lambing_status')
                animal.lambing_date = datetime.strptime(request.form.get('lambing_date'), '%Y-%m-%d').date() if request.form.get('lambing_date') else None

            elif animal.species == 'Cattle':
                animal.milk_production = float(request.form.get('milk_production')) if request.form.get('milk_production') else None
                animal.last_milking = datetime.strptime(request.form.get('last_milking'), '%Y-%m-%d').date() if request.form.get('last_milking') else None
                animal.milk_quality = request.form.get('milk_quality')
                animal.calving_status = request.form.get('calving_status')
                animal.calving_date = datetime.strptime(request.form.get('calving_date'), '%Y-%m-%d').date() if request.form.get('calving_date') else None
                animal.milk_fat_content = float(request.form.get('milk_fat_content')) if request.form.get('milk_fat_content') else None

            elif animal.species == 'Chicken':
                animal.egg_production = int(request.form.get('egg_production')) if request.form.get('egg_production') else None
                animal.egg_color = request.form.get('egg_color')
                animal.comb_type = request.form.get('comb_type')
                animal.laying_status = request.form.get('laying_status')
                animal.last_laying_date = datetime.strptime(request.form.get('last_laying_date'), '%Y-%m-%d').date() if request.form.get('last_laying_date') else None
                animal.egg_size = request.form.get('egg_size')

            elif animal.species not in VALID_SPECIES:
                animal.category = request.form.get('category')
                animal.special_needs = request.form.get('special_needs')
                animal.diet_requirements = request.form.get('diet_requirements')
                animal.habitat = request.form.get('habitat')

            # Validate required fields
            if not animal.tag_number:
                flash('Tag number is required', 'danger')
                return redirect(url_for('animals.edit', id=id))
            
            db.session.commit()
            flash('Animal updated successfully!', 'success')
            return redirect(url_for('animals.view', id=animal.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating animal: {str(e)}', 'danger')
            
    return render_template('animals/edit.html', animal=animal)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    animal = Animal.query.get_or_404(id)
    try:
        db.session.delete(animal)
        db.session.commit()
        flash('Animal deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting animal: {str(e)}', 'danger')
    return redirect(url_for('animals.index'))

@bp.route('/<int:id>/health', methods=['GET', 'POST'])
@login_required
def add_health_record(id):
    animal = Animal.query.get_or_404(id)
    if request.method == 'POST':
        try:
            health_record = HealthRecord(
                animal_id=animal.id,
                record_type=request.form.get('record_type'),
                date=datetime.strptime(request.form.get('date'), '%Y-%m-%d').date(),
                description=request.form.get('description'),
                treatment=request.form.get('treatment'),
                cost=float(request.form.get('cost')) if request.form.get('cost') else None,
                next_due_date=datetime.strptime(request.form.get('next_due_date'), '%Y-%m-%d').date() if request.form.get('next_due_date') else None,
                created_by_id=current_user.id
            )
            db.session.add(health_record)
            db.session.commit()
            flash('Health record added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding health record: {str(e)}', 'danger')
    return redirect(url_for('animals.view', id=id))
