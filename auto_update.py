import os
import requests
import json
from datetime import datetime

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

def obtener_datos_futbol():
    headers = {
        'x-rapidapi-key': FOOTBALL_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    
    hoy = datetime.now().strftime("%Y-%m-%d")
    endpoints = [
        f"https://v3.football.api-sports.io/fixtures?date={hoy}",
        "https://v3.football.api-sports.io/fixtures?live=all"
    ]

    for url in endpoints:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200: continue
            data = response.json()
            if data.get('errors'): continue

            partidos_reales = []
            for f in data.get('response', []):
                partidos_reales.append({
                    "liga": f['league']['name'],
                    "local": f['teams']['home']['name'],
                    "visitante": f['teams']['away']['name']
                })
            
            if partidos_reales:
                print(f"Exito: {len(partidos_reales)} partidos encontrados.")
                return partidos_reales
        except: continue
    return None

def generar_pronosticos_ia(datos_partidos):
    # Usamos gemini-1.5-flash (la versión 2.5 no existe comercialmente aún, usamos la estable más rápida)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    prompt_text = f"""
    Actúa como experto estadístico deportivo para el proyecto 'Pronosticos deportivos (IA)'. 
    Analiza estos partidos reales: {json.dumps(datos_partidos)}
    
    OBJETIVO: Generar pronósticos basados en Poisson y Kelly Fraccional.
    
    REGLAS DE ASIGNACIÓN:
    1. 'tip_05': 3 Partidos con alta probabilidad de +0.5 goles.
    2. 'tip_15': 3 Partidos con alta probabilidad de +1.5 goles.
    3. 'tip_1x2x': 3 Partidos de Doble Oportunidad (1X o 2X).
    4. 'tip_btts': 3 Partidos donde Ambos Marcan (BTTS).
    5. 'tip_as': 3 Partidos con Hándicap Asiático protector (HA 0.0 o HA +0.5).
    6. 'tip_bonus': Combinación de los 3 pronósticos más fiables de las categorías anteriores.

    IMPORTANTE: En 'puntos_actuales', indica SOLO el beneficio neto acumulado (ejemplo: si hay 110€, pon 10). NO incluyas los 100€ iniciales.

    FORMATO JSON ESTRICTO:
    {{
      "tip_05": ["Equipo A vs Equipo B | +0.5 Goles"],
      "tip_15": ["Equipo C vs Equipo D | +1.5 Goles"],
      "tip_1x2x": ["Equipo E vs Equipo F | Doble Oportunidad"],
      "tip_btts": ["Equipo G vs Equipo H | Ambos Marcan"],
      "tip_as": ["Equipo I vs Equipo J | HA Protector"],
      "tip_bonus": ["COMBINADA: Partido X + Partido Y | Cuota Total"],
      "progression": {{
        "puntos_actuales": 0,
        "analisis_tecnico": "Resumen breve de la jornada y por qué se eligieron estos picks."
      }}
    }}
    Responde SOLO el JSON.
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        res_json = response.json()
        return res_json['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        print(f"Error en IA: {e}")
        return None

def main():
    datos = obtener_datos_futbol()
    if not datos:
        print("Error: Sin datos de futbol.")
        return

    json_final = generar_pronosticos_ia(datos)
    if json_final:
        try:
            json_dict = json.loads(json_final)
            with open("tips.json", "w", encoding='utf-8') as f:
                json.dump(json_dict, f, ensure_ascii=False, indent=2)
            print("¡JSON actualizado con éxito!")
        except:
            print("Error al procesar el JSON de la IA.")

if __name__ == "__main__":
    main()
