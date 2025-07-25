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
            
        # Create a unique temporary directory for this upload
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, filename)
        
        try:
            # Save the file
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
                        
            return {
                'success': True,
                'url': result['secure_url'],
                'public_id': result['public_id']
            }
                
        except Exception as e:
            print(f"Error uploading to Cloudinary: {str(e)}")
            if 'file' in locals() and hasattr(file, 'filename'):
                print(f"Failed file: {file.filename}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            # تنظيف الملفات المؤقتة
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                print(f"Warning: Could not remove temporary directory {temp_dir}: {str(e)}")
        
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
    from requests.adapters import HTTPAdapter
    from urllib3.util import Retry
    
    # تكوين جلسة requests مع إعادة المحاولة التلقائية
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    try:
        print(f"Starting to create ZIP file at {local_path}")
        print(f"Number of files to process: {len(urls)}")
        
        # التأكد من وجود المجلد
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        with zipfile.ZipFile(local_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for index, url_info in enumerate(urls, 1):
                print(f"\nProcessing file {index}/{len(urls)}")
                print(f"URL: {url_info['url']}")
                print(f"Branch: {url_info['branch']}")
                print(f"Model: {url_info['model_name']}")
                print(f"Filename: {url_info['filename']}")
                
                try:
                    response = session.get(url_info['url'], timeout=30)
                    response.raise_for_status()  # سيرفع استثناءً إذا كان الرد غير ناجح
                    
                    # حفظ الملف في الأرشيف مع المسار المنظم
                    arcname = f"{url_info['branch']}/{url_info['model_name']}/{url_info['filename']}"
                    
                    # حفظ مؤقت للملف
                    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                        tmp_file.write(response.content)
                        tmp_file.flush()
                        
                        # التحقق من حجم الملف
                        file_size = os.path.getsize(tmp_file.name)
                        print(f"Downloaded file size: {file_size} bytes")
                        
                        if file_size > 0:
                            # إضافة الملف للأرشيف
                            zipf.write(tmp_file.name, arcname=arcname)
                            print(f"Added to ZIP: {arcname}")
                        else:
                            print(f"Warning: Empty file downloaded for {url_info['filename']}")
                        
                        # حذف الملف المؤقت
                        os.unlink(tmp_file.name)
                        
                except requests.exceptions.RequestException as e:
                    print(f"Error downloading {url_info['filename']}: {str(e)}")
                    continue
                except Exception as e:
                    print(f"Error processing {url_info['filename']}: {str(e)}")
                    continue
        
        # التحقق من حجم ملف ZIP النهائي
        zip_size = os.path.getsize(local_path)
        print(f"\nFinal ZIP file size: {zip_size} bytes")
        
        if zip_size > 0:
            print("ZIP file created successfully!")
            return True
        else:
            print("Error: Created ZIP file is empty")
            return False
            
    except Exception as e:
        print(f"Error creating zip file: {str(e)}")
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
                print(f"Cleaned up incomplete ZIP file: {local_path}")
            except:
                pass
        return False
