from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import List
import datetime

app = FastAPI()

# Permitir que la app Kivy se conecte
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_URL = "https://apuestasx5-backend.onrender.com/matches"  # tu API real

# Función para calcular probabilidades simuladas tipo Kelly (simplificado)
def analizar_partido(partido):
    # ejemplo de análisis estadístico simplificado:
    goles_totales = partido.get("goles_home", 1) + partido.get("goles_away", 1)
    over_1_5 = min(goles_totales / 5, 0.95)
    oneX_2X = 0.5 + (partido.get("goles_home", 0) - partido.get("goles_away", 0)) * 0.05
    oneX_2X = max(min(oneX_2X, 0.9), 0.1)
    btts = 0.6 if partido.get("goles_home", 0) > 0 and partido.get("goles_away", 0) > 0 else 0.3
    combinacion = max(over_1_5, oneX_2X, btts)
    return {
        **partido,
        "prob_over_1_5": round(over_1_5, 2),
        "prob_1X_2X": round(oneX_2X, 2),
        "prob_btts": round(btts, 2),
        "prob_combinacion": round(combinacion, 2)
    }

# Seleccionar top 3 de cada categoría
def seleccionar_top(partidos: List[dict], key: str):
    return sorted(partidos, key=lambda x: x[key], reverse=True)[:3]

@app.get("/matches")
def matches():
    try:
        respuesta = requests.get(API_URL, timeout=10)
        respuesta.raise_for_status()
        partidos = respuesta.json()  # asumimos que la API devuelve lista de partidos
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
