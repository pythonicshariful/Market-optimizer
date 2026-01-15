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
from data_ingestion import ingest_trends, ingest_mock_transactions, ingest_social_buzz
# Defer importing heavy modules (models) until needed to reduce startup memory

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

@flask_app.route('/api/export/excel', methods=['GET'])
def api_export_excel():
    """Export sales data to Excel format."""
    try:
        from export_utils import export_sales_excel
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        filepath = export_sales_excel(start_date, end_date)
        from flask import send_file
        return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@flask_app.route('/api/export/forecast', methods=['GET'])
def api_export_forecast():
    """Export forecast report."""
    try:
        from export_utils import generate_forecast_pdf
        from models import forecast_demand
        product = request.args.get('product', 'clothing')
        forecast_data = forecast_demand(product)
        filepath = generate_forecast_pdf(product, forecast_data)
        from flask import send_file
        return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@flask_app.route('/api/analytics/kpis', methods=['GET'])
def api_analytics_kpis():
    """Calculate comprehensive KPIs for dashboard analytics."""
    try:
        df = load_data('transactions')
        if df is None or df.empty:
            return jsonify({'error': 'No transaction data available'}), 404
        
        # Ensure date column is datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Calculate Total Revenue
        df['total_amount'] = df['quantity'] * df['price']
        total_revenue = float(df['total_amount'].sum())
        
        # Calculate growth rate (compare last 30 days vs previous 30 days)
        today = pd.Timestamp.now()
        last_30_days = df[df['date'] >= (today - pd.Timedelta(days=30))]
        prev_30_days = df[(df['date'] >= (today - pd.Timedelta(days=60))) & (df['date'] < (today - pd.Timedelta(days=30)))]
        
        last_30_revenue = float(last_30_days['total_amount'].sum()) if not last_30_days.empty else 0
        prev_30_revenue = float(prev_30_days['total_amount'].sum()) if not prev_30_days.empty else 1
        growth_rate = ((last_30_revenue - prev_30_revenue) / prev_30_revenue * 100) if prev_30_revenue > 0 else 0
        
        # Top 5 Products by Revenue
        product_revenue = df.groupby('product')['total_amount'].sum().sort_values(ascending=False)
        top_products = [{'name': k, 'revenue': float(v)} for k, v in product_revenue.head(5).items()]
        
        # Total Orders
        total_orders = len(df)
        
        # Average Order Value
        avg_order_value = float(df.groupby('transaction_id')['total_amount'].sum().mean()) if 'transaction_id' in df.columns else float(df['total_amount'].mean())
        
        # Unique Customers (if user_id exists)
        unique_customers = int(df['user_id'].nunique()) if 'user_id' in df.columns else 0
        
        # Today's Revenue
        today_revenue = float(df[df['date'] == today.date()]['total_amount'].sum()) if not df[df['date'] == today.date()].empty else 0
        
        # This Week's Revenue
        week_start = today - pd.Timedelta(days=today.dayofweek)
        week_revenue = float(df[df['date'] >= week_start.date()]['total_amount'].sum())
        
        # This Month's Revenue
        month_start = today.replace(day=1)
        month_revenue = float(df[df['date'] >= month_start.date()]['total_amount'].sum())
        
        # Product with highest growth
        last_month_df = df[df['date'] >= (today - pd.Timedelta(days=30))]
        prev_month_df = df[(df['date'] >= (today - pd.Timedelta(days=60))) & (df['date'] < (today - pd.Timedelta(days=30)))]
        
        growth_by_product = {}
        for product in df['product'].unique():
            last = last_month_df[last_month_df['product'] == product]['total_amount'].sum()
            prev = prev_month_df[prev_month_df['product'] == product]['total_amount'].sum()
            if prev > 0:
                growth_by_product[product] = ((last - prev) / prev * 100)
        
        trending_product = max(growth_by_product.items(), key=lambda x: x[1]) if growth_by_product else ('N/A', 0)
        
        return jsonify({
            'total_revenue': round(total_revenue, 2),
            'growth_rate': round(growth_rate, 2),
            'total_orders': total_orders,
            'avg_order_value': round(avg_order_value, 2),
            'unique_customers': unique_customers,
            'today_revenue': round(today_revenue, 2),
            'week_revenue': round(week_revenue, 2),
            'month_revenue': round(month_revenue, 2),
            'top_products': top_products,
            'trending_product': {
                'name': trending_product[0],
                'growth': round(trending_product[1], 2)
            }
        })
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@flask_app.route('/api/stock/alert', methods=['GET'])
def api_stock_alert():
    """Analyze inventory and predict stock-outs."""
    try:
        df = load_data('transactions')
        if df is None or df.empty:
            return jsonify({'error': 'No data'}), 404
        
        df['date'] = pd.to_datetime(df['date'])
        today = pd.Timestamp.now()
        last_30_days = df[df['date'] >= (today - pd.Timedelta(days=30))]
        
        alerts = []
        for product in df['product'].unique():
            product_sales = last_30_days[last_30_days['product'] == product]
            if len(product_sales) == 0:
                continue
            
            # Calculate daily average sales
            daily_avg = product_sales.groupby('date')['quantity'].sum().mean()
            total_sold_30d = product_sales['quantity'].sum()
            
            # Assume 100 units current stock (can be made dynamic)
            current_stock = 100
            days_until_stockout = int(current_stock / daily_avg) if daily_avg > 0 else 999
            reorder_point = int(daily_avg * 7)  # 1 week safety stock
            
            status = 'ok'
            if days_until_stockout < 7:
                status = 'critical'
            elif days_until_stockout < 14:
                status = 'warning'
            
            alerts.append({
                'product': product,
                'current_stock': current_stock,
                'daily_avg_sales': round(daily_avg, 2),
                'days_until_stockout': days_until_stockout,
                'reorder_point': reorder_point,
                'status': status,
                'recommendation': f"অর্ডার দিন {reorder_point} ইউনিট" if status != 'ok' else 'স্টক ভালো আছে'
            })
        
        return jsonify({'alerts': sorted(alerts, key=lambda x: x['days_until_stockout'])})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@flask_app.route('/api/trends/analysis', methods=['GET'])
def api_trends_analysis():
    """Analyze sales trends by day and time."""
    try:
        df = load_data('transactions')
        if df is None or df.empty:
            return jsonify({'error': 'No data'}), 404
        
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['date'].dt.day_name()
        df['total_amount'] = df['quantity'] * df['price']
        
        # Best selling days
        day_sales = df.groupby('day_of_week')['total_amount'].sum().to_dict()
        best_day = max(day_sales.items(), key=lambda x: x[1])
        
        # Weekly pattern
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekly_pattern = [{'day': day, 'revenue': float(day_sales.get(day, 0))} for day in days_order]
        
        # Month-over-month growth
        df['month'] = df['date'].dt.to_period('M')
        monthly_revenue = df.groupby('month')['total_amount'].sum()
        if len(monthly_revenue) >= 2:
            latest_month = monthly_revenue.iloc[-1]
            prev_month = monthly_revenue.iloc[-2]
            mom_growth = ((latest_month - prev_month) / prev_month * 100) if prev_month > 0 else 0
        else:
            mom_growth = 0
        
        return jsonify({
            'best_day': {'name': best_day[0], 'revenue': float(best_day[1])},
            'weekly_pattern': weekly_pattern,
            'mom_growth': round(mom_growth, 2),
            'recommendation': f"{best_day[0]} তে বেশি প্রচার চালান - সবচেয়ে বেশি বিক্রয় হয়!"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@flask_app.route('/api/customer/insights', methods=['GET'])
def api_customer_insights():
    """Customer RFM analysis and lifetime value."""
    try:
        df = load_data('transactions')
        if df is None or df.empty or 'user_id' not in df.columns:
            return jsonify({'error': 'No customer data'}), 404
        
        df['date'] = pd.to_datetime(df['date'])
        df['total_amount'] = df['quantity'] * df['price']
        today = pd.Timestamp.now()
        
        # RFM Analysis
        rfm = df.groupby('user_id').agg({
            'date': lambda x: (today - x.max()).days,  # Recency
            'transaction_id': 'count',  # Frequency
            'total_amount': 'sum'  # Monetary
        }).rename(columns={'date': 'recency', 'transaction_id': 'frequency', 'total_amount': 'monetary'})
        
        # Top 5 customers by value
        top_customers = rfm.nlargest(5, 'monetary')
        top_list = [{'customer_id': int(idx), 'total_spent': float(row['monetary']), 'orders': int(row['frequency'])} 
                    for idx, row in top_customers.iterrows()]
        
        # Average customer lifetime value
        avg_ltv = float(rfm['monetary'].mean())
        
        # Churn risk (customers who haven't bought in 60+ days)
        at_risk = len(rfm[rfm['recency'] > 60])
        
        return jsonify({
            'total_customers': len(rfm),
            'top_customers': top_list,
            'avg_ltv': round(avg_ltv, 2),
            'at_risk_customers': at_risk,
            'recommendation': f"{at_risk} জন ক্রেতা ঝুঁকিতে আছে - তাদের জন্য বিশেষ অফার দিন!"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@flask_app.route('/api/profit/analysis', methods=['GET'])
def api_profit_analysis():
    """Calculate profit margins for products."""
    try:
        df = load_data('transactions')
        if df is None or df.empty:
            return jsonify({'error': 'No data'}), 404
        
        # Assume 30% cost (can be made dynamic)
        cost_margin = 0.70
        
        df['total_amount'] = df['quantity'] * df['price']
        df['cost'] = df['total_amount'] * cost_margin
        df['profit'] = df['total_amount'] - df['cost']
        
        # Profit by product
        product_profit = df.groupby('product').agg({
            'total_amount': 'sum',
            'cost': 'sum',
            'profit': 'sum',
            'quantity': 'sum'
        }).reset_index()
        
        product_profit['profit_margin'] = (product_profit['profit'] / product_profit['total_amount'] * 100)
        
        # Most profitable products
        top_profit = product_profit.nlargest(5, 'profit')
        profit_list = [{'product': row['product'], 
                        'revenue': float(row['total_amount']), 
                        'profit': float(row['profit']),
                        'margin': round(row['profit_margin'], 2)}
                       for _, row in top_profit.iterrows()]
        
        total_profit = float(df['profit'].sum())
        total_margin = (total_profit / df['total_amount'].sum() * 100)
        
        best_margin_product = product_profit.loc[product_profit['profit_margin'].idxmax()]
        
        return jsonify({
            'total_profit': round(total_profit, 2),
            'profit_margin': round(total_margin, 2),
            'top_profitable': profit_list,
            'best_margin_product': {
                'name': best_margin_product['product'],
                'margin': round(best_margin_product['profit_margin'], 2)
            },
            'recommendation': f"{best_margin_product['product']} সবচেয়ে লাভজনক - এটি বেশি প্রচার করুন!"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@flask_app.route('/api/seasonal/predictor', methods=['GET'])
def api_seasonal_predictor():
    """Detect seasonal patterns for Bangladesh market."""
    try:
        df = load_data('transactions')
        if df is None or df.empty:
            return jsonify({'error': 'No data'}), 404
        
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.month
        df['total_amount'] = df['quantity'] * df['price']
        
        # Month-wise revenue
        monthly = df.groupby('month')['total_amount'].sum().to_dict()
        
        # Identify peak months
        peak_month = max(monthly.items(), key=lambda x: x[1])
        
        # Bangladesh-specific seasons
        month_names = {1: 'জানুয়ারি', 2: 'ফেব্রুয়ারি', 3: 'মার্চ (রমজান)', 4: 'এপ্রিল (ঈদ)', 
                      5: 'মে', 6: 'জুন', 7: 'জুলাই', 8: 'আগস্ট', 9: 'সেপ্টেম্বর', 
                      10: 'অক্টোবর', 11: 'নভেম্বর (শীত)', 12: 'ডিসেম্বর (শীত)'}
        
        # Ramadan/Eid products (March-May surge)
        eid_months = df[df['month'].isin([3, 4, 5])]
        eid_top_products = eid_months.groupby('product')['total_amount'].sum().nlargest(3)
        
        # Winter products (Nov-Feb surge)
        winter_months = df[df['month'].isin([11, 12, 1, 2])]
        winter_top_products = winter_months.groupby('product')['total_amount'].sum().nlargest(3)
        
        # Current month prediction
        current_month = pd.Timestamp.now().month
        upcoming_season = ""
        if current_month in [2, 3]:
            upcoming_season = "রমজান আসছে - খাদ্য ও পোশাক স্টক বাড়ান"
        elif current_month in [3, 4]:
            upcoming_season = "ঈদ আসছে - পোশাক, প্রসাধনী, খেলনা স্টক বাড়ান"
        elif current_month in [10, 11]:
            upcoming_season = "শীত আসছে - ইলেকট্রনিক্স, পোশাক স্টক বাড়ান"
        else:
            upcoming_season = "স্বাভাবিক মৌসুম - নিয়মিত স্টক বজায় রাখুন"
        
        return jsonify({
            'peak_month': {'month': peak_month[0], 'name': month_names.get(peak_month[0]), 'revenue': float(peak_month[1])},
            'eid_top_products': [{'product': k, 'revenue': float(v)} for k, v in eid_top_products.items()],
            'winter_top_products': [{'product': k, 'revenue': float(v)} for k, v in winter_top_products.items()],
            'upcoming_season': upcoming_season,
            'recommendation': upcoming_season
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@flask_app.route('/api/marketing/planner', methods=['GET'])
def api_marketing_planner():
    """Marketing campaign recommendations."""
    try:
        df = load_data('transactions')
        if df is None or df.empty:
            return jsonify({'error': 'No data'}), 404
        
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['date'].dt.dayofweek  # 0=Monday, 6=Sunday
        df['total_amount'] = df['quantity'] * df['price']
        
        # Best campaign days (Friday-Saturday বেশি বিক্রয়)
        day_performance = df.groupby('day_of_week')['total_amount'].mean()
        best_campaign_day = day_performance.idxmax()
        day_names = ['সোমবার', 'মঙ্গলবার', 'বুধবার', 'বৃহস্পতিবার', 'শুক্রবার', 'শনিবার', 'রবিবার']
        
        # Products that need promotion (low recent sales)
        today = pd.Timestamp.now()
        recent = df[df['date'] >= (today - pd.Timedelta(days=30))]
        old = df[(df['date'] >= (today - pd.Timedelta(days=60))) & (df['date'] < (today - pd.Timedelta(days=30)))]
        
        recent_sales = recent.groupby('product')['total_amount'].sum()
        old_sales = old.groupby('product')['total_amount'].sum()
        
        declining = []
        for product in df['product'].unique():
            r = recent_sales.get(product, 0)
            o = old_sales.get(product, 1)
            if r < o:
                decline_pct = ((o - r) / o * 100) if o > 0 else 0
                declining.append({'product': product, 'decline': round(decline_pct, 2)})
        
        declining = sorted(declining, key=lambda x: x['decline'], reverse=True)[:3]
        
        # Discount strategy
        discount_candidates = [item['product'] for item in declining]
        
        return jsonify({
            'best_campaign_day': day_names[best_campaign_day],
            'declining_products': declining,
            'discount_recommendations': discount_candidates,
            'recommended_discount': '15-20%',
            'recommendation': f"{day_names[best_campaign_day]} তে ক্যাম্পেইন চালান এবং {', '.join(discount_candidates[:2])} এ ডিসকাউন্ট দিন"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@flask_app.route('/api/compare', methods=['GET'])
def api_compare():
    """Compare multiple products."""
    try:
        products_param = request.args.get('products', 'clothing,electronics')
        products = [p.strip() for p in products_param.split(',')]
        
        df = load_data('transactions')
        comparison = {}
        
        for product in products:
            product_data = df[df['product'] == product]
            if not product_data.empty:
                comparison[product] = {
                    'total_sales': int(product_data['quantity'].sum()),
                    'avg_price': float(product_data['price'].mean()),
                    'transaction_count': len(product_data),
                    'avg_quantity': float(product_data['quantity'].mean())
                }
        
        return jsonify({'comparison': comparison})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@flask_app.route('/api/chat', methods=['GET','POST'])
def api_chat():
    prompt = None
    lang = 'en'
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        prompt = data.get('prompt')
        lang = data.get('lang', 'en')
    if not prompt:
        prompt = request.args.get('prompt', '')
        lang = request.args.get('lang', 'en')
    
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
        if lang == 'bn':
            final_prompt = f"{prompt}\n\nড্যাশবোর্ড প্রসঙ্গ:\n{ctx}\n\nঅনুগ্রহ করে একজন ব্যবসা পরামর্শদাতা হিসেবে উত্তর দিন, প্রাসঙ্গিক হলে ড্যাশবোর্ডের মান উল্লেখ করুন এবং স্পষ্ট পরামর্শ ও পরবর্তী পদক্ষেপ প্রদান করুন। বাংলায় উত্তর দিন।"
        else:
            final_prompt = f"{prompt}\n\nDashboard context:\n{ctx}\n\nPlease answer as a business advisor, referencing the dashboard values when relevant, and provide clear suggestions and next steps."

    model = get_llm()
    try:
        if model is None:
            # Fall back to generate_insight which handles dummy LLMs if possible
            resp = generate_insight(None, final_prompt, lang=lang)
        else:
            resp = generate_insight(model, final_prompt, lang=lang)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'response': resp})


@flask_app.route('/api/chat/stream', methods=['POST','GET'])
def api_chat_stream():
    # Streamed chat endpoint: returns a text/plain streamed body with incremental chunks
    prompt = None
    lang = 'en'
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        prompt = data.get('prompt')
        lang = data.get('lang', 'en')
    if not prompt:
        prompt = request.args.get('prompt', '')
        lang = request.args.get('lang', 'en')
    
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
        if lang == 'bn':
            final_prompt = f"{prompt}\n\nড্যাশবোর্ড প্রসঙ্গ:\n{ctx}\n\nঅনুগ্রহ করে একজন ব্যবসা পরামর্শদাতা হিসেবে উত্তর দিন, প্রাসঙ্গিক হলে ড্যাশবোর্ডের মান উল্লেখ করুন এবং স্পষ্ট পরামর্শ ও পরবর্তী পদক্ষেপ প্রদান করুন। সব উত্তর বাংলায় দিন।"
        else:
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