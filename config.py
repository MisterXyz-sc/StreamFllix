import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'streamflix-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Cloudinary Configuration - TAMBAHKAN INI
    CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', 'dzfkklsza')
    CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY', '588474134734416')
    CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET', '9c12YJe5rZSYSg7zROQuvmVZ7mg')