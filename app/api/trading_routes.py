from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..services.trading_service import TradingService

router = APIRouter()
service = TradingService()

class OrderRequest(BaseModel):
    pair: str
    order_type: str
    order_ordertype: str
    volume: float
    price: Optional[float] = None

@router.get('/balance')
async def balance():
    try:
        return await service.get_balance()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get('/ticker/{pair}')
async def ticker(pair: str):
    try:
        return await service.get_ticker(pair)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get('/ohlc/{pair}')
async def ohlc(pair: str, interval: int = 60):
    try:
        return await service.get_ohlc(pair, interval)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.post('/order')
async def order(req: OrderRequest):
    try:
        return await service.place_order(req.pair, req.order_type, req.order_ordertype, req.volume, req.price)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get('/orders')
async def open_orders():
    try:
        return await service.get_open_orders()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get('/history')
async def history():
    try:
        return await service.get_trade_history()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

