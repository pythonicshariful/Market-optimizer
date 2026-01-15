"""
Simple script to regenerate the database with all product data
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db

# Initialize database
init_db()

# Import and run data ingestion (skip trends which needs pytrends)
import pandas as pd
import numpy as np
import sqlite3

# === Mock Transactions ===
print("\n🔄 Generating transaction data...")

dates = pd.date_range(start='2024-01-15', end='2026-01-15', freq='D')

products_data = {
    'clothing': {'base_price': 800, 'variation': 400},
    'mobile': {'base_price': 15000, 'variation': 8000},
    'home_exercise': {'base_price': 3500, 'variation': 2000},
    'exercise_accessories': {'base_price': 600, 'variation': 300},
    'electronics': {'base_price': 5500, 'variation': 3000},
    'food': {'base_price': 350, 'variation': 150},
    'cosmetics': {'base_price': 850, 'variation': 400},
    'toys': {'base_price': 450, 'variation': 200}
}

all_data = []

for date in dates:
    for product, product_info in products_data.items():
        num_transactions = np.random.randint(2, 5)
        
        for _ in range(num_transactions):
            base_quantity = np.random.randint(5, 25)
            seasonal_boost = 1.0
            month = date.month
            
            if month in [3, 4] and product in ['food', 'clothing', 'cosmetics']:
                seasonal_boost = 1.8
            if month in [4, 5, 7, 8] and product in ['clothing', 'cosmetics', 'toys', 'mobile']:
                seasonal_boost = 2.2
            if month in [11, 12, 1, 2] and product in ['electronics', 'clothing', 'home_exercise']:
                seasonal_boost = 1.4
            if month == 1 and product in ['mobile', 'electronics', 'exercise_accessories', 'home_exercise']:
                seasonal_boost = 1.6
            
            day_of_week = date.dayofweek
            if day_of_week in [4, 5]:
                seasonal_boost *= 1.3
            
            quantity = max(1, int(base_quantity * seasonal_boost))
            base_price = product_info['base_price']
            price_variation = np.random.uniform(-product_info['variation']*0.4, product_info['variation']*0.4)
            price = max(base_price + price_variation, 100)
            
            if np.random.random() < 0.15:
                price *= 0.85
            
            all_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'product': product,
                'quantity': quantity,
                'price': round(price, 2),
                'user_id': np.random.randint(1, 51)
            })

df = pd.DataFrame(all_data)
os.makedirs('data', exist_ok=True)
df.to_csv('data/sales.csv', index=False)

print(f"\n✅ Generated {len(df):,} transactions")
print("\n📊 Transactions per product:")
for product in products_data.keys():
    count = len(df[df['product'] == product])
    print(f"   {product:25s}: {count:,} transactions")

conn = sqlite3.connect('ecommerce.db')
df.to_sql('transactions', conn, if_exists='replace', index=False)
conn.close()

print(f"\n✅ Loaded transactions into database")

# === Social Sentiment ===
print("\n🔄 Generating social sentiment data...")

conn = sqlite3.connect('ecommerce.db')
dates = pd.date_range(start='2025-01-01', end='2026-01-15', freq='W')

# Predefined sentiment scores for each product (0-1 scale, with slight variations)
base_sentiments = {
    'clothing': 0.75,
    'mobile': 0.82,
    'home_exercise': 0.70,
    'exercise_accessories': 0.68,
    'electronics': 0.72,
    'food': 0.78,
    'cosmetics': 0.80,
    'toys': 0.76
}

for product in products_data.keys():
    base_sentiment = base_sentiments.get(product, 0.70)
    sentiments = []
    
    for date in dates:
        # Add realistic variations to sentiment over time
        seasonal_variation = np.sin(date.dayofyear / 365.0 * 2 * np.pi) * 0.1
        random_noise = np.random.uniform(-0.08, 0.12)
        sentiment_score = base_sentiment + seasonal_variation + random_noise
        sentiment_score = max(0.35, min(0.95, sentiment_score))
        sentiments.append(sentiment_score)
    
    sentiment_df = pd.DataFrame({
        'date': dates,
        'product': product,
        'sentiment': sentiments
    })
    sentiment_df.to_sql('social_sentiment', conn, if_exists='append', index=False)

conn.close()

print(f"✅ Generated social sentiment data for {len(products_data)} products")
print("\n🎉 Database regeneration complete!")
print(f"📁 Database location: ecommerce.db")
print(f"📁 Sales CSV location: data/sales.csv")
