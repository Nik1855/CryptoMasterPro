import re
import time
import hashlib


class DataCache:
    def __init__(self, ttl=300):
        self.cache = {}
        self.ttl = ttl

    def get(self, key):
        item = self.cache.get(key)
        if item and (time.time() - item['timestamp']) < self.ttl:
            return item['data']
        return None

    def set(self, key, data):
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }


def is_valid_currency(currency):
    return re.match(r'^[A-Z]{2,6}(/USDT)?$', currency) is not None


def log_error(module, message):
    print(f"[{module} ERROR] {message}")
    # Actual implementation would save to DB


def generate_file_hash(file_path):
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return None