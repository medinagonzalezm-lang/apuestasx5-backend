from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import datetime
from typing import List
import requests
import os

app = FastAPI()

# ======================
# CORS
# ======================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
# CONFIG API REAL (API-FOOTBALL)
# ======================================================
API_KEY = os.getenv("FOOTBALL_API_KEY")  # 🔐 AQUÍ SE LEE LA KEY
API_URL = "https://v3.football.api-sports.io/fixtures"
HEADERS = {"x-apisports-key": API_KEY} if API_KEY else None


# ======================================================
# 1️⃣ PARTIDOS DEL DÍA
# ======================================================
@app.get("/partidos")
def partidos():
    today = datetime.date.today().strftime("%Y-%m-%d")

    # 🔁 MODO DEMO (sin API KEY)
    if not API_KEY:
        return [
            {
                "home": "Real Madrid",
                "away": "Barcelona",
                "league": "LaLiga",
                "home_goals_avg": 2.1,
                "away_goals_avg": 1.9,
                "home_concede_avg": 1.0,
                "away_concede_avg": 1.1,
            },
            {
                "home": "Bayern",
                "away": "Dortmund",
                "league": "Bundesliga",
                "home_goals_avg": 2.4,
                "away_goals_avg": 2.0,
                "home_concede_avg": 1.2,
                "away_concede_avg": 1.3,
            },
            {
                "home": "Arsenal",
                "away": "Tottenham",
                "league": "Premier League",
                "home_goals_avg": 1.8,
                "away_goals_avg": 1.7,
                "home_concede_avg": 1.1,
                "away_concede_avg": 1.2,
            },
        ]

    # 🔴 MODO REAL (con API KEY)
    params = {
        "date": today,
        "status": "NS"
    }

    r = requests.get(API_URL, headers=HEADERS, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    partidos = []

    for f in data.get("response", []):
        partidos.append({
            "home": f["teams"]["home"]["name"],
            "away": f["teams"]["away"]["name"],
            "league": f["league"]["name"],
            # ⚠️ Placeholder realista (la media real se puede calcular luego)
            "home_goals_avg": 1.5,
            "away_goals_avg": 1.3,
            "home_concede_avg": 1.2,
            "away_concede_avg": 1.3,
        })

    return partidos


# ======================================================
# 2️⃣ ANÁLISIS ESTADÍSTICO
# ======================================================
def analizar_partido(p):
    expected_goals = (
        p["home_goals_avg"]
        + p["away_goals_avg"]
        + p["home_concede_avg"]
        + p["away_concede_avg"]
    ) / 2

    prob_over_1_5 = 0.75 if expected_goals >= 2 else 0.45
    prob_btts = 0.70 if p["home_goals_avg"] > 1 and p["away_goals_avg"] > 1 else 0.35
    prob_1x_2x = 0.65 if p["home_goals_avg"] >= p["away_goals_avg"] else 0.55

    return {
        **p,
        "prob_over_1_5": round(prob_over_1_5, 2),
        "prob_btts": round(prob_btts, 2),
        "prob_1x_2x": round(prob_1x_2x, 2),
        "prob_combinada": round(max(prob_over_1_5, prob_btts, prob_1x_2x), 2),
    }


def top3(partidos: List[dict], key: str):
    return sorted(partidos, key=lambda x: x[key], reverse=True)[:3]


# ======================================================
# 3️⃣ ENDPOINT PRINCIPAL PARA KIVY
# ======================================================
@app.get("/matches")
def matches():
    partidos_data = partidos()
    analizados = [analizar_partido(p) for p in partidos_data]

    return {
        "over_1_5": top3(analizados, "prob_over_1_5"),
        "uno_x_dos_x": top3(analizados, "prob_1x_2x"),
        "btts": top3(analizados, "prob_btts"),
        "combinada": top3(analizados, "prob_combinada"),
        "fecha": str(datetime.date.today()),
    }
