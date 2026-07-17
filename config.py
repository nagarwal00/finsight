import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    db_url = os.environ.get('DATABASE_URL') or 'sqlite:///finsight.db'
    
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql+pg8000://', 1)
    elif db_url.startswith('postgresql://'):
        db_url = db_url.replace('postgresql://', 'postgresql+pg8000://', 1)
    
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False