import pandas as pd
import os
import threading
from datetime import datetime
import config  # Import the config file

TRANSACTION_DIR = r'C:\sources\OneByZero\transaction_data'
PROCESSED_LOG_FILE = 'last_processed_file.txt'  # To track the last processed file
lock = threading.Lock()
processing = False  # To ensure only one thread runs at a time
TRANSACTION_MODE = config.TRANSACTION_MODE

# Load the last processed file from the log
def get_last_processed_file():
    try:
        with open(PROCESSED_LOG_FILE, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return None

# Update the last processed file in the log
def update_last_processed_file(file_name):
    with open(PROCESSED_LOG_FILE, 'w') as file:
        file.write(file_name)

# Helper function to load new delta files based on the timestamp in the file name
def load_transactions():
    if TRANSACTION_MODE == "full":
        # Full load: process all transaction files
        all_files = [os.path.join(TRANSACTION_DIR, f) for f in os.listdir(TRANSACTION_DIR) if f.endswith('.csv')]
    else:
        # Delta load: process only files newer than the last processed file
        last_processed_file = get_last_processed_file()
        all_files = []
        for file_name in os.listdir(TRANSACTION_DIR):
            if file_name.endswith('.csv'):
                if last_processed_file is None or file_name > last_processed_file:
                    all_files.append(os.path.join(TRANSACTION_DIR, file_name))

    all_transactions = []
    for file_path in sorted(all_files):
        df = pd.read_csv(file_path)
        df['transactionDatetime'] = pd.to_datetime(df['transactionDatetime'])
        all_transactions.append(df)
        update_last_processed_file(os.path.basename(file_path))  # Update the last processed file

    if not all_transactions:
        return None  # No new files

    return pd.concat(all_transactions, ignore_index=True)

# Processing logic for the transactions
def process_transactions(transactions):
    if transactions is not None:
        transactions.to_parquet('store/transactions.parquet', index=False)
        print("First 10 rows of processed transactions:")
        print(transactions.head(10))
    else:
        print("No new transactions to process.")

# Threaded function to ensure only one execution at a time
def load_and_process_transactions():
    global processing

    # Prevent running if already in progress
    if processing:
        print("Transaction processing is already running. Skipping new request.")
        return

    with lock:
        processing = True
        try:
            transactions = load_transactions()
            process_transactions(transactions)
        finally:
            processing = False  # Reset after processing is complete

# Example to trigger the function in a thread
def trigger_transaction_processing():
    threading.Thread(target=load_and_process_transactions, daemon=True).start()
