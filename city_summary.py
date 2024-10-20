from flask import Blueprint, jsonify
import os
from datetime import datetime, timedelta
import pandas as pd
from config import Config

# Create a Flask blueprint for city summary
city_summary_bp = Blueprint('city_summary', __name__)

def load_product_references():
    """Load product reference data from CSV file."""
    df = pd.read_csv(Config.PRODUCT_REF_FILE)
    return {row['productId']: row for _, row in df.iterrows()}

def load_transactions(last_n_days):
    """Load transactions from the last n days."""
    transactions = []
    cutoff_date = datetime.now() - timedelta(days=last_n_days)
    
    for file in os.listdir(Config.TRANSACTION_DIR):
        if file.endswith(".csv"):
            file_path = os.path.join(Config.TRANSACTION_DIR, file)
            df = pd.read_csv(file_path)
            for _, row in df.iterrows():
                transaction_date = datetime.strptime(row['transactionDatetime'], '%Y-%m-%d %H:%M:%S')
                if transaction_date >= cutoff_date:
                    transactions.append(row)
    return transactions

def summarize_transactions_by_city(last_n_days):
    """Summarize transactions by manufacturing city."""
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

    return [{'cityName': city, 'totalAmount': total} for city, total in city_summary.items()]

@city_summary_bp.route('/assignment/transactionSummaryByManufacturingCity/<int:last_n_days>', methods=['GET'])
def get_transaction_summary_by_city(last_n_days):
    """API endpoint to get transaction summary by manufacturing city."""
    summary = summarize_transactions_by_city(last_n_days)
    return jsonify({"summary": summary})
