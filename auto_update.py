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
        print(f"Buscando TODOS los partidos de hoy ({hoy})...")
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
    # Lista de modelos por orden de prioridad para evitar el Error 404
    modelos = [
        "gemini-1.5-flash",
        "gemini-1.0-pro",
        "gemini-pro"
    ]
    
    for modelo in modelos:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={GEMINI_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            r = requests.post(url, json=payload, timeout=30)
            res = r.json()
            
            if 'candidates' in res:
                print(f"Éxito usando el modelo: {modelo}")
                return res['candidates'][0]['content']['parts'][0]['text'].strip()
            
            # Si el error no es un 404 (modelo no encontrado), imprimimos para saber qué pasa
            if 'error' in res and res['error'].get('code') != 404:
                print(f"Error en {modelo}: {res['error'].get('message')}")
                
        except Exception as e:
            continue
            
    print("Ninguno de los modelos de Google respondió correctamente.")
    return ""

def main():
    print("--- INICIANDO PROCESO PRONÓSTICOS DEPORTIVOS (IA) ---")
    todos = obtener_todos_los_partidos()
    
    if not todos:
        print("No se pudieron cargar los datos de fútbol.")
        return

    # Procesamos los 145 partidos para no perder ni una oportunidad de victoria
    lotes = [todos[i:i + 50] for i in range(0, len(todos), 50)]
    acumulado = ""

    for i, lote in enumerate(lotes):
        print(f"Analizando bloque {i+1} de {len(lotes)}...")
        prompt_lote = f"Selecciona los 8 mejores partidos para Over 1.5 goles y 1X2 de esta lista: {json.dumps(lote)}"
        res_lote = llamar_gemini(prompt_lote)
        acumulado += f"\nLote {i+1}: {res_lote}"

    print("Generando veredicto final para tips.json...")
    prompt_final = f"""
    Eres la IA de 'Pronosticos deportivos (IA)'. 
    Analiza estos candidatos: {acumulado}
    
    Genera un JSON con:
    - 'tip_05', 'tip_15' (3 picks de OVER 1.5 APUESTA cada uno).
    - 'tip_1x2x' (3 picks de 1X O 2X APUESTA).
    - 'tip_btts' (3 picks de BTTS APUESTA).
    - 'tip_bonus' (Los 3 mejores de toda la jornada).
    - 'puntos_actuales': BENEFICIO NETO (Resta 100 al total acumulado). Solo número.
    - 'analisis_tecnico': Resumen profesional de la jornada.

    Responde SOLO el JSON puro.
    """
    
    resultado = llamar_gemini(prompt_final)
    
    if resultado:
        try:
            if "```" in resultado:
                resultado = resultado.split("```")[1].replace("json", "").strip()
            
            json_data = json.loads(resultado)
            with open("tips.json", "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print("--- ¡ÉXITO! Jornada de 145 partidos analizada y guardada ---")
        except Exception as e:
            print(f"Error al procesar el JSON final: {e}")

if __name__ == "__main__":
    main()
