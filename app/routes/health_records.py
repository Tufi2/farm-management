from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.animal import Animal, HealthRecord
from datetime import datetime, date

bp = Blueprint('health_records', __name__, url_prefix='/health-records')

@bp.route('/')
@login_required
def index():
    """Display health records organized by animal type"""
    today = date.today()
    
    # Get records for each animal type
    sheep_records = (HealthRecord.query
                    .join(Animal)
                    .filter(Animal.species == 'Sheep')
                    .order_by(HealthRecord.date.desc())
                    .limit(5)
                    .all())
    
    cattle_records = (HealthRecord.query
                     .join(Animal)
                     .filter(Animal.species == 'Cattle')
                     .order_by(HealthRecord.date.desc())
                     .limit(5)
                     .all())
    
    goat_records = (HealthRecord.query
                   .join(Animal)
                   .filter(Animal.species == 'Goat')
                   .order_by(HealthRecord.date.desc())
                   .limit(5)
                   .all())
    
    chicken_records = (HealthRecord.query
                      .join(Animal)
                      .filter(Animal.species == 'Chicken')
                      .order_by(HealthRecord.date.desc())
                      .limit(5)
                      .all())

    return render_template('health_records/index.html',
                         sheep_records=sheep_records,
                         cattle_records=cattle_records,
                         goat_records=goat_records,
                         chicken_records=chicken_records,
                         today=today)

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
    
    return render_template('health_records/list.html',
                         records=records,
                         animal_type=species,
                         today=today)

# Keep your existing routes below this line
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
    """Edit an existing health record"""
    record = HealthRecord.query.get_or_404(id)
    
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
            
            record.record_type = request.form.get('record_type')
            record.date = record_date
            record.description = request.form.get('description')
            record.treatment = request.form.get('treatment')
            record.cost = cost
            record.next_due_date = next_due_date
            
            db.session.commit()
            flash('Health record updated successfully!', 'success')
            return redirect(url_for('health_records.view', id=record.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating health record: {str(e)}', 'danger')
            return redirect(url_for('health_records.edit', id=record.id))
    
    return render_template('health_records/edit.html', record=record)

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