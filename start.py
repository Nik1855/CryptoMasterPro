# start.py
import os
import sys
import logging
from main import main

if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    try:
        logger.info("Запуск CryptoMasterPro")
        main()
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
        print(f"Произошла критическая ошибка: {e}")
        sys.exit(1)
    finally:
        logger.info("Завершение работы CryptoMasterPro")