import os
import requests
import ccxt
import pandas as pd
from datetime import datetime, timedelta
from .database import save_historical_data, log_error
from .utils import DataCache

# Cache setup
price_cache = DataCache(ttl=60)
chain_cache = DataCache(ttl=3600)

# Blockchain explorers
BLOCKCHAIN_APIS = {
    "ETH": {
        "name": "Ethereum",
        "api_url": "https://api.etherscan.io/api",
        "api_key": os.getenv("ETHERSCAN_API_KEY")
    },
    "BSC": {
        "name": "Binance Smart Chain",
        "api_url": "https://api.bscscan.com/api",
        "api_key": os.getenv("BSCSCAN_API_KEY")
    },
    "MATIC": {
        "name": "Polygon",
        "api_url": "https://api.polygonscan.com/api",
        "api_key": os.getenv("POLYGONSCAN_API_KEY")
    },
    "ARB": {
        "name": "Arbitrum",
        "api_url": "https://api.arbiscan.io/api",
        "api_key": os.getenv("ARBISCAN_API_KEY")
    },
    "OP": {
        "name": "Optimism",
        "api_url": "https://api-optimistic.etherscan.io/api",
        "api_key": os.getenv("OPTIMISMSCAN_API_KEY")
    },
    "AVAX": {
        "name": "Avalanche",
        "api_url": "https://api.snowtrace.io/api",
        "api_key": os.getenv("SNOWSCAN_API_KEY")
    }
}


def safe_api_request(url, params=None, headers=None, timeout=10):
    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log_error("API", f"Request error: {e}")
        return None


def get_crypto_price(symbol):
    cached = price_cache.get(symbol)
    if cached:
        return cached

    try:
        exchange = ccxt.binance()
        ticker = exchange.fetch_ticker(symbol)
        price_data = {
            'price': ticker['last'],
            'high': ticker['high'],
            'low': ticker['low'],
            'change': ticker['percentage'],
            'volume': ticker['quoteVolume'],
            'symbol': symbol
        }
        price_cache.set(symbol, price_data)
        return price_data
    except Exception as e:
        log_error("PRICE", f"Error: {e}")
        return None


def fetch_historical_data_from_exchange(symbol, timeframe='4h', days=90):
    exchange = ccxt.binance()
    since = exchange.parse8601((datetime.utcnow() - timedelta(days=days)).isoformat())

    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        save_historical_data(symbol, ohlcv)
        return df
    except Exception as e:
        log_error("HIST_DATA", f"Error: {e}")
        return None


def get_whale_transactions(currency, min_value=500000):
    transactions = []
    for chain, config in BLOCKCHAIN_APIS.items():
        if not config['api_key']:
            continue

        cache_key = f"{currency}_{chain}"
        cached = chain_cache.get(cache_key)
        if cached:
            transactions.extend(cached)
            continue

        try:
            params = {
                'module': 'account',
                'action': 'tokentx',
                'contractaddress': currency,
                'sort': 'desc',
                'apikey': config['api_key'],
                'minvalue': min_value
            }
            data = safe_api_request(config['api_url'], params=params)
            if data and data.get('status') == '1':
                chain_transactions = data.get('result', [])[:5]
                chain_cache.set(cache_key, chain_transactions)
                transactions.extend(chain_transactions)
        except Exception as e:
            log_error("WHALE_TX", f"Chain {chain} error: {e}")

    return transactions


def get_ai_recommendation(context):
    headers = {
        "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a professional crypto trader. Provide detailed analysis."},
            {"role": "user", "content": context}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }

    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        if 'choices' in result and result['choices']:
            return result['choices'][0]['message']['content']
        return "❌ Failed to get AI recommendation"
    except Exception as e:
        log_error("AI_API", f"Error: {e}")
        return "❌ AI service unavailable"