import os

# Cloudinary configuration
CLOUDINARY_CLOUD_NAME = "dxrjyjxiq"  # ضع اسم السحابة الخاص بك من Cloudinary
CLOUDINARY_API_KEY = "164248476758576"      # ضع مفتاح API الخاص بك
CLOUDINARY_API_SECRET = "QKnKGzPjo4o44x-MWQw4Hd8bC4M" # ضع الرمز السري للـ API

# Flask configuration
SECRET_KEY = 'QKnKGzPjo4o44x-MWQw4Hd8bC4M'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Paths
UPLOAD_FOLDER = os.path.join('static', 'uploads')
TEMP_FOLDER = os.path.join('static', 'temp')

# Database
DATABASE = 'database.db'
