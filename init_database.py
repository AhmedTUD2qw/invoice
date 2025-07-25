from app import app
from models import db, User
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        print("Creating database tables...")
        
        # Drop existing tables
        print("Dropping existing tables...")
        db.drop_all()
        
        # Create tables
        print("Creating tables...")
        db.create_all()
        
        # Create default users
        print("Creating default users...")
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            role='admin'
        )
        seller = User(
            username='seller',
            password=generate_password_hash('seller123'),
            role='seller'
        )
        db.session.add(admin)
        db.session.add(seller)
        
        try:
            db.session.commit()
            print("Database initialization completed successfully!")
        except Exception as e:
            print(f"Error during initialization: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    init_db()
