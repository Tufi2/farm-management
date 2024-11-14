from app import db
from datetime import datetime

class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=True)  # Explicitly mark as nullable
    species = db.Column(db.String(50), nullable=False, index=True)
    breed = db.Column(db.String(50), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    weight = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='active', nullable=False)
    purchase_date = db.Column(db.Date, nullable=True)
    purchase_price = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Sheep-specific fields - all nullable
    wool_type = db.Column(db.String(50), nullable=True)
    last_shearing = db.Column(db.Date, nullable=True)
    fleece_weight = db.Column(db.Float, nullable=True)
    wool_grade = db.Column(db.String(20), nullable=True)
    lambing_status = db.Column(db.String(50), nullable=True)
    lambing_date = db.Column(db.Date, nullable=True)
    
    # Cattle-specific fields - all nullable
    milk_production = db.Column(db.Float, nullable=True)
    last_milking = db.Column(db.Date, nullable=True)  # Changed from DateTime to Date
    milk_quality = db.Column(db.String(20), nullable=True)
    calving_status = db.Column(db.String(50), nullable=True)
    calving_date = db.Column(db.Date, nullable=True)
    milk_fat_content = db.Column(db.Float, nullable=True)
    
    # Chicken-specific fields - all nullable
    egg_production = db.Column(db.Integer, nullable=True)
    egg_color = db.Column(db.String(20), nullable=True)
    comb_type = db.Column(db.String(20), nullable=True)
    laying_status = db.Column(db.String(20), nullable=True)
    last_laying_date = db.Column(db.Date, nullable=True)
    egg_size = db.Column(db.String(20), nullable=True)
    
    # Other animal fields - all nullable
    category = db.Column(db.String(50), nullable=True)
    special_needs = db.Column(db.Text, nullable=True)
    diet_requirements = db.Column(db.Text, nullable=True)
    habitat = db.Column(db.String(100), nullable=True)
    
    # Relationships with cascade delete
    health_records = db.relationship('HealthRecord', backref='animal', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Animal {self.tag_number}>'

    def get_specific_fields(self):
        """Return fields specific to the animal type"""
        if self.species == 'Sheep':
            return {
                'wool_type': self.wool_type,
                'last_shearing': self.last_shearing,
                'fleece_weight': self.fleece_weight,
                'wool_grade': self.wool_grade,
                'lambing_status': self.lambing_status,
                'lambing_date': self.lambing_date
            }
        elif self.species == 'Cattle':
            return {
                'milk_production': self.milk_production,
                'last_milking': self.last_milking,
                'milk_quality': self.milk_quality,
                'calving_status': self.calving_status,
                'calving_date': self.calving_date,
                'milk_fat_content': self.milk_fat_content
            }
        elif self.species == 'Chicken':
            return {
                'egg_production': self.egg_production,
                'egg_color': self.egg_color,
                'comb_type': self.comb_type,
                'laying_status': self.laying_status,
                'last_laying_date': self.last_laying_date,
                'egg_size': self.egg_size
            }
        else:  # Other animals
            return {
                'category': self.category,
                'special_needs': self.special_needs,
                'diet_requirements': self.diet_requirements,
                'habitat': self.habitat
            }


class HealthRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id', ondelete='CASCADE'), nullable=False)
    record_type = db.Column(db.String(50), nullable=False)  # Made nullable=False
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    treatment = db.Column(db.Text, nullable=True)
    cost = db.Column(db.Float, nullable=True)
    next_due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    
    def __repr__(self):
        return f'<HealthRecord {self.id} for Animal {self.animal_id}>'