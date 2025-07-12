import click
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from analysis import perform_full_analysis
import logging
import os
import json
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
import re

# Настройка логирования
logger = logging.getLogger(__name__)


def setup_commands(app):
    """Регистрирует команды для Click"""

    # Команда analyze
    @app.command("analyze")
    @click.argument("symbol")
    @click.option("--days", default=30, help="Количество дней для прогноза")
    def analyze_command(symbol, days):
        """Выполняет полный анализ криптовалюты"""
        logger.info(f"Запуск анализа для {symbol} на {days} дней")
        try:
            result = perform_full_analysis(symbol, days)

            if result:
                print(f"Анализ завершен успешно!")
                print(f"RMSE: {result['rmse']:.2f}")
                print(f"Тональность новостей: {result['news_sentiment']:.2f}")
                print(f"График сохранен: {result['plot_path']}")
                print(f"Данные прогноза: {result['csv_path']}")
            else:
                print("Ошибка при выполнении анализа")
        except Exception as e:
            logger.exception(f"Ошибка в analyze_command: {e}")
            print(f"Ошибка при выполнении анализа: {e}")

    # Команда update-data
    @app.command("update-data")
    def update_data_command():
        """Обновляет исторические данные для всех криптовалют"""
        try:
            cryptos = ['BTC-USD', 'ETH-USD', 'XRP-USD', 'LTC-USD', 'BCH-USD']
            today = datetime.now().strftime('%Y-%m-%d')

            for crypto in cryptos:
                file_path = f"data/{crypto}.csv"
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    last_date = pd.to_datetime(df['Date'].iloc[-1]).strftime('%Y-%m-%d')

                    if last_date != today:
                        logger.info(f"Обновление данных для {crypto} с {last_date} по {today}")
                        new_data = fetch_historical_data(crypto, last_date, today)

                        if new_data is not None and not new_data.empty:
                            updated_df = pd.concat([df, new_data])
                            updated_df.to_csv(file_path, index=False)
                            logger.info(f"Данные для {crypto} успешно обновлены")
                else:
                    logger.info(f"Загрузка полных данных для {crypto}")
                    df = fetch_historical_data(crypto)

                    if df is not None and not df.empty:
                        os.makedirs('data', exist_ok=True)
                        df.to_csv(file_path, index=False)
                        logger.info(f"Данные для {crypto} сохранены")
        except Exception as e:
            logger.exception(f"Ошибка в update_data_command: {e}")
            print(f"Ошибка при обновлении данных: {e}")

    # Команда sentiment
    @app.command("sentiment")
    @click.argument("query")
    @click.option("--num", default=20, help="Количество статей для анализа")
    def sentiment_command(query, num):
        """Анализирует тональность новостей по запросу"""
        try:
            sentiment = fetch_news_sentiment(query, num)
            print(f"Средняя тональность новостей по запросу '{query}': {sentiment:.2f}")
        except Exception as e:
            logger.exception(f"Ошибка в sentiment_command: {e}")
            print(f"Ошибка при анализе тональности: {e}")

# Остальные функции остаются без изменений
# ...