from flask import Blueprint, jsonify, current_app
import os
from datetime import datetime, timedelta
import pandas as pd

# Create a Flask blueprint for city summary
city_summary_bp = Blueprint('city_summary', __name__)

def load_product_references():
    """Load product reference data from CSV file."""
    df = pd.read_csv(current_app.config['PRODUCT_REF_FILE'])
    return {row['productId']: row for _, row in df.iterrows()}

def load_transactions(last_n_days):
    """Load transactions from the last n days."""
    transactions = []
    cutoff_date = datetime.now() - timedelta(days=last_n_days)
    
    for file in os.listdir(current_app.config['TRANSACTION_DIR']):
        if file.endswith(".csv"):
            file_path = os.path.join(current_app.config['TRANSACTION_DIR'], file)
            df = pd.read_csv(file_path)
            for _, row in df.iterrows():
                transaction_date = datetime.strptime(row['transactionDatetime'], '%Y-%m-%d %H:%M:%S')
                if transaction_date >= cutoff_date:
                    transactions.append(row)
    return transactions

def summarize_transactions_by_city(last_n_days, cache, cached_keys):
    """Summarize transactions by manufacturing city."""
    # Create a unique cache key for this request
    cache_key = f"city_summary_{last_n_days}"

    # Check if the result is already cached
    cached_summary = cache.get(cache_key)
    if cached_summary is not None:
        return cached_summary  # Return cached data if available

    transactions = load_transactions(last_n_days)
    product_references = load_product_references()
    city_summary = {}

    for transaction in transactions:
        product_id = transaction['productId']
        amount = transaction['transactionAmount']
        
        product_ref = product_references.get(product_id, {})
        city_name = product_ref.get('productManufacturingCity', 'Unknown')
        
        if city_name not in city_summary:
            city_summary[city_name] = 0
        city_summary[city_name] += amount

    result = [{'cityName': city, 'totalAmount': total} for city, total in city_summary.items()]

    # Cache the result
    cache.set(cache_key, result, timeout=600)  # Cache for 10 minutes
    cached_keys.append(cache_key)  # Track the cached key

    return result

@city_summary_bp.route('/assignment/transactionSummaryByManufacturingCity/<int:last_n_days>', methods=['GET'])
def get_transaction_summary_by_city(last_n_days):
    """API endpoint to get transaction summary by manufacturing city."""
    # Access cache and cached_keys from current_app context
    cache = current_app.extensions['cache']
    cached_keys = current_app.config.get('cached_keys', [])
    
    summary = summarize_transactions_by_city(last_n_days, cache, cached_keys)
    return jsonify({"summary": summary})
