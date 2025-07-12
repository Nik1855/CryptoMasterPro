import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from datetime import datetime, timedelta
import logging
import os
import json
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
import re
import time

# Настройка логирования
logger = logging.getLogger(__name__)


def fetch_historical_data(symbol='BTC-USD', start_date='2015-01-01', end_date=None):
    """Загружает исторические данные о ценах криптовалюты с Yahoo Finance."""
    try:
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1={pd.Timestamp(start_date).timestamp():.0f}&period2={pd.Timestamp(end_date).timestamp():.0f}&interval=1d"
        logger.info(f"Загрузка данных для {symbol} с {start_date} по {end_date}")

        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        response.raise_for_status()
        data = response.json()

        if not data.get('chart') or not data['chart'].get('result'):
            logger.error("Некорректный ответ от API")
            return None

        result = data['chart']['result'][0]
        timestamps = result['timestamp']
        quotes = result['indicators']['quote'][0]
        closes = quotes['close']

        df = pd.DataFrame({
            'Date': pd.to_datetime(timestamps, unit='s'),
            'Close': closes
        })
        df.dropna(inplace=True)
        logger.info(f"Успешно загружено {len(df)} записей для {symbol}")
        return df
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных для {symbol}: {e}")
        return None


def fetch_news_sentiment(query='Bitcoin', num_articles=20):
    """Собирает новостные статьи и анализирует их тональность."""
    try:
        base_url = "https://news.google.com/search?q={}"
        url = base_url.format(query.replace(' ', '%20'))
        logger.info(f"Сбор новостей по запросу: {query}")

        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('article')[:num_articles]

        sentiments = []
        for i, article in enumerate(articles):
            title_elem = article.find('a', class_='DY5T1d')
            if not title_elem:
                continue

            title = title_elem.text
            clean_title = re.sub(r'[^\w\s]', '', title)

            # Анализ тональности
            analysis = TextBlob(clean_title)
            sentiment = analysis.sentiment.polarity
            sentiments.append(sentiment)

            if i < 5:  # Логируем только первые 5 заголовков
                logger.info(f"Заголовок {i + 1}: {title[:60]}... | Тональность: {sentiment:.2f}")

        avg_sentiment = np.mean(sentiments) if sentiments else 0
        logger.info(f"Проанализировано {len(sentiments)} статей, средняя тональность: {avg_sentiment:.2f}")
        return avg_sentiment
    except Exception as e:
        logger.error(f"Ошибка при сборе новостей: {e}")
        return 0


def prepare_data(data, look_back=60):
    """Подготавливает данные для LSTM модели."""
    try:
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(data['Close'].values.reshape(-1, 1))

        X, y = [], []
        for i in range(look_back, len(scaled_data)):
            X.append(scaled_data[i - look_back:i, 0])
            y.append(scaled_data[i, 0])

        X = np.array(X)
        y = np.array(y)
        X = np.reshape(X, (X.shape[0], X.shape[1], 1))

        logger.info(f"Данные подготовлены: X.shape={X.shape}, y.shape={y.shape}")
        return X, y, scaler
    except Exception as e:
        logger.error(f"Ошибка подготовки данных: {e}")
        raise


def build_lstm_model(input_shape):
    """Строит и компилирует LSTM модель."""
    try:
        model = Sequential()
        model.add(LSTM(50, return_sequences=True, input_shape=input_shape))
        model.add(LSTM(50, return_sequences=False))
        model.add(Dense(25))
        model.add(Dense(1))

        model.compile(optimizer='adam', loss='mean_squared_error')
        logger.info("LSTM модель успешно создана")
        return model
    except Exception as e:
        logger.error(f"Ошибка создания модели: {e}")
        raise


def perform_full_analysis(symbol='BTC-USD', days_to_predict=30):
    """Выполняет полный анализ: сбор данных, обучение модели и прогнозирование."""
    start_time = time.time()
    logger.info(f"Начало анализа для {symbol}")

    try:
        # Загрузка исторических данных
        df = fetch_historical_data(symbol)
        if df is None or df.empty:
            logger.error(f"Не удалось загрузить данные для {symbol}")
            return None

        # Сбор новостных данных
        news_sentiment = fetch_news_sentiment()
        logger.info(f"Средняя тональность новостей: {news_sentiment:.2f}")

        # Подготовка данных
        look_back = 60
        X, y, scaler = prepare_data(df, look_back)

        # Разделение на обучающую и тестовую выборки
        train_size = int(len(X) * 0.8)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]

        # Построение и обучение модели
        model = build_lstm_model((X_train.shape[1], 1))
        logger.info("Обучение модели...")
        model.fit(X_train, y_train, batch_size=32, epochs=10, validation_split=0.1, verbose=0)
        logger.info("Обучение модели завершено")

        # Оценка модели
        test_predictions = model.predict(X_test)
        test_predictions = scaler.inverse_transform(test_predictions)
        y_test_actual = scaler.inverse_transform(y_test.reshape(-1, 1))

        rmse = np.sqrt(mean_squared_error(y_test_actual, test_predictions))
        logger.info(f"RMSE на тестовых данных: {rmse:.2f}")

        # Прогнозирование будущих цен
        last_sequence = X_test[-1]
        future_predictions = []

        logger.info("Прогнозирование будущих цен...")
        for _ in range(days_to_predict):
            next_pred = model.predict(last_sequence.reshape(1, look_back, 1), verbose=0)
            future_predictions.append(next_pred[0, 0])
            last_sequence = np.append(last_sequence[1:], next_pred[0, 0])

        # Применяем коррекцию на основе новостной тональности
        sentiment_factor = 1 + (news_sentiment * 0.05)
        future_predictions = [p * sentiment_factor for p in future_predictions]

        future_predictions = scaler.inverse_transform(
            np.array(future_predictions).reshape(-1, 1)
        )

        # Генерация дат для прогноза
        last_date = df['Date'].iloc[-1]
        future_dates = [last_date + timedelta(days=i) for i in range(1, days_to_predict + 1)]

        # Визуализация результатов
        plt.figure(figsize=(14, 6))
        plt.plot(df['Date'], df['Close'], label='Исторические данные')
        plt.plot(future_dates, future_predictions, 'ro-', label='Прогноз')
        plt.title(f'Прогноз цен на {symbol}')
        plt.xlabel('Дата')
        plt.ylabel('Цена (USD)')
        plt.legend()
        plt.grid(True)

        # Сохранение результатов
        os.makedirs('results', exist_ok=True)
        plot_path = os.path.join('results', f'{symbol}_forecast_{datetime.now().strftime("%Y%m%d%H%M")}.png')
        plt.savefig(plot_path)
        plt.close()

        # Сохранение данных прогноза
        forecast_df = pd.DataFrame({
            'Date': future_dates,
            'Forecast': future_predictions.flatten()
        })
        csv_path = os.path.join('results', f'{symbol}_forecast_{datetime.now().strftime("%Y%m%d%H%M")}.csv')
        forecast_df.to_csv(csv_path, index=False)

        duration = time.time() - start_time
        logger.info(f"Анализ завершен за {duration:.2f} сек. Результаты сохранены в {plot_path} и {csv_path}")

        return {
            'symbol': symbol,
            'historical_data': df,
            'forecast_dates': future_dates,
            'forecast_prices': future_predictions.flatten().tolist(),
            'rmse': rmse,
            'news_sentiment': news_sentiment,
            'plot_path': plot_path,
            'csv_path': csv_path,
            'processing_time': duration
        }
    except Exception as e:
        logger.exception(f"Ошибка в perform_full_analysis: {e}")
        return None