import cloudinary
import cloudinary.uploader
import cloudinary.api
from config import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
import os
import tempfile
import time
import requests
from werkzeug.utils import secure_filename

# تهيئة Cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

def verify_cloudinary_connection():
    """
    التحقق من الاتصال بـ Cloudinary
    """
    import requests
    try:
        # تحقق من الاتصال بالإنترنت أولاً
        requests.get("https://api.cloudinary.com", timeout=5)
        
        # تحقق من صحة بيانات الاعتماد
        cloudinary.api.ping()
        return True, None
    except requests.exceptions.ConnectionError:
        return False, "لا يمكن الاتصال بخدمة Cloudinary. يرجى التحقق من اتصال الإنترنت الخاص بك"
    except Exception as e:
        if "Invalid credentials" in str(e):
            return False, "بيانات اعتماد Cloudinary غير صحيحة. يرجى التحقق من الإعدادات"
        return False, f"خطأ في الاتصال: {str(e)}"

def upload_file(file, branch, model_name):
    """
    رفع ملف إلى Cloudinary
    """
    try:
        if not file or not file.filename:
            raise ValueError("No file provided")
            
        # تأمين اسم الملف
        filename = secure_filename(file.filename)
        if not filename:
            raise ValueError("Invalid filename")
            
        # التحقق من الاتصال بـ Cloudinary
        connection_ok, error_message = verify_cloudinary_connection()
        if not connection_ok:
            raise ConnectionError(error_message)
            
        # Save file temporarily to ensure it's readable
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        file.save(temp_path)
        
        print(f"Uploading file {filename} to Cloudinary...")
        print(f"File size: {os.path.getsize(temp_path)} bytes")
        print(f"Target folder: invoices/{branch}/{model_name}")
        
        # محاولة الرفع مع إعادة المحاولة
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # رفع الملف إلى Cloudinary
                result = cloudinary.uploader.upload(
                    temp_path,
                    folder=f"invoices/{branch}/{model_name}",
                    public_id=os.path.splitext(filename)[0],  # Remove extension from public_id
                    overwrite=True,
                    resource_type="auto",
                    timeout=30  # زيادة مهلة الاتصال
                )
                break  # نجح الرفع
            except Exception as upload_error:
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} failed, retrying...")
                    time.sleep(2)  # انتظار قبل إعادة المحاولة
                else:
                    raise upload_error  # رفع الخطأ بعد استنفاد جميع المحاولات
        
        # Clean up temp file
        os.remove(temp_path)
        
        print(f"Upload successful. URL: {result.get('secure_url')}")
        
        return {
            'success': True,
            'url': result['secure_url'],
            'public_id': result['public_id']
        }
    except Exception as e:
        print(f"Error uploading to Cloudinary: {str(e)}")
        if 'file' in locals() and hasattr(file, 'filename'):
            print(f"Failed file: {file.filename}")
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        return {
            'success': False,
            'error': str(e)
        }

def delete_file(public_id):
    """
    حذف ملف من Cloudinary
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        return {
            'success': True,
            'result': result
        }
    except Exception as e:
        print(f"Error deleting from Cloudinary: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def create_zip_from_urls(urls, local_path):
    """
    إنشاء ملف ZIP من روابط Cloudinary
    """
    import zipfile
    import requests
    
    try:
        with zipfile.ZipFile(local_path, 'w') as zipf:
            for url_info in urls:
                response = requests.get(url_info['url'])
                if response.status_code == 200:
                    # حفظ الملف في الأرشيف مع المسار المنظم
                    arcname = f"{url_info['branch']}/{url_info['model_name']}/{url_info['filename']}"
                    # حفظ مؤقت للملف
                    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                        tmp_file.write(response.content)
                        tmp_file.flush()
                        # إضافة الملف للأرشيف
                        zipf.write(tmp_file.name, arcname=arcname)
                        # حذف الملف المؤقت
                        os.unlink(tmp_file.name)
        return True
    except Exception as e:
        print(f"Error creating zip file: {str(e)}")
        return False
