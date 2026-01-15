import os
import requests
import json
from datetime import datetime

# Configuración confirmada por el diagnóstico
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

def obtener_partidos():
    # URL Directa que sí funcionó en el diagnóstico
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-apisports-key": FOOTBALL_KEY
    }
    
    hoy = datetime.now().strftime("%Y-%m-%d")
    try:
        print(f"Buscando partidos para hoy ({hoy}) en API-SPORTS...")
        r = requests.get(f"{url}?date={hoy}", headers=headers, timeout=15)
        res = r.json()
        
        if res.get('response'):
            print(f"Éxito: {len(res['response'])} partidos encontrados.")
            return [{
                "liga": f['league']['name'],
                "local": f['teams']['home']['name'],
                "visitante": f['teams']['away']['name']
            } for f in res['response']]
        else:
            print(f"No hay partidos o error: {res.get('errors')}")
            return None
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

def analizar_con_ia(partidos):
    # Endpoint de Gemini
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    prompt = f"""
    Eres el analista oficial de 'Pronosticos deportivos (IA)'.
    Analiza estadísticamente estos partidos: {json.dumps(partidos[:40])}
    
    Genera un JSON con este formato exacto:
    - 'tip_05': 3 picks de OVER 1.5 APUESTA (aunque el nombre sea 05, usa la lógica de +1.5 goles como pide el proyecto).
    - 'tip_15': 3 picks de OVER 1.5 APUESTA.
    - 'tip_1x2x': 3 picks de 1X O 2X APUESTA.
    - 'tip_btts': 3 picks de BTTS APUESTA (Ambos marcan).
    - 'tip_bonus': Los 3 más fiables de los anteriores.
    - 'puntos_actuales': Calcula el BENEFICIO NETO. Resta SIEMPRE 100 al beneficio acumulado total. Solo el número.
    - 'analisis_tecnico': Resumen breve de la jornada.

    Responde SOLO el JSON puro, sin markdown.
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        r = requests.post(url, json=payload, timeout=30)
        res = r.json()
        texto = res['candidates'][0]['content']['parts'][0]['text'].strip()
        if "```" in texto:
            texto = texto.split("```")[1].replace("json", "").strip()
        return texto
    except Exception as e:
        print(f"Error IA: {e}")
        return None

def main():
    print("--- INICIANDO PRONÓSTICOS DEPORTIVOS (IA) ---")
    datos = obtener_partidos()
    
    if not datos:
        print("Error: No se pudieron obtener datos de fútbol.")
        return

    print("Analizando con Gemini...")
    resultado = analizar_con_ia(datos)
    
    if resultado:
        try:
            final_json = json.loads(resultado)
            with open("tips.json", "w", encoding="utf-8") as f:
                json.dump(final_json, f, indent=2, ensure_ascii=False)
            print("--- ¡ÉXITO! tips.json actualizado en el repositorio ---")
        except:
            print("Error al procesar JSON.")

if __name__ == "__main__":
    main()
