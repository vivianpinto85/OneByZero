from flask import Flask, jsonify
import pandas as pd
import os
from datetime import datetime, timedelta
import time
import threading
from file_loader import trigger_transaction_processing
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# Initialize the Limiter
limiter = Limiter(
    get_remote_address,  # Use the client's IP address to rate limit
    app=app,
    default_limits=["200 per day", "50 per hour"]  # Default limits for all endpoints
)

def periodic_file_check():
    while True:
        print("Checking for new data in transaction_data folder...")
        trigger_transaction_processing() 
        time.sleep(300)

@app.route('/assignment/transaction/<int:transaction_id>', methods=['GET'])
@limiter.limit("10 per minute")  # Rate limit this endpoint to 10 requests per minute
def get_transaction(transaction_id):
    parquet_path = os.path.join("store", "transactions.parquet")

    try:
        df = pd.read_parquet(parquet_path, engine='pyarrow')
        transaction = df.set_index('transactionId').loc[transaction_id]
        return jsonify(transaction.to_dict())
    except FileNotFoundError:
        return jsonify({"error": "Parquet file not found"}), 404
    except KeyError:
        return jsonify({"error": "Transaction not found"}), 404

TRANSACTIONS_PARQUET_PATH = os.path.join("store", "transactions.parquet")
PRODUCTS_PARQUET_PATH = os.path.join("store", "product_reference.parquet")

@app.route('/assignment/transactionSummaryByProducts/<int:last_n_days>', methods=['GET'])
@limiter.limit("5 per minute")  # Rate limit this endpoint to 5 requests per minute
def transaction_summary(last_n_days):
    try:
        transactions_df = pd.read_parquet(TRANSACTIONS_PARQUET_PATH, engine='pyarrow')
        cutoff_date = datetime.now() - timedelta(days=last_n_days)
        transactions_df['transactionDatetime'] = pd.to_datetime(transactions_df['transactionDatetime'])
        recent_transactions = transactions_df[transactions_df['transactionDatetime'] >= cutoff_date]

        summary = recent_transactions.groupby('productId').agg(
            total_amount=('transactionAmount', 'sum'),
            transaction_count=('transactionId', 'count')
        ).reset_index()

        return jsonify(summary.to_dict(orient='records'))

    except FileNotFoundError as e:
        return jsonify({"error": f"File not found: {e}"}), 404
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

@app.route('/assignment/transactionSummaryByManufacturingCity/<int:last_n_days>', methods=['GET'])
@limiter.limit("5 per minute")  # Rate limit this endpoint to 5 requests per minute
def transaction_summary_by_manufacturing_city(last_n_days):
    try:
        transactions_df = pd.read_parquet(TRANSACTIONS_PARQUET_PATH, engine='pyarrow')
        products_df = pd.read_parquet(PRODUCTS_PARQUET_PATH, engine='pyarrow')
        merged_df = transactions_df.merge(products_df, on='productId', how='left')

        end_date = datetime.now()
        start_date = end_date - timedelta(days=last_n_days)

        filtered_df = merged_df[
            (merged_df['transactionDatetime'] >= start_date) &
            (merged_df['transactionDatetime'] <= end_date)
        ]

        summary = filtered_df.groupby('productManufacturingCity').agg(
            totalAmount=('transactionAmount', 'sum')
        ).reset_index()

        output = {"summary": summary.to_dict(orient='records')}
        return jsonify(output)

    except FileNotFoundError as e:
        return jsonify({"error": f"File not found: {e}"}), 404
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

file_check_thread = threading.Thread(target=periodic_file_check)
file_check_thread.daemon = True  # Ensure the thread exits when the main program exits
file_check_thread.start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', threaded=True, port=8080)
