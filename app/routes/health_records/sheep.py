from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.animal import Animal, HealthRecord
from datetime import datetime, date
import json

# Create sheep blueprint
bp = Blueprint('sheep', __name__, url_prefix='/health-records/sheep')

@bp.route('/')
@login_required
def index():
    """List all sheep health records"""
    records = (HealthRecord.query
              .join(Animal)
              .filter(Animal.species == 'Sheep')
              .order_by(HealthRecord.date.desc())
              .all())
    return render_template('health_records/sheep/list.html',
                         records=records,
                         animal_type='Sheep',
                         today=date.today())

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Add a new sheep health record"""
    if request.method == 'POST':
        try:
            # Get the sheep by tag number
            tag_number = request.form.get('tag_number')
            sheep = Animal.query.filter_by(tag_number=tag_number, species='Sheep').first()
            
            if not sheep:
                flash('Sheep not found with this tag number', 'danger')
                return redirect(url_for('health_records.sheep.add'))
            
            # Check for existing record today
            existing_record = HealthRecord.query.filter_by(
                animal_id=sheep.id,
                date=date.today()
            ).first()
            
            if existing_record:
                flash('A health record already exists for this sheep today', 'warning')
                return redirect(url_for('health_records.sheep.add'))

            # Build structured description
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
                },
                "Parasite Control": {
                    "Last Check Date": request.form.get('last_check_date'),
                    "Status": request.form.get('parasite_status'),
                    "Treatment": request.form.get('treatment_details')
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
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': 'Health record added successfully!'})
            
            flash('Health record added successfully!', 'success')
            return redirect(url_for('health_records.sheep.index'))
            
        except Exception as e:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': str(e)}), 400
            
            flash(f'Error adding health record: {str(e)}', 'danger')
            return redirect(url_for('health_records.sheep.add'))
    
    return render_template('health_records/sheep/add.html',
                         animal_type='Sheep',
                         today=date.today())

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit a sheep health record"""
    record = HealthRecord.query.get_or_404(id)
    
    if record.animal.species != 'Sheep':
        flash('Invalid record type', 'danger')
        return redirect(url_for('health_records.sheep.index'))
    
    try:
        description = json.loads(record.description) if record.description else {}
    except:
        description = {}
    
    if request.method == 'POST':
        try:
            # Update description with new data
            new_description = {
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
                },
                "Parasite Control": {
                    "Last Check Date": request.form.get('last_check_date'),
                    "Status": request.form.get('parasite_status'),
                    "Treatment": request.form.get('treatment_details')
                }
            }
            
            record.description = json.dumps(new_description, indent=2)
            record.treatment = request.form.get('treatment_details')
            
            db.session.commit()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': 'Record updated successfully',
                    'redirectUrl': url_for('health_records.sheep.view', id=record.id)
                })
            
            flash('Health record updated successfully!', 'success')
            return redirect(url_for('health_records.sheep.view', id=record.id))
            
        except Exception as e:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': str(e)}), 400
            
            flash(f'Error updating record: {str(e)}', 'danger')
            return redirect(url_for('health_records.sheep.edit', id=record.id))
    
    # Extract data for the template
    data = {
        'weight': description.get('Basic Information', {}).get('Weight'),
        'health_status': description.get('Health Status', {}).get('Current'),
        'vaccination_status': description.get('Health Status', {}).get('Vaccination'),
        
        'pregnancy_status': description.get('Lambing', {}).get('Status'),
        'due_date': description.get('Lambing', {}).get('Due Date'),
        'number_of_lambs': description.get('Lambing', {}).get('Number of Lambs'),
        'lambing_ease': description.get('Lambing', {}).get('Lambing Ease'),
        'lambing_notes': description.get('Lambing', {}).get('Notes'),
        
        'foot_condition': description.get('Foot Health', {}).get('Condition'),
        'last_foot_check': description.get('Foot Health', {}).get('Last Check'),
        'foot_notes': description.get('Foot Health', {}).get('Notes'),
        
        'behavior_pattern': description.get('Behavior', {}).get('Pattern'),
        'stress_level': description.get('Behavior', {}).get('Stress Level'),
        'behavior_notes': description.get('Behavior', {}).get('Notes'),
        
        'wool_quality': description.get('Wool Quality', {}).get('Condition'),
        'wool_texture': description.get('Wool Quality', {}).get('Texture'),
        'last_shearing': description.get('Wool Quality', {}).get('Last Shearing'),
        'next_shearing': description.get('Wool Quality', {}).get('Next Shearing'),
        
        'last_check_date': description.get('Parasite Control', {}).get('Last Check Date'),
        'parasite_status': description.get('Parasite Control', {}).get('Status'),
        'treatment_details': description.get('Parasite Control', {}).get('Treatment')
    }
    
    return render_template('health_records/sheep/edit.html',
                         record=record,
                         data=data,
                         animal_type='Sheep')

@bp.route('/<int:id>')
@login_required
def view(id):
    """View a sheep health record"""
    record = HealthRecord.query.get_or_404(id)
    
    if record.animal.species != 'Sheep':
        flash('Invalid record type', 'danger')
        return redirect(url_for('health_records.sheep.index'))
    
    try:
        description = json.loads(record.description) if record.description else {}
    except:
        description = {}
    
    # Extract data for the template
    data = {
        'tag_number': record.animal.tag_number,
        'record_date': record.date.strftime('%Y-%m-%d'),
        'weight': description.get('Basic Information', {}).get('Weight'),
        
        'health_status': description.get('Health Status', {}).get('Current'),
        'vaccination_status': description.get('Health Status', {}).get('Vaccination'),
        
        'pregnancy_status': description.get('Lambing', {}).get('Status'),
        'due_date': description.get('Lambing', {}).get('Due Date'),
        'number_of_lambs': description.get('Lambing', {}).get('Number of Lambs'),
        'lambing_ease': description.get('Lambing', {}).get('Lambing Ease'),
        'lambing_notes': description.get('Lambing', {}).get('Notes'),
        
        'foot_condition': description.get('Foot Health', {}).get('Condition'),
        'last_foot_check': description.get('Foot Health', {}).get('Last Check'),
        'foot_notes': description.get('Foot Health', {}).get('Notes'),
        
        'behavior_pattern': description.get('Behavior', {}).get('Pattern'),
        'stress_level': description.get('Behavior', {}).get('Stress Level'),
        'behavior_notes': description.get('Behavior', {}).get('Notes'),
        
        'wool_quality': description.get('Wool Quality', {}).get('Condition'),
        'wool_texture': description.get('Wool Quality', {}).get('Texture'),
        'last_shearing': description.get('Wool Quality', {}).get('Last Shearing'),
        'next_shearing': description.get('Wool Quality', {}).get('Next Shearing'),
        
        'last_check_date': description.get('Parasite Control', {}).get('Last Check Date'),
        'parasite_status': description.get('Parasite Control', {}).get('Status'),
        'treatment_details': description.get('Parasite Control', {}).get('Treatment')
    }
    
    return render_template('health_records/sheep/view.html',
                         record=record,
                         data=data,
                         today=date.today(),
                         animal_type='Sheep')