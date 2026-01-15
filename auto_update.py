import os
import requests
import json
import google.generativeai as genai
from datetime import datetime

# Configuración de llaves
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

# Configurar SDK de Google
genai.configure(api_key=GEMINI_KEY)

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

def analizar_con_sdk(prompt):
    try:
        # Usamos el modelo flash a través del SDK oficial
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error SDK Gemini: {e}")
        return ""

def main():
    print("--- INICIANDO PROCESO CON SDK OFICIAL ---")
    todos = obtener_todos_los_partidos()
    
    if not todos:
        print("No se pudieron cargar los datos de fútbol.")
        return

    # Dividimos los 145 partidos en bloques para análisis total
    lotes = [todos[i:i + 50] for i in range(0, len(todos), 50)]
    acumulado = ""

    for i, lote in enumerate(lotes):
        print(f"Analizando bloque {i+1} de {len(lotes)}...")
        prompt_lote = f"Analiza estos partidos y dime cuáles son los 5 mejores para ganar o empatar: {json.dumps(lote)}"
        res_lote = analizar_con_sdk(prompt_lote)
        acumulado += f"\nCandidatos Lote {i+1}: {res_lote}"

    print("Generando veredicto final en tips.json...")
    prompt_final = f"""
    Eres la IA de 'Pronosticos deportivos (IA)'. 
    Analiza estos candidatos pre-seleccionados de la jornada: {acumulado}
    
    Genera un JSON con:
    - 'tip_05' y 'tip_15' (3 picks de OVER 1.5 APUESTA cada uno).
    - 'tip_1x2x' (3 picks de 1X O 2X APUESTA).
    - 'tip_btts' (3 picks de BTTS APUESTA).
    - 'tip_bonus' (Los 3 mejores de toda la jornada).
    - 'puntos_actuales': BENEFICIO NETO (Resta 100 al beneficio total acumulado). Solo número.
    - 'analisis_tecnico': Resumen profesional de la jornada completa analizada.

    Responde ÚNICAMENTE el JSON puro.
    """
    
    resultado = analizar_con_sdk(prompt_final)
    
    if resultado:
        try:
            # Limpiamos posibles etiquetas de markdown
            limpio = resultado.replace("```json", "").replace("```", "").strip()
            json_data = json.loads(limpio)
            with open("tips.json", "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print("--- ¡ÉXITO! Jornada completa analizada y guardada ---")
        except Exception as e:
            print(f"Error al procesar JSON final: {e}")
            print(f"Texto recibido: {resultado}")

if __name__ == "__main__":
    main()
