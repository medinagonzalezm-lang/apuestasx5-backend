from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import List
import datetime
import os  # Para leer la API key de variable de entorno

app = FastAPI()

# Permitir que la app Kivy se conecte
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Leer la API key de variable de entorno
API_KEY = os.environ.get("API_KEY")  # <--- Asegúrate de configurar esto en Render
API_URL = "https://api-de-partidos-reales.com/matches"  # Tu API real

# Función para analizar partido con probabilidades Kelly y demás
def analizar_partido(partido):
    # Ejemplo de análisis estadístico simplificado
    goles_home = partido.get("home_goals", 1)
    goles_away = partido.get("away_goals", 1)
    
    # Over 1.5 goles
    over_1_5 = min((goles_home + goles_away) / 5, 0.95)

    # 1X / 2X (probabilidad ajustada por diferencia de goles)
    oneX_2X = 0.5 + (goles_home - goles_away) * 0.05
    oneX_2X = max(min(oneX_2X, 0.9), 0.1)

    # Ambos marcan
    btts = 0.6 if goles_home > 0 and goles_away > 0 else 0.3

    # Combinada: la mayor probabilidad
    combinacion = max(over_1_5, oneX_2X, btts)

    return {
        **partido,
        "prob_over_1_5": round(over_1_5, 2),
        "prob_1X_2X": round(oneX_2X, 2),
        "prob_btts": round(btts, 2),
        "prob_combinacion": round(combinacion, 2)
    }

# Seleccionar top 3 según clave de probabilidad
def seleccionar_top(partidos: List[dict], key: str):
    return sorted(partidos, key=lambda x: x[key], reverse=True)[:3]

@app.get("/matches")
def matches():
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}

    try:
        respuesta = requests.get(API_URL, headers=headers, timeout=10)
        respuesta.raise_for_status()
        partidos = respuesta.json()  # Lista de partidos
    except Exception as e:
        return {"error": "No se pudieron obtener los partidos de la API", "detalle": str(e)}

    # Analizar partidos
    partidos_analizados = [analizar_partido(p) for p in partidos]

    return {
        "over_1_5": seleccionar_top(partidos_analizados, "prob_over_1_5"),
        "1X_2X": seleccionar_top(partidos_analizados, "prob_1X_2X"),
        "btts": seleccionar_top(partidos_analizados, "prob_btts"),
        "combinacion": seleccionar_top(partidos_analizados, "prob_combinacion"),
        "fecha": str(datetime.date.today())
    }
