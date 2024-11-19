from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.animal import Animal, HealthRecord
from app import db
from datetime import datetime
from sqlalchemy import or_

# Define valid species constants
VALID_SPECIES = ['Sheep', 'Cattle', 'Chicken', 'Other']
VALID_TYPES = ['sheep', 'cattle', 'chicken', 'other']

bp = Blueprint('animals', __name__, url_prefix='/animals')

@bp.route('/')
@login_required
def index():
    """Display all animals with search and filter capabilities"""
    search_query = request.args.get('search', '').strip()
    animal_type = request.args.get('type', 'all').lower()
    
    # Start with base query
    base_query = Animal.query
    
    # Apply search if provided
    if search_query:
        search_terms = [term.strip() for term in search_query.split()]
        search_filters = []
        for term in search_terms:
            search_filters.append(
                or_(
                    Animal.tag_number.ilike(f'%{term}%'),
                    Animal.name.ilike(f'%{term}%'),
                    Animal.breed.ilike(f'%{term}%')
                )
            )
        base_query = base_query.filter(or_(*search_filters))

    # Get separate lists for each animal type based on filters
    if animal_type == 'all':
        sheep_list = base_query.filter_by(species='Sheep').all()
        cattle_list = base_query.filter_by(species='Cattle').all()
        chicken_list = base_query.filter_by(species='Chicken').all()
        other_list = base_query.filter(Animal.species.notin_(['Sheep', 'Cattle', 'Chicken'])).all()
    else:
        sheep_list = base_query.filter_by(species='Sheep').all() if animal_type == 'sheep' else []
        cattle_list = base_query.filter_by(species='Cattle').all() if animal_type == 'cattle' else []
        chicken_list = base_query.filter_by(species='Chicken').all() if animal_type == 'chicken' else []
        other_list = base_query.filter(Animal.species.notin_(['Sheep', 'Cattle', 'Chicken'])).all() if animal_type == 'other' else []
    
    return render_template('animals/index.html', 
                         sheep_list=sheep_list, 
                         cattle_list=cattle_list,
                         chicken_list=chicken_list,
                         other_list=other_list,
                         search_query=search_query,
                         animal_type=animal_type)

@bp.route('/check-tag-number')
@login_required
def check_tag_number():
    """Check if a tag number already exists"""
    tag_number = request.args.get('tag_number', '').strip()
    # If ID is provided, exclude current animal from check for edit operations
    current_id = request.args.get('current_id')
    
    query = Animal.query.filter_by(tag_number=tag_number)
    if current_id:
        query = query.filter(Animal.id != int(current_id))
        
    exists = query.first() is not None
    return jsonify({'exists': exists})

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Add a new animal with duplicate tag number validation"""
    animal_type = request.args.get('type', 'sheep').lower()
    
    if animal_type not in VALID_TYPES:
        flash('Invalid animal type selected', 'danger')
        return redirect(url_for('animals.index'))
    
    if request.method == 'POST':
        try:
            # Check for duplicate tag number
            tag_number = request.form.get('tag_number').strip()
            existing_animal = Animal.query.filter_by(tag_number=tag_number).first()
            
            if existing_animal:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'error': 'duplicate_tag',
                        'message': f'An animal with tag number {tag_number} already exists.'
                    }), 400
                flash(f'Tag number {tag_number} already exists', 'danger')
                return redirect(url_for('animals.add', type=animal_type))

            # Determine species based on animal type
            if animal_type == 'other':
                species = request.form.get('category', 'Other')
            else:
                species = animal_type.capitalize()
                
            if animal_type != 'other' and species not in VALID_SPECIES:
                flash('Invalid species selected', 'danger')
                return redirect(url_for('animals.add', type=animal_type))
            
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

            db.session.add(animal)
            db.session.commit()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': f'New {species.lower()} added successfully!'})
                
            flash(f'New {species.lower()} added successfully!', 'success')
            return redirect(url_for('animals.index'))
            
        except Exception as e:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'error', 'message': str(e)}), 400
                
            flash(f'Error adding animal: {str(e)}', 'danger')
            return redirect(url_for('animals.add', type=animal_type))
            
    return render_template('animals/add.html', animal_type=animal_type)

@bp.route('/<int:id>')
@login_required
def view(id):
    """View a specific animal's details"""
    animal = Animal.query.get_or_404(id)
    return render_template('animals/view.html', animal=animal)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit an existing health record"""
    record = HealthRecord.query.get_or_404(id)
    animal_type = record.animal.species
    
    try:
        description = json.loads(record.description) if record.description else {}
    except:
        description = {}
    
    if request.method == 'GET':
        # Extract data from the description dictionary
        data = {
            # Basic Information
            'tag_number': record.animal.tag_number,
            'weight': description.get('Basic Information', {}).get('Weight'),
            
            # Health Status
            'health_status': description.get('Health Status', {}).get('Current'),
            'vaccination_status': description.get('Health Status', {}).get('Vaccination'),
            
            # Lambing History
            'pregnancy_status': description.get('Lambing', {}).get('Status'),
            'due_date': description.get('Lambing', {}).get('Due Date'),
            'number_of_lambs': description.get('Lambing', {}).get('Number of Lambs'),
            'lambing_ease': description.get('Lambing', {}).get('Lambing Ease'),
            'lambing_notes': description.get('Lambing', {}).get('Notes'),
            
            # Foot Health
            'foot_condition': description.get('Foot Health', {}).get('Condition'),
            'last_foot_check': description.get('Foot Health', {}).get('Last Check'),
            'foot_notes': description.get('Foot Health', {}).get('Notes'),
            
            # Behavior
            'behavior_pattern': description.get('Behavior', {}).get('Pattern'),
            'stress_level': description.get('Behavior', {}).get('Stress Level'),
            'behavior_notes': description.get('Behavior', {}).get('Notes'),
            
            # Wool Quality
            'wool_quality': description.get('Wool Quality', {}).get('Condition'),
            'wool_texture': description.get('Wool Quality', {}).get('Texture'),
            'last_shearing': description.get('Wool Quality', {}).get('Last Shearing'),
            'next_shearing': description.get('Wool Quality', {}).get('Next Shearing'),
            
            # Treatment Details
            'treatment_details': record.treatment
        }
        
        return render_template('health_records/edit.html',
                            record=record,
                            data=data,
                            animal_type=animal_type)

    if request.method == 'POST':
        try:
            # Build updated description dictionary
            description = {
                "Basic Information": {
                    "Weight": request.form.get('weight')
                },
                "Health Status": {
                    "Current": request.form.get('health_status'),
                    "Vaccination": request.form.get('vaccination_status')
                },
                "Lambing": {
                    "Status": request.form.get('pregnancy_status'),
                    "Due Date": request.form.get('due_date'),
                    "Number of Lambs": request.form.get('number_of_lambs'),
                    "Lambing Ease": request.form.get('lambing_ease'),
                    "Notes": request.form.get('lambing_notes')
                },
                "Foot Health": {
                    "Condition": request.form.get('foot_condition'),
                    "Last Check": request.form.get('last_foot_check'),
                    "Notes": request.form.get('foot_notes')
                },
                "Behavior": {
                    "Pattern": request.form.get('behavior_pattern'),
                    "Stress Level": request.form.get('stress_level'),
                    "Notes": request.form.get('behavior_notes')
                },
                "Wool Quality": {
                    "Condition": request.form.get('wool_quality'),
                    "Texture": request.form.get('wool_texture'),
                    "Last Shearing": request.form.get('last_shearing'),
                    "Next Shearing": request.form.get('next_shearing')
                }
            }

            # Update record
            record.description = json.dumps(description, indent=2)
            record.treatment = request.form.get('treatment_details')
            
            # Handle numeric fields
            try:
                if request.form.get('cost'):
                    record.cost = float(request.form.get('cost'))
            except ValueError:
                record.cost = None

            # Handle date fields
            try:
                if request.form.get('next_due_date'):
                    record.next_due_date = datetime.strptime(
                        request.form.get('next_due_date'), '%Y-%m-%d'
                    ).date()
            except ValueError:
                record.next_due_date = None
            
            db.session.commit()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': 'Health record updated successfully',
                    'redirectUrl': url_for('health_records.view', id=record.id)
                })
            
            flash('Health record updated successfully!', 'success')
            return redirect(url_for('health_records.view', id=record.id))
            
        except Exception as e:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': str(e)}), 400
            
            flash(f'Error updating health record: {str(e)}', 'danger')
            return redirect(url_for('health_records.edit', id=record.id))

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete an animal"""
    animal = Animal.query.get_or_404(id)
    try:
        db.session.delete(animal)
        db.session.commit()
        flash('Animal deleted successfully!', 'success')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True}), 200
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting animal: {str(e)}', 'danger')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': str(e)}), 400
            
    return redirect(url_for('animals.index'))

@bp.route('/bulk-delete', methods=['POST'])
@login_required
def bulk_delete():
    """Delete multiple animals at once"""
    try:
        data = request.get_json()
        if not data or 'ids' not in data:
            return jsonify({'error': 'No animals specified'}), 400
            
        Animal.query.filter(Animal.id.in_(data['ids'])).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({'success': True}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/<int:id>/health', methods=['GET', 'POST'])
@login_required
def add_health_record(id):
    """Add a health record for a specific animal"""
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
                created_by_id=current_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(health_record)
            db.session.commit()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': 'Health record added successfully!'})
                
            flash('Health record added successfully!', 'success')
            return redirect(url_for('animals.view', id=animal.id))
            
        except Exception as e:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'error', 'message': str(e)}), 400
                
            flash(f'Error adding health record: {str(e)}', 'danger')
            
    return render_template('health_records/add.html', animal=animal)

@bp.route('/<int:id>/health/records')
@login_required
def list_health_records(id):
    """List all health records for a specific animal"""
    animal = Animal.query.get_or_404(id)
    records = HealthRecord.query.filter_by(animal_id=id).order_by(HealthRecord.date.desc()).all()
    return render_template('health_records/list.html', animal=animal, records=records)

@bp.route('/<int:id>/health/<int:record_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_health_record(id, record_id):
    """Edit a specific health record"""
    animal = Animal.query.get_or_404(id)
    record = HealthRecord.query.get_or_404(record_id)
    
    if record.animal_id != animal.id:
        flash('Invalid health record', 'danger')
        return redirect(url_for('animals.view', id=id))
        
    if request.method == 'POST':
        try:
            record.record_type = request.form.get('record_type')
            record.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
            record.description = request.form.get('description')
            record.treatment = request.form.get('treatment')
            record.cost = float(request.form.get('cost')) if request.form.get('cost') else None
            record.next_due_date = datetime.strptime(request.form.get('next_due_date'), '%Y-%m-%d').date() if request.form.get('next_due_date') else None
            
            db.session.commit()
            flash('Health record updated successfully!', 'success')
            return redirect(url_for('animals.view', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating health record: {str(e)}', 'danger')
            
    return render_template('health_records/edit.html', animal=animal, record=record)

@bp.route('/<int:id>/health/<int:record_id>/delete', methods=['POST'])
@login_required
def delete_health_record(id, record_id):
    """Delete a specific health record"""
    animal = Animal.query.get_or_404(id)
    record = HealthRecord.query.get_or_404(record_id)
    
    if record.animal_id != animal.id:
        flash('Invalid health record', 'danger')
        return redirect(url_for('animals.view', id=id))
        
    try:
        db.session.delete(record)
        db.session.commit()
        flash('Health record deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting health record: {str(e)}', 'danger')
        
    return redirect(url_for('animals.view', id=id))