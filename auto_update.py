import os
import requests
import json
from datetime import datetime

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

def obtener_datos_futbol():
    url = "https://v3.football.api-sports.io/fixtures?next=50"
    headers = {'x-rapidapi-key': FOOTBALL_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
    try:
        response = requests.get(url, headers=headers)
        return response.json()
    except: return None

def generar_pronosticos_ia(datos_partidos):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    
    prompt_text = f"""
    Actúa como mi experto analista deportivo y estadístico avanzado. Analiza estos partidos para hoy ({fecha_hoy}): {datos_partidos}.
    
    ESTRATEGIA DE PROTECCIÓN DE CAPITAL (BONUS):
    - En la categoría 'tip_bonus', DEBES incluir al menos 1 o 2 selecciones de Hándicap Asiático (HA) con líneas de protección (ej. HA 0.0, HA +0.5, HA -1.0).
    - El objetivo es MINIMIZAR pérdidas: prioriza mercados que ofrezcan DEVOLUCIÓN (Push) en resultados frontera.
    - No importa que la cuota sea menor si la seguridad de no perder el capital es mayor.

    REGLAS ESTADÍSTICAS:
    1. Utiliza Distribución de Poisson y Simulación Monte Carlo para descartar partidos volátiles.
    2. Usa Criterio de Kelly Fraccional (0.25) para el Stake sugerido.

    FORMATO JSON OBLIGATORIO:
    {{
      "tip_05": [3 partidos de +1.5 goles con xG alto],
      "tip_15": [3 partidos de bajo riesgo],
      "tip_1x2x": [3 partidos con Doble Oportunidad o HA protectores],
      "tip_btts": [3 partidos de Ambos Marcan/No Marcan],
      "tip_as": [Los 3 eventos con mayor probabilidad conjunta],
      "tip_bonus": [LA COMBINADA SEGURA: Incluye 1-2 Hándicaps Asiáticos protectores para minimizar pérdidas, Cuota Total y Stake],
      "progression": {{
        "puntos_actuales": (progreso actual sobre base 100),
        "analisis_tecnico": "Explicación del uso de Hándicaps Asiáticos hoy para proteger el bankroll y resumen ejecutivo."
      }}
    }}
    Responde UNICAMENTE el JSON puro.
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        res_json = response.json()
        return res_json['candidates'][0]['content']['parts'][0]['text'].strip()
    except:
        return None

def main():
    print(f"Generando pronósticos con protección de Hándicap Asiático...")
    datos = obtener_datos_futbol()
    if not datos: return

    json_final = generar_pronosticos_ia(datos)
    if not json_final: return

    try:
        json_dict = json.loads(json_final)
        with open("tips.json", "w", encoding='utf-8') as f:
            json.dump(json_dict, f, ensure_ascii=False, indent=2)
        print("¡ÉXITO! tips.json actualizado con estrategia de Hándicap Asiático y bajo riesgo.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
