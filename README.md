# 🧠 Competitor Intelligence Dashboard

An AI-powered Streamlit app to track, summarize, and visualize changelog updates from competitor websites.

## 🚀 Features

- 🔍 **Smart Web Scraping**: Automatically extracts changelog updates from multiple platforms.
- 🤖 **AI Summaries (GPT-4o)**: Converts raw updates into bullet-point summaries and strategic insights.
- 🛑 **Fallback Mechanism**: If scraping fails, GPT auto-generates realistic changelog content.
- 📈 **Momentum Analysis**: Computes impact scores and confidence levels for each competitor.
- 🧑‍💼 **Persona Views**: Filter summaries for PMs, Sales, and Design teams.
- ➕ **Add Competitors**: Dynamically add new companies and analyze their changelogs.
- 🔐 **Secrets Management**: Secure OpenAI API key via \`st.secrets\`.
- 🌐 **Deployed on Streamlit Cloud**

---

## 🧩 Tech Stack

- Python 3.10+
- Streamlit
- BeautifulSoup4
- LXML
- Playwright (for dynamic scraping)
- OpenAI GPT-4o
- Plotly for graphs

---

## 🛠️ Setup Instructions

### 1. 🔑 Add OpenAI API Key

Create a `.streamlit/secrets.toml` file or use the Streamlit Cloud Secrets tab:

```toml
OPENAI_API_KEY = "your-openai-key"
```

### 2. 📦 Install Requirements

```
pip install -r requirements.txt
```

### 3. ▶️ Run Locally

```
streamlit run app.py
```

## 🏗 Project Structure

```
├── app.py                # Main Streamlit dashboard
├── config.py             # Competitor list config
├── scraper.py            # Handles changelog scraping
├── summarizer.py         # GPT-4o summary generation
├── dashboard.py          # UI helper functions (cards, charts)
├── database.py           # DB management (optional)
├── notifier.py           # Slack notifications (optional)
├── requirements.txt
└── .streamlit/secrets.toml
```
## 📦 Optional Features
If you want to enable advanced features:

PostgreSQL Database → Configure DATABASE_URL in .env or secrets.toml

Slack Alerts → Add SLACK_WEBHOOK_URL in secrets.toml

# 👤 Created By
Dachepally Akhila


This is my first PR
