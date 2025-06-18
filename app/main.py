from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.trading_routes import router as trading_router

app = FastAPI(title="Trading Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trading_router, prefix="/api")

@app.get("/health")
async def health():
    return {"status": "ok"}

