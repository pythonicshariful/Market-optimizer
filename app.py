# File: app.py
import os

# Load `.env` file into the process environment if present (simple, safe parser).
def _load_local_env(path=None):
    path = path or os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(path):
        return
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                # Do not override existing environment values
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass

# Load project .env early so LLM/backends pick up keys automatically
_load_local_env()
from flask import Flask, request, jsonify
import threading
from database import init_db, load_data
# Defer importing heavy modules (data_ingestion, models) until needed to reduce startup memory

from llm import load_llm, generate_insight, generate_insight_stream
from flask import Response
from utils import explain_model
from sklearn.linear_model import LinearRegression
import pandas as pd

# LLM (lazy-loaded to avoid heavy startup at import time)
llm = None

def get_llm():
    global llm
    if llm is None:
        try:
            llm = load_llm()
        except Exception:
            llm = None
    return llm

def gather_dashboard_context(product='clothing'):
    """Gather a short textual summary of current dashboard state for `product`.

    This function pulls forecast, pricing, recommendations and social signal
    and returns a concise human-readable summary to prepend to LLM prompts.
    """
    parts = []
    try:
        # Forecast (take last yhat)
        from models import forecast_demand
        fc = forecast_demand(product)
        if hasattr(fc, 'tail'):
            recent = fc.tail(1).iloc[0]
            parts.append(f"Forecast (next period) yhat={recent.get('yhat', 'NA'):.2f}")
    except Exception:
        parts.append("Forecast: unavailable")
    try:
        # Price details
        df = load_data('transactions')
        current_price = float(df[df['product'] == product]['price'].mean()) if (df is not None and not df.empty) else 0.0
        from models import train_pricing_model, optimize_price
        model = train_pricing_model(product)
        new_price = float(optimize_price(model, current_price))
        parts.append(f"Price: current={current_price:.2f}, optimized={new_price:.2f}")
    except Exception:
        parts.append("Price: unavailable")
    try:
        from models import build_recommender, recommend_products
        algo = build_recommender()
        recs = recommend_products(algo, user_id=1, n=5) if callable(recommend_products) else []
        if recs:
            parts.append("Top recommendations: " + ", ".join(map(str, recs[:5])))
    except Exception:
        parts.append("Recommendations: unavailable")
    try:
        df = load_data('social_sentiment')
        sentiment = float(df[df['product'] == product]['sentiment'].mean()) if (df is not None and not df.empty) else 0.0
        parts.append(f"Social sentiment (avg): {sentiment:.2f}")
    except Exception:
        parts.append("Social sentiment: unavailable")
    try:
        from models import build_graph, graph_insights
        G = build_graph()
        insights = graph_insights(G, product)
        parts.append(f"Graph: {insights}")
    except Exception:
        parts.append("Graph: unavailable")

    return "\n".join(parts)

# Flask App
flask_app = Flask(__name__)

@flask_app.route('/api/forecast', methods=['GET'])
def api_forecast():
    product = request.args.get('product', 'clothing')
    try:
        from models import forecast_demand
        forecast = forecast_demand(product)
        return jsonify(forecast.to_dict(orient='records'))
    except Exception as e:
        # Return a JSON error message so the client can display useful feedback
        return jsonify({'error': str(e)}), 500

@flask_app.route('/api/price', methods=['GET'])
def api_price():
    product = request.args.get('product', 'clothing')
    df = load_data('transactions')
    current_price = float(df[df['product']==product]['price'].mean()) if not df.empty else 0.0
    from models import train_pricing_model, optimize_price
    model = train_pricing_model(product)
    new_price = float(optimize_price(model, current_price))
    return jsonify({'optimized_price': new_price, 'current_price': current_price})

@flask_app.route('/api/recommend', methods=['GET'])
def api_recommend():
    user_id = int(request.args.get('user_id', 1))
    from models import build_recommender, recommend_products
    algo = build_recommender()
    recs = recommend_products(algo, user_id)
    return jsonify({'recommendations': recs})

@flask_app.route('/api/price_details', methods=['GET'])
def api_price_details():
    product = request.args.get('product', 'clothing')
    df = load_data('transactions')
    current_price = float(df[df['product'] == product]['price'].mean()) if not df.empty else 0.0
    from models import train_pricing_model, optimize_price
    model = train_pricing_model(product)
    new_price = float(optimize_price(model, current_price))
    # Create simple explanation using a placeholder linear model (mirrors Streamlit behavior)
    try:
        mock_data = pd.DataFrame({'price': [current_price]})
        mock_model = LinearRegression().fit(mock_data, [current_price])
        expl = explain_model(mock_model, mock_data)
        explanation = expl.values.tolist() if hasattr(expl, 'values') else [str(expl)]
    except Exception:
        explanation = []
    return jsonify({'current_price': current_price, 'optimized_price': new_price, 'explanation': explanation})

@flask_app.route('/api/graph', methods=['GET'])
def api_graph():
    product = request.args.get('product', 'clothing')
    from models import build_graph, graph_insights
    G = build_graph()
    insights = graph_insights(G, product)
    # Provide nodes/edges for simple network visualization
    nodes = [{'id': n, 'label': str(n)} for n in G.nodes()]
    edges = [{'from': u, 'to': v, 'value': G[u][v].get('weight', 1)} for u, v in G.edges()]
    return jsonify({'insights': insights, 'nodes': nodes, 'edges': edges})

# Simple product catalog (static/sample)
@flask_app.route('/api/products', methods=['GET'])
def api_products():
    """Return a small product catalog; in future this can be DB-backed."""
    # Simple sample catalog with external placeholder images to avoid adding binary assets
    products = [
        {
            'id': 1,
            'name': 'Lovely Linen Shirt',
            'price': 28.99,
            'old_price': 39.99,
            'currency': 'USD',
            'image': 'https://via.placeholder.com/400x300.png?text=Linen+Shirt',
            'stock': 23,
            'rating': 4.6,
            'short_desc': 'Cool, comfy, and camera-ready—linen that breathes all day.',
            'tags': ['Best Seller','Eco'],
            'eta_days': 2
        },
        {
            'id': 2,
            'name': 'Smart Home Charger',
            'price': 45.00,
            'old_price': 59.00,
            'currency': 'USD',
            'image': 'https://via.placeholder.com/400x300.png?text=Charger',
            'stock': 8,
            'rating': 4.4,
            'short_desc': 'Fast charge without fuss—power up in a snap.',
            'tags': ['New'],
            'eta_days': 3
        },
        {
            'id': 3,
            'name': 'Everyday Tote Bag',
            'price': 19.50,
            'old_price': None,
            'currency': 'USD',
            'image': 'https://via.placeholder.com/400x300.png?text=Tote+Bag',
            'stock': 120,
            'rating': 4.2,
            'short_desc': 'Carry everything with style—durable, light, and washable.',
            'tags': ['Budget'],
            'eta_days': 1
        }
    ]
    return jsonify({'products': products})

@flask_app.route('/api/social', methods=['GET'])
def api_social():
    product = request.args.get('product', 'clothing')
    df = load_data('social_sentiment')
    sentiment = float(df[df['product'] == product]['sentiment'].mean()) if (df is not None and not df.empty) else 0.0
    return jsonify({'sentiment': sentiment})

@flask_app.route('/api/social_series', methods=['GET'])
def api_social_series():
    product = request.args.get('product', 'clothing')
    df = load_data('social_sentiment')
    dfp = df[df['product'] == product].sort_values('date') if (df is not None and not df.empty) else None
    series = dfp.to_dict(orient='records') if dfp is not None and not dfp.empty else []
    return jsonify({'series': series})

@flask_app.route('/api/chat', methods=['GET','POST'])
def api_chat():
    prompt = None
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        prompt = data.get('prompt')
    if not prompt:
        prompt = request.args.get('prompt', '')
    # Optionally include dashboard context to ground answers
    product = request.args.get('product', None)
    include_ctx = request.args.get('include_context', 'true').lower() != 'false'
    ctx = ''
    if include_ctx:
        try:
            ctx = gather_dashboard_context(product or 'clothing')
        except Exception:
            ctx = ''

    final_prompt = prompt
    if ctx:
        final_prompt = f"{prompt}\n\nDashboard context:\n{ctx}\n\nPlease answer as a business advisor, referencing the dashboard values when relevant, and provide clear suggestions and next steps."

    model = get_llm()
    try:
        if model is None:
            # Fall back to generate_insight which handles dummy LLMs if possible
            resp = generate_insight(None, final_prompt)
        else:
            resp = generate_insight(model, final_prompt)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'response': resp})


@flask_app.route('/api/chat/stream', methods=['POST','GET'])
def api_chat_stream():
    # Streamed chat endpoint: returns a text/plain streamed body with incremental chunks
    prompt = None
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        prompt = data.get('prompt')
    if not prompt:
        prompt = request.args.get('prompt', '')
    product = request.args.get('product', None)
    include_ctx = request.args.get('include_context', 'true').lower() != 'false'
    ctx = ''
    if include_ctx:
        try:
            ctx = gather_dashboard_context(product or 'clothing')
        except Exception:
            ctx = ''
    final_prompt = prompt
    if ctx:
        final_prompt = f"{prompt}\n\nDashboard context:\n{ctx}\n\nPlease answer as a business advisor, referencing the dashboard values when relevant, and provide clear suggestions and next steps."

    model = get_llm()

    def gen():
        try:
            # Use streaming generator from llm.py
            for chunk in generate_insight_stream(model, final_prompt):
                if chunk is None:
                    continue
                # Ensure we send utf-8 text chunks
                yield chunk
        except Exception as e:
            yield f"ERROR: {e}"

    return Response(gen(), mimetype='text/plain; charset=utf-8')

@flask_app.route('/', methods=['GET'])
def index():
    # Serve the static single-page dashboard explicitly when available to avoid
    # falling back to a directory index response from another HTTP server.
    index_path = os.path.join(flask_app.root_path, 'static', 'index.html')
    if os.path.exists(index_path):
        from flask import send_from_directory
        return send_from_directory(os.path.join(flask_app.root_path, 'static'), 'index.html')
    # If the static index is not present for whatever reason, return a helpful JSON message
    return jsonify({
        'message': 'AI E-Commerce Engine (Flask API running). Static UI not available.',
        'endpoints': ['/api/forecast', '/api/price', '/api/recommend', '/api/price_details', '/api/graph', '/api/social', '/api/chat']
    })

# Also serve /index.html explicitly to avoid accidental directory listings by other servers
@flask_app.route('/index.html', methods=['GET'])
def index_html():
    index_path = os.path.join(flask_app.root_path, 'static', 'index.html')
    if os.path.exists(index_path):
        from flask import send_from_directory
        return send_from_directory(os.path.join(flask_app.root_path, 'static'), 'index.html')
    return jsonify({'message': 'index.html not found'})

def run_flask():
    flask_app.run(debug=False, use_reloader=False, port=5000)

# Streamlit App
def run_streamlit():
    # Import Streamlit and heavy model functions only when Streamlit UI is requested.
    import streamlit as st
    # Delay-import heavy model functions used only by Streamlit UI
    from models import forecast_demand, train_pricing_model, optimize_price, build_recommender, recommend_products, build_graph, graph_insights

    st.title("AI E-Commerce Engine for SMEs (Bangladesh)")
    st.sidebar.selectbox("Language", ["English", "Bangla"]) 

    product = st.text_input("Enter Product", "clothing")

    if st.button("Forecast Demand"):
        forecast = forecast_demand(product)
        st.dataframe(forecast)
        st.write(generate_insight(llm, f"Explain demand for {product}: {forecast['yhat'].mean()}"))

    if st.button("Optimize Price"):
        df = load_data('transactions')
        current_price = df[df['product']==product]['price'].mean()
        model = train_pricing_model(product)
        new_price = optimize_price(model, current_price)
        st.write(f"Optimized Price: {new_price}")
        # Explain
        # Mock data for explain
        mock_data = pd.DataFrame({'price': [current_price]})
        mock_model = LinearRegression().fit(mock_data, [current_price])  # Placeholder
        expl = explain_model(mock_model, mock_data)
        st.write("SHAP Explanation:", expl.values)

    if st.button("Recommend Products"):
        algo = build_recommender()
        recs = recommend_products(algo)
        st.write(f"Recommendations: {recs}")

    if st.button("Graph Insights"):
        G = build_graph()
        insights = graph_insights(G, product)
        st.write(insights)

    if st.button("Social Buzz"):
        df = load_data('social_sentiment')
        sentiment = df[df['product']==product]['sentiment'].mean() if not df.empty else 0
        st.write(f"Sentiment: {sentiment}")

    # Chat Copilot
    st.subheader("ROI Copilot")
    user_input = st.text_input("Ask a question (e.g., Why restock?)")
    if user_input:
        prompt = f"Answer in business context: {user_input}"
        st.write(generate_insight(llm, prompt))

# Main
if __name__ == '__main__':
    init_db()
    # Ingest data (run once) — skip when SKIP_INGEST=1 to speed local development
    if os.environ.get('SKIP_INGEST', '').lower() not in ('1', 'true'):
        try:
            ingest_trends()
        except Exception as e:
            import warnings
            warnings.warn(f"ingest_trends failed: {e}")
        try:
            ingest_mock_transactions()
        except Exception as e:
            import warnings
            warnings.warn(f"ingest_mock_transactions failed: {e}")
        try:
            ingest_social_buzz()
        except Exception as e:
            import warnings
            warnings.warn(f"ingest_social_buzz failed: {e}")
    
    # Run Streamlit UI only when launched via `streamlit run` (avoids missing ScriptRunContext warnings)
    import os
    if os.environ.get('STREAMLIT_SERVER_RUN') == 'true':
        # When running Streamlit, start Flask in background so the UI can run in the main thread
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        run_streamlit()
    else:
        # When running via `python app.py`, run Flask in the foreground (blocking) so the process stays alive
        print("Streamlit UI not started. To view the UI, run:\n\n    streamlit run app.py\n\nStarting Flask API on http://127.0.0.1:5000 ...")
        run_flask()