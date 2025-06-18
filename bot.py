import asyncio
from typing import List

from app.services.trading_service import TradingService


async def moving_average_strategy(
    pair: str = "XXBTZUSD", interval: int = 1, volume: float = 0.001, window: int = 5
) -> None:
    """Run a naive moving-average strategy indefinitely."""
    service = TradingService()
    try:
        while True:
            candles = await service.get_ohlc(pair, interval)
            closes: List[float] = [float(c[4]) for c in candles[-window:]]
            average = sum(closes) / len(closes)
            ticker = await service.get_ticker(pair)
            price = float(ticker.get("c", [0])[0])
            print(f"Price: {price} SMA{window}: {average}")

            if price > average * 1.01:
                print("Buying...")
                resp = await service.place_order(pair, "buy", "market", volume)
                print("Order response:", resp)
            elif price < average * 0.99:
                print("Selling...")
                resp = await service.place_order(pair, "sell", "market", volume)
                print("Order response:", resp)

            await asyncio.sleep(interval * 60)
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(moving_average_strategy())
