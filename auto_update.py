import os
import requests
import json
from datetime import datetime

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

def obtener_todos_los_partidos():
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": FOOTBALL_KEY}
    hoy = datetime.now().strftime("%Y-%m-%d")
    
    try:
        print(f"Buscando partidos para hoy ({hoy})...")
        r = requests.get(f"{url}?date={hoy}", headers=headers, timeout=15)
        res = r.json()
        if res.get('response'):
            partidos = res['response']
            print(f"Encontrados {len(partidos)} partidos.")
            return [f"{p['teams']['home']['name']} vs {p['teams']['away']['name']} ({p['league']['name']})" for p in partidos]
        return None
    except Exception as e:
        print(f"Error Fútbol: {e}")
        return None

def llamar_gemini(prompt):
    # Intentamos la URL más limpia y directa de Google AI Studio
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        r = requests.post(url, json=payload, timeout=30)
        res = r.json()
        
        # Si da error 404, probamos con la versión v1beta automáticamente
        if 'error' in res and res['error']['code'] == 404:
            url_beta = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
            r = requests.post(url_beta, json=payload, timeout=30)
            res = r.json()

        if 'candidates' in res:
            return res['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            print(f"Error de la IA: {res.get('error', {}).get('message', 'Sin respuesta')}")
            return ""
    except Exception as e:
        print(f"Error de conexión IA: {e}")
        return ""

def main():
    print("--- INICIANDO PROCESO PRONÓSTICOS DEPORTIVOS (IA) ---")
    todos = obtener_todos_los_partidos()
    
    if not todos:
        print("No se pudieron cargar los datos de fútbol.")
        return

    # Procesar los 145 partidos en bloques para no perder información
    lotes = [todos[i:i + 50] for i in range(0, len(todos), 50)]
    acumulado = ""

    for i, lote in enumerate(lotes):
        print(f"Analizando bloque {i+1} de {len(lotes)}...")
        prompt_lote = f"Selecciona los 10 mejores partidos para Over 1.5 goles de esta lista: {json.dumps(lote)}"
        res_lote = llamar_gemini(prompt_lote)
        acumulado += f"\nLote {i+1}: {res_lote}"

    print("Generando archivo tips.json definitivo...")
    prompt_final = f"""
    Eres la IA de 'Pronosticos deportivos (IA)'. 
    Basado en estos partidos pre-seleccionados de toda la jornada: {acumulado}
    
    Genera un JSON con:
    - 'tip_05' y 'tip_15' (3 picks de OVER 1.5 APUESTA cada uno).
    - 'tip_1x2x' (3 picks de 1X O 2X APUESTA).
    - 'tip_btts' (3 picks de BTTS APUESTA).
    - 'tip_bonus' (Los 3 más fiables de toda la jornada analizada).
    - 'puntos_actuales': BENEFICIO NETO (Total acumulado menos 100).
    - 'analisis_tecnico': Un resumen profesional.

    IMPORTANTE: Responde SOLO el JSON puro.
    """
    
    resultado = llamar_gemini(prompt_final)
    
    if resultado:
        try:
            if "```" in resultado:
                resultado = resultado.split("```")[1].replace("json", "").strip()
            
            json_data = json.loads(resultado)
            with open("tips.json", "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print("--- ¡ÉXITO! Se ha procesado la jornada completa de 145 partidos ---")
        except Exception as e:
            print(f"Error al procesar el JSON final: {e}")

if __name__ == "__main__":
    main()
