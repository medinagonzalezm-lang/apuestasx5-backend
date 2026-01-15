import os
import requests
import json
from datetime import datetime

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

def obtener_partidos():
    headers = {
        'x-rapidapi-key': FOOTBALL_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    url = f"https://v3.football.api-sports.io/fixtures?date={datetime.now().strftime('%Y-%m-%d')}"
    try:
        r = requests.get(url, headers=headers, timeout=15)
        res = r.json()
        partidos = []
        for f in res.get('response', [])[:40]:
            partidos.append({
                "liga": f['league']['name'],
                "local": f['teams']['home']['name'],
                "visitante": f['teams']['away']['name']
            })
        return partidos
    except:
        return None

def analizar_con_ia(datos_partidos):
    # Usamos la URL directa de la API v1 (la más estable)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    prompt = f"""
    Eres un experto en apuestas. Analiza estos partidos: {json.dumps(datos_partidos)}
    Genera un JSON con: tip_05, tip_15, tip_1x2x, tip_btts, tip_as, tip_bonus (3 picks cada uno).
    En 'puntos_actuales', pon el BENEFICIO NETO (Resta 100 del total acumulado).
    En 'analisis_tecnico', un resumen breve.
    Responde SOLO el JSON puro, sin bloques de código.
    """

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        res_json = response.json()
        
        if 'candidates' in res_json:
            texto = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
            # Limpiar si la IA devuelve ```json ... ```
            if "```" in texto:
                texto = texto.split("```")[1].replace("json", "").strip()
            return texto
        else:
            print(f"Error de API: {res_json}")
            return None
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

def main():
    print("Iniciando IA (Conexión Directa v1)...")
    partidos = obtener_partidos()
    if not partidos:
        print("No se obtuvieron partidos.")
        return

    resultado = analizar_con_ia(partidos)
    if resultado:
        try:
            json_data = json.loads(resultado)
            with open("tips.json", "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print("¡EXITO! tips.json actualizado.")
        except:
            print("Error al procesar el JSON de la IA.")

if __name__ == "__main__":
    main()
