from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
import uvicorn
from dotenv import load_dotenv
import os
from pathlib import Path
from app.api.trading_routes import router as trading_router

# Chargement des variables d'environnement
load_dotenv()

# Création de l'application FastAPI
app = FastAPI(title="Trading Bot API")

# Configuration des dossiers
BASE_DIR = Path(__file__).resolve().parent

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À modifier en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes de trading
app.include_router(trading_router, prefix="/api", tags=["trading"])

# Montage des routes statiques pour l'interface web
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def index():
    """Renvoie la page d'accueil de l'interface web"""
    html_file = BASE_DIR / "templates" / "index.html"
    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 