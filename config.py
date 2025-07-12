import os
import json
import threading


class Config:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._load_config()
            return cls._instance

    def _load_config(self):
        self.config_path = 'config.json'
        self.default_config = {
            'favorite_pairs': ["BTC/USDT", "ETH/USDT", "SOL/USDT"],
            'subscribers': [],
            'interval': '4h',
            'whale_threshold': 500000,
            'monitored_currencies': {},
            'alert_settings': {},
            'telegram_channels': ["cryptosignals", "whalepool", "altcoinbuzz"],
            'whale_rating': {},
            'lstm_models': {},
            'auto_improvement': True
        }

        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.data = json.load(f)
            else:
                self.data = self.default_config.copy()
                self.save()

            # Add missing keys
            for key, value in self.default_config.items():
                if key not in self.data:
                    self.data[key] = value
                    self.save()
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Config load error: {e}")
            self.data = self.default_config.copy()

    def save(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.data, f, indent=4)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        with self._lock:
            self.data[key] = value
            self.save()

    def get(self, key, default=None):
        return self.data.get(key, default)

    def update_monitored_currency(self, chat_id, currency, add=True):
        with self._lock:
            chat_id = str(chat_id)
            if chat_id not in self.data['monitored_currencies']:
                self.data['monitored_currencies'][chat_id] = []

            if add:
                if currency not in self.data['monitored_currencies'][chat_id]:
                    self.data['monitored_currencies'][chat_id].append(currency)
            else:
                if currency in self.data['monitored_currencies'][chat_id]:
                    self.data['monitored_currencies'][chat_id].remove(currency)

            self.save()

    def get_lstm_model_path(self, symbol):
        return self.data['lstm_models'].get(symbol)

    def set_lstm_model_path(self, symbol, path):
        with self._lock:
            self.data['lstm_models'][symbol] = path
            self.save()

    def toggle_auto_improvement(self, status):
        with self._lock:
            self.data['auto_improvement'] = status
            self.save()