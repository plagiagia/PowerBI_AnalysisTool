import os
import secrets
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def generate_secret_key() -> str:
    """Generate a secure random secret key."""
    return secrets.token_hex(32)


class Config:
    """Base configuration."""
    # App configuration
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or generate_secret_key()

    # File paths - simplified to use direct paths from app root
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
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
    # Use a fixed key for testing to ensure reproducibility
    SECRET_KEY = 'test-secret-key-do-not-use-in-production'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False

    def __init__(self):
        # Ensure SECRET_KEY is explicitly set in production via environment variable
        if not os.environ.get('SECRET_KEY'):
            raise ValueError(
                "SECRET_KEY environment variable must be set in production. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        self.SECRET_KEY = os.environ.get('SECRET_KEY')


# Configuration dictionary to easily select environment
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config():
    """
    Return the appropriate configuration object based on environment.

    Uses FLASK_DEBUG for Flask 2.3+ compatibility.
    Falls back to FLASK_ENV for backwards compatibility.
    """
    # Check for explicit environment setting
    env = os.environ.get('FLASK_ENV')

    # Use FLASK_DEBUG as the primary indicator (Flask 2.3+ recommended)
    if os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes'):
        env = 'development'
    elif env is None:
        # Default to development if nothing is set
        env = 'default'

    return config.get(env, config['default'])
