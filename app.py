from fastapi import FastAPI
import requests
import os
import json
from datetime import date

app = FastAPI()

# API key desde variable de entorno
API_KEY = os.getenv("API_FOOTBALL_KEY")
API_URL = "https://apuestasx5-backend.onrender.com/matches"  # tu endpoint original o de API-Football

CACHE_FILE = "data/daily_picks.json"

# --------------------------------------------------
#  Funciones de cache
# --------------------------------------------------
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(data):
    os.makedirs("data", exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)

# --------------------------------------------------
#  Función principal de picks diarios
# --------------------------------------------------
def get_daily_picks():
    today_str = str(date.today())
    cache = load_cache()

    # Si cache existe y es de hoy, devolverlo
    if cache.get("date") == today_str:
        return cache

    # Si no, fetch + analizar + guardar cache
    matches = fetch_matches()
    picks = analyze_matches(matches)

    cache = {
        "date": today_str,
        "over15": picks["over15"],
        "double": picks["double"],
        "btts": picks["btts"],
        "combo": picks["combo"]
    }

    save_cache(cache)
    return cache

# --------------------------------------------------
#  Fetch partidos del día
# --------------------------------------------------
def fetch_matches():
    # Aquí puedes cambiar a tu API real si quieres
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        response = requests.get(API_URL, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()  # asumimos que devuelve lista de partidos
    except Exception as e:
        print("ERROR FETCH:", e)
        return []

# --------------------------------------------------
#  Función de análisis simulada
# --------------------------------------------------
def analyze_matches(matches):
    """
    Devuelve los 3 mejores de cada tipo.
    Aquí puedes poner tu algoritmo estadístico real de Kelly y probabilidades.
    """
    over15 = []
    double = []
    btts = []
    combo = []

    for i, match in enumerate(matches[:10]):  # analizamos los primeros 10 para no gastar mucho
        # Simulamos análisis
        over15.append({"match": match, "tip": "+1.5 goles"})
        double.append({"match": match, "tip": "1X / 2X"})
        btts.append({"match": match, "tip": "BTT"})
        combo.append({"match": match, "tip": "Combo"})

    # Tomamos solo 3 picks por tipo
    return {
        "over15": over15[:3],
        "double": double[:3],
        "btts": btts[:3],
        "combo": combo[:3]
    }

# --------------------------------------------------
#  Endpoints para la app
# --------------------------------------------------
@app.get("/picks/over15")
def get_over15():
    return get_daily_picks()["over15"]

@app.get("/picks/double")
def get_double():
    return get_daily_picks()["double"]

@app.get("/picks/btts")
def get_btts():
    return get_daily_picks()["btts"]

@app.get("/picks/combo")
def get_combo():
    return get_daily_picks()["combo"]

# --------------------------------------------------
#  Root
# --------------------------------------------------
@app.get("/")
def root():
    return {"status": "Backend OK"}
