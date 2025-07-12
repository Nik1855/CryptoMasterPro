import os
import time
import threading
import requests
from .database import get_unresolved_errors, mark_error_resolved, log_error
from .config import Config
from .auto_coder import AutoCoder

config = Config()


class SelfImprovementSystem:
    def __init__(self, bot):
        self.bot = bot
        self.running = False
        self.thread = None
        self.auto_coder = AutoCoder(bot)

    def start_self_check(self):
        if config['auto_improvement']:
            self.running = True
            self.thread = threading.Thread(target=self._self_check_loop, daemon=True)
            self.thread.start()
            log_error("SELF_IMPROVE", "System started")

    def _self_check_loop(self):
        while self.running:
            try:
                errors = get_unresolved_errors()
                if not errors.empty:
                    for _, error in errors.iterrows():
                        self.attempt_fix(error)
                time.sleep(3600)  # Check hourly
            except Exception as e:
                log_error("SELF_CHECK", f"Loop error: {e}")
                time.sleep(600)

    def attempt_fix(self, error):
        error_id = error['rowid']
        module = error['module']
        error_text = error['error_text']

        try:
            # Attempt automatic fix
            if self.auto_coder.attempt_auto_fix(module, error_text):
                mark_error_resolved(error_id)
                log_error("SELF_IMPROVE", f"Fixed error {error_id} in {module}")
                return True

            # If auto-fix fails, notify admin
            self.notify_admin(error_id, module, error_text)
            return False
        except Exception as e:
            log_error("AUTO_FIX", f"Error fixing {error_id}: {e}")
            return False

    def notify_admin(self, error_id, module, error_text):
        try:
            for admin_id in config['subscribers']:
                self.bot.send_message(
                    admin_id,
                    f"⚠️ **System Attention Needed**\n\n"
                    f"Module: `{module}`\n"
                    f"Error ID: {error_id}\n"
                    f"Error: `{error_text[:200]}`\n\n"
                    "Please review when possible",
                    parse_mode='Markdown'
                )
        except Exception as e:
            log_error("ADMIN_NOTIFY", f"Error: {e}")

    def add_new_feature(self, feature_description):
        if config['auto_improvement']:
            return self.auto_coder.create_feature(feature_description)
        return False

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()