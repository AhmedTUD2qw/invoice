import cloudinary
import cloudinary.api
from config import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
import sqlite3
from config import DATABASE

# تهيئة Cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

def check_uploads():
    print("جاري التحقق من الصور المرفوعة على Cloudinary...")
    
    # جلب قائمة الصور من Cloudinary
    result = cloudinary.api.resources(
        type="upload",
        prefix="invoices/",  # المجلد الذي نستخدمه لرفع الفواتير
        max_results=500
    )
    
    print("\nالصور الموجودة على Cloudinary:")
    print("--------------------------------")
    for resource in result.get('resources', []):
        print(f"اسم الملف: {resource['public_id']}")
        print(f"حجم الملف: {resource['bytes'] / 1024:.2f} KB")
        print(f"رابط الملف: {resource['secure_url']}")
        print("--------------------------------")
    
    print(f"\nإجمالي عدد الصور: {len(result.get('resources', []))}")
    
    # التحقق من قاعدة البيانات
    print("\nالتحقق من قاعدة البيانات...")
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    invoices = cursor.execute('''
        SELECT image_name, cloudinary_url, cloudinary_public_id 
        FROM invoices
    ''').fetchall()
    
    print(f"\nعدد الفواتير في قاعدة البيانات: {len(invoices)}")
    print("\nتفاصيل الفواتير في قاعدة البيانات:")
    print("--------------------------------")
    for invoice in invoices:
        print(f"اسم الملف: {invoice['image_name']}")
        print(f"معرف Cloudinary: {invoice['cloudinary_public_id']}")
        print(f"رابط Cloudinary: {invoice['cloudinary_url']}")
        print("--------------------------------")

if __name__ == '__main__':
    check_uploads()
