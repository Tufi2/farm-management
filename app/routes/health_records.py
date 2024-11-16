from flask import Blueprint, json, jsonify, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.animal import Animal, HealthRecord
from datetime import datetime, date
from sqlalchemy import or_

bp = Blueprint('health_records', __name__, url_prefix='/health-records')

@bp.route('/')
@login_required
def index():
    """Display health records with search functionality"""
    search_query = request.args.get('search', '').strip()
    record_type = request.args.get('type', 'all').lower()
    
    # Base query
    base_query = HealthRecord.query.join(Animal)
    
    # Apply search if provided
    if search_query:
        base_query = base_query.filter(
            or_(
                Animal.tag_number.ilike(f'%{search_query}%'),
                Animal.name.ilike(f'%{search_query}%'),
                HealthRecord.record_type.ilike(f'%{search_query}%'),
                HealthRecord.description.ilike(f'%{search_query}%')
            )
        )
    
    # Get records for each animal type
    sheep_records = (base_query.filter(Animal.species == 'Sheep')
                    .order_by(HealthRecord.date.desc())
                    .limit(5)
                    .all())
    
    cattle_records = (base_query.filter(Animal.species == 'Cattle')
                     .order_by(HealthRecord.date.desc())
                     .limit(5)
                     .all())
    
    goat_records = (base_query.filter(Animal.species == 'Goat')
                   .order_by(HealthRecord.date.desc())
                   .limit(5)
                   .all())
    
    chicken_records = (base_query.filter(Animal.species == 'Chicken')
                      .order_by(HealthRecord.date.desc())
                      .limit(5)
                      .all())

    return render_template('health_records/index.html',
                         sheep_records=sheep_records,
                         cattle_records=cattle_records,
                         goat_records=goat_records,
                         chicken_records=chicken_records,
                         search_query=search_query,
                         record_type=record_type,
                         today=date.today())

@bp.route('/type/<animal_type>')
@login_required
def list_by_type(animal_type):
    """Display all health records for a specific animal type"""
    today = date.today()
    
    # Capitalize the first letter for comparison with database
    species = animal_type.capitalize()
    
    # Base query with joins and filters
    records = (HealthRecord.query
              .join(Animal)
              .filter(Animal.species == species)
              .order_by(HealthRecord.date.desc())
              .all())
    
    return render_template('health_records/list.html',
                         records=records,
                         animal_type=species,
                         today=today)
@bp.route('/sheep/add', methods=['GET', 'POST'])
@login_required
def add_sheep():
    if request.method == 'POST':
        try:
            # Get the sheep by tag number
            tag_number = request.form.get('tag_number')
            sheep = Animal.query.filter_by(tag_number=tag_number, species='Sheep').first()
            
            if not sheep:
                flash('Sheep not found with this tag number', 'danger')
                return redirect(url_for('health_records.add_sheep'))
            
            # Check if a health record already exists for today
            existing_record = HealthRecord.query.filter_by(
                animal_id=sheep.id,
                date=date.today()
            ).first()
            
            if existing_record:
                flash('A health record already exists for this sheep today', 'warning')
                return redirect(url_for('health_records.add_sheep'))

            # Organize the description in a structured way
            description = {
                "Health Status": {
                    "Current": request.form.get('health_status'),
                    "Vaccination": request.form.get('vaccination_status')
                },
                "Wool Quality": {
                    "Condition": request.form.get('wool_quality'),
                    "Texture": request.form.get('wool_texture'),
                    "Last Shearing": request.form.get('last_shearing'),
                    "Next Shearing": request.form.get('next_shearing')
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
                }
            }

            record = HealthRecord(
                animal_id=sheep.id,
                record_type='Health Check',
                date=date.today(),
                description=json.dumps(description, indent=2),
                treatment=request.form.get('treatment_details'),
                created_by_id=current_user.id,
                created_at=datetime.utcnow()
            )
            
            db.session.add(record)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Health record added successfully!'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    return render_template('health_records/add.html',
                         animal_type='Sheep',
                         today=date.today())
@bp.route('/cattle/add', methods=['GET', 'POST'])
@login_required
def add_cattle():
    if request.method == 'POST':
        try:
            # Get the cattle by tag number
            tag_number = request.form.get('tag_number')
            cattle = Animal.query.filter_by(tag_number=tag_number, species='Cattle').first()
            
            if not cattle:
                flash('Cattle not found with this tag number', 'danger')
                return redirect(url_for('health_records.add_cattle'))
            
            # Check for existing record today
            existing_record = HealthRecord.query.filter_by(
                animal_id=cattle.id,
                date=date.today()
            ).first()
            
            if existing_record:
                flash('A health record already exists for this cattle today', 'warning')
                return redirect(url_for('health_records.add_cattle'))

            description = {
                "Health Status": {
                    "Current": request.form.get('health_status'),
                    "Vaccination": request.form.get('vaccination_status')
                },
                "Production": {
                    "Milk Production": request.form.get('milk_production'),
                    "Milk Quality": request.form.get('milk_quality')
                },
                "Physical Condition": {
                    "Weight": request.form.get('weight'),
                    "Body Condition": request.form.get('body_condition'),
                    "Notes": request.form.get('condition_notes')
                },
                "Behavior": {
                    "Pattern": request.form.get('behavior_pattern'),
                    "Notes": request.form.get('behavior_notes')
                }
            }

            record = HealthRecord(
                animal_id=cattle.id,
                record_type='Health Check',
                date=date.today(),
                description=json.dumps(description, indent=2),
                treatment=request.form.get('treatment_details'),
                created_by_id=current_user.id,
                created_at=datetime.utcnow()
            )
            
            db.session.add(record)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Health record added successfully!'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    return render_template('health_records/add.html',
                         animal_type='Cattle',
                         today=date.today())
    

@bp.route('/goat/add', methods=['GET', 'POST'])
@login_required
def add_goat():
    if request.method == 'POST':
        try:
            tag_number = request.form.get('tag_number')
            goat = Animal.query.filter_by(tag_number=tag_number, species='Goat').first()
            
            if not goat:
                flash('Goat not found with this tag number', 'danger')
                return redirect(url_for('health_records.add_goat'))
            
            existing_record = HealthRecord.query.filter_by(
                animal_id=goat.id,
                date=date.today()
            ).first()
            
            if existing_record:
                flash('A health record already exists for this goat today', 'warning')
                return redirect(url_for('health_records.add_goat'))

            description = {
                "Health Status": {
                    "Current": request.form.get('health_status'),
                    "Vaccination": request.form.get('vaccination_status')
                },
                "Production": {
                    "Milk Production": request.form.get('milk_production'),
                    "Kidding Status": request.form.get('kidding_status')
                },
                "Physical Condition": {
                    "Weight": request.form.get('weight'),
                    "Body Condition": request.form.get('body_condition'),
                    "Notes": request.form.get('condition_notes')
                },
                "Behavior": {
                    "Pattern": request.form.get('behavior_pattern'),
                    "Notes": request.form.get('behavior_notes')
                }
            }

            record = HealthRecord(
                animal_id=goat.id,
                record_type='Health Check',
                date=date.today(),
                description=json.dumps(description, indent=2),
                treatment=request.form.get('treatment_details'),
                created_by_id=current_user.id,
                created_at=datetime.utcnow()
            )
            
            db.session.add(record)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Health record added successfully!'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    return render_template('health_records/add.html',
                         animal_type='Goat',
                         today=date.today())
    
@bp.route('/chicken/add', methods=['GET', 'POST'])
@login_required
def add_chicken():
    if request.method == 'POST':
        try:
            tag_number = request.form.get('tag_number')
            chicken = Animal.query.filter_by(tag_number=tag_number, species='Chicken').first()
            
            if not chicken:
                flash('Chicken not found with this tag number', 'danger')
                return redirect(url_for('health_records.add_chicken'))
            
            existing_record = HealthRecord.query.filter_by(
                animal_id=chicken.id,
                date=date.today()
            ).first()
            
            if existing_record:
                flash('A health record already exists for this chicken today', 'warning')
                return redirect(url_for('health_records.add_chicken'))

            description = {
                "Health Status": {
                    "Current": request.form.get('health_status'),
                    "Vaccination": request.form.get('vaccination_status')
                },
                "Production": {
                    "Egg Production": request.form.get('egg_production'),
                    "Egg Quality": request.form.get('egg_quality')
                },
                "Physical Condition": {
                    "Weight": request.form.get('weight'),
                    "Feather Condition": request.form.get('feather_condition'),
                    "Notes": request.form.get('condition_notes')
                },
                "Behavior": {
                    "Pattern": request.form.get('behavior_pattern'),
                    "Notes": request.form.get('behavior_notes')
                }
            }

            record = HealthRecord(
                animal_id=chicken.id,
                record_type='Health Check',
                date=date.today(),
                description=json.dumps(description, indent=2),
                treatment=request.form.get('treatment_details'),
                created_by_id=current_user.id,
                created_at=datetime.utcnow()
            )
            
            db.session.add(record)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Health record added successfully!'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    return render_template('health_records/add.html',
                         animal_type='Chicken',
                         today=date.today()) 

@bp.route('/add/<int:animal_id>', methods=['GET', 'POST'])
@login_required
def add(animal_id):
    """Add a new health record for a specific animal"""
    animal = Animal.query.get_or_404(animal_id)
    
    if request.method == 'POST':
        try:
            # Parse the date strings
            record_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
            next_due_date = None
            if request.form.get('next_due_date'):
                next_due_date = datetime.strptime(request.form.get('next_due_date'), '%Y-%m-%d').date()
            
            # Parse cost if provided
            cost = None
            if request.form.get('cost'):
                cost = float(request.form.get('cost'))
            
            record = HealthRecord(
                animal_id=animal.id,
                record_type=request.form.get('record_type'),
                date=record_date,
                description=request.form.get('description'),
                treatment=request.form.get('treatment'),
                cost=cost,
                next_due_date=next_due_date,
                created_by_id=current_user.id,
                created_at=datetime.utcnow()
            )
            
            db.session.add(record)
            db.session.commit()
            
            flash('Health record added successfully!', 'success')
            return redirect(url_for('animals.view', id=animal.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding health record: {str(e)}', 'danger')
            return redirect(url_for('health_records.add', animal_id=animal.id))
    
    today = date.today()
    return render_template('health_records/add.html', 
                         animal=animal,
                         today=today)

@bp.route('/<int:id>')
@login_required
def view(id):
    """View a specific health record"""
    record = HealthRecord.query.get_or_404(id)
    today = date.today()
    return render_template('health_records/view.html', 
                         record=record,
                         today=today)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    record = HealthRecord.query.get_or_404(id)
    
    if request.method == 'GET':
        # Parse the stored description JSON
        description = json.loads(record.description)
        return render_template('health_records/edit.html',
                            record=record,
                            description=description)
    
    if request.method == 'POST':
        try:
            # Complete description structure matching add form
            description = {
                "Health Status": {
                    "Current": request.form.get('health_status'),
                    "Vaccination": request.form.get('vaccination_status')
                },
                "Wool Quality": {
                    "Condition": request.form.get('wool_quality'),
                    "Texture": request.form.get('wool_texture'),
                    "Last Shearing": request.form.get('last_shearing'),
                    "Next Shearing": request.form.get('next_shearing')
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
                "Parasite Control": {
                    "Status": request.form.get('parasite_status'),
                    "Last Check Date": request.form.get('last_check_date'),
                    "Treatment Details": request.form.get('treatment_details')
                }
            }
            
            record.description = json.dumps(description, indent=2)
            record.treatment = request.form.get('treatment_details')
            record.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Record updated successfully'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete a health record"""
    record = HealthRecord.query.get_or_404(id)
    animal_id = record.animal_id
    
    try:
        db.session.delete(record)
        db.session.commit()
        flash('Health record deleted successfully!', 'success')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return '', 204
        
        return redirect(url_for('animals.view', id=animal_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting health record: {str(e)}', 'danger')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return 'Error deleting record', 500
        
        return redirect(url_for('health_records.view', id=id))

@bp.route('/bulk-delete', methods=['POST'])
@login_required
def bulk_delete():
    """Delete multiple health records at once"""
    try:
        data = request.get_json()
        if not data or 'ids' not in data:
            return 'No records specified', 400
            
        HealthRecord.query.filter(HealthRecord.id.in_(data['ids'])).delete(synchronize_session=False)
        db.session.commit()
        
        return '', 204
        
    except Exception as e:
        db.session.rollback()
        return str(e), 500
    
@bp.route('/get-animal/<tag_number>')
@login_required
def get_animal(tag_number):
    """Get animal details by tag number"""
    animal = Animal.query.filter_by(tag_number=tag_number).first()
    if animal:
        return jsonify({
            'id': animal.id,
            'name': animal.name,
            'species': animal.species,
            'breed': animal.breed
        })
    return jsonify({'error': 'Animal not found'}), 404
    
