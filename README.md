# Trading Bot API

This repository contains a minimal example of a trading bot using the Kraken API.
It exposes a small REST API built with FastAPI.

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
   If the credentials are missing, the service runs in demo mode with fake data.

3. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

Open <http://127.0.0.1:8000/docs> in your browser to explore the API.

## Example usage

With the server running you can query endpoints using any HTTP client. For instance, to check your balance:

```bash
curl http://127.0.0.1:8000/api/balance
```


