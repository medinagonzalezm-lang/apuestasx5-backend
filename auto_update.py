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
    # Los endpoints que SÍ funcionan en el plan gratuito
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
                print(f"Éxito: {len(partidos_reales)} partidos encontrados para hoy.")
                return partidos_reales
        except: continue

    return None

def generar_pronosticos_ia(datos_partidos):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    prompt_text = f"""
    Actúa como experto estadístico deportivo. Analiza estos partidos: {json.dumps(datos_partidos)}
    
    OBJETIVO: Generar pronósticos de MÁXIMA SEGURIDAD.
    1. Usa NOMBRES REALES.
    2. En 'tip_bonus', incluye Hándicaps Asiáticos (HA 0.0 o HA +0.5) para minimizar riesgo de pérdida.
    3. Usa Poisson y Kelly Fraccional (0.25) para gestión de bankroll.
    
    FORMATO JSON:
    {{
      "tip_05": ["⚽ Local vs Visitante | +1.5 Goles"],
      "tip_15": ["⚽ Local vs Visitante | Doble Oportunidad"],
      "tip_1x2x": ["⚽ Local vs Visitante | HA Protector"],
      "tip_btts": ["⚽ Local vs Visitante | BTTS"],
      "tip_as": ["⚽ Local vs Visitante | Pick Seguro"],
      "tip_bonus": ["⚽ COMBINADA: Local vs Visitante (HA Protector) + Partido 2 | Cuota y Stake"],
      "progression": {{
        "puntos_actuales": 100,
        "analisis_tecnico": "Hoy priorizamos HA para asegurar que el empate nos devuelva el capital."
      }}
    }}
    Responde SOLO el JSON.
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"}
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        res_json = response.json()
        return res_json['candidates'][0]['content']['parts'][0]['text'].strip()
    except: return None

def main():
    datos = obtener_datos_futbol()
    if not datos:
        print("Error: No se pudieron obtener datos con el plan gratuito.")
        return

    json_final = generar_pronosticos_ia(datos)
    if json_final:
        try:
            json_dict = json.loads(json_final)
            with open("tips.json", "w", encoding='utf-8') as f:
                json.dump(json_dict, f, ensure_ascii=False, indent=2)
            print("¡TODO LISTO! El sistema de Pronósticos IA está funcionando correctamente.")
        except: print("Error en formato final.")

if __name__ == "__main__":
    main()
