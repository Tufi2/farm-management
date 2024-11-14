from app import create_app, db

app = create_app()

# Create an application context
with app.app_context():
    try:
        # This will create any new tables and update existing ones
        db.create_all()
        print("Database schema updated successfully!")
    except Exception as e:
        print(f"Error updating database schema: {str(e)}")