import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration."""
    # App configuration
    DEBUG = True
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
    
    # File paths - simplified to use direct paths from app root
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # Get the directory containing this file
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    REPORT_JSON_PATH = os.path.join(DATA_DIR, 'report.json')
    MEASURE_DEPENDENCIES_TSV_PATH = os.path.join(DATA_DIR, 'MeasureDependencies.tsv')
    MODEL_JSON_PATH = os.path.join(DATA_DIR, 'model.json')
    
    # UI configuration
    APP_NAME = "Power BI Analysis Tool"
    APP_VERSION = "1.0.0"
    APP_AUTHOR = "Dimitrios"
    
    # Feature flags
    ENABLE_MODEL_INSIGHTS = True
    ENABLE_REPORT_INSIGHTS = True
    ENABLE_SOURCE_EXPLORER = True
    ENABLE_DAX_EXPLORER = True
    ENABLE_LINEAGE_VIEW = True
    
    # Performance settings
    MAX_VISUALS_PER_PAGE = 100


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = False
    TESTING = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    # In production, set this from environment variable
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    def __init__(self):
        # Ensure SECRET_KEY is set in production
        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable must be set in production")


# Configuration dictionary to easily select environment
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Return the appropriate configuration object based on environment."""
    env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default'])
