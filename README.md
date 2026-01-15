# 🚀 AI-First Commerce for Everyone (AFCE)

> বাংলাদেশের ছোট ব্যবসায়ীদের জন্য AI-powered মার্কেট বিশ্লেষণ টুল

<img align="right" width="150" src="https://via.placeholder.com/150/6366f1/ffffff?text=AFCE" alt="AFCE Logo">

**মূল বৈশিষ্ট্য:**
- 🇧🇩 বাংলা ভাষা সাপোর্ট
- 🌙 ডার্ক মোড
- 📊 চাহিদা পূর্বাভাস
- 💰 স্বয়ংক্রিয় মূল্য নির্ধারণ
- 🤖 AI চ্যাটবট (বাংলায়)
- 📥 Excel রিপোর্ট এক্সপোর্ট

---

## 📖 সুচিপত্র

1. [দ্রুত শুরু করুন](#-দ্রুত-শুরু-করুন)
2. [বৈশিষ্ট্যসমূহ](#-বৈশিষ্ট্যসমূহ)
3. [স্ক্রিনশট](#-স্ক্রিনশট)
4. [কিভাবে কাজ করে](#-কিভাবে-কাজ-করে)
5. [সহায়তা](#-সহায়তা)

---

## ⚡ দ্রুত শুরু করুন

### ১. প্রয়োজনীয় জিনিস
- Python 3.9+
- Gemini API Key ([ফ্রিতে পান](https://aistudio.google.com/app/apikey))

### ২. ইনস্টল করুন

```bash
# প্রজেক্ট download করুন
git clone https://github.com/Faheeman/market-optimizer.git
cd market-optimizer

# Dependencies ইনস্টল করুন
pip install -r requirements.txt
```

### ৩. API Key সেটআপ করুন

#### Option A: .env ফাইল (সুপারিশকৃত)
```bash
# .env.example কপি করুন
copy .env.example .env

# .env file edit করুন এবং আপনার key দিন
notepad .env
```

`.env` file এ লিখুন:
```env
GEMINI_API_KEY=your_api_key_here
```

#### Option B: config.py এ সরাসরি
`config.py` খুলে এই লাইন edit করুন:
```python
GEMINI_API_KEY = 'your_api_key_here'
```

### ৪. চালু করুন

```bash
# অ্যাপ চালান
python app.py

# Browser এ খুলুন: http://localhost:5000
```

🎉 **Done!** Dashboard খোলা উচিত!

---

## 🌟 বৈশিষ্ট্যসমূহ

### 📊 Demand Forecasting (চাহিদা পূর্বাভাস)
- পরবর্তী ৩০ দিনের বিক্রয় পূর্বাভাস
- Prophet algorithm ব্যবহার করে
- সিজনাল ট্রেন্ড শনাক্তকরণ

### 💰 Price Optimization (মূল্য নির্ধারণ)
- স্বয়ংক্রিয় সর্বোত্তম মূল্য নির্ধারণ
- Price elasticity বিশ্লেষণ
- লাভ সর্বোচ্চকরণ

### 🎯 Product Recommendations (পণ্য সুপারিশ)
- জনপ্রিয় পণ্য চিহ্নিতকরণ
- Stock management পরামর্শ
- Collaborative filtering

### 💬 AI Chatbot (বাংলায়)
- বাংলা ও ইংরেজিতে প্রশ্ন করুন
- Context-aware উত্তর
- Gemini AI powered

### 📥 Export & Reports
- Excel format এ রিপোর্ট
- Forecast summaries
- Product comparison

### 🎨 Modern UI
- বাংলা language support
- Dark/Light mode toggle
- Responsive design
- Glassmorphism effects

---

## 📸 স্ক্রিনশট

### Dashboard (Light Mode)
![Dashboard Light](https://via.placeholder.com/800x400/ffffff/6366f1?text=Dashboard+Light+Mode)

### Dashboard (Dark Mode)
![Dashboard Dark](https://via.placeholder.com/800x400/0f172a/c4b5fd?text=Dashboard+Dark+Mode)

### Bengali Interface
![Bengali UI](https://via.placeholder.com/800x400/ffffff/059669?text=Bengali+Interface)

---

## 🧠 কিভাবে কাজ করে

### Data Flow
```
📊 Data Sources
    ↓
💾 Database (SQLite)
    ↓
🤖 ML Models
    - Prophet (Forecasting)
    - Price Optimization
    - Sentiment Analysis
    ↓
🌐 Flask API
    ↓
💻 Web Dashboard
```

### AI Components

1. **Forecasting Engine**
   - Algorithm: Facebook Prophet
   - Input: Historical sales data
   - Output: 30-day forecast with confidence intervals

2. **Price Optimizer**
   - Algorithm: Reinforcement Learning (PPO)
   - Input: Current price, sales volume
   - Output: Optimal price point

3. **Recommendation System**
   - Algorithm: Popularity-based + Collaborative filtering
   - Input: Transaction history
   - Output: Top 5 products to stock

4. **AI Chat**
   - Model: Google Gemini 2.0
   - Language: Bengali + English
   - Context: Dashboard metrics

---

## 📚 বিস্তারিত গাইড

### বাংলায় সম্পূর্ণ ব্যবহার নির্দেশিকা:
📖 **[USAGE_GUIDE_BANGLA.md](USAGE_GUIDE_BANGLA.md)** পড়ুন

এতে আছে:
- ✅ Step-by-step setup
- ✅ প্রতিটি feature এর ব্যবহার
- ✅ AI কিভাবে উত্তর দেয়
- ✅ সমস্যা সমাধান
- ✅ উদাহরণ সহ

---

## 🛠️ Configuration

### এই ফাইলগুলো edit করুন:

**`config.py`** - Main configuration
```python
GEMINI_API_KEY = 'your_key'
DEFAULT_LANGUAGE = 'bn'  # 'bn' for Bengali, 'en' for English
DEFAULT_THEME = 'light'  # 'light' or 'dark'
PRODUCTS = ['clothing', 'electronics', 'food', 'cosmetics', 'toys']
```

**`.env`** - Environment variables
```env
GEMINI_API_KEY=your_key
PORT=5000
DEBUG=False
```

---

## 🌐 API Endpoints

### Forecasting
```bash
GET /api/forecast?product=clothing
```

### Price Optimization
```bash
GET /api/price?product=electronics
```

### Recommendations
```bash
GET /api/recommend
```

### AI Chat
```bash
POST /api/chat
Body: {"prompt": "আমার দোকানে কি পণ্য রাখব?", "lang": "bn"}
```

### Export
```bash
GET /api/export/excel
GET /api/export/forecast?product=clothing
```

### Product Comparison
```bash
GET /api/compare?products=clothing,electronics
```

---

## 🎯 Use Cases

### Small Retail Store
- Track daily sales
- Forecast Eid demand
- Optimize prices for maximum profit

### E-commerce Business
- Multi-product analysis
- Seasonal trend detection
- Stock alerts

### Market Vendor
- Know what to buy tomorrow
- Understand customer sentiment
- Get AI advice in Bengali

---

## 🏗️ Project Structure

```
Market-optimizer/
├── app.py                    # Main Flask application
├── config.py                 # Configuration (API keys)
├── llm.py                    # AI/LLM integration
├── models.py                 # ML models
├── data_ingestion.py         # Data loading
├── database.py               # Database operations
├── export_utils.py           # Export functionality
├── utils.py                  # Utility functions
├── static/
│   ├── index.html           # Web dashboard
│   ├── main.js              # Frontend logic
│   ├── styles.css           # Styling
│   └── translations.json    # i18n strings
├── data/
│   ├── ecommerce.db         # SQLite database
│   └── sales.csv            # Sample data
├── exports/                 # Generated reports
├── requirements.txt         # Dependencies
├── README.md               # This file
└── USAGE_GUIDE_BANGLA.md   # Bengali guide
```

---

## 🧪 Testing

```bash
# Test API
curl http://localhost:5000/api/forecast?product=clothing

# Test AI Chat
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "আমার দোকানের জন্য পরামর্শ দিন", "lang": "bn"}'
```

---

## 🐛 সমস্যা সমাধান

### API key কাজ করছে না?
```bash
# Validate করুন
python config.py

# Manual test
python -c "from config import get_gemini_api_key; print(get_gemini_api_key())"
```

### Port 5000 busy?
```bash
# অন্য port ব্যবহার করুন
set PORT=5001
python app.py
```

### Dependencies install হচ্ছে না?
```bash
# Virtual environment তৈরি করুন
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - Free to use and modify

---

## 👨‍💻 Author

**AI-First Commerce Team**
- Built for Bangladesh SMEs
- Powered by Google Gemini & Prophet

---

## 🙏 Acknowledgments

- Google Gemini AI
- Facebook Prophet
- Flask & Streamlit
- Bootstrap & Chart.js

---

## 📞 Support

- 📖 **Documentation**: [USAGE_GUIDE_BANGLA.md](USAGE_GUIDE_BANGLA.md)
- 💬 **Issues**: [GitHub Issues](https://github.com/Faheeman/market-optimizer/issues)
- 📧 **Email**: support@afce.bd (example)

---

## 🎉 Start Using Today!

```bash
# Clone
git clone https://github.com/Faheeman/market-optimizer.git

# Install
cd market-optimizer
pip install -r requirements.txt

# Configure
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run
python app.py

# Open browser: http://localhost:5000
```

**আপনার ব্যবসা বাড়ান AI এর শক্তি দিয়ে! 🚀**

---

Made with ❤️ for Bangladesh 🇧🇩
