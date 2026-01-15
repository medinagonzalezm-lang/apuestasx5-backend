import os
import requests
import json
import time
from google import genai
from datetime import datetime

# Configuración
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

client = genai.Client(api_key=GEMINI_KEY)

def obtener_partidos():
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": FOOTBALL_KEY}
    hoy = datetime.now().strftime("%Y-%m-%d")
    
    try:
        r = requests.get(f"{url}?date={hoy}", headers=headers, timeout=15)
        res = r.json()
        if res.get('response'):
            partidos = res['response']
            print(f"Encontrados {len(partidos)} partidos.")
            # Formato ultra-compacto
            return [f"{p['teams']['home']['name']} vs {p['teams']['away']['name']} ({p['league']['name']})" for p in partidos]
        return None
    except Exception as e:
        print(f"Error Fútbol: {e}")
        return None

def analizar_con_ia(prompt):
    try:
        # Usamos gemini-2.0-flash que ya confirmamos que responde
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        if "429" in str(e):
            print("Límite de cuota alcanzado. Esperando 30 segundos...")
            time.sleep(30) # Pausa larga si hay saturación
            return ""
        print(f"Error Gemini: {e}")
        return ""

def main():
    print("--- INICIANDO PRONÓSTICOS DEPORTIVOS (IA) - OPTIMIZADO ---")
    todos = obtener_partidos()
    
    if not todos:
        return

    # Dividimos en 2 bloques grandes para reducir el número de peticiones
    mitad = len(todos) // 2
    lotes = [todos[:mitad], todos[mitad:]]
    acumulado = ""

    for i, lote in enumerate(lotes):
        print(f"Analizando bloque {i+1} de 2...")
        prompt_lote = f"Selecciona los 15 mejores partidos para Over 1.5 y 1X2 de esta lista: {json.dumps(lote)}"
        res = analizar_con_ia(prompt_lote)
        acumulado += f"\n{res}"
        time.sleep(10) # Pausa de cortesía para no saturar la API gratuita

    print("Generando veredicto final...")
    prompt_final = f"""
    Eres la IA de 'Pronosticos deportivos (IA)'. 
    Analiza estos candidatos: {acumulado}
    
    Genera un JSON con:
    - 'tip_05', 'tip_15' (3 picks OVER 1.5 cada uno).
    - 'tip_1x2x' (3 picks 1X o 2X).
    - 'tip_btts' (3 picks BTTS).
    - 'tip_bonus' (Los 3 mejores de toda la jornada).
    - 'puntos_actuales': BENEFICIO NETO (Resta 100 al total acumulado). Solo número.
    - 'analisis_tecnico': Resumen profesional de la jornada completa.

    Responde SOLO el JSON puro.
    """
    
    time.sleep(5)
    resultado = analizar_con_ia(prompt_final)
    
    if resultado:
        try:
            limpio = resultado.replace("```json", "").replace("```", "").strip()
            json_data = json.loads(limpio)
            with open("tips.json", "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print("--- ¡ÉXITO! Jornada analizada correctamente ---")
        except:
            print("Error al procesar JSON.")

if __name__ == "__main__":
    main()
