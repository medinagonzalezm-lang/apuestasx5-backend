import os
import requests
import json
from datetime import datetime

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

def obtener_datos_futbol():
    # Buscamos los próximos 50 partidos de las ligas más importantes para asegurar datos
    # Ligas: 140 (España), 39 (Inglaterra), 135 (Italia), 78 (Alemania), 61 (Francia)
    url = "https://v3.football.api-sports.io/fixtures?next=50"
    
    headers = {
        'x-rapidapi-key': FOOTBALL_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    
    try:
        print("Consultando API de Fútbol...")
        response = requests.get(url, headers=headers)
        data = response.json()
        
        # DEBUG: Imprimimos si la API nos da algún error de mensaje
        if data.get('errors'):
            print(f"Errores detectados en la API: {data['errors']}")
            return None

        partidos_reales = []
        fixtures = data.get('response', [])
        
        for f in fixtures:
            partidos_reales.append({
                "liga": f['league']['name'],
                "local": f['teams']['home']['name'],
                "visitante": f['teams']['away']['name'],
                "fecha": f['fixture']['date']
            })
            
        if not partidos_reales:
            print("La API devolvió 0 partidos. Intentando con un rango más amplio...")
            return None
            
        print(f"Se han encontrado {len(partidos_reales)} partidos reales.")
        return partidos_reales
    except Exception as e:
        print(f"Fallo de conexión: {e}")
        return None

def generar_pronosticos_ia(datos_partidos):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    # PROMPT DE ANALISTA PROFESIONAL
    prompt_text = f"""
    Actúa como experto estadístico. Usa estos partidos: {json.dumps(datos_partidos)}
    
    TAREA: Genera un JSON con pronósticos de BAJO RIESGO.
    - REGLA: Usa NOMBRES REALES de los equipos.
    - ESTRATEGIA BONUS: Incluye al menos 2 Hándicaps Asiáticos protectores (HA 0.0 o HA +0.5) para minimizar pérdidas.
    - MATEMÁTICAS: Usa Poisson y Kelly Fraccional (0.25).
    
    FORMATO JSON:
    {{
      "tip_05": ["⚽ Local vs Visitante | +1.5 Goles", "..."],
      "tip_15": ["⚽ Local vs Visitante | Doble Oportunidad 1X/X2", "..."],
      "tip_1x2x": ["⚽ Local vs Visitante | HA Protector", "..."],
      "tip_btts": ["⚽ Local vs Visitante | BTTS", "..."],
      "tip_as": ["⚽ Local vs Visitante | Pick Seguro", "..."],
      "tip_bonus": ["⚽ COMBINADA SEGURA: Equipo A vs Equipo B (HA 0.0) + Partido 2 | Cuota y Stake"],
      "progression": {{
        "puntos_actuales": 100,
        "analisis_tecnico": "Resumen ejecutivo: Por qué usamos HA hoy para proteger el capital."
      }}
    }}
    Responde SOLO el JSON.
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {
            "temperature": 0.0,
            "responseMimeType": "application/json"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        res_json = response.json()
        return res_json['candidates'][0]['content']['parts'][0]['text'].strip()
    except: return None

def main():
    datos = obtener_datos_futbol()
    if not datos:
        print("No se pudo obtener información de los partidos.")
        return

    json_final = generar_pronosticos_ia(datos)
    if not json_final:
        print("La IA no pudo procesar los datos.")
        return

    try:
        json_dict = json.loads(json_final)
        with open("tips.json", "w", encoding='utf-8') as f:
            json.dump(json_dict, f, ensure_ascii=False, indent=2)
        print("¡LOGRADO! tips.json actualizado con datos reales y protección asiática.")
    except Exception as e:
        print(f"Error al guardar JSON: {e}")

if __name__ == "__main__":
    main()
