import csv
import random
import os
import requests
from datetime import datetime, timedelta

# Constants
TRANSACTION_DIR = r'C:\sources\OneByZero\transactions'
PRODUCT_REF_FILE = r'C:\sources\OneByZero\reference_data\ProductReference.csv'
FILES_PER_DAY = 5
RECORDS_PER_FILE = 5
DAYS_TO_GENERATE = 5

# Function to load product IDs from the reference file
def load_product_ids():
    product_ids = []
    with open(PRODUCT_REF_FILE, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            product_ids.append(row['productId'])
    return product_ids

# Function to generate random transactions
def generate_random_transactions(start_datetime, num_transactions, product_ids, start_transaction_id):
    transactions = []
    for i in range(num_transactions):
        transaction_id = start_transaction_id + i
        product_id = random.choice(product_ids)
        transaction_amount = round(random.uniform(100, 5000), 2)  # Random amount
        transaction_datetime = start_datetime + timedelta(minutes=i * 5)
        transactions.append((transaction_id, product_id, transaction_amount, transaction_datetime.strftime('%Y-%m-%d %H:%M:%S')))
    return transactions

# Function to create a transaction file
def create_transaction_file(transactions, date):
    timestamp = date.strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(TRANSACTION_DIR, f'Transaction_{timestamp}.csv')

    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['transactionId', 'productId', 'transactionAmount', 'transactionDatetime'])
        writer.writerows(transactions)

# Function to clear cache via API call
def clear_cache():
    response = requests.get("http://localhost:8080/assignment/clear_cache")
    print("Cache cleared in app.py after generating transactions")
    if response.status_code == 200:
        cleared_data = response.json()
        print("Cache cleared successfully. Cleared items:")
        for item in cleared_data.get("cleared_items", []):
            print(f"- {item}")
    else:
        print(f"Failed to clear cache. Status code: {response.status_code}")

if __name__ == '__main__':
    # Load product IDs
    product_ids = load_product_ids()

    # Start with an initial transaction ID
    transaction_id = 1

    # Generate transactions for the past 5 days
    for day_offset in range(DAYS_TO_GENERATE):
        current_date = datetime.now() - timedelta(days=day_offset)
        start_time = current_date.replace(hour=15, minute=0, second=0)

        for file_num in range(FILES_PER_DAY):
            file_time = start_time + timedelta(minutes=file_num * 5)
            transactions = generate_random_transactions(file_time, RECORDS_PER_FILE, product_ids, transaction_id)
            create_transaction_file(transactions, file_time)
            transaction_id += RECORDS_PER_FILE

    clear_cache()
    print(f"Generated {FILES_PER_DAY * DAYS_TO_GENERATE} files with {RECORDS_PER_FILE} transactions each.")
