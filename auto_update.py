import os
import requests
import json
from google import genai
from datetime import datetime

# Configuración
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

# Nueva forma de inicializar el cliente en 2026
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
            return [f"{p['teams']['home']['name']} vs {p['teams']['away']['name']} ({p['league']['name']})" for p in partidos]
        return None
    except Exception as e:
        print(f"Error Fútbol: {e}")
        return None

def analizar_con_ia(prompt):
    try:
        # Usamos el modelo más moderno y estable: gemini-2.0-flash
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Error en la nueva API de Gemini: {e}")
        return ""

def main():
    print("--- INICIANDO PROCESO PRONÓSTICOS DEPORTIVOS (IA) - VERSIÓN 2.0 ---")
    todos = obtener_partidos()
    
    if not todos:
        print("No se obtuvieron datos de fútbol.")
        return

    # Dividimos los 145 partidos en bloques
    lotes = [todos[i:i + 50] for i in range(0, len(todos), 50)]
    acumulado = ""

    for i, lote in enumerate(lotes):
        print(f"Analizando bloque {i+1} de {len(lotes)} con Gemini 2.0...")
        prompt_lote = f"Analiza estos partidos y selecciona los mejores para Over 1.5 y 1X2: {json.dumps(lote)}"
        res_lote = analizar_con_ia(prompt_lote)
        acumulado += f"\nCandidatos Lote {i+1}: {res_lote}"

    print("Generando veredicto final...")
    prompt_final = f"""
    Eres la IA de 'Pronosticos deportivos (IA)'. 
    Analiza estos candidatos: {acumulado}
    
    Genera un JSON con:
    - 'tip_05', 'tip_15' (3 picks OVER 1.5 APUESTA cada uno).
    - 'tip_1x2x' (3 picks 1X O 2X APUESTA).
    - 'tip_btts' (3 picks BTTS APUESTA).
    - 'tip_bonus' (Los 3 mejores de toda la jornada).
    - 'puntos_actuales': BENEFICIO NETO (Resta 100 al acumulado). Solo el número.
    - 'analisis_tecnico': Resumen profesional.

    Responde SOLO el JSON puro.
    """
    
    resultado = analizar_con_ia(prompt_final)
    
    if resultado:
        try:
            limpio = resultado.replace("```json", "").replace("```", "").strip()
            json_data = json.loads(limpio)
            with open("tips.json", "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print("--- ¡ÉXITO! Análisis completado con Gemini 2.0 ---")
        except Exception as e:
            print(f"Error al procesar JSON: {e}")

if __name__ == "__main__":
    main()
