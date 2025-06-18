# Kraken Trading Bot

This repository contains a simple trading bot that works with the Kraken API.
Provide your API credentials in a `.env` file and run the bot to execute a naive
moving-average strategy. An optional FastAPI server exposes an interactive
dashboard so you can view balances, open orders and trade history in your
browser.


## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your Kraken credentials:
   ```
   KRAKEN_API_KEY=your_key
   KRAKEN_API_SECRET=your_secret
   ```
   If the credentials are missing, the bot runs in demo mode with fake data.

3. Run the trading bot:
   ```bash
   python bot.py
   ```

You can still start the optional API server with:
```bash
uvicorn app.main:app --reload
```
Then open <http://127.0.0.1:8000> in your browser to view the trading dashboard.
The API documentation is still available at <http://127.0.0.1:8000/docs> if needed.

