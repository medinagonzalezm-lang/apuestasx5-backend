import os, requests, json
from datetime import datetime

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

def obtener_datos():
    h = {'x-rapidapi-key': FOOTBALL_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
    hoy = datetime.now().strftime("%Y-%m-%d")
    url = f"https://v3.football.api-sports.io/fixtures?date={hoy}"
    try:
        r = requests.get(url, headers=h, timeout=10)
        data = r.json()
        return [{"liga": f['league']['name'], "local": f['teams']['home']['name'], "visitante": f['teams']['away']['name']} for f in data.get('response', [])]
    except: return None

def generar_ia(datos):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = f"""
    Analiza: {json.dumps(datos)}
    Responde SOLO un JSON con estas 6 llaves exactas:
    1. 'tip_05': 3 partidos de +0.5 goles.
    2. 'tip_15': 3 partidos de +1.5 goles.
    3. 'tip_1x2x': 3 de Doble Oportunidad.
    4. 'tip_btts': 3 de Ambos Marcan.
    5. 'tip_as': 3 de Handicap Asiatico Protector.
    6. 'tip_bonus': Los 3 mejores de los anteriores.
    En 'puntos_actuales' de 'progression', pon SOLO el beneficio (Total menos 100).
    JSON:
    {{
      "tip_05": [], "tip_15": [], "tip_1x2x": [], "tip_btts": [], "tip_as": [], "tip_bonus": [],
      "progression": {{"puntos_actuales": 0, "analisis_tecnico": ""}}
    }}
    """
    try:
        r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json"}})
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except: return None

if __name__ == "__main__":
    d = obtener_datos()
    if d:
        res = generar_ia(d)
        if res:
            with open("tips.json", "w", encoding='utf-8') as f:
                json.dump(json.loads(res), f, ensure_ascii=False, indent=2)
