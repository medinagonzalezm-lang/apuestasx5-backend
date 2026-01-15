import os
import requests
import json
from datetime import datetime

# Configuración de llaves desde GitHub Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

def obtener_partidos():
    # Endpoint de RapidAPI con la nueva clave
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    headers = {
        "x-rapidapi-key": FOOTBALL_KEY,
        "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
    }
    
    hoy = datetime.now().strftime("%Y-%m-%d")
    try:
        print(f"Consultando partidos para hoy: {hoy}...")
        r = requests.get(f"{url}?date={hoy}", headers=headers, timeout=15)
        res = r.json()
        
        if res.get('response'):
            print(f"¡Éxito! Se han obtenido {len(res['response'])} partidos.")
            return [{
                "liga": f['league']['name'],
                "local": f['teams']['home']['name'],
                "visitante": f['teams']['away']['name']
            } for f in res['response']]
        else:
            print(f"La API no devolvió partidos. Respuesta: {res}")
            return None
    except Exception as e:
        print(f"Error de conexión con la API de Fútbol: {e}")
        return None

def analizar_con_ia(partidos):
    # Endpoint de Gemini 1.5 Flash (Estable)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    # Prompt ajustado a tus requisitos de Pronósticos deportivos (IA)
    prompt = f"""
    Actúa como el motor de análisis de 'Pronosticos deportivos (IA)'. 
    Analiza estos partidos: {json.dumps(partidos[:40])}
    
    Genera un JSON con este formato exacto:
    - 'tip_05', 'tip_15', 'tip_1x2x', 'tip_btts', 'tip_as', 'tip_bonus' (3 partidos por cada uno).
    - 'puntos_actuales': Calcula el beneficio neto restando 100 al total acumulado de beneficios. Solo el número.
    - 'analisis_tecnico': Un resumen técnico de la jornada.

    Responde ÚNICAMENTE el código JSON puro, sin bloques de texto ni markdown.
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        r = requests.post(url, json=payload, timeout=30)
        res = r.json()
        
        if 'candidates' in res:
            texto = res['candidates'][0]['content']['parts'][0]['text'].strip()
            # Limpieza de posibles bloques de código markdown
            if "```" in texto:
                texto = texto.split("```")[1].replace("json", "").strip()
            return texto
        else:
            print(f"Error en la respuesta de Gemini: {res}")
            return None
    except Exception as e:
        print(f"Error de comunicación con Gemini: {e}")
        return None

def main():
    print("--- INICIANDO PROCESO DE PRONÓSTICOS (IA) ---")
    datos_partidos = obtener_partidos()
    
    if not datos_partidos:
        print("ERROR: No hay datos para analizar. Deteniendo proceso.")
        return

    print("Enviando datos a Gemini para análisis estadístico...")
    resultado_ia = analizar_con_ia(datos_partidos)
    
    if resultado_ia:
        try:
            # Validación y guardado del archivo final
            json_final = json.loads(resultado_ia)
            with open("tips.json", "w", encoding="utf-8") as f:
                json.dump(json_final, f, indent=2, ensure_ascii=False)
            print("--- ¡ÉXITO! tips.json generado correctamente ---")
        except Exception as e:
            print(f"Error al procesar el JSON de la IA: {e}")
            print(f"Contenido recibido: {resultado_ia}")

if __name__ == "__main__":
    main()
