import pandas as pd
import numpy as np
from pytrends.request import TrendReq
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from database import DB_PATH, load_data
import sqlite3

nltk.download('vader_lexicon', quiet=True)

def ingest_trends(products=['clothing', 'electronics'], regions='BD'):
    pytrends = TrendReq(hl='en-US', tz=360)
    conn = sqlite3.connect(DB_PATH)
    for product in products:
        pytrends.build_payload([product], cat=0, timeframe='today 5-y', geo=regions)
        data = pytrends.interest_over_time()
        if not data.empty:
            data = data.reset_index()
            data['product'] = product
            data.to_sql('trends', conn, if_exists='append', index=False)
    conn.close()

def ingest_mock_transactions():
   
    try:
        df = pd.read_csv('data/sales.csv')  
    except FileNotFoundError:
        dates = pd.date_range(start='2020-01-01', end='2025-12-16', freq='D')
        products = np.random.choice(['clothing', 'electronics', 'food'], size=len(dates))
        quantities = np.random.randint(1, 100, size=len(dates))
        prices = np.random.uniform(100, 1000, size=len(dates))
        df = pd.DataFrame({'date': dates, 'product': products, 'quantity': quantities, 'price': prices})
        df.to_csv('data/sales.csv', index=False)
    conn = sqlite3.connect(DB_PATH)
    df.to_sql('transactions', conn, if_exists='replace', index=False)
    conn.close()

def ingest_social_buzz(products=['clothing']):
    
    sia = SentimentIntensityAnalyzer()
    conn = sqlite3.connect(DB_PATH)
    dates = pd.date_range(start='2025-01-01', end='2025-12-16', freq='M')
    for product in products:
        sentiments = [sia.polarity_scores(f"Love this {product}!")['compound'] for _ in dates]
        df = pd.DataFrame({'date': dates, 'product': product, 'sentiment': sentiments})
        df.to_sql('social_sentiment', conn, if_exists='append', index=False)
    conn.close()