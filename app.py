from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, send_file, jsonify, after_this_request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
import os
import shutil
from datetime import datetime
import time
import atexit
from models import MODELS, db, Invoice
from werkzeug.utils import secure_filename
import zipfile
from werkzeug.utils import secure_filename
from datetime import datetime
import zipfile

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['TEMP_FOLDER'] = os.path.join('static', 'temp')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with app
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

# إنشاء المجلدات المطلوبة
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

# تنظيف الملفات المؤقتة
def cleanup_temp_files():
    temp_folder = app.config['TEMP_FOLDER']
    current_time = time.time()
    for filename in os.listdir(temp_folder):
        file_path = os.path.join(temp_folder, filename)
        # حذف الملفات المؤقتة الأقدم من ساعة
        if os.path.isfile(file_path) and current_time - os.path.getmtime(file_path) > 3600:
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error cleaning up {file_path}: {str(e)}")

# تنظيف الملفات المؤقتة عند إغلاق التطبيق
atexit.register(cleanup_temp_files)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

DATABASE = 'database.db'

# User class for flask-login
class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

    def get_id(self):
        return str(self.id)

# Database helpers

def get_db():
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Database error: {str(e)}")
        return None

def init_db():
    conn = sqlite3.connect(DATABASE)
    try:
        db = conn.cursor()
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_name TEXT NOT NULL,
            model_name TEXT NOT NULL,
            branch TEXT NOT NULL,
            supervisor TEXT NOT NULL,
            upload_date TEXT NOT NULL,
            user_id INTEGER,
            cloudinary_url TEXT,
            cloudinary_public_id TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        conn.commit()
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

# قائمة المشرفين المباشرين
SUPERVISORS = ['طارق يحيى', 'حسام خطاب', 'جمال عزت']

# صفحة رفع الفواتير العامة
@app.route('/', methods=['GET', 'POST'])
def public_upload():
    if request.method == 'POST':
        try:
            from storage import upload_file  # استيراد دالة الرفع إلى Cloudinary
            
            model_name = request.form.get('model_name', '')
            branch = request.form.get('branch', '')
            supervisor = request.form.get('supervisor', '')
            files = request.files.getlist('invoice_images[]')
            
            # تحقق من صحة البيانات
            if not model_name or not branch or not supervisor or not files:
                flash('يرجى تعبئة جميع الحقول')
                return redirect(url_for('public_upload'))
            
            if model_name not in MODELS:
                flash('يرجى اختيار موديل صحيح من القائمة')
                return redirect(url_for('public_upload'))
                
            if supervisor not in SUPERVISORS:
                flash('يرجى اختيار مشرف صحيح من القائمة')
                return redirect(url_for('public_upload'))
            
            if not any(file.filename for file in files):
                flash('يرجى اختيار ملف واحد على الأقل')
                return redirect(url_for('public_upload'))
            
            uploaded_files = []
            db = get_db()
            
            for file in files:
                if file and file.filename:
                    try:
                        print(f"\nProcessing file: {file.filename}")
                        print(f"Model: {model_name}, Branch: {branch}")
                        
                        # تحقق من امتداد الملف
                        allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.PNG', '.JPG', '.JPEG'}
                        ext = os.path.splitext(file.filename)[1].lower()
                        if ext not in allowed_extensions:
                            flash(f'نوع الملف {ext} غير مدعوم. الأنواع المدعومة: {", ".join(allowed_extensions)}')
                            continue

                        # رفع الملف إلى Cloudinary
                        upload_result = upload_file(file, branch, model_name)
                        
                        if upload_result['success']:
                            filename = secure_filename(file.filename)
                            base, ext = os.path.splitext(filename)
                            filename = f"{base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
                            
                            uploaded_files.append(filename)
                            
                            print(f"File successfully uploaded to Cloudinary. Saving to database...")
                            
                            # حفظ معلومات الملف في قاعدة البيانات مع روابط Cloudinary
                            db.execute('''INSERT INTO invoices 
                                (image_name, model_name, branch, supervisor, upload_date, cloudinary_url, cloudinary_public_id) 
                                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                                (filename, model_name, branch, supervisor,
                                 datetime.now().strftime('%Y-%m-%d %H:%M'),
                                 upload_result['url'],
                                 upload_result['public_id']))
                            print(f"Database entry created successfully")
                        else:
                            error_msg = upload_result.get('error', 'Unknown error')
                            print(f"Error uploading to Cloudinary: {error_msg}")
                            flash(f'حدث خطأ أثناء رفع الملف {file.filename}: {error_msg}')
                            
                    except Exception as e:
                        print(f"Error processing file {file.filename}: {str(e)}")
                        flash(f'حدث خطأ أثناء معالجة الملف {file.filename}')
                        continue
            
            if uploaded_files:
                db.commit()
                flash(f'تم رفع {len(uploaded_files)} ملفات بنجاح')
            else:
                flash('لم يتم رفع أي ملفات')
                
        except Exception as e:
            print(f"Error: {str(e)}")
            flash('حدث خطأ أثناء رفع الملفات')
        
        return redirect(url_for('public_upload'))

    # جلب قائمة الفروع المستخدمة
    try:
        db = get_db()
        branches = db.execute('SELECT DISTINCT branch FROM invoices ORDER BY branch').fetchall()
        branches = [branch['branch'] for branch in branches]
    except Exception as e:
        print(f"Error fetching branches: {str(e)}")
        branches = []
    
    return render_template('public_upload.html', models=MODELS, branches=branches, supervisors=SUPERVISORS)

# User loader for flask-login
@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if user:
        return User(user['id'], user['username'], user['role'])
    return None

# تسجيل الدخول للمدير
from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user and check_password_hash(user['password'], password):
            user_obj = User(user['id'], user['username'], user['role'])
            login_user(user_obj)
            if user['role'] == 'seller':
                return redirect(url_for('upload_invoice'))
            else:
                return redirect(url_for('admin_view'))
        else:
            flash('بيانات الدخول غير صحيحة')
    return render_template('login.html')

# رفع فاتورة (للبائع)
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_invoice():
    if current_user.role != 'seller':
        return redirect(url_for('view_invoices'))
    if request.method == 'POST':
        model_name = request.form['model_name']
        branch = request.form['branch']
        file = request.files['invoice_image']
        if file and model_name and branch:
            branch_folder = os.path.join(app.config['UPLOAD_FOLDER'], branch)
            os.makedirs(branch_folder, exist_ok=True)
            filename = secure_filename(file.filename)
            save_path = os.path.join(branch_folder, filename)
            file.save(save_path)
            db = get_db()
            db.execute('INSERT INTO invoices (image_name, model_name, branch, upload_date, user_id) VALUES (?, ?, ?, ?, ?)',
                       (filename, model_name, branch, datetime.now().strftime('%Y-%m-%d %H:%M'), current_user.id))
            db.commit()
            flash('تم رفع الفاتورة بنجاح')
            return redirect(url_for('upload_invoice'))
        else:
            flash('يرجى تعبئة جميع الحقول')
    return render_template('upload.html')

# لوحة تحكم المدير
@app.route('/admin')
@login_required
def admin_view():
    if current_user.role != 'admin':
        flash('لا يمكنك الوصول إلى هذه الصفحة')
        return redirect(url_for('login'))
        
    db = get_db()
    branch = request.args.get('branch', '')
    model_name = request.args.get('model_name', '')
    supervisor = request.args.get('supervisor', '')
    
    # جلب قائمة الفروع المتوفرة
    branches = db.execute('SELECT DISTINCT branch FROM invoices ORDER BY branch').fetchall()
    branches = [b['branch'] for b in branches]
    
    # بناء query الفلترة
    query = 'SELECT * FROM invoices WHERE 1=1'
    params = []
    filtered = False
    
    if branch:
        query += ' AND branch = ?'
        params.append(branch)
        filtered = True
    if model_name:
        query += ' AND model_name = ?'
        params.append(model_name)
        filtered = True
    if supervisor:
        query += ' AND supervisor = ?'
        params.append(supervisor)
        filtered = True
        
    query += ' ORDER BY upload_date DESC'
    invoices = db.execute(query, params).fetchall()
    
    return render_template('admin.html',
                         invoices=invoices,
                         branches=branches,
                         models=MODELS,
                         supervisors=SUPERVISORS,
                         filtered=filtered)

# تحميل الفواتير المفلترة
@app.route('/download_filtered')
@login_required
def download_filtered():
    if current_user.role != 'admin':
        return redirect(url_for('login'))
        
    try:
        from storage import create_zip_from_urls
        
        branch = request.args.get('branch', '')
        model_name = request.args.get('model_name', '')
        supervisor = request.args.get('supervisor', '')
        
        db = get_db()
        query = 'SELECT * FROM invoices WHERE 1=1'
        params = []
        
        if branch:
            query += ' AND branch = ?'
            params.append(branch)
        if model_name:
            query += ' AND model_name = ?'
            params.append(model_name)
        if supervisor:
            query += ' AND supervisor = ?'
            params.append(supervisor)
            
        invoices = db.execute(query, params).fetchall()
        
        if not invoices:
            flash('لا توجد فواتير للتحميل')
            return redirect(url_for('admin_view'))
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_name = f'invoices_{timestamp}.zip'
        if branch and model_name:
            zip_name = f'{branch}_{model_name}_{timestamp}.zip'
        elif branch:
            zip_name = f'{branch}_{timestamp}.zip'
        elif model_name:
            zip_name = f'{model_name}_{timestamp}.zip'
            
        zip_path = os.path.join(app.config['TEMP_FOLDER'], zip_name)
        
        # تجميع روابط الصور من Cloudinary
        urls = [{
            'url': invoice['cloudinary_url'],
            'filename': invoice['image_name'],
            'branch': invoice['branch'],
            'model_name': invoice['model_name']
        } for invoice in invoices]
        
        # إنشاء ملف ZIP من روابط Cloudinary
        if create_zip_from_urls(urls, zip_path):
            @after_this_request
            def remove_file(response):
                try:
                    cleanup_temp_files()
                except Exception as e:
                    print(f"Error: {str(e)}")
                return response
                    
            return send_file(zip_path, 
                            as_attachment=True, 
                            download_name=zip_name)
                        
    except Exception as e:
        print(f"Error in download_filtered: {str(e)}")
        flash('حدث خطأ أثناء تحميل الملفات')
        return redirect(url_for('admin_view'))

# البحث في الموديلات
@app.route('/api/search_models')
def search_models():
    query = request.args.get('q', '').upper()
    if not query:
        return jsonify([])
    
    matching_models = [model for model in MODELS if query in model.upper()]
    return jsonify(matching_models)

# البحث في الفروع
@app.route('/api/search_branches')
def search_branches():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    db = get_db()
    branches = db.execute('''
        SELECT DISTINCT branch 
        FROM invoices 
        WHERE branch LIKE ? 
        ORDER BY branch
    ''', (f'%{query}%',)).fetchall()
    
    return jsonify([branch['branch'] for branch in branches])


# حذف فرع بالكامل
@app.route('/delete_branch', methods=['POST'])
@login_required
def delete_branch():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'غير مصرح لك بهذه العملية'})
    
    branch = request.form.get('branch')
    if not branch:
        return jsonify({'success': False, 'message': 'لم يتم تحديد الفرع'})
    
    try:
        from storage import delete_file
        
        db = get_db()
        # جلب جميع الفواتير للفرع
        invoices = db.execute('SELECT * FROM invoices WHERE branch = ?', (branch,)).fetchall()
        
        # حذف الملفات من Cloudinary
        for invoice in invoices:
            if invoice['cloudinary_public_id']:
                delete_result = delete_file(invoice['cloudinary_public_id'])
                if not delete_result['success']:
                    print(f"Error deleting file from Cloudinary: {delete_result.get('error')}")
        
        # حذف من قاعدة البيانات
        db.execute('DELETE FROM invoices WHERE branch = ?', (branch,))
        db.commit()
        
        return jsonify({
            'success': True,
            'message': f'تم حذف الفرع {branch} وجميع الفواتير المرتبطة به بنجاح'
        })
        
    except Exception as e:
        print(f"Error deleting branch: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء حذف الفرع'
        })

# حذف فاتورة
@app.route('/delete/<int:invoice_id>', methods=['POST'])
@login_required
def delete_invoice(invoice_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
        
    from storage import delete_file
        
    db = get_db()
    invoice = db.execute('SELECT * FROM invoices WHERE id = ?', (invoice_id,)).fetchone()
    
    if invoice:
        # حذف الملف من Cloudinary
        if invoice['cloudinary_public_id']:
            delete_result = delete_file(invoice['cloudinary_public_id'])
            if not delete_result['success']:
                flash('حدث خطأ أثناء حذف الملف')
                return redirect(url_for('admin_view'))
            
        # حذف من قاعدة البيانات
        db.execute('DELETE FROM invoices WHERE id = ?', (invoice_id,))
        db.commit()
        
        flash('تم حذف الفاتورة بنجاح')
    else:
        flash('الفاتورة غير موجودة')
        
    return redirect(url_for('admin_view'))

# تسجيل الخروج
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

def create_default_users():
    db = get_db()
    user_count = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    if user_count == 0:
        # إضافة مدير وبائع افتراضيين
        db.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                   ('admin', generate_password_hash('admin123'), 'admin'))
        db.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                   ('seller', generate_password_hash('seller123'), 'seller'))
        db.commit()

if __name__ == '__main__':
    init_db()
    create_default_users()
    app.run(debug=True)
