import os

# Security Key
SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')

# Database URI
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///chat.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Gemini API Key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyBYwtFNIN9V6gQDmj3yjNxzYwmj_1KkvsA')
