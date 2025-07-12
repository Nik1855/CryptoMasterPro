import logging
import traceback
from .database import log_error


class ErrorHandler:
    def __init__(self, bot):
        self.bot = bot

    def handle_error(self, module, exception):
        error_trace = traceback.format_exc()
        error_msg = f"{type(exception).__name__}: {str(exception)}"
        log_error(module, f"{error_msg}\n{error_trace}")

        # Notify admin if critical
        if isinstance(exception, (MemoryError, SystemError)):
            self.notify_admin(module, error_msg)

    def handle_critical_error(self, exception):
        error_trace = traceback.format_exc()
        module = "CRITICAL"
        error_msg = f"{type(exception).__name__}: {str(exception)}"
        log_error(module, f"{error_msg}\n{error_trace}")
        self.notify_admin(module, error_msg)

    def notify_admin(self, module, error_msg):
        try:
            for admin_id in self.bot.config['subscribers']:
                self.bot.send_message(
                    admin_id,
                    f"🚨 **Critical System Error**\n\n"
                    f"Module: `{module}`\n"
                    f"Error: `{error_msg[:300]}`",
                    parse_mode='Markdown'
                )
        except Exception as e:
            logging.error(f"Admin notify failed: {e}")