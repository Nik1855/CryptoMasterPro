import os
import sys
import logging

# Настройка базового пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Основная функция запуска приложения"""
    try:
        logger.info("Запуск CryptoMasterPro")

        # Импортируем и запускаем основной модуль
        from main import main as app_main
        app_main()

    except Exception as e:
        logger.exception(f"Необработанная ошибка: {e}")
        print(f"Произошла критическая ошибка: {e}")
        sys.exit(1)
    finally:
        logger.info("Завершение работы CryptoMasterPro")


if __name__ == "__main__":
    main()