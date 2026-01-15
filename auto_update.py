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
            # Enviamos información compacta para maximizar la capacidad de la IA
            return [f"{p['teams']['home']['name']} vs {p['teams']['away']['name']} ({p['league']['name']})" for p in partidos]
        return None
    except Exception as e:
        print(f"Error de conexión Fútbol: {e}")
        return None

def analizar_lote(lote, num_lote):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = f"Analiza este lote #{num_lote} de partidos y selecciona los 8 mejores candidatos para Over 1.5, Doble Oportunidad (1X/2X) y Ambos marcan (BTTS): {json.dumps(lote)}. Responde solo con los nombres de los partidos elegidos."
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        r = requests.post(url, json=payload, timeout=30)
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Error analizando lote {num_lote}: {e}")
        return ""

def analisis_final(candidatos_acumulados):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    prompt = f"""
    Eres el analista jefe de 'Pronosticos deportivos (IA)'. 
    Basándote en estos finalistas seleccionados de toda la jornada: {candidatos_acumulados}
    
    Genera el JSON FINAL con los 3 mejores absolutos por categoría:
    - 'tip_05' y 'tip_15': 3 picks de OVER 1.5 APUESTA.
    - 'tip_1x2x': 3 picks de 1X O 2X APUESTA.
    - 'tip_btts': 3 picks de BTTS APUESTA.
    - 'tip_bonus': Los 3 más fiables de la jornada completa.
    
    Métricas de seguimiento:
    - 'puntos_actuales': Beneficio neto mensual (Resta 100 al total acumulado). Solo el número.
    - 'analisis_tecnico': Resumen profesional de la jornada (más de 140 partidos analizados).

    Responde ÚNICAMENTE el JSON puro.
    """

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2}
    }
    try:
        r = requests.post(url, json=payload, timeout=40)
        res = r.json()
        texto = res['candidates'][0]['content']['parts'][0]['text'].strip()
        # Limpieza de bloques de código markdown
        if "```" in texto:
            texto = texto.split("```")[1].replace("json", "").strip()
        return texto
    except Exception as e:
        print(f"Error en veredicto final: {e}")
        return None

def main():
    print("--- INICIANDO ANÁLISIS MASIVO DE JORNADA COMPLETA ---")
    todos = obtener_todos_los_partidos()
    
    if not todos:
        print("No se pudieron cargar partidos de la API de Fútbol.")
        return

    # División en lotes de 50 partidos para un análisis exhaustivo
    lotes = [todos[i:i + 50] for i in range(0, len(todos), 50)]
    pre_seleccionados = ""

    print(f"Procesando {len(lotes)} lotes de partidos...")
    for i, lote in enumerate(lotes):
        print(f"Analizando lote {i+1}...")
        res_lote = analizar_lote(lote, i+1)
        pre_seleccionados += f"\nCandidatos Lote {i+1}: {res_lote}"

    print("Generando veredicto final sobre toda la jornada...")
    resultado_final = analisis_final(pre_seleccionados)
    
    if resultado_final:
        try:
            # Validamos que sea un JSON correcto antes de guardar
            json_data = json.loads(resultado_final)
            with open("tips.json", "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print("--- ¡ÉXITO! tips.json actualizado con la jornada completa ---")
        except Exception as e:
            print(f"Error al procesar el JSON final: {e}")
            print(f"Texto recibido: {resultado_final}")

if __name__ == "__main__":
    main()
