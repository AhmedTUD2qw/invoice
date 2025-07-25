from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, send_file, jsonify, after_this_request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
import os
import shutil
from datetime import datetime
import time
import atexit
from models import MODELS, db, Invoice, User
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import zipfile

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['TEMP_FOLDER'] = os.path.join('static', 'temp')
database_url = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PREFERRED_URL_SCHEME'] = 'https'  # للتأكد من استخدام HTTPS

# Initialize SQLAlchemy with app
db.init_app(app)

# Create tables
def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.first():
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
                print("Default users created successfully!")
            except Exception as e:
                print(f"Error creating default users: {str(e)}")
                db.session.rollback()

# Initialize database on startup
with app.app_context():
    db.create_all()
    init_db()

# Create tables
with app.app_context():
    try:
        # Create all tables
        db.create_all()
        
        # Check if users already exist
        if not User.query.first():
            # Create default users
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
            db.session.commit()
            print("Default users created successfully!")
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        db.session.rollback()

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

def init_db():
    db.create_all()
    # Create default users if they don't exist
    if not User.query.first():
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
        db.session.commit()

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
                            new_invoice = Invoice(
                                image_name=filename,
                                model_name=model_name,
                                branch=branch,
                                supervisor=supervisor,
                                upload_date=datetime.now(),
                                cloudinary_url=upload_result['url'],
                                cloudinary_public_id=upload_result['public_id']
                            )
                            db.session.add(new_invoice)
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
                db.session.commit()
                flash(f'تم رفع {len(uploaded_files)} ملفات بنجاح')
            else:
                flash('لم يتم رفع أي ملفات')
                
        except Exception as e:
            print(f"Error: {str(e)}")
            flash('حدث خطأ أثناء رفع الملفات')
        
        return redirect(url_for('public_upload'))

    # جلب قائمة الفروع المستخدمة
    try:
        branches = db.session.query(Invoice.branch).distinct().order_by(Invoice.branch).all()
        branches = [branch[0] for branch in branches]
    except Exception as e:
        print(f"Error fetching branches: {str(e)}")
        branches = []
    
    return render_template('public_upload.html', models=MODELS, branches=branches, supervisors=SUPERVISORS)

# User loader for flask-login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# تسجيل الدخول للمدير
from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                if user.role == 'seller':
                    return redirect(url_for('upload_invoice'))
                else:
                    return redirect(url_for('admin_view'))
            else:
                flash('بيانات الدخول غير صحيحة')
        except Exception as e:
            print(f"Login error: {str(e)}")
            flash('حدث خطأ في تسجيل الدخول')
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
            new_invoice = Invoice(
                image_name=filename,
                model_name=model_name,
                branch=branch,
                upload_date=datetime.now(),
                user_id=current_user.id
            )
            db.session.add(new_invoice)
            db.session.commit()
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
        
    branch = request.args.get('branch', '')
    model_name = request.args.get('model_name', '')
    supervisor = request.args.get('supervisor', '')
    
    # جلب قائمة الفروع المتوفرة
    branches = db.session.query(Invoice.branch).distinct().order_by(Invoice.branch).all()
    branches = [b[0] for b in branches]
    
    # بناء query الفلترة
    query = Invoice.query
    filtered = False
    
    if branch:
        query = query.filter(Invoice.branch == branch)
        filtered = True
    if model_name:
        query = query.filter(Invoice.model_name == model_name)
        filtered = True
    if supervisor:
        query = query.filter(Invoice.supervisor == supervisor)
        filtered = True
        
    invoices = query.order_by(Invoice.upload_date.desc()).all()
    
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
        
        query = Invoice.query

        if branch:
            query = query.filter(Invoice.branch == branch)
        if model_name:
            query = query.filter(Invoice.model_name == model_name)
        if supervisor:
            query = query.filter(Invoice.supervisor == supervisor)
            
        invoices = query.all()
        
        if not invoices:
            flash('لا توجد فواتير للتحميل')
            return redirect(url_for('admin_view'))
        
        # استخدام اسم الملف المرسل من الواجهة، أو إنشاء اسم افتراضي
        zip_name = request.args.get('filename', None)
        if not zip_name:
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
            'url': invoice.cloudinary_url,
            'filename': invoice.image_name,
            'branch': invoice.branch,
            'model_name': invoice.model_name
        } for invoice in invoices]
        
        # إنشاء ملف ZIP من روابط Cloudinary
        success = create_zip_from_urls(urls, zip_path)
        
        if success:
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
        else:
            flash('حدث خطأ أثناء إنشاء ملف التحميل')
            return redirect(url_for('admin_view'))
                        
    except Exception as e:
        print(f"Error in download_filtered: {str(e)}")
        flash('حدث خطأ أثناء تحميل الملفات')
        return redirect(url_for('admin_view'))
                        
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
    
    branches = db.session.query(Invoice.branch).distinct().filter(
        Invoice.branch.ilike(f'%{query}%')
    ).order_by(Invoice.branch).all()
    
    return jsonify([branch[0] for branch in branches])


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
        
        # جلب جميع الفواتير للفرع
        invoices = Invoice.query.filter_by(branch=branch).all()
        
        # حذف الملفات من Cloudinary
        for invoice in invoices:
            if invoice.cloudinary_public_id:
                delete_result = delete_file(invoice.cloudinary_public_id)
                if not delete_result['success']:
                    print(f"Error deleting file from Cloudinary: {delete_result.get('error')}")
        
        # حذف من قاعدة البيانات
        Invoice.query.filter_by(branch=branch).delete()
        db.session.commit()
        
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
        
    invoice = Invoice.query.get(invoice_id)
    
    if invoice:
        # حذف الملف من Cloudinary
        if invoice.cloudinary_public_id:
            delete_result = delete_file(invoice.cloudinary_public_id)
            if not delete_result['success']:
                flash('حدث خطأ أثناء حذف الملف')
                return redirect(url_for('admin_view'))
            
        # حذف من قاعدة البيانات
        db.session.delete(invoice)
        db.session.commit()
        
        flash('تم حذف الفاتورة بنجاح')
    else:
        flash('الفاتورة غير موجودة')
        
    return redirect(url_for('admin_view'))

# تغيير كلمة المرور
@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'غير مصرح لك بهذه العملية'})
    
    try:
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # التحقق من صحة البيانات
        if not all([old_password, new_password, confirm_password]):
            return jsonify({'success': False, 'message': 'جميع الحقول مطلوبة'})
            
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'كلمة المرور الجديدة غير متطابقة'})
            
        if not check_password_hash(current_user.password, old_password):
            return jsonify({'success': False, 'message': 'كلمة المرور الحالية غير صحيحة'})
            
        # تحديث كلمة المرور
        current_user.password = generate_password_hash(new_password)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تغيير كلمة المرور بنجاح'
        })
        
    except Exception as e:
        print(f"Error changing password: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء تغيير كلمة المرور'
        })

# إدارة المشرفين
@app.route('/manage_supervisors', methods=['POST'])
@login_required
def manage_supervisors():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'غير مصرح لك بهذه العملية'})
    
    try:
        action = request.form.get('action')
        supervisor = request.form.get('supervisor')
        
        if not supervisor:
            return jsonify({'success': False, 'message': 'يرجى إدخال اسم المشرف'})
            
        global SUPERVISORS
        
        if action == 'add':
            if supervisor in SUPERVISORS:
                return jsonify({'success': False, 'message': 'المشرف موجود بالفعل'})
            SUPERVISORS.append(supervisor)
            SUPERVISORS.sort()  # ترتيب القائمة
            
        elif action == 'remove':
            if supervisor not in SUPERVISORS:
                return jsonify({'success': False, 'message': 'المشرف غير موجود'})
            SUPERVISORS.remove(supervisor)
            
        else:
            return jsonify({'success': False, 'message': 'عملية غير صالحة'})
            
        return jsonify({
            'success': True,
            'message': 'تم تحديث قائمة المشرفين بنجاح',
            'supervisors': SUPERVISORS
        })
        
    except Exception as e:
        print(f"Error managing supervisors: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء تحديث قائمة المشرفين'
        })

# تسجيل الخروج
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

def create_default_users():
    try:
        # إضافة مدير وبائع افتراضيين إذا لم يكونوا موجودين
        if not User.query.first():
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
            db.session.commit()
            print("Successfully created default users")
    except Exception as e:
        print(f"Error creating default users: {str(e)}")
        db.session.rollback()

if __name__ == '__main__':
    with app.app_context():
        init_db()
        create_default_users()
    app.run(debug=True)
