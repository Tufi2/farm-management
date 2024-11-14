from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.animal import Animal, HealthRecord
from app import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import re

# Define valid species constants
VALID_SPECIES = ['Sheep', 'Cattle', 'Chicken', 'Other']
VALID_TYPES = ['sheep', 'cattle', 'chicken', 'other']

bp = Blueprint('animals', __name__, url_prefix='/animals')

def validate_tag_number(tag_number):
    """Validate tag number format and uniqueness"""
    # Check if tag number is empty
    if not tag_number:
        return False, "Tag number is required"
        
    # Check tag number format (alphanumeric, no special characters except dash)
    if not re.match("^[A-Za-z0-9-]+$", tag_number):
        return False, "Tag number can only contain letters, numbers, and dashes"
        
    # Check if tag number already exists
    existing_animal = Animal.query.filter_by(tag_number=tag_number).first()
    if existing_animal:
        return False, "An animal with this tag number already exists"
        
    return True, None

@bp.route('/check-tag/<tag_number>')
@login_required
def check_tag(tag_number):
    """API endpoint to check tag number availability"""
    exists = Animal.query.filter_by(tag_number=tag_number).first() is not None
    return jsonify({'exists': exists})

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
            # Validate tag number
            tag_number = request.form.get('tag_number')
            is_valid, error_message = validate_tag_number(tag_number)
            if not is_valid:
                flash(error_message, 'danger')
                return redirect(url_for('animals.add', type=animal_type))

            # Determine species based on animal type
            if animal_type == 'other':
                species = request.form.get('category', 'Other')
            else:
                species = animal_type.capitalize()
                
            # Validate species if not 'other'
            if animal_type != 'other' and species not in VALID_SPECIES:
                flash('Invalid species selected', 'danger')
                return redirect(url_for('animals.add', type=animal_type))

            # Create new animal instance
            animal = Animal(
                tag_number=tag_number,
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

            try:
                db.session.add(animal)
                db.session.commit()
                flash(f'New {species.lower()} added successfully!', 'success')
                return redirect(url_for('animals.index'))
            except IntegrityError:
                db.session.rollback()
                flash('An animal with this tag number already exists.', 'danger')
                return redirect(url_for('animals.add', type=animal_type))
            
        except ValueError as e:
            flash(f'Invalid data format: {str(e)}', 'danger')
            return redirect(url_for('animals.add', type=animal_type))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding animal: {str(e)}', 'danger')
            return redirect(url_for('animals.add', type=animal_type))
            
    return render_template('animals/add.html', animal_type=animal_type)

# ... [rest of your existing routes remain the same] ...

def validate_animal_data(form_data):
    """Validate animal data before saving"""
    errors = []
    
    # Required fields
    if not form_data.get('tag_number'):
        errors.append('Tag number is required')
    if not form_data.get('species'):
        errors.append('Species is required')
        
    # Numeric fields
    try:
        if form_data.get('weight'):
            float(form_data.get('weight'))
        if form_data.get('purchase_price'):
            float(form_data.get('purchase_price'))
    except ValueError:
        errors.append('Invalid numeric value provided')
        
    return errors
@bp.route('/<int:id>/view')
@login_required
def view(id):
    animal = Animal.query.get_or_404(id)
    return render_template('animals/view.html', animal=animal)