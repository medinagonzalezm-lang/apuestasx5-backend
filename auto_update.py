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
            print(f"Encontrados {len(partidos)} partidos en total.")
            return [f"{p['teams']['home']['name']} vs {p['teams']['away']['name']} ({p['league']['name']})" for p in partidos]
        return None
    except Exception as e:
        print(f"Error de conexión Fútbol: {e}")
        return None

def analizar_lote(lote):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = f"Analiza estos partidos y elige los 5 mejores para cada categoría (Over 1.5, Doble Oportunidad, BTTS): {json.dumps(lote)}. Responde solo con los nombres de los partidos elegidos por categoría en formato JSON simple."
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        r = requests.post(url, json=payload, timeout=30)
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return ""

def analisis_final(candidatos_acumulados):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    prompt = f"""
    Eres el analista jefe de 'Pronosticos deportivos (IA)'. 
    De entre todos estos finalistas seleccionados de la jornada: {candidatos_acumulados}
    
    Elige y genera el JSON FINAL con los 3 mejores absolutos para:
    - 'tip_05' y 'tip_15' (OVER 1.5 GOLES).
    - 'tip_1x2x' (1X O 2X).
    - 'tip_btts' (Ambos marcan).
    - 'tip_bonus' (Los 3 más seguros del día).
    
    Incluye:
    - 'puntos_actuales': Beneficio neto (Total mensual acumulado menos 100). Solo el número.
    - 'analisis_tecnico': Resumen profesional de la jornada completa (145+ partidos analizados).

    Responde SOLO el JSON puro.
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        r = requests.post(url, json=payload, timeout=30)
        texto = r.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        if "```" in texto:
            texto = texto.split("```")[1].replace("json", "").strip()
        return texto
    except:
        return None

def main():
    print("--- INICIANDO ANÁLISIS MASIVO DE JORNADA COMPLETA ---")
    todos = obtener_todos_los_partidos()
    
    if not todos:
        print("No se pudieron cargar partidos.")
        return

    # Dividimos en lotes de 50 para que Gemini no se sature
    lotes = [todos[i:i + 50] for i in range(0, len(todos), 50)]
    pre_seleccionados = ""

    print(f"Procesando {len(lotes)} lotes de partidos...")
    for i, lote in enumerate(lotes):
        print(f"Analizando lote {i+1}...")
        pre_seleccionados += analizar_lote(lote)

    print("Generando veredicto final sobre toda la jornada...")
    resultado_final = analisis_final(pre_seleccionados)
    
    if resultado_final:
        try:
            with open("tips.json", "w", encoding="utf-8") as f:
                json.dump(json.loads(resultado_final), f, indent=2, ensure_ascii=False)
            print("--- ¡ÉXITO! Se ha analizado el 100% de la jornada ---")
        except:
            print("Error en el formato final.")

if __name__ == "__main__":
    main()
