import asyncio
from typing import List

from app.services.trading_service import TradingService


async def moving_average_strategy(
    pair: str = "XXBTZUSD",
    interval: int = 1,
    short_window: int = 5,
    long_window: int = 20,
    risk: float = 0.1,
) -> None:
    """Run a simple moving-average crossover strategy."""
    service = TradingService()
    position = 0
    base_asset = pair[:4]
    try:
        while True:
            candles = await service.get_ohlc(pair, interval)
            closes: List[float] = [float(c[4]) for c in candles]
            if len(closes) < long_window:
                await asyncio.sleep(interval * 60)
                continue

            short_ma = sum(closes[-short_window:]) / short_window
            long_ma = sum(closes[-long_window:]) / long_window

            ticker = await service.get_ticker(pair)
            price = float(ticker.get("c", [0])[0])
            balance = await service.get_balance_asset(base_asset)
            volume = balance * risk
            if volume <= 0:
                volume = 0.001

            print(
                f"Price: {price} SMA{short_window}: {short_ma} SMA{long_window}: {long_ma}"
            )

            if short_ma > long_ma and position <= 0:
                print("Buying...")
                resp = await service.place_order(pair, "buy", "market", volume)
                position = 1
                print("Order response:", resp)
            elif short_ma < long_ma and position >= 0:
                print("Selling...")
                resp = await service.place_order(pair, "sell", "market", volume)
                position = -1
                print("Order response:", resp)

            await asyncio.sleep(interval * 60)
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(moving_average_strategy())
