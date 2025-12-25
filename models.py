
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from prophet import Prophet
try:
    from pycaret.regression import setup, compare_models, finalize_model
    PYCARET_AVAILABLE = True
except Exception:
    setup = compare_models = finalize_model = None
    PYCARET_AVAILABLE = False
    import warnings
    warnings.warn("PyCaret not available or incompatible with this Python version. Some features will be disabled.", RuntimeWarning)
import networkx as nx

try:
    import faiss
    FAISS_AVAILABLE = True
except Exception:
    faiss = None
    FAISS_AVAILABLE = False
    import warnings
    warnings.warn("faiss not available; RAG features limited.", RuntimeWarning)
from database import load_data
# Demand Forecasting
def forecast_demand(product='clothing'):
    df = load_data('transactions')
    df_product = df[df['product'] == product][['date', 'quantity']].rename(columns={'date': 'ds', 'quantity': 'y'})
    if df_product.empty:
        raise ValueError(f"No transaction data available for product '{product}'")
    df_product['ds'] = pd.to_datetime(df_product['ds'])
    if len(df_product) < 10:

        raise ValueError(f"Not enough data to forecast for product '{product}' (need >=10 rows)")
    try:
        m = Prophet()
        m.fit(df_product)
        future = m.make_future_dataframe(periods=30)
        forecast = m.predict(future)
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(30)
    except Exception as e:
       
        raise RuntimeError(f"Forecasting failed: {e}")

class PricingEnv:
    def __init__(self, data):
        self.data = data['price'].values
        self.current_step = 0
        self.max_steps = len(self.data)

    def reset(self):
        self.current_step = 0
        return self._get_obs(), {}

    def _get_obs(self):
        return np.array([self.data[self.current_step]], dtype=np.float32)

    def step(self, action):
        new_price = self.data[self.current_step] * (1 + action / 10)  # Action: -5 to 5% change
        reward = -abs(new_price - self.data[self.current_step])  # Simple reward: minimize deviation for demo
        self.current_step += 1
        done = self.current_step >= self.max_steps
        truncated = False
        return self._get_obs(), reward, done, truncated, {}

def train_pricing_model(product='clothing'):
    df = load_data('transactions')
    df_product = df[df['product'] == product]
    try:
       
        from stable_baselines3 import PPO
        from stable_baselines3.common.vec_env import DummyVecEnv
        env = DummyVecEnv([lambda: PricingEnv(df_product)])
        model = PPO('MlpPolicy', env, verbose=0)
        model.learn(total_timesteps=1000)  # Short training for demo
        return model
    except Exception:
       
        class SimpleModel:
            def predict(self, obs):
                return (np.array([0.0]), None)
        return SimpleModel()

def optimize_price(model, current_price):
    obs = np.array([current_price], dtype=np.float32)
    action, _ = model.predict(obs)
    new_price = current_price * (1 + action[0] / 10)
    return new_price

# Recommendation System
def build_recommender():
    df = load_data('transactions')
    # Try to use Surprise SVD recommender if available
    try:
        from surprise import Dataset, Reader, SVD
        df['user_id'] = np.random.randint(1, 100, len(df))
        df['rating'] = np.random.uniform(1, 5, len(df))
        reader = Reader(rating_scale=(1, 5))
        data = Dataset.load_from_df(df[['user_id', 'product', 'rating']], reader)
        trainset = data.build_full_trainset()
        algo = SVD()
        algo.fit(trainset)
        return algo
    except Exception:
        # Fallback: popularity-based recommender
        counts = df['product'].value_counts()
        class PopularityRecommender:
            def __init__(self, counts):
                self.counts = counts
            def predict(self, user_id, product):
                class Pred:
                    def __init__(self, iid, est):
                        self.iid = iid
                        self.est = est
                return Pred(product, self.counts.get(product, 0))
            def recommend(self, n=5):
                return list(self.counts.index[:n])
        return PopularityRecommender(counts) 

def recommend_products(algo, user_id=1, n=5):
    products = load_data('transactions')['product'].unique()
    preds = [algo.predict(user_id, prod) for prod in products]
    top = sorted(preds, key=lambda x: x.est, reverse=True)[:n]
    return [pred.iid for pred in top]

# Graph Neural Networks (simplified with NetworkX)
def build_graph():
    df = load_data('transactions')
    G = nx.Graph()
    for _, row in df.iterrows():
        G.add_edge(row['product'], f"user_{np.random.randint(1,10)}", weight=row['quantity'])
    return G

def graph_insights(G, product):
    if product in G:
        neighbors = list(G.neighbors(product))
        return f"Related to: {neighbors}"
    return "No relations"

# Hybrid RAG + MCP (simplified)
# Keep in-memory lists always; create a FAISS index only when available
documents = []  # List of texts
embeddings = []  # List of vectors
if FAISS_AVAILABLE:
    try:
        index = faiss.IndexFlatL2(768)  # Assume embedding dim
    except Exception:
        index = None
else:
    index = None

def add_to_rag(text, embedding):
    global index, documents, embeddings
    documents.append(text)
    embeddings.append(embedding)
    if index is not None:
        try:
            index.add(np.array([embedding]))
        except Exception:
            # ignore faiss errors at runtime
            pass

# Helper: provide a regression model using PyCaret when available, else fallback to sklearn
def get_regression_model(X, y):
    """Return a fitted regression model.

    Tries to use PyCaret's compare_models pipeline when available; otherwise falls back
    to a simple sklearn LinearRegression fit. X can be array-like or dataframe-like.
    """
    if PYCARET_AVAILABLE and setup is not None and compare_models is not None:
        try:
            import pandas as pd
            df = pd.concat([pd.DataFrame(X), pd.Series(y, name='target')], axis=1)
            # Lightweight, non-interactive setup
            setup(df, target='target', silent=True, html=False, verbose=False)
            model = compare_models()
            return finalize_model(model)
        except Exception:
            # Fall through to sklearn fallback
            pass

    # sklearn fallback
    from sklearn.linear_model import LinearRegression
    return LinearRegression().fit(X, y)