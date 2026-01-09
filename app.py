from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import List
import datetime
import os

app = FastAPI()

# Permitir que la app Kivy se conecte
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Poner tu API real aquí
API_URL = "https://tu-api-real.com/matches"  # <--- Cambiar por tu API real
API_KEY = os.getenv("API_KEY")  # Si tu API necesita key, poner en entorno de Render

# Función para analizar partidos y calcular probabilidades
def analizar_partido(partido):
    """
    Analiza un partido y devuelve probabilidades para:
    - over 1.5 goles
    - 1X/2X
    - ambos marcan (BTT)
    - combinada (la más segura)
    """
    # Extraer datos básicos
    goles_home = partido.get("goals_home", 1)
    goles_away = partido.get("goals_away", 1)

    # Probabilidad Over 1.5 goles
    over_1_5 = min((goles_home + goles_away) / 5, 0.95)

    # Probabilidad 1X/2X simplificada
    oneX_2X = 0.5 + (goles_home - goles_away) * 0.05
    oneX_2X = max(min(oneX_2X, 0.9), 0.1)

    # Probabilidad ambos marcan (BTT)
    btts = 0.6 if goles_home > 0 and goles_away > 0 else 0.3

    # Probabilidad combinada: la que más seguridad da
    combinacion = max(over_1_5, oneX_2X, btts)

    return {
        **partido,
        "prob_over_1_5": round(over_1_5, 2),
        "prob_1X_2X": round(oneX_2X, 2),
        "prob_btts": round(btts, 2),
        "prob_combinacion": round(combinacion, 2)
    }

# Selecciona los top 3 de cada categoría
def seleccionar_top(partidos: List[dict], key: str):
    return sorted(partidos, key=lambda x: x[key], reverse=True)[:3]

@app.get("/matches")
def matches():
    # Llamada a la API real
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
    try:
        respuesta = requests.get(API_URL, headers=headers, timeout=10)
        respuesta.raise_for_status()
        partidos = respuesta.json()  # Lista de partidos diarios reales
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
