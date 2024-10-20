from flask import Flask, jsonify
import os
import csv
from threading import Thread
from products_summary import summarize_transactions_by_products
from city_summary import city_summary_bp
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(city_summary_bp)

# Initialize Flask-Limiter
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])
cache = Cache(app)
cached_keys = []

# Load product reference data into memory
product_reference = {}
with open(app.config['PRODUCT_REF_FILE'], mode='r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        product_reference[row['productId']] = {
            'productName': row['productName'],
            'productManufacturingCity': row['productManufacturingCity']
        }

# Transactions data in memory
transactions = {}
loading_transactions = False

def load_transactions_in_background():
    """Load transactions from the folder in a background thread."""
    global transactions, loading_transactions
    loading_transactions = True
    for filename in os.listdir(app.config['TRANSACTION_DIR']):
        if filename.endswith('.csv'):
            file_path = os.path.join(app.config['TRANSACTION_DIR'], filename)
            with open(file_path, mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    transaction_id = int(row['transactionId'])
                    transactions[transaction_id] = {
                        'productId': row['productId'],
                        'transactionAmount': float(row['transactionAmount']),
                        'transactionDatetime': row['transactionDatetime']
                    }
    loading_transactions = False

def start_background_transaction_loading():
    """Start loading transactions in the background."""
    thread = Thread(target=load_transactions_in_background)
    thread.start()

@app.route('/assignment/transaction/<int:transaction_id>', methods=['GET'])
@cache.cached(timeout=300)
@limiter.limit("10 per minute")
def get_transaction(transaction_id):
    """Get transaction details by transaction ID."""
    global cached_keys
    if loading_transactions:
        return jsonify({"message": "Data is still loading. Please try again later."}), 202

    cache_key = f"transaction_{transaction_id}"
    if cache_key not in cached_keys:
        cached_keys.append(cache_key)

    transaction = transactions.get(transaction_id)
    if transaction:
        product_info = product_reference.get(transaction['productId'], {})
        return jsonify({
            "transactionId": transaction_id,
            "productName": product_info.get('productName', 'Unknown'),
            "transactionAmount": transaction['transactionAmount'],
            "transactionDatetime": transaction['transactionDatetime']
        })
    return jsonify({"error": "Transaction not found"}), 404

@app.route('/assignment/transactionSummaryByProducts/<int:last_n_days>', methods=['GET'])
@cache.cached(timeout=600)
@limiter.limit("10 per minute")
def get_transaction_summary_by_products(last_n_days):
    """Get transaction summary by products over the last n days."""
    if loading_transactions:
        return jsonify({"message": "Data is still loading. Please try again later."}), 202

    summary = summarize_transactions_by_products(last_n_days, app.config['TRANSACTION_DIR'], app.config['PRODUCT_REF_FILE'])
    return jsonify({"summary": summary})

@app.route('/assignment/clear_cache', methods=['GET'])
def clear_cache():
    """Clear the cached memory to load fresh data."""
    global cached_keys
    cleared_items = cached_keys.copy()
    cache.clear()
    cached_keys = []
    return jsonify({"cleared_items": cleared_items, "message": "Cache cleared"}), 200

if __name__ == '__main__':
    start_background_transaction_loading()
    app.run(debug=app.config['DEBUG'], host=app.config['HOST'], port=app.config['PORT'])
