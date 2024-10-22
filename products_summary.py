import os
import pandas as pd
from datetime import datetime, timedelta

def summarize_transactions_by_products(last_n_days, transactions_folder, product_reference_file, cache, cached_keys):
    """Summarize transactions by products over the last n days."""
    # Create a unique cache key for the request
    cache_key = f"products_summary_{last_n_days}"

    # Check if the summary is already cached
    if cache_key in cached_keys:
        cached_summary = cache.get(cache_key)
        if cached_summary is not None:
            return cached_summary  # Return cached data if available

    end_date = datetime.now()
    start_date = end_date - timedelta(days=last_n_days)

    transaction_data = pd.DataFrame()

    for file_name in os.listdir(transactions_folder):
        if file_name.endswith('.csv'):
            file_path = os.path.join(transactions_folder, file_name)
            temp_data = pd.read_csv(file_path)
            transaction_data = pd.concat([transaction_data, temp_data], ignore_index=True)

    transaction_data['transactionDatetime'] = pd.to_datetime(transaction_data['transactionDatetime'])

    filtered_data = transaction_data[(transaction_data['transactionDatetime'] >= start_date) & 
                                      (transaction_data['transactionDatetime'] <= end_date)]

    product_reference = pd.read_csv(product_reference_file)

    summary_data = filtered_data.merge(product_reference, on='productId', how='left')

    summary = summary_data.groupby('productName').agg(totalAmount=('transactionAmount', 'sum')).reset_index()

    # Cache the result
    cache.set(cache_key, summary.to_dict(orient='records'), timeout=600)  # Cache for 10 minutes
    cached_keys.append(cache_key)

    return summary.to_dict(orient='records')
