import os
import time
import base64
import hashlib
import hmac
import urllib.parse
import aiohttp
import asyncio
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('KRAKEN_API_KEY')
API_SECRET = os.getenv('KRAKEN_API_SECRET')

class TradingService:
    """Minimal async client for Kraken REST API with demo mode."""

    def __init__(self) -> None:
        self.api_url = "https://api.kraken.com"
        self.session: aiohttp.ClientSession | None = None
        self.api_key = API_KEY
        self.api_secret = API_SECRET
        self.demo_mode = not (self.api_key and self.api_secret)
        self.nonce = int(time.time() * 1000)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    def _get_nonce(self) -> str:
        self.nonce += 1
        return str(self.nonce)

    async def _make_request(self, endpoint: str, data: Dict[str, Any] | None = None, auth: bool = False) -> Dict[str, Any]:
        if self.demo_mode:
            return await self._demo_response(endpoint)

        url = f"{self.api_url}{endpoint}"
        session = await self._get_session()
        headers = {}
        if auth:
            if not self.api_key or not self.api_secret:
                raise RuntimeError("API credentials missing")
            data = data or {}
            data['nonce'] = self._get_nonce()
            post_data = urllib.parse.urlencode(data)
            encoded = (data['nonce'] + post_data).encode()
            message = endpoint.encode() + hashlib.sha256(encoded).digest()
            mac = hmac.new(base64.b64decode(self.api_secret), message, hashlib.sha512)
            sig = base64.b64encode(mac.digest()).decode()
            headers = {'API-Key': self.api_key, 'API-Sign': sig}
            async with session.post(url, headers=headers, data=data) as resp:
                return await resp.json()
        else:
            async with session.get(url) as resp:
                return await resp.json()

    async def _demo_response(self, endpoint: str) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        if endpoint.endswith('/Balance'):
            return {
                'ZUSD': '1000.0',
                'XXBT': '0.5',
            }
        if endpoint.startswith('/0/public/Ticker'):
            pair = endpoint.split('pair=')[1]
            return {pair: {'c': ['50000.0', '1']}}
        if endpoint.startswith('/0/public/OHLC'):
            pair = endpoint.split('pair=')[1].split('&')[0]
            return {pair: [[time.time(), '1', '1', '1', '1', '1', '1', '1'] for _ in range(2)]}
        if endpoint.endswith('/OpenOrders'):
            return {'open': {}}
        if endpoint.endswith('/TradesHistory'):
            return {'trades': {}}
        if endpoint.endswith('/AddOrder'):
            return {'txid': ['DEMO']}
        if endpoint.endswith('/CancelOrder'):
            return {'count': 1}
        return {}

    async def get_balance(self) -> Dict[str, Any]:
        data = await self._make_request('/0/private/Balance', auth=True)
        return data

    async def get_balance_asset(self, asset: str) -> float:
        """Return the available balance for a specific asset."""
        balances = await self.get_balance()
        try:
            return float(balances.get(asset, 0.0))
        except (TypeError, ValueError):
            return 0.0


    async def get_ticker(self, pair: str) -> Dict[str, Any]:
        data = await self._make_request(f'/0/public/Ticker?pair={pair}')
        return data.get(pair, {})

    async def get_ohlc(self, pair: str, interval: int = 60) -> List[List[Any]]:
        data = await self._make_request(f'/0/public/OHLC?pair={pair}&interval={interval}')
        return data.get(pair, [])

    async def place_order(self, pair: str, order_type: str, order_ordertype: str, volume: float, price: float | None = None) -> Dict[str, Any]:
        params = {
            'pair': pair,
            'type': order_type,
            'ordertype': order_ordertype,
            'volume': str(volume),
        }
        if price is not None:
            params['price'] = str(price)
        return await self._make_request('/0/private/AddOrder', data=params, auth=True)

    async def get_open_orders(self) -> Dict[str, Any]:
        data = await self._make_request('/0/private/OpenOrders', auth=True)
        return data.get('open', {})

    async def get_trade_history(self) -> Dict[str, Any]:
        data = await self._make_request('/0/private/TradesHistory', auth=True)
        return data.get('trades', {})

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        params = {'txid': order_id}
        return await self._make_request('/0/private/CancelOrder', data=params, auth=True)

    async def close(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()

