import click
import logging
from commands import setup_commands

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@click.group()
def cli():
    """CryptoMasterPro - Комплексный инструмент для анализа и прогнозирования криптовалют"""
    pass

# Регистрируем команды сразу при импорте
setup_commands(cli)

def main():
    """Основная функция для запуска приложения"""
    try:
        logger.info("Запуск приложения CryptoMasterPro")
        cli()
    except Exception as e:
        logger.exception(f"Ошибка в main: {e}")
        print(f"Произошла ошибка: {e}")

if __name__ == '__main__':
    main()