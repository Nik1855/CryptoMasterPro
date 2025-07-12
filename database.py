import sqlite3
import threading
import pandas as pd
from datetime import datetime, timedelta

db_lock = threading.Lock()


def init_db():
    with db_lock:
        conn = sqlite3.connect('crypto_data.db', check_same_thread=False)
        c = conn.cursor()

        # Historical price data
        c.execute('''CREATE TABLE IF NOT EXISTS historical_data
        (
            symbol
            TEXT,
            timestamp
            INTEGER,
            open
            REAL,
            high
            REAL,
            low
            REAL,
            close
            REAL,
            volume
            REAL,
            PRIMARY
            KEY
                     (
            symbol,
            timestamp
                     ))''')

        # Whale transactions
        c.execute('''CREATE TABLE IF NOT EXISTS whale_transactions
                     (
                         currency
                         TEXT,
                         amount
                         REAL,
                         amount_usd
                         REAL,
                         from_address
                         TEXT,
                         to_address
                         TEXT,
                         direction
                         TEXT,
                         chain
                         TEXT,
                         tx_hash
                         TEXT
                         PRIMARY
                         KEY,
                         timestamp
                         INTEGER,
                         whale_rating
                         REAL
                     )''')

        # User alerts
        c.execute('''CREATE TABLE IF NOT EXISTS user_alerts
        (
            user_id
            INTEGER,
            currency
            TEXT,
            condition_type
            TEXT,
            threshold
            REAL,
            is_active
            INTEGER,
            PRIMARY
            KEY
                     (
            user_id,
            currency,
            condition_type
                     ))''')

        # Error logs
        c.execute('''CREATE TABLE IF NOT EXISTS error_logs
                     (
                         timestamp
                         INTEGER,
                         module
                         TEXT,
                         error_text
                         TEXT,
                         resolved
                         INTEGER
                         DEFAULT
                         0
                     )''')

        # Indexes
        c.execute('''CREATE INDEX IF NOT EXISTS idx_symbol_time
            ON historical_data (symbol, timestamp)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_user_currency
            ON user_alerts (user_id, currency)''')

        conn.commit()
        return conn


def fetch_historical_data(symbol, days=30):
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    start_timestamp = int(start_date.timestamp() * 1000)
    end_timestamp = int(end_date.timestamp() * 1000)

    with db_lock:
        conn = sqlite3.connect('crypto_data.db', check_same_thread=False)
        query = f"""
            SELECT timestamp, open, high, low, close, volume
            FROM historical_data
            WHERE symbol = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC
        """
        df = pd.read_sql_query(query, conn, params=(symbol, start_timestamp, end_timestamp))
        return df


def save_historical_data(symbol, data):
    with db_lock:
        conn = sqlite3.connect('crypto_data.db', check_same_thread=False)
        cursor = conn.cursor()
        for row in data:
            timestamp = row[0]
            open_price = row[1]
            high = row[2]
            low = row[3]
            close = row[4]
            volume = row[5]
            cursor.execute('''
                INSERT OR REPLACE INTO historical_data
                (symbol, timestamp, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, timestamp, open_price, high, low, close, volume))
        conn.commit()


def add_user_alert(user_id, currency, condition_type, threshold):
    try:
        with db_lock:
            conn = sqlite3.connect('crypto_data.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_alerts
                (user_id, currency, condition_type, threshold, is_active)
                VALUES (?, ?, ?, ?, 1)
            ''', (user_id, currency, condition_type, threshold))
            conn.commit()
            return True
    except Exception as e:
        print(f"Alert creation error: {e}")
        return False


def get_active_alerts():
    with db_lock:
        conn = sqlite3.connect('crypto_data.db', check_same_thread=False)
        query = "SELECT * FROM user_alerts WHERE is_active = 1"
        return pd.read_sql_query(query, conn)


def save_whale_transaction(transaction):
    with db_lock:
        conn = sqlite3.connect('crypto_data.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
                       INSERT
                       OR IGNORE INTO whale_transactions
            (currency, amount, amount_usd, from_address, to_address,
            direction, chain, tx_hash, timestamp, whale_rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ''', transaction)
        conn.commit()


def log_error(module, error_text):
    with db_lock:
        conn = sqlite3.connect('crypto_data.db', check_same_thread=False)
        cursor = conn.cursor()
        timestamp = int(datetime.utcnow().timestamp())
        cursor.execute('''
                       INSERT INTO error_logs (timestamp, module, error_text)
                       VALUES (?, ?, ?)
                       ''', (timestamp, module, str(error_text)))
        conn.commit()


def get_unresolved_errors():
    with db_lock:
        conn = sqlite3.connect('crypto_data.db', check_same_thread=False)
        query = "SELECT * FROM error_logs WHERE resolved = 0"
        return pd.read_sql_query(query, conn)


def mark_error_resolved(error_id):
    with db_lock:
        conn = sqlite3.connect('crypto_data.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
                       UPDATE error_logs
                       SET resolved = 1
                       WHERE rowid = ?
                       ''', (error_id,))
        conn.commit()


# Initialize database on import
DB_CONN = init_db()