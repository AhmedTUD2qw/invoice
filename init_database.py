import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = 'database.db'

def init_db():
    print("Creating database tables...")
    with sqlite3.connect(DATABASE) as db:
        # إنشاء جدول المستخدمين
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )''')
        
        # إنشاء جدول الفواتير
        db.execute('''CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_name TEXT NOT NULL,
            model_name TEXT NOT NULL,
            branch TEXT NOT NULL,
            supervisor TEXT NOT NULL,
            upload_date TEXT NOT NULL,
            cloudinary_url TEXT,
            cloudinary_public_id TEXT,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        
        # التحقق من وجود المستخدم الافتراضي
        admin = db.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
        if not admin:
            print("Creating default admin user...")
            db.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                      ('admin', generate_password_hash('admin123'), 'admin'))
        
        db.commit()
        print("Database initialization completed successfully!")

if __name__ == '__main__':
    init_db()
