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
            # Formato ultra-compacto para maximizar capacidad
            return [f"{p['teams']['home']['name']}-{p['teams']['away']['name']}({p['league']['name']})" for p in partidos]
        return None
    except Exception as e:
        print(f"Error Fútbol: {e}")
        return None

def llamar_gemini(prompt):
    # Ruta corregida para evitar el error 404 de 'model not found'
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "topP": 0.95,
            "maxOutputTokens": 1024
        }
    }
    
    try:
        r = requests.post(url, json=payload, timeout=40)
        res = r.json()
        
        if 'candidates' in res and len(res['candidates']) > 0:
            return res['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            # Si v1beta falla, intentamos v1 automáticamente con el mismo payload
            url_v1 = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
            r = requests.post(url_v1, json=payload, timeout=40)
            res = r.json()
            if 'candidates' in res:
                return res['candidates'][0]['content']['parts'][0]['text'].strip()
            
            print(f"Error IA: {res.get('error', {}).get('message', 'Unknown error')}")
            return ""
    except Exception as e:
        print(f"Error de red IA: {e}")
        return ""

def main():
    print("--- INICIANDO PROCESO PRONÓSTICOS DEPORTIVOS (IA) ---")
    todos = obtener_todos_los_partidos()
    
    if not todos:
        print("No se obtuvieron partidos de la API.")
        return

    # Procesamos por lotes de 50 para analizar el 100% de la jornada
    lotes = [todos[i:i + 50] for i in range(0, len(todos), 50)]
    acumulado_filtro = ""

    for i, lote in enumerate(lotes):
        print(f"Analizando bloque {i+1} de {len(lotes)}...")
        prompt_lote = f"De estos partidos, dime los 5 mejores para Over 1.5 goles y 1X2: {','.join(lote)}"
        acumulado_filtro += llamar_gemini(prompt_lote)

    print("Generando archivo tips.json final...")
    prompt_final = f"""
    Eres el experto de 'Pronosticos deportivos (IA)'. 
    Usa estos candidatos: {acumulado_filtro}
    
    Genera un JSON con:
    - 'tip_05', 'tip_15' (3 picks OVER 1.5 cada uno).
    - 'tip_1x2x' (3 picks 1X o 2X).
    - 'tip_btts' (3 picks Ambos Marcan).
    - 'tip_bonus' (Los 3 mejores del día).
    - 'puntos_actuales': Beneficio neto (Suma total menos 100). Solo número.
    - 'analisis_tecnico': Resumen breve de la jornada.

    Responde SOLO JSON puro.
    """
    
    resultado = llamar_gemini(prompt_final)
    
    if resultado:
        try:
            if "```" in resultado:
                resultado = resultado.split("```")[1].replace("json", "").strip()
            
            json_data = json.loads(resultado)
            with open("tips.json", "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print("--- ¡ÉXITO! Análisis de jornada completa guardado ---")
        except Exception as e:
            print(f"Error parseando JSON: {e}")

if __name__ == "__main__":
    main()
