import os
import time
import base64
import hashlib
import hmac
import urllib.parse
import aiohttp
import json
import asyncio
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import logging
import random

# Configuration du logging
logging.basicConfig(
    filename='trading_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('trading_service')

# Chargement des variables d'environnement
load_dotenv()
API_KEY = os.getenv('KRAKEN_API_KEY')
API_SECRET = os.getenv('KRAKEN_API_SECRET')

# Log pour déboguer les clés API
logger.info(f"API Key présente: {'Oui' if API_KEY else 'Non'}")
logger.info(f"API Secret présente: {'Oui' if API_SECRET else 'Non'}")

# Mode démo si les clés API ne sont pas définies
DEMO_MODE = not (API_KEY and API_SECRET)

class TradingService:
    def __init__(self):
        self.api_url = "https://api.kraken.com"
        self.api_key = API_KEY
        self.api_secret = API_SECRET
        self.session = None
        self.demo_mode = DEMO_MODE
        self._nonce = int(time.time() * 1000000)
        self._last_request_time = {}  # Pour limiter le taux de requêtes
        self._request_interval = 3  # Intervalle minimum entre les requêtes (en secondes)
        
        if self.demo_mode:
            logger.warning("Mode démo activé - données fictives utilisées")
        else:
            logger.info("Mode réel activé - utilisation de l'API Kraken")

    def _get_nonce(self):
        """Génère un nonce unique et croissant basé sur les microsecondes"""
        current_nonce = int(time.time() * 1000000)  # Utiliser les microsecondes
        if current_nonce <= self._nonce:
            current_nonce = self._nonce + 1
        self._nonce = current_nonce
        return str(current_nonce)

    async def _get_session(self):
        """Obtient une session aiohttp ou en crée une nouvelle"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def _wait_for_rate_limit(self, endpoint: str):
        """Attend le temps nécessaire pour respecter la limite de taux"""
        current_time = time.time()
        if endpoint in self._last_request_time:
            time_since_last_request = current_time - self._last_request_time[endpoint]
            if time_since_last_request < self._request_interval:
                await asyncio.sleep(self._request_interval - time_since_last_request)
        self._last_request_time[endpoint] = time.time()

    async def _make_request(self, endpoint: str, data: dict = None, auth: bool = False):
        """Effectue une requête à l'API Kraken avec gestion des limites de taux"""
        if self.demo_mode:
            return await self._get_demo_data(endpoint, data)
            
        await self._wait_for_rate_limit(endpoint)
            
        if data is None:
            data = {}
            
        url = f"{self.api_url}{endpoint}"
        session = await self._get_session()
        
        if auth:
            if not self.api_key or not self.api_secret:
                raise ValueError("API KEY ou API SECRET non défini")
                
            data['nonce'] = self._get_nonce()
            logger.info(f"Envoi requête authentifiée vers {endpoint}")
            
            try:
                # Créer la signature
                post_data = urllib.parse.urlencode(data)
                encoded = (str(data['nonce']) + post_data).encode()
                message = endpoint.encode() + hashlib.sha256(encoded).digest()
                
                decoded_secret = base64.b64decode(self.api_secret)
                signature = base64.b64encode(
                    hmac.new(decoded_secret, message, hashlib.sha512).digest()
                ).decode()
                
                headers = {
                    'API-Key': self.api_key,
                    'API-Sign': signature
                }
                logger.info(f"Signature générée avec succès pour {endpoint}")
            except Exception as e:
                logger.error(f"Erreur lors de la génération de la signature: {str(e)}")
                raise
        else:
            headers = {}
            
        try:
            if auth or data:
                async with session.post(url, headers=headers, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('error') and len(result['error']) > 0:
                            logger.error(f"Erreur API pour {endpoint}: {result['error']}")
                            raise Exception(f"API Error: {result['error']}")
                        logger.info(f"Requête réussie vers {endpoint}")
                        return result.get('result', {})
                    else:
                        text = await response.text()
                        logger.error(f"Erreur HTTP {response.status} pour {endpoint}: {text}")
                        raise Exception(f"API Error: Status {response.status}, {text}")
            else:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('error') and len(result['error']) > 0:
                            logger.error(f"Erreur API pour {endpoint}: {result['error']}")
                            raise Exception(f"API Error: {result['error']}")
                        logger.info(f"Requête réussie vers {endpoint}")
                        return result.get('result', {})
                    else:
                        text = await response.text()
                        logger.error(f"Erreur HTTP {response.status} pour {endpoint}: {text}")
                        raise Exception(f"API Error: Status {response.status}, {text}")
        except Exception as e:
            logger.error(f"Erreur lors de la requête vers {endpoint}: {str(e)}")
            raise
    
    async def _get_demo_data(self, endpoint: str, data: dict = None):
        """Génère des données de démonstration pour le mode sans API"""
        await asyncio.sleep(0.2)  # Simuler un délai réseau
        
        if '/Balance' in endpoint:
            return {
                'ZUSD': 10000.75,
                'XXBT': 0.5,
                'XETH': 5.3,
                'XRP': 2000.0,
                'XLTC': 10.5,
                'DOT': 150.0
            }
        
        elif '/Ticker' in endpoint:
            pair = data.get('pair') if data else endpoint.split('?pair=')[1].split('&')[0]
            base_price = 30000 if 'BTC' in pair else (1800 if 'ETH' in pair else 50)
            current_price = base_price * (1 + random.uniform(-0.02, 0.02))
            
            return {
                pair: {
                    'c': [str(current_price), '10'],  # Prix actuel, volume
                    'b': [str(current_price * 0.999), '5', '10'],  # Meilleur bid
                    'a': [str(current_price * 1.001), '2', '5'],  # Meilleur ask
                    'v': ['1000', '5000'],  # Volume 24h
                    'p': [str(current_price * 0.995), str(current_price * 0.997)],  # Prix moyen
                    't': ['2500', '5000'],  # Nombre de trades
                    'l': [str(current_price * 0.98), str(current_price * 0.97)],  # Plus bas
                    'h': [str(current_price * 1.02), str(current_price * 1.03)],  # Plus haut
                    'o': str(current_price * 0.998)  # Ouverture
                }
            }
        
        elif '/OHLC' in endpoint:
            pair = endpoint.split('?pair=')[1].split('&')[0]
            interval = int(endpoint.split('interval=')[1]) if 'interval=' in endpoint else 60
            base_price = 30000 if 'BTC' in pair else (1800 if 'ETH' in pair else 50)
            
            # Générer des données OHLC fictives
            ohlc_data = []
            now = int(time.time())
            
            # Générer 100 bougies
            for i in range(100):
                candle_time = now - (100 - i) * interval
                open_price = base_price * (1 + random.uniform(-0.05, 0.05))
                close_price = open_price * (1 + random.uniform(-0.02, 0.02))
                high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.01))
                low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.01))
                volume = random.uniform(0.5, 10)
                
                ohlc_data.append([
                    candle_time,
                    str(open_price),
                    str(high_price),
                    str(low_price),
                    str(close_price),
                    str(open_price),  # vwap
                    str(volume),
                    str(int(volume * 10))
                ])
            
            return {pair: ohlc_data}
        
        elif '/OpenOrders' in endpoint:
            # Aucun ordre ouvert
            return {'open': {}}
        
        elif '/TradesHistory' in endpoint:
            # Historique des trades fictifs
            return {'trades': {}}
        
        elif '/AddOrder' in endpoint:
            order_id = f"DEMO-{int(time.time())}"
            return {'txid': [order_id]}
        
        elif '/CancelOrder' in endpoint:
            return {'count': 1}
        
        elif '/market/analysis' in endpoint:
            # Générer une analyse de marché fictive
            return {
                'indicators': {
                    'rsi': random.uniform(30, 70),
                    'macd': {
                        'macd': random.uniform(-100, 100),
                        'signal': random.uniform(-100, 100),
                        'histogram': random.uniform(-50, 50)
                    },
                    'bollinger_bands': {
                        'upper': random.uniform(31000, 32000),
                        'middle': random.uniform(30000, 31000),
                        'lower': random.uniform(29000, 30000)
                    }
                },
                'trend': random.choice(['bullish', 'bearish', 'neutral']),
                'confidence': random.uniform(0, 1),
                'recommendation': random.choice(['buy', 'sell', 'hold']),
                'support_levels': [29000, 28500, 28000],
                'resistance_levels': [31000, 31500, 32000]
            }
        
        else:
            return {}  # Réponse par défaut

    async def get_balance(self) -> Dict[str, Any]:
        """Récupère le solde du compte"""
        try:
            result = await self._make_request('/0/private/Balance', auth=True)
            # Convertir les strings en float pour le front-end
            balance = {k: float(v) for k, v in result.items()}
            return balance
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            raise

    async def get_ticker(self, pair: str) -> Dict[str, Any]:
        """Récupère les données du ticker pour une paire"""
        try:
            result = await self._make_request(f'/0/public/Ticker?pair={pair}')
            return result.get(pair, {})
        except Exception as e:
            logger.error(f"Error getting ticker for {pair}: {str(e)}")
            raise

    async def get_ohlc(self, pair: str, interval: int = 60) -> List[List[float]]:
        """Récupère les données OHLC pour une paire de trading"""
        try:
            endpoint = f"/0/public/OHLC?pair={pair}&interval={interval}"
            result = await self._make_request(endpoint)
            
            # Kraken renvoie les données OHLC dans un format spécial
            # La clé est soit le nom de la paire, soit un nom modifié (ex: XXBTZUSD pour BTCUSD)
            pair_key = None
            for key in result.keys():
                if key != 'last':  # 'last' est un timestamp, pas les données OHLC
                    pair_key = key
                    break
                    
            if not pair_key or not result[pair_key]:
                logger.error(f"Pas de données OHLC disponibles pour {pair}")
                return []
                
            # Convertir les données en format utilisable
            ohlc_data = []
            for candle in result[pair_key]:
                # Format Kraken: [time, open, high, low, close, vwap, volume, count]
                ohlc_data.append([
                    float(candle[0]),  # timestamp
                    float(candle[1]),  # open
                    float(candle[2]),  # high
                    float(candle[3]),  # low
                    float(candle[4]),  # close
                    float(candle[5]),  # vwap
                    float(candle[6]),  # volume
                    float(candle[7])   # count
                ])
            
            return ohlc_data
            
        except Exception as e:
            logger.error(f"Error getting OHLC data for {pair}: {str(e)}")
            raise

    async def place_order(self, pair: str, order_type: str, order_ordertype: str, volume: float, price: float = None) -> Dict[str, Any]:
        """Place un ordre"""
        try:
            data = {
                'pair': pair,
                'type': order_type,  # buy or sell
                'ordertype': order_ordertype,  # market or limit
                'volume': str(volume),
            }
            
            if order_ordertype == 'limit' and price is not None:
                data['price'] = str(price)
                
            # Options supplémentaires pour la gestion des risques
            data['oflags'] = 'fcib'  # Fill-or-Kill
                
            result = await self._make_request('/0/private/AddOrder', data=data, auth=True)
            return result
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            raise

    async def get_open_orders(self) -> Dict[str, Any]:
        """Récupère les ordres ouverts"""
        try:
            result = await self._make_request('/0/private/OpenOrders', auth=True)
            return result.get('open', {})
        except Exception as e:
            logger.error(f"Error getting open orders: {str(e)}")
            raise

    async def get_trade_history(self) -> Dict[str, Any]:
        """Récupère l'historique des trades"""
        try:
            data = {
                'trades': True,
                'start': int(time.time() - 7 * 24 * 3600)  # 7 derniers jours
            }
            result = await self._make_request('/0/private/TradesHistory', data=data, auth=True)
            return result.get('trades', {})
        except Exception as e:
            logger.error(f"Error getting trade history: {str(e)}")
            raise

    async def cancel_order(self, orderid: str) -> Dict[str, Any]:
        """Annule un ordre"""
        try:
            data = {'txid': orderid}
            result = await self._make_request('/0/private/CancelOrder', data=data, auth=True)
            return result
        except Exception as e:
            logger.error(f"Error cancelling order {orderid}: {str(e)}")
            raise

    async def analyze_market(self, pair: str) -> Dict[str, Any]:
        """Analyse le marché pour une paire de trading"""
        try:
            # Récupérer les données OHLC
            ohlc_data = await self.get_ohlc(pair)
            if not ohlc_data:
                raise ValueError("Pas de données OHLC disponibles")

            # Convertir en DataFrame pandas
            if not isinstance(ohlc_data, list) or len(ohlc_data) == 0:
                raise ValueError("Données OHLC invalides")
                
            df = pd.DataFrame(ohlc_data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count'
            ])
            
            # Convertir les colonnes en nombres et gérer les valeurs manquantes
            for col in ['open', 'high', 'low', 'close', 'vwap', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df.dropna()  # Supprimer les lignes avec des valeurs manquantes
            
            if len(df) == 0:
                raise ValueError("Pas assez de données valides pour l'analyse")

            # Calculer les indicateurs techniques
            # Vérifier qu'il y a assez de données pour les calculs
            min_periods = max(50, 26)  # Le plus grand nombre de périodes nécessaires
            if len(df) < min_periods:
                raise ValueError(f"Pas assez de données pour l'analyse (minimum {min_periods} périodes requises)")

            # RSI avec gestion des divisions par zéro
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=14).mean()
            rs = gain / loss.replace(0, float('inf'))  # Éviter division par zéro
            rsi = 100 - (100 / (1 + rs))

            # MACD avec périodes minimales
            exp1 = df['close'].ewm(span=12, min_periods=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, min_periods=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, min_periods=9, adjust=False).mean()
            histogram = macd - signal

            # Bandes de Bollinger avec périodes minimales
            sma = df['close'].rolling(window=20, min_periods=20).mean()
            std = df['close'].rolling(window=20, min_periods=20).std()
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)

            # Niveaux de support et résistance avec vérification de la taille des données
            lookback = min(50, len(df))
            recent_lows = df['low'].tail(lookback).nsmallest(3).mean()
            recent_highs = df['high'].tail(lookback).nlargest(3).mean()

            # Déterminer la tendance avec gestion des erreurs
            try:
                short_ma = df['close'].rolling(window=10, min_periods=10).mean().iloc[-1]
                long_ma = df['close'].rolling(window=30, min_periods=30).mean().iloc[-1]
                current_price = df['close'].iloc[-1]
                
                if pd.isna(short_ma) or pd.isna(long_ma) or pd.isna(current_price):
                    raise ValueError("Données manquantes pour l'analyse de tendance")

                if short_ma > long_ma and current_price > upper_band.iloc[-1]:
                    trend = "bullish"
                    confidence = min((short_ma / long_ma - 1) * 5, 1)
                    recommendation = "sell" if rsi.iloc[-1] > 70 else "hold"
                elif short_ma < long_ma and current_price < lower_band.iloc[-1]:
                    trend = "bearish"
                    confidence = min((1 - short_ma / long_ma) * 5, 1)
                    recommendation = "buy" if rsi.iloc[-1] < 30 else "hold"
                else:
                    trend = "neutral"
                    confidence = 0.5
                    recommendation = "hold"
            except Exception as e:
                logger.warning(f"Erreur lors de l'analyse de tendance: {str(e)}")
                trend = "neutral"
                confidence = 0.5
                recommendation = "hold"

            return {
                "indicators": {
                    "rsi": float(rsi.iloc[-1]),
                    "macd": {
                        "macd": float(macd.iloc[-1]),
                        "signal": float(signal.iloc[-1]),
                        "histogram": float(histogram.iloc[-1])
                    },
                    "bollinger_bands": {
                        "upper": float(upper_band.iloc[-1]),
                        "middle": float(sma.iloc[-1]),
                        "lower": float(lower_band.iloc[-1])
                    }
                },
                "trend": trend,
                "confidence": float(confidence),
                "recommendation": recommendation,
                "support_levels": [float(recent_lows)],
                "resistance_levels": [float(recent_highs)]
            }
        except Exception as e:
            logger.error(f"Error analyzing market for {pair}: {str(e)}")
            raise

    async def auto_trade(self, pair: str) -> Dict[str, Any]:
        """Exécute un trade automatique basé sur l'analyse du marché"""
        try:
            # Obtenir l'analyse du marché
            analysis = await self.analyze_market(pair)
            
            # Décider si on doit trader
            confidence = analysis['confidence']
            trend = analysis['trend']
            
            # Récupérer le solde du compte
            balance = await self.get_balance()
            
            # Extraire la devise de base et de quote de la paire
            # Par exemple, pour BTCEUR, base = BTC, quote = EUR
            if 'USD' in pair:
                base = pair.replace('USD', '')
                quote = 'ZUSD'  # Kraken utilise ZUSD pour USD
            else:
                # Pour d'autres paires, il faudrait adapter cette logique
                base = pair[:3]
                quote = pair[3:]
            
            # Normaliser les noms des devises selon les conventions Kraken
            if base == 'BTC':
                base = 'XXBT'
            elif base == 'ETH':
                base = 'XETH'
            
            # Vérifier si on a assez de fonds
            base_balance = balance.get(base, 0)
            quote_balance = balance.get(quote, 0)
            
            # Si la confiance est suffisante, placer un ordre
            if confidence >= 70:
                if trend == 'bullish' and quote_balance > 10:  # Acheter si bullish
                    # Calculer le montant à acheter (10% du solde disponible)
                    volume = 0.1 * quote_balance / analysis['current_price']
                    
                    # Placer l'ordre d'achat
                    order_result = await self.place_order(
                        pair=pair,
                        order_type='buy',
                        order_ordertype='market',
                        volume=volume
                    )
                    
                    return {
                        'action': 'buy',
                        'pair': pair,
                        'volume': volume,
                        'price': analysis['current_price'],
                        'confidence': confidence,
                        'order_id': order_result.get('txid', [None])[0]
                    }
                    
                elif trend == 'bearish' and base_balance > 0:  # Vendre si bearish
                    # Calculer le montant à vendre (10% du solde disponible)
                    volume = 0.1 * base_balance
                    
                    # Placer l'ordre de vente
                    order_result = await self.place_order(
                        pair=pair,
                        order_type='sell',
                        order_ordertype='market',
                        volume=volume
                    )
                    
                    return {
                        'action': 'sell',
                        'pair': pair,
                        'volume': volume,
                        'price': analysis['current_price'],
                        'confidence': confidence,
                        'order_id': order_result.get('txid', [None])[0]
                    }
            
            # Si la confiance n'est pas suffisante, ne pas trader
            return {
                'action': 'hold',
                'pair': pair,
                'confidence': confidence,
                'reason': 'Confidence too low or insufficient balance'
            }
            
        except Exception as e:
            logger.error(f"Error in auto trade for {pair}: {str(e)}")
            raise
            
    async def close(self):
        """Ferme la session aiohttp"""
        if self.session and not self.session.closed:
            await self.session.close() 