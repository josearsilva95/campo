import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    SESSION_PERMANENT = False
    EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "")
    EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "")
    EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")
    URL_SISTEMA = os.getenv("URL_SISTEMA", "http://localhost:5000")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
