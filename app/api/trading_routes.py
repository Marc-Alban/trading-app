from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, List
import json
from ..services.trading_service import TradingService
from pydantic import BaseModel
import asyncio

router = APIRouter()
trading_service = TradingService()

# Modèles de données
class OrderRequest(BaseModel):
    pair: str
    order_type: str  # buy or sell
    order_ordertype: str  # market or limit
    volume: float
    price: float = None

class TradeRequest(BaseModel):
    pair: str

@router.get("/balance")
async def get_balance():
    """Récupère le solde du compte"""
    try:
        balance = await trading_service.get_balance()
        return {"status": "success", "data": balance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération du solde: {str(e)}")

@router.get("/ticker/{pair}")
async def get_ticker(pair: str):
    """Récupère les données de ticker pour une paire de trading"""
    try:
        ticker = await trading_service.get_ticker(pair)
        return {"status": "success", "data": ticker}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération du ticker: {str(e)}")

@router.get("/ohlc/{pair}")
async def get_ohlc(pair: str, interval: int = 60):
    """Récupère les données OHLC pour une paire de trading"""
    try:
        ohlc = await trading_service.get_ohlc(pair, interval)
        return {"status": "success", "data": ohlc}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données OHLC: {str(e)}")

@router.post("/order")
async def place_order(order: OrderRequest):
    """Place un nouvel ordre de trading"""
    try:
        result = await trading_service.place_order(
            pair=order.pair,
            order_type=order.order_type,
            order_ordertype=order.order_ordertype,
            volume=order.volume,
            price=order.price
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du placement de l'ordre: {str(e)}")

@router.get("/orders")
async def get_orders():
    """Récupère les ordres ouverts"""
    try:
        orders = await trading_service.get_open_orders()
        return {"status": "success", "data": orders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des ordres: {str(e)}")

@router.get("/history")
async def get_history():
    """Récupère l'historique des trades"""
    try:
        history = await trading_service.get_trade_history()
        return {"status": "success", "data": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de l'historique: {str(e)}")

@router.post("/trade/auto")
async def auto_trade(request: TradeRequest):
    """Exécute un trade automatique basé sur l'analyse du marché"""
    try:
        result = await trading_service.auto_trade(request.pair)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du trading automatique: {str(e)}")

@router.post("/trade/auto/background")
async def auto_trade_background(request: TradeRequest, background_tasks: BackgroundTasks):
    """Programme un trade automatique en arrière-plan"""
    try:
        # Ajouter la tâche à exécuter en arrière-plan
        background_tasks.add_task(trading_service.auto_trade, request.pair)
        return {"status": "success", "message": f"Trading automatique programmé pour {request.pair}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la programmation du trading: {str(e)}")

@router.get("/market/analysis/{pair}")
async def get_market_analysis(pair: str):
    """Récupère l'analyse du marché pour une paire de trading"""
    try:
        analysis = await trading_service.analyze_market(pair)
        return {"status": "success", "data": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse du marché: {str(e)}")

@router.delete("/order/{orderid}")
async def cancel_order(orderid: str):
    """Annule un ordre ouvert"""
    try:
        result = await trading_service.cancel_order(orderid)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'annulation de l'ordre: {str(e)}") 