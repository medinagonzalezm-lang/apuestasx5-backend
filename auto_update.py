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
    """Función centralizada para llamar a la IA con manejo de errores robusto"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ],
        "generationConfig": {"temperature": 0.1}
    }
    
    try:
        r = requests.post(url, json=payload, timeout=40)
        res = r.json()
        
        # Verificamos si Google bloqueó la respuesta
        if 'candidates' not in res:
            print(f"Advertencia: La IA no devolvió candidatos. Respuesta completa: {res}")
            return ""
            
        texto = res['candidates'][0]['content']['parts'][0]['text'].strip()
        return texto
    except Exception as e:
        print(f"Error en llamada a Gemini: {e}")
        return ""

def main():
    print("--- INICIANDO ANÁLISIS DE JORNADA COMPLETA ---")
    todos = obtener_todos_los_partidos()
    
    if not todos:
        print("No se pudieron cargar partidos.")
        return

    # Procesar lotes
    lotes = [todos[i:i + 50] for i in range(0, len(todos), 50)]
    pre_seleccionados = ""

    for i, lote in enumerate(lotes):
        print(f"Filtrando lote {i+1} de {len(lotes)}...")
        prompt_lote = f"Lista los 5 partidos más probables para Over 1.5 goles de esta lista: {json.dumps(lote)}. Responde solo los nombres."
        pre_seleccionados += llamar_gemini(prompt_lote)

    print("Generando veredicto final para 'Pronosticos deportivos (IA)'...")
    prompt_final = f"""
    Basado en estos partidos pre-seleccionados: {pre_seleccionados}
    
    Genera un JSON con:
    - 'tip_05', 'tip_15' (3 picks OVER 1.5 cada uno).
    - 'tip_1x2x' (3 picks 1X O 2X).
    - 'tip_btts' (3 picks Ambos Marcan).
    - 'tip_bonus' (Los 3 mejores de todos).
    - 'puntos_actuales': Beneficio neto (Total - 100). Solo número.
    - 'analisis_tecnico': Resumen de la jornada.

    Responde SOLO JSON puro.
    """
    
    resultado_final = llamar_gemini(prompt_final)
    
    if resultado_final:
        try:
            # Limpiamos markdown si existe
            if "```" in resultado_final:
                resultado_final = resultado_final.split("```")[1].replace("json", "").strip()
            
            json_data = json.loads(resultado_final)
            with open("tips.json", "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print("--- ¡ACTUALIZACIÓN COMPLETADA EXITOSAMENTE! ---")
        except Exception as e:
            print(f"Error al procesar el JSON final: {e}")

if __name__ == "__main__":
    main()
