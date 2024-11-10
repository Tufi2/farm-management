from app import db
from datetime import datetime

class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag_number = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100))
    species = db.Column(db.String(50), nullable=False)  # Sheep, Cattle, Chicken, Other
    breed = db.Column(db.String(50))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(20))
    weight = db.Column(db.Float)
    status = db.Column(db.String(20), default='active')  # active, sold, deceased
    purchase_date = db.Column(db.Date)
    purchase_price = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Sheep-specific fields
    wool_type = db.Column(db.String(50))
    last_shearing = db.Column(db.Date)
    fleece_weight = db.Column(db.Float)
    wool_grade = db.Column(db.String(20))
    lambing_status = db.Column(db.String(50))
    lambing_date = db.Column(db.Date)
    
    # Cattle-specific fields
    milk_production = db.Column(db.Float)  # Daily milk production in liters
    last_milking = db.Column(db.DateTime)
    milk_quality = db.Column(db.String(20))
    calving_status = db.Column(db.String(50))
    calving_date = db.Column(db.Date)
    milk_fat_content = db.Column(db.Float)
    
    # Chicken-specific fields
    egg_production = db.Column(db.Integer)  # Daily egg production
    egg_color = db.Column(db.String(20))
    comb_type = db.Column(db.String(20))
    laying_status = db.Column(db.String(20))
    last_laying_date = db.Column(db.Date)
    egg_size = db.Column(db.String(20))
    
    # Other animal fields
    category = db.Column(db.String(50))  # For other animals: type of animal
    special_needs = db.Column(db.Text)
    diet_requirements = db.Column(db.Text)
    habitat = db.Column(db.String(100))
    
    # Relationships
    health_records = db.relationship('HealthRecord', backref='animal', lazy=True)
    
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
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)
    record_type = db.Column(db.String(50))  # vaccination, treatment, checkup
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    treatment = db.Column(db.Text)
    cost = db.Column(db.Float)
    next_due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __repr__(self):
        return f'<HealthRecord {self.id} for Animal {self.animal_id}>'