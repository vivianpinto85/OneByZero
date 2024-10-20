import csv
import random
import os
import requests
from datetime import datetime, timedelta

# Constants
TRANSACTION_DIR = r'C:\sources\OneByZero\transactions'
PRODUCT_IDS = [10, 20, 30]

# Function to generate random transactions
def generate_random_transactions(start_date, end_date, num_transactions):
    transactions = []
    for _ in range(num_transactions):
        transaction_id = len(transactions) + 1
        product_id = random.choice(PRODUCT_IDS)
        transaction_amount = random.uniform(100, 5000)  # Random amount
        transaction_datetime = start_date + timedelta(minutes=random.randint(0, 5))
        transactions.append((transaction_id, product_id, transaction_amount, transaction_datetime))
    return transactions

# Function to create a transaction file
def create_transaction_file(transactions):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(TRANSACTION_DIR, f'Transaction_{timestamp}.csv')
    
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['transactionId', 'productId', 'transactionAmount', 'transactionDatetime'])
        writer.writerows(transactions)
        
def clearCache():
    response = requests.get("http://localhost:8080/assignment/clear_cache")
    print("Cache cleared in app.py after generating transactions")
     # Check if the response was successful
    if response.status_code == 200:
        # Parse the JSON response to get the cleared items
        cleared_data = response.json()
        print("Cache cleared successfully. Cleared items:")
        for item in cleared_data.get("cleared_items", []):
            print(f"- {item}")
    else:
        print(f"Failed to clear cache. Status code: {response.status_code}")

    return 0

if __name__ == '__main__':
    start_date = datetime(2018, 1, 1, 10, 10)
    end_date = datetime(2018, 1, 1, 10, 20)
    transactions = generate_random_transactions(start_date, end_date, 100)
    create_transaction_file(transactions)
    clearCache()
    print(f"Generated {len(transactions)} transactions.")
