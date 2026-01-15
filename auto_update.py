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
            # Compactamos al máximo para que la IA procese la jornada completa
            return [f"{p['teams']['home']['name']} vs {p['teams']['away']['name']}" for p in partidos]
        return None
    except Exception as e:
        print(f"Error Fútbol: {e}")
        return None

def llamar_gemini(prompt):
    # USAMOS 'gemini-1.5-flash-latest' que es la ruta más compatible actualmente
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2
        }
    }
    
    try:
        r = requests.post(url, json=payload, timeout=40)
        res = r.json()
        
        if 'candidates' in res and len(res['candidates']) > 0:
            return res['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            # Imprimimos el error real de Google para diagnóstico
            print(f"Respuesta inesperada de Google: {json.dumps(res)}")
            return ""
    except Exception as e:
        print(f"Error de red IA: {e}")
        return ""

def main():
    print("--- INICIANDO PROCESO PRONÓSTICOS DEPORTIVOS (IA) ---")
    todos = obtener_todos_los_partidos()
    
    if not todos:
        print("No se obtuvieron partidos de la API de Fútbol.")
        return

    # Dividimos en lotes para asegurar que analice los 145 partidos
    lotes = [todos[i:i + 50] for i in range(0, len(todos), 50)]
    acumulado = ""

    for i, lote in enumerate(lotes):
        print(f"Analizando bloque {i+1} de {len(lotes)}...")
        prompt_lote = f"De estos partidos, selecciona los mejores para Over 1.5 y Ambos Marcan: {', '.join(lote)}"
        acumulado += llamar_gemini(prompt_lote)

    print("Generando veredicto final en tips.json...")
    prompt_final = f"""
    Eres el analista de 'Pronosticos deportivos (IA)'. 
    Basado en estos candidatos: {acumulado}
    
    Genera un JSON con:
    - 'tip_05', 'tip_15' (3 picks de OVER 1.5 APUESTA cada uno).
    - 'tip_1x2x' (3 picks de 1X O 2X APUESTA).
    - 'tip_btts' (3 picks de BTTS APUESTA).
    - 'tip_bonus' (Los 3 más fiables de toda la jornada).
    - 'puntos_actuales': BENEFICIO NETO (Suma total acumulada menos 100).
    - 'analisis_tecnico': Resumen de la jornada.

    Responde SOLO JSON puro.
    """
    
    resultado = llamar_gemini(prompt_final)
    
    if resultado:
        try:
            # Limpiar markdown si la IA lo incluye
            if "```" in resultado:
                resultado = resultado.split("```")[1].replace("json", "").strip()
            
            json_data = json.loads(resultado)
            with open("tips.json", "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print("--- ¡ÉXITO! Análisis completado y tips.json actualizado ---")
        except Exception as e:
            print(f"Error al procesar el JSON final: {e}")
            print(f"Texto recibido: {resultado}")

if __name__ == "__main__":
    main()
