"""
Generate comprehensive e-commerce database with detailed product information
Including specific models, variants, and attributes for all product categories
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db
import pandas as pd
import numpy as np
import sqlite3

# Initialize database
init_db()

print("\n🔄 Generating BIG detailed e-commerce data with product models/variants...")

# Define specific products with models/variants for each category
PRODUCT_CATALOG = {
    'mobile': [
        {'name': 'Samsung Galaxy A54', 'price': 38000, 'variation': 3000},
        {'name': 'iPhone 13', 'price': 85000, 'variation': 5000},
        {'name': 'Xiaomi Redmi Note 12', 'price': 25000, 'variation': 2000},
        {'name': 'Realme 11 Pro', 'price': 32000, 'variation': 2500},
        {'name': 'Oppo Reno 10', 'price': 42000, 'variation': 3000},
        {'name': 'iPhone 14 Pro', 'price': 125000, 'variation': 8000},
        {'name': 'Samsung Galaxy S23', 'price': 95000, 'variation': 6000},
        {'name': 'Vivo V29', 'price': 36000, 'variation': 2800},
        {'name': 'OnePlus Nord CE 3', 'price': 28000, 'variation': 2200},
        {'name': 'Google Pixel 7a', 'price': 52000, 'variation': 3500},
    ],
    'clothing': [
        {'name': 'Men Cotton T-Shirt', 'price': 450, 'variation': 150},
        {'name': 'Ladies Kurti', 'price': 1200, 'variation': 400},
        {'name': 'Men Formal Shirt', 'price': 1800, 'variation': 500},
        {'name': 'Ladies Saree', 'price': 3500, 'variation': 1500},
        {'name': 'Men Jeans Pant', 'price': 1600, 'variation': 400},
        {'name': 'Ladies Salwar Kameez', 'price': 2800, 'variation': 800},
        {'name': 'Kids T-Shirt', 'price': 350, 'variation': 100},
        {'name': 'Polo Shirt', 'price': 950, 'variation': 250},
        {'name': 'Ladies Palazzo', 'price': 850, 'variation': 200},
        {'name': 'Punjabi (Men)', 'price': 2200, 'variation': 600},
    ],
    'home_exercise': [
        {'name': 'Treadmill Electric', 'price': 45000, 'variation': 8000},
        {'name': 'Exercise Bike', 'price': 18000, 'variation': 3000},
        {'name': 'Weight Bench', 'price': 12000, 'variation': 2000},
        {'name': 'Dumbbell Set 20kg', 'price': 3500, 'variation': 500},
        {'name': 'Home Gym Multi-Station', 'price': 65000, 'variation': 10000},
        {'name': 'Rowing Machine', 'price': 28000, 'variation': 4000},
        {'name': 'Pull-up Bar', 'price': 1800, 'variation': 300},
        {'name': 'Ab Wheel Roller', 'price': 650, 'variation': 150},
    ],
    'exercise_accessories': [
        {'name': 'Yoga Mat Premium', 'price': 1200, 'variation': 300},
        {'name': 'Resistance Bands Set', 'price': 850, 'variation': 200},
        {'name': 'Gym Gloves', 'price': 550, 'variation': 150},
        {'name': 'Skipping Rope', 'price': 280, 'variation': 80},
        {'name': 'Fitness Tracker Watch', 'price': 3500, 'variation': 800},
        {'name': 'Gym Bag', 'price': 1100, 'variation': 250},
        {'name': 'Water Bottle (1L)', 'price': 450, 'variation': 100},
        {'name': 'Ankle Weights', 'price': 950, 'variation': 200},
        {'name': 'Foam Roller', 'price': 1400, 'variation': 300},
        {'name': 'Yoga Block Set', 'price': 680, 'variation': 150},
    ],
    'electronics': [
        {'name': 'Smart LED TV 43"', 'price': 38000, 'variation': 5000},
        {'name': 'Laptop HP Core i5', 'price': 52000, 'variation': 6000},
        {'name': 'Bluetooth Speaker', 'price': 2800, 'variation': 600},
        {'name': 'Wireless Earbuds', 'price': 3200, 'variation': 800},
        {'name': 'Power Bank 20000mAh', 'price': 1650, 'variation': 350},
        {'name': 'Smart Watch', 'price': 4500, 'variation': 1000},
        {'name': 'USB-C Hub', 'price': 1200, 'variation': 250},
        {'name': 'Webcam HD', 'price': 3800, 'variation': 600},
        {'name': 'Gaming Mouse', 'price': 1850, 'variation': 400},
        {'name': 'Mechanical Keyboard', 'price': 5500, 'variation': 1200},
    ],
    'food': [
        {'name': 'Basmati Rice 5kg', 'price': 550, 'variation': 100},
        {'name': 'Mustard Oil 1L', 'price': 180, 'variation': 30},
        {'name': 'Premium Tea 500g', 'price': 320, 'variation': 60},
        {'name': 'Honey Pure 500g', 'price': 450, 'variation': 80},
        {'name': 'Dates Premium 1kg', 'price': 680, 'variation': 120},
        {'name': 'Mixed Nuts 500g', 'price': 850, 'variation': 150},
        {'name': 'Olive Oil 500ml', 'price': 920, 'variation': 180},
        {'name': 'Organic Flour 2kg', 'price': 280, 'variation': 50},
        {'name': 'Chocolate Box', 'price': 650, 'variation': 120},
        {'name': 'Instant Noodles Pack', 'price': 380, 'variation': 70},
    ],
    'cosmetics': [
        {'name': 'Face Cream Moisturizer', 'price': 1200, 'variation': 300},
        {'name': 'Lipstick Matte', 'price': 650, 'variation': 150},
        {'name': 'Shampoo Anti-Dandruff', 'price': 420, 'variation': 80},
        {'name': 'Face Wash Gel', 'price': 380, 'variation': 70},
        {'name': 'Perfume 50ml', 'price': 1800, 'variation': 400},
        {'name': 'Hair Serum', 'price': 950, 'variation': 200},
        {'name': 'Sunscreen SPF 50', 'price': 850, 'variation': 180},
        {'name': 'Makeup Kit Complete', 'price': 2800, 'variation': 600},
        {'name': 'Eye Shadow Palette', 'price': 1100, 'variation': 250},
        {'name': 'Nail Polish Set', 'price': 580, 'variation': 120},
    ],
    'toys': [
        {'name': 'Remote Control Car', 'price': 1800, 'variation': 400},
        {'name': 'Barbie Doll Set', 'price': 1200, 'variation': 250},
        {'name': 'LEGO Building Blocks', 'price': 2500, 'variation': 500},
        {'name': 'Stuffed Teddy Bear', 'price': 650, 'variation': 150},
        {'name': 'Puzzle Game 1000pcs', 'price': 850, 'variation': 180},
        {'name': 'Educational Tablet', 'price': 3500, 'variation': 700},
        {'name': 'Kitchen Play Set', 'price': 1450, 'variation': 300},
        {'name': 'Cricket Bat (Kids)', 'price': 950, 'variation': 200},
        {'name': 'Drone Toy', 'price': 4200, 'variation': 800},
        {'name': 'Board Game Family', 'price': 1100, 'variation': 220},
    ],
}

# Generate BIG dataset: 3 years of data
dates = pd.date_range(start='2023-01-15', end='2026-01-15', freq='D')

all_data = []
transaction_id = 1

print(f"📅 Date range: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")
print(f"📦 Total unique products: {sum(len(items) for items in PRODUCT_CATALOG.values())}")

for date in dates:
    for category, products in PRODUCT_CATALOG.items():
        # Each category gets 3-6 transactions per day
        num_transactions = np.random.randint(3, 7)
        
        for _ in range(num_transactions):
            # Pick a random product from this category
            product_detail = np.random.choice(products)
            
            # Quantity
            base_quantity = np.random.randint(1, 15)
            
            # Seasonal variations
            seasonal_boost = 1.0
            month = date.month
            
            # Ramadan boost (March-April)
            if month in [3, 4] and category in ['food', 'clothing', 'cosmetics']:
                seasonal_boost = 2.0
            
            # Eid boost (April-May and July-August)
            if month in [4, 5, 7, 8] and category in ['clothing', 'cosmetics', 'toys', 'mobile']:
                seasonal_boost = 2.3
            
            # Winter boost (November-February)
            if month in [11, 12, 1, 2] and category in ['electronics', 'clothing', 'home_exercise']:
                seasonal_boost = 1.5
            
            # New Year boost (January)
            if month == 1 and category in ['mobile', 'electronics', 'exercise_accessories', 'home_exercise']:
                seasonal_boost = 1.7
            
            # Weekend boost (Friday-Saturday)
            if date.dayofweek in [4, 5]:
                seasonal_boost *= 1.2
            
            quantity = max(1, int(base_quantity * seasonal_boost))
            
            # Price with variation
            base_price = product_detail['price']
            price_var = np.random.uniform(-product_detail['variation']*0.3, product_detail['variation']*0.3)
            price = max(base_price + price_var, 50)
            
            # Random discounts (20% chance)
            if np.random.random() < 0.20:
                price *= 0.82  # 18% discount
            
            all_data.append({
                'transaction_id': transaction_id,
                'date': date.strftime('%Y-%m-%d'),
                'category': category,
                'product': category,  # Keep for compatibility with existing code
                'product_name': product_detail['name'],
                'quantity': quantity,
                'price': round(price, 2),
                'user_id': np.random.randint(1, 101),  # 100 simulated users
                'discount_applied': price != (base_price + price_var)
            })
            transaction_id += 1

df = pd.DataFrame(all_data)

# Save to CSV
os.makedirs('data', exist_ok=True)
df.to_csv('data/sales.csv', index=False)

print(f"\n✅ Generated {len(df):,} transactions")
print(f"\n📊 Transactions per category:")
for category in PRODUCT_CATALOG.keys():
    count = len(df[df['category'] == category])
    unique_products = df[df['category'] == category]['product_name'].nunique()
    print(f"   {category:25s}: {count:,} transactions | {unique_products} unique products")

# Save to database
conn = sqlite3.connect('ecommerce.db')
df.to_sql('transactions', conn, if_exists='replace', index=False)
conn.close()

print(f"\n✅ Loaded {len(df):,} transactions into database")

# === Social Sentiment ===
print("\n🔄 Generating social sentiment data...")

conn = sqlite3.connect('ecommerce.db')
sentiment_dates = pd.date_range(start='2023-01-15', end='2026-01-15', freq='W')

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

for category in PRODUCT_CATALOG.keys():
    base_sentiment = base_sentiments.get(category, 0.70)
    sentiments = []
    
    for date in sentiment_dates:
        seasonal_var = np.sin(date.dayofyear / 365.0 * 2 * np.pi) * 0.1
        random_noise = np.random.uniform(-0.08, 0.12)
        sentiment_score = base_sentiment + seasonal_var + random_noise
        sentiment_score = max(0.35, min(0.95, sentiment_score))
        sentiments.append(sentiment_score)
    
    sentiment_df = pd.DataFrame({
        'date': sentiment_dates,
        'product': category,  # Keep for compatibility
        'sentiment': sentiments
    })
    sentiment_df.to_sql('social_sentiment', conn, if_exists='append', index=False)

conn.close()

print(f"✅ Generated social sentiment data for {len(PRODUCT_CATALOG)} categories")
print(f"\n🎉 BIG DATABASE COMPLETE!")
print(f"📁 Database: ecommerce.db ({transaction_id:,} transactions)")
print(f"📁 CSV: data/sales.csv")
print(f"📦 Total unique products: {df['product_name'].nunique()}")
print(f"👥 Total unique users: {df['user_id'].nunique()}")
