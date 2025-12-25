import sqlite3
import os
import pandas as pd

DB_PATH = 'data/ecommerce.db'

def init_db():
    if not os.path.exists('data'):
        os.makedirs('data')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS trends (date TEXT, product TEXT, interest INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (date TEXT, product TEXT, quantity INTEGER, price REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS social_sentiment (date TEXT, product TEXT, sentiment REAL)''')
    conn.commit()
    conn.close()

def load_data(table):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(f'SELECT * FROM {table}', conn)
    conn.close()
    return df