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
    """Generate realistic sample transaction data for Bangladeshi e-commerce"""
    try:
        df = pd.read_csv('data/sales.csv')  
    except FileNotFoundError:
        # Create realistic Bangladeshi e-commerce data with 2 years of history
        dates = pd.date_range(start='2024-01-15', end='2026-01-15', freq='D')
        
        # Bangladeshi product categories with realistic prices (in BDT)
        products_data = {
            'clothing': {'base_price': 800, 'variation': 400, 'seasonality': 'eid'},
            'mobile': {'base_price': 15000, 'variation': 8000, 'seasonality': 'year_round'},
            'home_exercise': {'base_price': 3500, 'variation': 2000, 'seasonality': 'winter'},
            'exercise_accessories': {'base_price': 600, 'variation': 300, 'seasonality': 'year_round'},
            'electronics': {'base_price': 5500, 'variation': 3000, 'seasonality': 'winter'},
            'food': {'base_price': 350, 'variation': 150, 'seasonality': 'ramadan'},
            'cosmetics': {'base_price': 850, 'variation': 400, 'seasonality': 'eid'},
            'toys': {'base_price': 450, 'variation': 200, 'seasonality': 'winter'}
        }
        
        all_data = []
        
        for date in dates:
            # Ensure EVERY product gets transactions every day for better forecasting
            for product, product_info in products_data.items():
                # Minimum 2-4 transactions per product per day
                num_transactions = np.random.randint(2, 5)
                
                for _ in range(num_transactions):
                    # Base quantity with random variation
                    base_quantity = np.random.randint(5, 25)
                    
                    # Seasonal boost (Eid, Ramadan, Winter effects)
                    seasonal_boost = 1.0
                    month = date.month
                    
                    # Ramadan boost (March-April typically)
                    if month in [3, 4] and product in ['food', 'clothing', 'cosmetics']:
                        seasonal_boost = 1.8
                    
                    # Eid boost (April-May and July-August)
                    if month in [4, 5, 7, 8] and product in ['clothing', 'cosmetics', 'toys', 'mobile']:
                        seasonal_boost = 2.2
                    
                    # Winter boost (November-February)
                    if month in [11, 12, 1, 2] and product in ['electronics', 'clothing', 'home_exercise']:
                        seasonal_boost = 1.4
                    
                    # New Year boost (January)
                    if month == 1 and product in ['mobile', 'electronics', 'exercise_accessories', 'home_exercise']:
                        seasonal_boost = 1.6
                    
                    # Weekly pattern (Friday-Saturday peak)
                    day_of_week = date.dayofweek
                    if day_of_week in [4, 5]:  # Friday, Saturday
                        seasonal_boost *= 1.3
                    
                    quantity = max(1, int(base_quantity * seasonal_boost))
                    
                    # Price with variation and seasonal adjustment
                    base_price = product_info['base_price']
                    price_variation = np.random.uniform(-product_info['variation']*0.4, product_info['variation']*0.4)
                    price = max(base_price + price_variation, 100)  # Minimum price 100 BDT
                    
                    # Add some promotional discounts randomly
                    if np.random.random() < 0.15:  # 15% chance of discount
                        price *= 0.85  # 15% discount
                    
                    all_data.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'product': product,
                        'quantity': quantity,
                        'price': round(price, 2),
                        'user_id': np.random.randint(1, 51)  # 50 simulated users
                    })
        
        df = pd.DataFrame(all_data)
        df.to_csv('data/sales.csv', index=False)
        
        # Print statistics per product
        print(f"\n✅ Generated {len(df)} realistic transactions for {len(products_data)} products")
        print("\n📊 Transactions per product:")
        for product in products_data.keys():
            count = len(df[df['product'] == product])
            print(f"   {product}: {count} transactions")
    
    conn = sqlite3.connect(DB_PATH)
    df.to_sql('transactions', conn, if_exists='replace', index=False)
    conn.close()
    print(f"\n✅ Loaded {len(df)} transactions into database")

def ingest_social_buzz(products=['clothing', 'mobile', 'home_exercise', 'exercise_accessories', 'electronics', 'food', 'cosmetics', 'toys']):
    """Generate realistic social sentiment data"""
    sia = SentimentIntensityAnalyzer()
    conn = sqlite3.connect(DB_PATH)
    dates = pd.date_range(start='2025-01-01', end='2026-01-15', freq='W')  # Weekly data
    
    # Realistic product sentiments in Bangladdeshi market
    product_sentiments = {
        'clothing': [
            'Perfect for Eid!', 'Great quality fabric', 'Love this dress!',
            'Nice collection', 'Highly recommended', 'Fast delivery'
        ],
        'mobile': [
            'Excellent phone!', 'Good battery life', 'Fast performance',
            'Value for money', 'Camera is amazing', 'Best in budget'
        ],
        'home_exercise': [
            'Great quality treadmill!', 'Perfect for home gym',  
            'Sturdy and durable', 'Good value', 'Helps stay fit'
        ],
        'exercise_accessories': [
            'Nice yoga mat', 'Good quality', 'Perfect resistance bands',
            'Very useful', 'Affordable price'
        ],
        'electronics': [
            'Good product', 'Fast shipping', 'Works perfectly',
            'Value for money', 'Recommended'
        ],
        'food': [
            'Fresh products', 'Quality is good', 'Timely delivery',
            'Always fresh', 'Great service'
        ],
        'cosmetics': [
            'Amazing lipstick!', 'Skin feels great', 'Love this brand',
            'Perfect shade', 'Long lasting'
        ],
        'toys': [
            'Kids love it!', 'Educational toy', 'Great gift',
            'Safe for kids', 'Good quality'
        ]
    }
    
    for product in products:
        sentiments = []
        for date in dates:
            # Pick random comment for product
            comment = np.random.choice(product_sentiments.get(product, ['Good product']))
            sentiment_score = sia.polarity_scores(comment)['compound']
            
            # Add some noise but keep mostly positive (0.4-0.95 range)
            sentiment_score = max(0.35, min(0.95, sentiment_score + np.random.uniform(-0.15, 0.25)))
            sentiments.append(sentiment_score)
        
        df = pd.DataFrame({
            'date': dates,
            'product': product,
            'sentiment': sentiments
        })
        df.to_sql('social_sentiment', conn, if_exists='append', index=False)
    
    conn.close()
    print(f"✅ Generated social sentiment data for {len(products)} products")
