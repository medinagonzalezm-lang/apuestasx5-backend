from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI(
    title="Pronósticos deportivos (IA)",
    description="Backend oficial de Pronósticos deportivos (IA)",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def cargar_tips():
    with open("tips.json", "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/")
def root():
    return {"status": "ok", "app": "Pronósticos deportivos (IA)"}

@app.get("/tip/{tip_id}")
def obtener_tip(tip_id: str):
    tips = cargar_tips()
    if tip_id not in tips:
        return {"error": "Tip no encontrado"}
    return tips[tip_id]
