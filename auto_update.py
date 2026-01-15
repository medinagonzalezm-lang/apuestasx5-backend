import os
import requests
import json
from datetime import datetime

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

def obtener_partidos():
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": FOOTBALL_KEY}
    hoy = datetime.now().strftime("%Y-%m-%d")
    
    try:
        print(f"Buscando partidos para hoy ({hoy})...")
        r = requests.get(f"{url}?date={hoy}", headers=headers, timeout=15)
        res = r.json()
        
        if res.get('response'):
            # Enviamos 100 partidos pero de forma muy compacta para no saturar la IA
            partidos = res['response'][:100]
            print(f"Éxito: {len(partidos)} partidos seleccionados para análisis profundo.")
            return [f"{p['teams']['home']['name']} vs {p['teams']['away']['name']} ({p['league']['name']})" for p in partidos]
        else:
            return None
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

def analizar_con_ia(lista_partidos):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    # Prompt optimizado para manejar volumen sin errores de 'candidates'
    prompt = f"""
    Eres el experto analista de 'Pronosticos deportivos (IA)'. 
    Analiza esta lista de 100 partidos: {json.dumps(lista_partidos)}
    
    Tu tarea es seleccionar los mejores pronósticos basados en probabilidades estadísticas:
    1. 'tip_05': 3 picks con alta prob. de más de 1.5 goles (OVER 1.5 APUESTA).
    2. 'tip_15': 3 picks de OVER 1.5 APUESTA.
    3. 'tip_1x2x': 3 picks donde el local o el visitante no pierden (1X O 2X APUESTA).
    4. 'tip_btts': 3 picks donde ambos marquen (BTTS APUESTA).
    5. 'tip_bonus': Los 3 más probables de toda la lista (Combinación fiable).
    
    Otros datos:
    - 'puntos_actuales': Indica el BENEFICIO NETO mensual (Suma total menos 100). Solo el número.
    - 'analisis_tecnico': Un resumen de 15 palabras sobre la tendencia de hoy.

    IMPORTANTE: Responde SOLO el JSON puro.
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        r = requests.post(url, json=payload, timeout=30)
        res = r.json()
        
        if 'candidates' in res and res['candidates']:
            texto = res['candidates'][0]['content']['parts'][0]['text'].strip()
            # Limpiar markdown si la IA lo pone
            if "```" in texto:
                texto = texto.split("```")[1].replace("json", "").strip()
            return texto
        else:
            # Si Gemini da error por volumen, el log nos dirá por qué
            print(f"Error en respuesta IA: {res}")
            return None
    except Exception as e:
        print(f"Error de red IA: {e}")
        return None

def main():
    print("--- INICIANDO PROCESO (IA) ---")
    datos = obtener_partidos()
    
    if not datos:
        print("No se obtuvieron partidos.")
        return

    print("Analizando 100 partidos con Gemini...")
    resultado = analizar_con_ia(datos)
    
    if resultado:
        try:
            # Validar y guardar
            final_json = json.loads(resultado)
            with open("tips.json", "w", encoding="utf-8") as f:
                json.dump(final_json, f, indent=2, ensure_ascii=False)
            print("--- ¡ÉXITO! tips.json actualizado con 100 partidos analizados ---")
        except Exception as e:
            print(f"Error en JSON: {e}")
            print(f"Contenido: {resultado}")

if __name__ == "__main__":
    main()
