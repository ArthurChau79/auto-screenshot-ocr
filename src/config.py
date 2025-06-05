import os
from typing import Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Debug: Print current working directory and check if .env exists
current_dir = os.getcwd()
env_path = os.path.join(current_dir, '.env')

# API Configuration
API_KEY = os.getenv('API_KEY')
print(f"API_KEY found: {'Yes' if API_KEY else 'No'}")

if not API_KEY:
    raise ValueError("API_KEY environment variable is not set")

# Screenshot Directory Configuration
WATCH_DIR = os.getenv('WATCH_DIR')
if not WATCH_DIR:
    raise ValueError("WATCH_DIR environment variable is not set")
print(f"WATCH_DIR found: {WATCH_DIR}")

# Image Processing Configuration
MAX_IMAGE_SIZE = 1024  # Maximum dimension for image compression
IMAGE_QUALITY = 85  # JPEG quality for compressed images

# UI Configuration
DEFAULT_WINDOW_SIZE = (800, 600)

# OCR Configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
TIMEOUT = 30  # seconds for API requests

def load_config() -> Dict:
    """Load configuration from environment variables and return as a dictionary."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv('API_KEY')
    if not api_key:
        raise ValueError("API_KEY not found in environment variables")
    
    # Get watch directory from environment
    watch_dir = os.getenv('WATCH_DIR')
    if not watch_dir:
        raise ValueError("WATCH_DIR not found in environment variables")
    
    # Web presets configuration
    web_presets = {
        "Google": "https://www.google.com/search?q=",
        "Wikipedia": "https://en.wikipedia.org/wiki/Special:Search?search=",
        "Google Translate": "https://translate.google.com/?text="
    }
    
    return {
        'api_key': api_key,
        'watch_dir': watch_dir,
        'web_presets': web_presets
    } 