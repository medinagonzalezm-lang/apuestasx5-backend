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
    
    # Intentos en orden de prioridad
    endpoints = [
        "https://v3.football.api-sports.io/fixtures?next=20", # Próximos 20 globales
        "https://v3.football.api-sports.io/fixtures?live=all", # Partidos en vivo ahora
        "https://v3.football.api-sports.io/fixtures?league=140&season=2025&next=10" # LaLiga específica
    ]

    for url in endpoints:
        try:
            print(f"Probando conexión con: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"Error de servidor ({response.status_code}): {response.text}")
                continue

            data = response.json()
            
            # Verificamos si hay errores de autenticación en el JSON
            if data.get('errors'):
                print(f"La API reporta errores de acceso: {data['errors']}")
                continue

            partidos_reales = []
            for f in data.get('response', []):
                partidos_reales.append({
                    "liga": f['league']['name'],
                    "local": f['teams']['home']['name'],
                    "visitante": f['teams']['away']['name']
                })
            
            if partidos_reales:
                print(f"¡Conexión exitosa! {len(partidos_reales)} partidos encontrados.")
                return partidos_reales
                
        except Exception as e:
            print(f"Fallo técnico en este intento: {e}")
            continue

    print("⚠️ No se pudo obtener datos reales. Revisa si FOOTBALL_API_KEY es correcta en GitHub Secrets.")
    return None

def generar_pronosticos_ia(datos_partidos):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    prompt_text = f"""
    Actúa como analista PRO. Usa estos partidos REALES: {json.dumps(datos_partidos)}
    TAREA: Genera un JSON con pronósticos de BAJO RIESGO.
    - REGLA: Usa NOMBRES REALES de los equipos.
    - ESTRATEGIA BONUS: Incluye al menos 1 Hándicap Asiático protector (HA 0.0 o HA +0.5).
    - PROCESO: Aplica Poisson y Kelly (0.25).
    
    FORMATO JSON:
    {{
      "tip_05": ["⚽ Equipo A vs Equipo B | +1.5 Goles"],
      "tip_15": ["⚽ Equipo C vs Equipo D | Doble Oportunidad"],
      "tip_1x2x": ["⚽ Equipo E vs Equipo F | HA Protector"],
      "tip_btts": ["⚽ Equipo G vs Equipo H | BTTS"],
      "tip_as": ["⚽ Equipo I vs Equipo J | Pick Seguro"],
      "tip_bonus": ["⚽ COMBINADA: Equipo K vs L (HA 0.0) + Equipo M vs N | Cuota y Stake"],
      "progression": {{
        "puntos_actuales": 100,
        "analisis_tecnico": "Resumen de por qué estos hándicaps asiáticos hoy."
      }}
    }}
    Responde SOLO el JSON puro.
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
    if not datos: return

    json_final = generar_pronosticos_ia(datos)
    if not json_final: return

    try:
        json_dict = json.loads(json_final)
        with open("tips.json", "w", encoding='utf-8') as f:
            json.dump(json_dict, f, ensure_ascii=False, indent=2)
        print("¡TODO LISTO! tips.json actualizado con datos verificados.")
    except:
        print("Error procesando JSON final.")

if __name__ == "__main__":
    main()
