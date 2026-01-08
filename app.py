from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import datetime
from typing import List

app = FastAPI()

# CORS para permitir conexión desde la app Kivy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
# 1️⃣ ENDPOINT BASE: PARTIDOS EN CRUDO
# (aquí luego conectas la API REAL de fútbol)
# ======================================================
@app.get("/partidos")
def partidos():
    # ⚠️ Datos de ejemplo (ESTO FUNCIONA)
    # Cuando conectes API real, aquí va el requests.get(...)
    return [
        {"home": "Real Madrid", "away": "Barcelona", "goles_home": 2, "goles_away": 1},
        {"home": "Betis", "away": "Sevilla", "goles_home": 1, "goles_away": 1},
        {"home": "Villarreal", "away": "Valencia", "goles_home": 2, "goles_away": 0},
        {"home": "Athletic", "away": "Real Sociedad", "goles_home": 3, "goles_away": 2},
        {"home": "Osasuna", "away": "Celta", "goles_home": 1, "goles_away": 0},
    ]


# ======================================================
# 2️⃣ ANÁLISIS ESTADÍSTICO (tipo Kelly simplificado)
# ======================================================
def analizar_partido(p):
    goles_totales = p["goles_home"] + p["goles_away"]

    prob_over_1_5 = min(goles_totales / 4, 0.95)
    prob_1x_2x = 0.55 if p["goles_home"] >= p["goles_away"] else 0.45
    prob_btts = 0.65 if p["goles_home"] > 0 and p["goles_away"] > 0 else 0.3

    return {
        **p,
        "prob_over_1_5": round(prob_over_1_5, 2),
        "prob_1x_2x": round(prob_1x_2x, 2),
        "prob_btts": round(prob_btts, 2),
        "prob_combinada": round(max(prob_over_1_5, prob_1x_2x, prob_btts), 2),
    }


def top3(partidos: List[dict], key: str):
    return sorted(partidos, key=lambda x: x[key], reverse=True)[:3]


# ======================================================
# 3️⃣ ENDPOINT PRINCIPAL PARA LA APP
# ======================================================
@app.get("/matches")
def matches():
    try:
        r = requests.get("https://apuestasx5-backend.onrender.com/partidos", timeout=10)
        r.raise_for_status()
        partidos = r.json()
    except Exception as e:
        return {"error": str(e)}

    analizados = [analizar_partido(p) for p in partidos]

    return {
        "over_1_5": top3(analizados, "prob_over_1_5"),
        "uno_x_dos_x": top3(analizados, "prob_1x_2x"),
        "btts": top3(analizados, "prob_btts"),
        "combinada": top3(analizados, "prob_combinada"),
        "fecha": str(datetime.date.today()),
    }

