import os
import requests
import json
from datetime import datetime

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

def obtener_partidos():
    # Intentamos las tres rutas posibles para evitar el error 4xSe
    rutas = [
        {
            "url": "https://api-football-v1.p.rapidapi.com/v3/fixtures",
            "headers": {
                "x-rapidapi-key": FOOTBALL_KEY,
                "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
            }
        },
        {
            "url": "https://v3.football.api-sports.io/fixtures",
            "headers": {"x-apisports-key": FOOTBALL_KEY}
        }
    ]
    
    hoy = datetime.now().strftime("%Y-%m-%d")
    partidos_encontrados = []

    for r_info in rutas:
        try:
            print(f"Probando endpoint: {r_info['url']}...")
            r = requests.get(f"{r_info['url']}?date={hoy}", headers=r_info['headers'], timeout=15)
            res = r.json()
            
            if res.get('response'):
                print("¡CONECTADO EXITOSAMENTE!")
                for f in res['response']:
                    partidos_encontrados.append({
                        "liga": f['league']['name'],
                        "local": f['teams']['home']['name'],
                        "visitante": f['teams']['away']['name']
                    })
                if partidos_encontrados: break
            else:
                print(f"Respuesta sin datos: {res.get('errors') or res.get('message')}")
        except Exception as e:
            print(f"Error en este intento: {e}")

    return partidos_encontrados[:40]

def analizar_con_ia(partidos):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    prompt = f"""
    Eres analista para 'Pronosticos deportivos (IA)'. Analiza: {json.dumps(partidos)}
    Genera JSON con: tip_05, tip_15, tip_1x2x, tip_btts, tip_as, tip_bonus.
    En 'puntos_actuales', pon solo el BENEFICIO (Total acumulado - 100).
    Responde SOLO JSON puro.
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        r = requests.post(url, json=payload, timeout=30)
        res = r.json()
        texto = res['candidates'][0]['content']['parts'][0]['text'].strip()
        if "```" in texto:
            texto = texto.split("```")[1].replace("json", "").strip()
        return texto
    except Exception as e:
        print(f"Error IA: {e}")
        return None

def main():
    print("--- INICIANDO PROCESO DE ACTUALIZACIÓN ---")
    datos = obtener_partidos()
    
    if not datos:
        print("ERROR: No se pudo validar la FOOTBALL_API_KEY. Asegúrate de copiarla de RapidAPI o API-Sports Dashboard.")
        return

    print(f"Analizando {len(datos)} partidos...")
    resultado = analizar_con_ia(datos)
    
    if resultado:
        try:
            final_json = json.loads(resultado)
            with open("tips.json", "w", encoding="utf-8") as f:
                json.dump(final_json, f, indent=2, ensure_ascii=False)
            print("--- PROCESO FINALIZADO CON ÉXITO ---")
        except:
            print("Error al procesar el resultado de la IA.")

if __name__ == "__main__":
    main()
