import os
import requests
import json
import google.generativeai as genai
from datetime import datetime

# Configuración
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

# Configurar el SDK oficial
genai.configure(api_key=GEMINI_KEY)

def obtener_partidos():
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
            # Enviamos info compacta: Local vs Visitante (Liga)
            return [f"{p['teams']['home']['name']} vs {p['teams']['away']['name']} ({p['league']['name']})" for p in partidos]
        return None
    except Exception as e:
        print(f"Error Fútbol: {e}")
        return None

def analizar_con_ia(prompt):
    try:
        # Usamos gemini-1.5-flash a través del SDK oficial
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error en el SDK de Gemini: {e}")
        return ""

def main():
    print("--- INICIANDO PROCESO PRONÓSTICOS DEPORTIVOS (IA) ---")
    todos = obtener_partidos()
    
    if not todos:
        print("No se obtuvieron datos de fútbol.")
        return

    # Dividimos los 145 partidos en bloques de 50 para análisis total
    lotes = [todos[i:i + 50] for i in range(0, len(todos), 50)]
    pre_seleccionados = ""

    for i, lote in enumerate(lotes):
        print(f"Analizando bloque {i+1} de {len(lotes)}...")
        prompt_lote = f"Analiza estos partidos y selecciona los 10 con mayor probabilidad de Over 1.5 goles o victoria local/visitante: {json.dumps(lote)}"
        res_lote = analizar_con_ia(prompt_lote)
        pre_seleccionados += f"\nCandidatos Lote {i+1}: {res_lote}"

    print("Generando veredicto final en tips.json...")
    prompt_final = f"""
    Eres la IA de 'Pronosticos deportivos (IA)'. 
    Basado en estos candidatos: {pre_seleccionados}
    
    Genera un JSON con:
    - 'tip_05', 'tip_15' (3 picks OVER 1.5 APUESTA cada uno).
    - 'tip_1x2x' (3 picks 1X O 2X APUESTA).
    - 'tip_btts' (3 picks BTTS APUESTA).
    - 'tip_bonus' (Los 3 mejores de la jornada completa).
    - 'puntos_actuales': BENEFICIO NETO (Calcula el total y resta 100). Solo el número.
    - 'analisis_tecnico': Resumen profesional de la jornada.

    Responde ÚNICAMENTE el JSON puro.
    """
    
    resultado = analizar_con_ia(prompt_final)
    
    if resultado:
        try:
            # Limpiar posibles etiquetas de markdown
            limpio = resultado.replace("```json", "").replace("```", "").strip()
            json_data = json.loads(limpio)
            with open("tips.json", "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print("--- ¡ÉXITO! tips.json actualizado con la jornada completa ---")
        except Exception as e:
            print(f"Error al procesar JSON final: {e}")
            print(f"Texto recibido: {resultado}")

if __name__ == "__main__":
    main()
