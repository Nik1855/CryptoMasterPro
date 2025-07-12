import time
import threading
import pandas as pd
from datetime import datetime
from .config import Config
from .database import get_active_alerts, save_whale_transaction
from .api import get_crypto_price, get_whale_transactions
from .analysis import perform_full_analysis
from .utils import log_error


class MonitoringService:
    def __init__(self, bot):
        self.bot = bot
        self.running = False
        self.thread = None
        self.config = Config()

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()
        log_error("MONITORING", "Service started")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        log_error("MONITORING", "Service stopped")

    def _monitor(self):
        while self.running:
            try:
                # 1. Check alerts
                self._check_alerts()

                # 2. Check whale activity
                self._detect_whale_activity()

                # 3. Hourly analysis
                if datetime.now().minute == 0:
                    self._hourly_analysis()

                time.sleep(60)
            except Exception as e:
                log_error("MONITORING", f"Error: {e}")
                time.sleep(120)

    def _check_alerts(self):
        alerts = get_active_alerts()
        if alerts.empty:
            return

        for _, alert in alerts.iterrows():
            try:
                price_data = get_crypto_price(alert['currency'])
                if not price_data:
                    continue

                # Check conditions and send alerts
                # (Implementation based on alert type)
            except Exception as e:
                log_error("ALERT_CHECK", f"Error: {e}")

    def _detect_whale_activity(self):
        monitored = self.config.get('monitored_currencies', {})
        for currencies in monitored.values():
            for currency in currencies:
                try:
                    transactions = get_whale_transactions(currency)
                    for tx in transactions:
                        if float(tx['value']) > self.config['whale_threshold']:
                            self._notify_whale_transaction(tx)
                            save_whale_transaction((
                                currency, float(tx['value']), float(tx['valueUSD']),
                                tx['from'], tx['to'], tx.get('direction', 'UNKNOWN'),
                                tx.get('chain', 'UNKNOWN'), tx['hash'],
                                int(tx['timeStamp']), 0.0
                            ))
                except Exception as e:
                    log_error("WHALE_DETECT", f"Currency {currency} error: {e}")

    def _notify_whale_transaction(self, tx):
        message = (
            f"🐳 **WHALE ALERT!**\n\n"
            f"**Currency:** {tx['tokenSymbol']}\n"
            f"**Amount:** ${float(tx['valueUSD']):,.2f}\n"
            f"**From:** {tx['from'][:10]}...\n"
            f"**To:** {tx['to'][:10]}...\n"
            f"**Chain:** {tx.get('chain', 'UNKNOWN')}"
        )

        subscribers = self.config['subscribers']
        for user_id in subscribers:
            try:
                self.bot.send_message(user_id, message, parse_mode='Markdown')
            except Exception as e:
                log_error("WHALE_NOTIFY", f"Error: {e}")

    def _hourly_analysis(self):
        monitored = self.config.get('monitored_currencies', {})
        for chat_id_str, currencies in monitored.items():
            chat_id = int(chat_id_str)
            for currency in currencies:
                try:
                    chart_path, report = perform_full_analysis(currency)
                    if chart_path and report:
                        with open(chart_path, 'rb') as chart_file:
                            self.bot.send_photo(
                                chat_id,
                                chart_file,
                                caption=report[:1000],
                                parse_mode='Markdown'
                            )
                        if len(report) > 1000:
                            self.bot.send_message(chat_id, report[1000:], parse_mode='Markdown')
                except Exception as e:
                    log_error("HOURLY_ANALYSIS", f"Currency {currency} error: {e}")