# config.py

import os

class Config:
    # General Config
    DEBUG = os.environ.get('FLASK_DEBUG') or False
    HOST = os.environ.get('FLASK_HOST') or '0.0.0.0'
    PORT = os.environ.get('FLASK_PORT') or 8080

    # Cache Config
    CACHE_TYPE = 'SimpleCache'  # Use simple in-memory cache
    CACHE_DEFAULT_TIMEOUT = 300  # Cache timeout in seconds (5 minutes)

    # Paths
    TRANSACTION_DIR = os.path.join(os.getcwd(), 'transactions')
    PRODUCT_REF_FILE = os.path.join(os.getcwd(), 'reference_data', 'ProductReference.csv')
