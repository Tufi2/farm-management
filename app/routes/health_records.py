from flask import Blueprint, json, jsonify, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.animal import Animal, HealthRecord
from datetime import datetime, date
from sqlalchemy import or_
from flask import send_file
import csv
from io import StringIO, BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
from jinja2.exceptions import TemplateNotFound


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

from flask import render_template
from flask_login import login_required
from jinja2.exceptions import TemplateNotFound
from datetime import date

@bp.route('/type/<animal_type>')
@login_required
def list_by_type(animal_type):
    """Display all health records for a specific animal type"""
    today = date.today()
    
    # Capitalize the first letter for comparison with database
    species = animal_type.capitalize()
    
    records = (HealthRecord.query
              .join(Animal)
              .filter(Animal.species == species)
              .order_by(HealthRecord.date.desc())
              .all())

    # First try animal-specific template
    try:
        # Update the path to match your folder structure
        return render_template(f'health_records/{animal_type.lower()}/list.html',
                             records=records,
                             animal_type=species,
                             today=today)
    except TemplateNotFound:
        # Fallback to shared template
        try:
            return render_template('health_records/shared/list.html',
                                 records=records,
                                 animal_type=species,
                                 today=today)
        except TemplateNotFound as e:
            print(f"Debug - Looking for templates at:")
            print(f"1. health_records/{animal_type.lower()}/list.html")
            print(f"2. health_records/shared/list.html")
            raise e
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
                "Basic Information": {
                    "Weight": request.form.get('weight')
                },
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
    
    # Initialize empty data for GET request
    data = {
        'weight': '',
        'health_status': '',
        'vaccination_status': '',
        'pregnancy_status': '',
        'due_date': '',
        'number_of_lambs': '',
        'lambing_ease': '',
        'lambing_notes': '',
        'foot_condition': '',
        'last_foot_check': '',
        'foot_notes': '',
        'behavior_pattern': '',
        'stress_level': '',
        'behavior_notes': '',
        'wool_quality': '',
        'wool_texture': '',
        'last_shearing': '',
        'next_shearing': '',
        'treatment_details': ''
    }
    
    return render_template('health_records/sheep/add.html',
                         animal_type='Sheep',
                         data=data,
                         today=date.today())
# Update the cattle route in health_records.py
@bp.route('/cattle/add', methods=['GET', 'POST'])
@login_required
def add_cattle():
    """Add a new cattle health record"""
    if request.method == 'POST':
        try:
            tag_number = request.form.get('tag_number')
            cattle = Animal.query.filter_by(tag_number=tag_number, species='Cattle').first()
            
            if not cattle:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False, 
                        'message': 'Cattle not found with this tag number'
                    }), 404
                flash('Cattle not found with this tag number', 'danger')
                return redirect(url_for('health_records.add_cattle'))

            # Check for existing record
            existing_record = HealthRecord.query.filter_by(
                animal_id=cattle.id,
                date=date.today()
            ).first()
            
            if existing_record:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'message': 'A health record already exists for this cattle today'
                    }), 400
                flash('A health record already exists for this cattle today', 'warning')
                return redirect(url_for('health_records.add_cattle'))

            # Structure the data
            description = {
                "Vital Signs": {
                    "Temperature": request.form.get('temperature'),
                    "Heart Rate": request.form.get('heart_rate'),
                    "Respiratory Rate": request.form.get('respiratory_rate'),
                    "Weight": request.form.get('weight'),
                    "Body Condition Score": request.form.get('body_condition_score')
                },
                "Health Status": {
                    "Current": request.form.get('health_status')
                },
                "Vaccination Records": {
                    "Vaccines": [
                        {
                            "Type": vtype,
                            "Date Given": vdate,
                            "Next Due": ndate
                        }
                        for vtype, vdate, ndate in zip(
                            request.form.getlist('vaccine_type[]'),
                            request.form.getlist('vaccine_date[]'),
                            request.form.getlist('vaccine_next_due[]')
                        )
                    ]
                },
                "Reproductive Health": {
                    "Status": request.form.get('reproductive_status'),
                    "Last Calving Date": request.form.get('last_calving_date'),
                    "Notes": request.form.get('calving_notes')
                },
                "Milk Production": {
                    "Daily Volume": request.form.get('milk_production'),
                    "Quality Grade": request.form.get('milk_quality'),
                    "Fat Content": request.form.get('fat_content')
                },
                "Treatment": {
                    "Type": request.form.get('treatment_type'),
                    "Veterinarian": request.form.get('veterinarian'),
                    "Details": request.form.get('treatment_details')
                },
                "Nutrition": {
                    "Feed Type": request.form.get('feed_type'),
                    "Feed Amount": request.form.get('feed_amount'),
                    "Dietary Notes": request.form.get('dietary_notes')
                }
            }

            # Create the record
            record = HealthRecord(
                animal_id=cattle.id,
                record_type='Health Check',
                date=date.today(),
                description=json.dumps(description, indent=2),
                created_by_id=current_user.id,
                created_at=datetime.utcnow()
            )
            
            db.session.add(record)
            db.session.commit()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': 'Health record added successfully!'
                })
            
            flash('Health record added successfully!', 'success')
            return redirect(url_for('health_records.index'))
            
        except Exception as e:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'message': str(e)
                }), 400
            
            flash(f'Error adding health record: {str(e)}', 'danger')
            return redirect(url_for('health_records.add_cattle'))
    
    # For GET requests
    return render_template('health_records/cattle/add_cattle.html',
                         today=date.today())
    
    


@bp.route('/cattle/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_cattle(id):
    """Edit a cattle health record"""
    record = HealthRecord.query.get_or_404(id)
    
    if record.animal.species != 'Cattle':
        flash('Invalid animal type', 'error')
        return redirect(url_for('health_records.index'))
    
    if request.method == 'GET':
        try:
            description = json.loads(record.description) if record.description else {}
            
            # Extract data for the form
            data = {
                'temperature': description.get('Vital Signs', {}).get('Temperature'),
                'heart_rate': description.get('Vital Signs', {}).get('Heart Rate'),
                'respiratory_rate': description.get('Vital Signs', {}).get('Respiratory Rate'),
                'weight': description.get('Vital Signs', {}).get('Weight'),
                'body_condition_score': description.get('Vital Signs', {}).get('Body Condition Score'),
                'vaccination_records': description.get('Vaccination Records', {}).get('Vaccines', []),
                'reproductive_status': description.get('Reproductive Health', {}).get('Status'),
                'last_calving_date': description.get('Reproductive Health', {}).get('Last Calving Date'),
                'calving_notes': description.get('Reproductive Health', {}).get('Notes'),
                'milk_production': description.get('Milk Production', {}).get('Daily Volume'),
                'milk_quality': description.get('Milk Production', {}).get('Quality Grade'),
                'fat_content': description.get('Milk Production', {}).get('Fat Content'),
                'treatment_type': description.get('Treatment', {}).get('Type'),
                'veterinarian': description.get('Treatment', {}).get('Veterinarian'),
                'treatment_details': description.get('Treatment', {}).get('Details')
            }
            
            return render_template('health_records/cattle/edit_cattle.html',
                               record=record,
                               data=data,
                               today=date.today())
                               
        except Exception as e:
            flash(f'Error loading record: {str(e)}', 'danger')
            return redirect(url_for('health_records.index'))
    
    if request.method == 'POST':
        try:
            # Structure the updated data
            description = {
                "Vital Signs": {
                    "Temperature": request.form.get('temperature'),
                    "Heart Rate": request.form.get('heart_rate'),
                    "Respiratory Rate": request.form.get('respiratory_rate'),
                    "Weight": request.form.get('weight'),
                    "Body Condition Score": request.form.get('body_condition_score')
                },
                "Vaccination Records": {
                    "Vaccines": [
                        {
                            "Type": vtype,
                            "Date Given": vdate,
                            "Next Due": ndate
                        }
                        for vtype, vdate, ndate in zip(
                            request.form.getlist('vaccine_type[]'),
                            request.form.getlist('vaccine_date[]'),
                            request.form.getlist('vaccine_next_due[]')
                        ) if vtype and vdate
                    ]
                },
                "Reproductive Health": {
                    "Status": request.form.get('reproductive_status'),
                    "Last Calving Date": request.form.get('last_calving_date'),
                    "Notes": request.form.get('calving_notes')
                },
                "Milk Production": {
                    "Daily Volume": request.form.get('milk_production'),
                    "Quality Grade": request.form.get('milk_quality'),
                    "Fat Content": request.form.get('fat_content')
                },
                "Treatment": {
                    "Type": request.form.get('treatment_type'),
                    "Veterinarian": request.form.get('veterinarian'),
                    "Details": request.form.get('treatment_details')
                }
            }

            # Update the record
            record.description = json.dumps(description, indent=2)
            db.session.commit()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': 'Health record updated successfully',
                    'redirectUrl': url_for('health_records.view_cattle', id=record.id)
                })
            
            flash('Health record updated successfully!', 'success')
            return redirect(url_for('health_records.view_cattle', id=record.id))
            
        except Exception as e:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': str(e)}), 400
            
            flash(f'Error updating health record: {str(e)}', 'danger')
            return redirect(url_for('health_records.edit_cattle', id=record.id))    

    


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
    """View a health record with species-specific details"""
    record = HealthRecord.query.get_or_404(id)
    
    try:
        description = json.loads(record.description) if record.description else {}
        data = {}

        if record.animal.species == 'Sheep':
            # Keep existing sheep data structure
            data = {
                # Basic Information
                'tag_number': record.animal.tag_number,
                'weight': description.get('Basic Information', {}).get('Weight'),
                'record_date': record.date.strftime('%Y-%m-%d'),
                
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
            template = 'health_records/sheep/view.html'

        elif record.animal.species == 'Cattle':
            # Structure data for cattle view matching the form
            data = {
                # Basic Information
                'basic_info': {
                    'tag_number': record.animal.tag_number,
                    'weight': description.get('Vital Signs', {}).get('Weight'),
                    'record_date': record.date.strftime('%Y-%m-%d')
                },
                
                # Vital Signs
                'vital_signs': {
                    'temperature': f"{description.get('Vital Signs', {}).get('Temperature', 'N/A')}°C",
                    'heart_rate': f"{description.get('Vital Signs', {}).get('Heart Rate', 'N/A')} BPM",
                    'respiratory_rate': f"{description.get('Vital Signs', {}).get('Respiratory Rate', 'N/A')}/min",
                    'body_condition_score': description.get('Vital Signs', {}).get('Body Condition Score', 'N/A')
                },

                # Milk Production
                'milk_production': {
                    'daily_volume': f"{description.get('Milk Production', {}).get('Daily Volume', 'N/A')} L",
                    'quality_grade': description.get('Milk Production', {}).get('Quality Grade', 'N/A'),
                    'fat_content': f"{description.get('Milk Production', {}).get('Fat Content', 'N/A')}%"
                },

                # Vaccination Records - now as a list for easier table rendering
                'vaccination_records': [
                    {
                        'type': vaccine.get('Type', 'N/A'),
                        'date_given': vaccine.get('Date Given', 'N/A'),
                        'next_due': vaccine.get('Next Due', 'N/A'),
                        'status': 'Up to date'  # Will be updated below
                    }
                    for vaccine in description.get('Vaccination Records', {}).get('Vaccines', [])
                ],

                # Reproductive Health
                'reproductive_health': {
                    'status': description.get('Reproductive Health', {}).get('Status', 'N/A'),
                    'last_calving_date': description.get('Reproductive Health', {}).get('Last Calving Date', 'N/A'),
                    'notes': description.get('Reproductive Health', {}).get('Notes', 'N/A')
                }
            }

            # Update vaccination statuses
            today = date.today()
            for vaccine in data['vaccination_records']:
                if vaccine['next_due'] != 'N/A':
                    try:
                        next_due_date = datetime.strptime(vaccine['next_due'], '%Y-%m-%d').date()
                        vaccine['status'] = 'Due' if next_due_date <= today else 'Up to date'
                    except (ValueError, TypeError):
                        vaccine['status'] = 'N/A'
                        
            template = 'health_records/cattle/view_cattle.html'  # Changed from view_cattle.html
            
        else:
            flash('Unsupported animal type', 'warning')
            return redirect(url_for('health_records.index'))

        return render_template(template,
                            record=record,
                            data=data,
                            today=date.today())

    except Exception as e:
        print(f"Error processing record: {str(e)}")  # For debugging
        flash(f"Error loading health record: {str(e)}", 'danger')
        return redirect(url_for('health_records.index'))

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit an sheep health record"""
    record = HealthRecord.query.get_or_404(id)
    
   # Add validation for sheep records
    if record.animal.species != 'Sheep':
        flash('Invalid record type. Please use the appropriate edit page.', 'warning')
        return redirect(url_for('health_records.index')) 
    
    
    try:
        description = json.loads(record.description) if record.description else {}
    except:
        description = {}
    
    if request.method == 'GET':
        # Extract data from the description dictionary
        data = {
            # Basic Information
            'tag_number': record.animal.tag_number,
            'weight': description.get('Physical Condition', {}).get('Weight'),
            
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
            
            # Behavior (changed from Flock Behavior to match add route)
            'behavior_pattern': description.get('Behavior', {}).get('Pattern'),
            'stress_level': description.get('Behavior', {}).get('Stress Level'),
            'behavior_notes': description.get('Behavior', {}).get('Notes'),
            
            # Wool Quality
            'wool_quality': description.get('Wool Quality', {}).get('Condition'),
            'wool_texture': description.get('Wool Quality', {}).get('Texture'),
            'last_shearing': description.get('Wool Quality', {}).get('Last Shearing'),
            'next_shearing': description.get('Wool Quality', {}).get('Next Shearing'),
            
            # Parasite Control
            'last_check_date': description.get('Parasite Control', {}).get('Last Check Date'),
            'parasite_status': description.get('Parasite Control', {}).get('Status'),
            'treatment_details': description.get('Parasite Control', {}).get('Treatment')
        }
        
        return render_template('health_records/sheep/edit.html',
                            record=record,
                            data=data,
                            animal_type='Sheep')

    if request.method == 'POST':
        try:
            # Build updated description dictionary
            description = {
                "Physical Condition": {
                    "Weight": request.form.get('weight'),
                    "Notes": request.form.get('physical_notes')
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
                "Behavior": {  # Changed from Flock Behavior to match add route
                    "Pattern": request.form.get('behavior_pattern'),
                    "Stress Level": request.form.get('stress_level'),
                    "Notes": request.form.get('behavior_notes')
                },
                "Wool Quality": {
                    "Condition": request.form.get('wool_quality'),
                    "Texture": request.form.get('wool_texture'),
                    "Last Shearing": request.form.get('last_shearing'),
                    "Next Shearing": request.form.get('next_shearing')
                },
                "Parasite Control": {
                    "Last Check Date": request.form.get('last_check_date'),
                    "Status": request.form.get('parasite_status'),
                    "Treatment": request.form.get('treatment_details')
                }
            }

            # Validate required fields
            if not request.form.get('health_status'):
                raise ValueError("Health Status is required")

            # Update record
            record.description = json.dumps(description, indent=2)
            
            # If there's a cost associated with treatment
            if request.form.get('treatment_cost'):
                try:
                    record.cost = float(request.form.get('treatment_cost'))
                except ValueError:
                    record.cost = None

            # Update next due date if provided
            if request.form.get('next_due_date'):
                try:
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
            
        except ValueError as ve:
            # Handle validation errors
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': str(ve)}), 400
            flash(str(ve), 'danger')
            return redirect(url_for('health_records.edit', id=record.id))
            
        except Exception as e:
            # Handle other errors
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': str(e)}), 400
            
            flash(f'Error updating health record: {str(e)}', 'danger')
            return redirect(url_for('health_records.edit', id=record.id))
        
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
        
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True}), 200
        
        return redirect(url_for('health_records.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting health record: {str(e)}', 'danger')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)}), 400
        
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
@bp.route('/<int:id>/download/<format>')
@login_required
def download(id, format):
    """Download health record in specified format"""
    record = HealthRecord.query.get_or_404(id)
    description = json.loads(record.description) if record.description else {}

    if format == 'pdf':
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        elements.append(Paragraph(f"Health Record - {record.animal.tag_number}", styles['Title']))
        elements.append(Spacer(1, 20))

        # Data to display
        data = [
            # Basic Information
            ['Basic Information', ''],
            ['Tag Number', record.animal.tag_number],
            ['Animal Type', record.animal.species],
            ['Record Date', record.date.strftime('%Y-%m-%d')],
            ['', ''],  # Spacer row

            # Health Status
            ['Health Status', ''],
            ['Current Status', description.get('Health Status', {}).get('Current', 'N/A')],
            ['Vaccination Status', description.get('Health Status', {}).get('Vaccination', 'N/A')],
            ['', ''],  # Spacer row
        ]

        # Add Wool Quality if it exists
        if description.get('Wool Quality'):
            data.extend([
                ['Wool Quality', ''],
                ['Condition', description['Wool Quality'].get('Condition', 'N/A')],
                ['Texture', description['Wool Quality'].get('Texture', 'N/A')],
                ['Last Shearing', description['Wool Quality'].get('Last Shearing', 'N/A')],
                ['Next Shearing', description['Wool Quality'].get('Next Shearing', 'N/A')],
                ['', ''],  # Spacer row
            ])

        # Add Lambing History if it exists
        if description.get('Lambing'):
            data.extend([
                ['Lambing History', ''],
                ['Status', description['Lambing'].get('Status', 'N/A')],
                ['Due Date', description['Lambing'].get('Due Date', 'N/A')],
                ['Number of Lambs', description['Lambing'].get('Number of Lambs', 'N/A')],
                ['Lambing Ease', description['Lambing'].get('Lambing Ease', 'N/A')],
                ['Notes', description['Lambing'].get('Notes', 'N/A')],
                ['', ''],  # Spacer row
            ])

        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        
        # Generate PDF
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(
            buffer,
            download_name=f'health_record_{record.animal.tag_number}_{datetime.now().strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )

    elif format == 'csv':
        # Create CSV
        si = StringIO()
        writer = csv.writer(si)
        
        # Write headers and data
        writer.writerow(['Health Record Details'])
        writer.writerow(['', ''])
        
        # Basic Information
        writer.writerow(['Basic Information'])
        writer.writerow(['Tag Number', record.animal.tag_number])
        writer.writerow(['Animal Type', record.animal.species])
        writer.writerow(['Record Date', record.date.strftime('%Y-%m-%d')])
        writer.writerow(['', ''])

        # Health Status
        writer.writerow(['Health Status'])
        writer.writerow(['Current Status', description.get('Health Status', {}).get('Current', 'N/A')])
        writer.writerow(['Vaccination Status', description.get('Health Status', {}).get('Vaccination', 'N/A')])
        writer.writerow(['', ''])

        # Add more sections as needed...

        # Create the CSV response
        output = si.getvalue()
        si.close()
        
        return send_file(
            BytesIO(output.encode()),
            download_name=f'health_record_{record.animal.tag_number}_{datetime.now().strftime("%Y%m%d")}.csv',
            mimetype='text/csv'
        )

    return 'Invalid format', 400
    
