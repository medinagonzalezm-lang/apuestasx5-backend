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
    url = f"https://v3.football.api-sports.io/fixtures?date={hoy}"

    try:
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        partidos_reales = []
        # Seleccionamos una muestra de partidos
        for f in data.get('response', [])[:40]:
            partidos_reales.append({
                "liga": f['league']['name'],
                "local": f['teams']['home']['name'],
                "visitante": f['teams']['away']['name']
            })
        return partidos_reales
    except Exception as e:
        print(f"Error Football API: {e}")
        return None

def generar_pronosticos_ia(datos_partidos):
    # Cambiamos a v1 que es la versión estable actual
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    prompt_text = f"""
    Eres un analista deportivo experto. Genera un JSON con pronósticos para estos partidos: {json.dumps(datos_partidos)}
    
    INSTRUCCIONES:
    1. 'tip_05': 3 picks de +0.5 goles.
    2. 'tip_15': 3 picks de +1.5 goles.
    3. 'tip_1x2x': 3 picks de Doble Oportunidad.
    4. 'tip_btts': 3 picks de Ambos Marcan.
    5. 'tip_as': 3 picks de Handicap Asiatico.
    6. 'tip_bonus': Los 3 mejores de los anteriores.
    7. En 'puntos_actuales', pon solo el BENEFICIO (Total acumulado menos 100).
    
    Responde SOLO el JSON puro:
    {{
      "tip_05": ["Equipo A vs Equipo B | +0.5"],
      "tip_15": ["Equipo C vs Equipo D | +1.5"],
      "tip_1x2x": ["Equipo E vs Equipo F | 1X"],
      "tip_btts": ["Equipo G vs Equipo H | BTTS"],
      "tip_as": ["Equipo I vs Equipo J | HA 0.0"],
      "tip_bonus": ["Combinada..."],
      "progression": {{
        "puntos_actuales": 0,
        "analisis_tecnico": "Breve analisis."
      }}
    }}
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json"
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        res_json = response.json()
        
        if 'candidates' in res_json:
            return res_json['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            print(f"Respuesta inesperada de Google: {res_json}")
            return None
    except Exception as e:
        print(f"Error en peticion: {e}")
        return None

def main():
    print("Iniciando actualizacion...")
    datos = obtener_datos_futbol()
    if not datos:
        print("No se pudieron obtener partidos.")
        return

    print(f"Procesando {len(datos)} partidos...")
    resultado = generar_pronosticos_ia(datos)
    
    if resultado:
        try:
            json_dict = json.loads(resultado)
            with open("tips.json", "w", encoding='utf-8') as f:
                json.dump(json_dict, f, ensure_ascii=False, indent=2)
            print("¡ACTUALIZACIÓN COMPLETADA EXITOSAMENTE!")
        except:
            print("Error: La IA no devolvió un JSON válido.")

if __name__ == "__main__":
    main()
