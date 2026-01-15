# File: config.py
# Configuration file for Market Optimizer
# আপনার API keys এবং settings এখানে রাখুন

import os

# ====================================
# Gemini API Configuration
# ====================================
# নিচের লাইনে আপনার Gemini API key দিন
# Get your API key from: https://aistudio.google.com/app/apikey

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

# যদি আপনি .env file ব্যবহার করেন, তাহলে সেখানে এভাবে লিখুন:
# GEMINI_API_KEY=your_api_key_here

# অথবা সরাসরি এখানে লিখতে পারেন (তবে সুরক্ষিত নয়):
# GEMINI_API_KEY = 'AIzaSy...'  # আপনার key এখানে

# Gemini Model Settings
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash-exp')

# যদি আপনি অন্য model ব্যবহার করতে চান:
# Options: 'gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-2.0-flash-exp'

# ====================================
# OpenAI API Configuration (Optional)
# ====================================
# যদি OpenAI ব্যবহার করতে চান
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4')

# ====================================
# Database Settings
# ====================================
DATABASE_PATH = 'data/ecommerce.db'

# ====================================
# Application Settings
# ====================================
# Debug mode (development এ True, production এ False)
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Flask server port
PORT = int(os.environ.get('PORT', 5000))

# Skip data ingestion (দ্রুত startup এর জন্য)
SKIP_INGEST = os.environ.get('SKIP_INGEST', 'False').lower() == 'true'

# ====================================
# UI Settings
# ====================================
# Default language ('en' or 'bn')
DEFAULT_LANGUAGE = 'bn'  # বাংলা default

# Default theme ('light' or 'dark')
DEFAULT_THEME = 'light'

# ====================================
# Data Settings
# ====================================
# পণ্যের তালিকা (এখানে আপনার পণ্য যোগ করুন)
PRODUCTS = ['clothing', 'electronics', 'food', 'cosmetics', 'toys']

# ট্রেন্ড ট্র্যাকিং এর জন্য অঞ্চল
REGIONS = 'BD'  # Bangladesh

# ====================================
# Export Settings
# ====================================
EXPORT_DIR = 'exports'

# ====================================
# Helper Functions
# ====================================
def get_gemini_api_key():
    """
    Gemini API key পান।
    
    Priority:
    1. Environment variable থেকে
    2. .env file থেকে
    3. এই config file থেকে
    """
    if GEMINI_API_KEY:
        return GEMINI_API_KEY
    
    # Check .env file
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('GEMINI_API_KEY='):
                    return line.split('=', 1)[1].strip().strip('"').strip("'")
    
    return None

def validate_api_key():
    """
    API key আছে কিনা চেক করুন।
    """
    key = get_gemini_api_key()
    if not key:
        print("\n⚠️  WARNING: Gemini API key পাওয়া যায়নি!")
        print("\nকীভাবে API key সেট করবেন:")
        print("1. https://aistudio.google.com/app/apikey থেকে API key নিন")
        print("2. .env file তৈরি করুন এবং লিখুন:")
        print("   GEMINI_API_KEY=your_api_key_here")
        print("অথবা")
        print("3. config.py file এ GEMINI_API_KEY = 'your_key' লিখুন\n")
        return False
    return True

def get_config():
    """
    সম্পূর্ণ configuration dictionary ফেরত দিন।
    """
    return {
        'gemini_api_key': get_gemini_api_key(),
        'gemini_model': GEMINI_MODEL,
        'openai_api_key': OPENAI_API_KEY,
        'openai_model': OPENAI_MODEL,
        'database_path': DATABASE_PATH,
        'debug': DEBUG,
        'port': PORT,
        'skip_ingest': SKIP_INGEST,
        'default_language': DEFAULT_LANGUAGE,
        'default_theme': DEFAULT_THEME,
        'products': PRODUCTS,
        'regions': REGIONS,
        'export_dir': EXPORT_DIR
    }

# Auto-validate on import
if __name__ != '__main__':
    validate_api_key()
