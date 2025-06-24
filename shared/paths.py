"""
Centralized path configuration for Cthulhu News project.
"""

from pathlib import Path
from envparse import env
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
WEB_ROOT = PROJECT_ROOT / "web"
DB_ROOT = PROJECT_ROOT / "db"

# Environment configurable paths
LOGS_DIR = str(env.str("LOGS_DIR", default="logs"))
DATA_DIR = str(env.str("DATA_DIR", default="data"))
STATIC_DIR = str(env.str("STATIC_DIR", default="static"))

# Image paths
CTHULHU_IMAGE_DIR = WEB_ROOT / DATA_DIR / "images"

# Static web paths
HTML_STATIC_DIR = WEB_ROOT / STATIC_DIR
STATIC_IMAGE_DIR = HTML_STATIC_DIR / "cthulhu-images"

# Template paths
TEMPLATES_DIR = WEB_ROOT / "templates"

# Log file paths
LOG_FILE_DIR = PROJECT_ROOT / LOGS_DIR
WEB_APP_LOG_PATH = LOG_FILE_DIR / "web_app_log.log"
WEB_ETL_LOG_PATH = LOG_FILE_DIR / "web_etl_log.log" 
DB_ETL_LOG_PATH = LOG_FILE_DIR / "db_etl_log.log"

# Database paths
DB_DATA_DIR = DB_ROOT / DATA_DIR
DB_LOGS_DIR = DB_ROOT / "logs"
DB_SECRETS_DIR = DB_ROOT / "secrets"

def ensure_directories():
    """Create all required directories if they don't exist."""
    directories = [
        CTHULHU_IMAGE_DIR,
        HTML_STATIC_DIR,
        STATIC_IMAGE_DIR,
        LOG_FILE_DIR,
        DB_DATA_DIR,
        DB_LOGS_DIR,
        DB_SECRETS_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(exist_ok=True, parents=True)

# Initialize directories on import
ensure_directories()