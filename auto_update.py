import os
import requests
import json
from datetime import datetime

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

def obtener_datos_futbol():
    # Aumentamos a 50 para tener más donde elegir
    url = "https://v3.football.api-sports.io/fixtures?next=50"
    headers = {'x-rapidapi-key': FOOTBALL_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        # Simplificamos los datos para que Gemini no se sature
        partidos_reales = []
        for f in data.get('response', []):
            partidos_reales.append({
                "liga": f['league']['name'],
                "local": f['teams']['home']['name'],
                "visitante": f['teams']['away']['name'],
                "fecha": f['fixture']['date']
            })
        return partidos_reales
    except: return None

def generar_pronosticos_ia(datos_partidos):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    # PROMPT REFORZADO: Prohibido inventar nombres
    prompt_text = f"""
    URGENTE: Usa SOLO estos partidos reales para el análisis: {json.dumps(datos_partidos)}
    
    INSTRUCCIONES:
    1. PROHIBIDO usar nombres genéricos como 'Partido 1' o 'Equipo A'. Usa los NOMBRES REALES de los equipos proporcionados.
    2. Aplica Distribución de Poisson y selección de bajo riesgo (Hándicaps Asiáticos y Doble Oportunidad).
    3. En 'tip_bonus', incluye 1-2 Hándicaps Asiáticos protectores (ej. HA 0.0 o HA +1.0) para minimizar pérdidas.
    4. GESTIÓN: Usa Kelly Fraccional (0.25).
    
    FORMATO JSON:
    {{
      "tip_05": ["⚽ Local vs Visitante | +0.5 Goles", "..."],
      "tip_15": ["⚽ Local vs Visitante | +1.5 Goles", "..."],
      "tip_1x2x": ["⚽ Local vs Visitante | 1X o X2", "..."],
      "tip_btts": ["⚽ Local vs Visitante | BTTS Sí/No", "..."],
      "tip_as": ["⚽ Local vs Visitante | Pronóstico seguro", "..."],
      "tip_bonus": ["⚽ Combinada: Local vs Visitante (HA 0.0) + Otro Partido | Cuota y Stake"],
      "progression": {{
        "puntos_actuales": (calcula sobre base 100),
        "analisis_tecnico": "Explicación breve de por qué estos hándicaps asiáticos hoy."
      }}
    }}
    Responde SOLO el JSON.
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {
            "temperature": 0.0, # Bajamos a CERO para que no invente NADA
            "responseMimeType": "application/json"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        res_json = response.json()
        return res_json['candidates'][0]['content']['parts'][0]['text'].strip()
    except: return None

def main():
    print(f"Generando pronósticos REALES con equipos de la API...")
    datos = obtener_datos_futbol()
    if not datos: 
        print("No hay datos de la API de fútbol")
        return

    json_final = generar_pronosticos_ia(datos)
    if not json_final: return

    try:
        json_dict = json.loads(json_final)
        with open("tips.json", "w", encoding='utf-8') as f:
            json.dump(json_dict, f, ensure_ascii=False, indent=2)
        print("¡ÉXITO! tips.json actualizado con DATOS REALES.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
