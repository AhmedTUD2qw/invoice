import cloudinary
import cloudinary.api
from config import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET

def test_cloudinary_connection():
    print("Testing Cloudinary connection...")
    
    # Configure Cloudinary
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET
    )
    
    try:
        # Test the connection
        print("Attempting to ping Cloudinary...")
        result = cloudinary.api.ping()
        print("Connection successful!")
        print(f"Response: {result}")
        return True
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_cloudinary_connection()
