import os

# General Config
DEBUG = os.environ.get('FLASK_DEBUG') or False
HOST = os.environ.get('FLASK_HOST') or '0.0.0.0'
PORT = os.environ.get('FLASK_PORT') or 8080

# Cache Config
CACHE_TYPE = 'SimpleCache'  # Use simple in-memory cache
CACHE_DEFAULT_TIMEOUT = 300  # Cache timeout in seconds (5 minutes)

# Paths
DATA_DIR = "transaction_data"  # Modify this path if your CSV files are located elsewhere
OUTPUT_DIR = "store"  # Modify this path if you want to store Parquet files elsewhere

# Set csv file loading to parquet mode: "delta" or "full"
TRANSACTION_MODE = "delta"

# Define transaction_data_path if needed
transaction_data_path = os.path.join(DATA_DIR)  # Set the path based on your configuration
