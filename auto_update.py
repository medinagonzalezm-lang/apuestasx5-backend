import os
import requests
import json
from datetime import datetime, timedelta

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

def obtener_partidos():
    # Intentamos las dos combinaciones posibles de la API de Fútbol
    configuraciones = [
        {
            "url": "https://v3.football.api-sports.io/fixtures",
            "headers": {"x-apisports-key": FOOTBALL_KEY}
        },
        {
            "url": "https://v3.football.api-sports.io/fixtures",
            "headers": {
                "x-rapidapi-key": FOOTBALL_KEY,
                "x-rapidapi-host": "v3.football.api-sports.io"
            }
        }
    ]
    
    hoy = datetime.now().strftime("%Y-%m-%d")
    partidos_encontrados = []

    for conf in configuraciones:
        try:
            print(f"Probando conexión con: {conf['url']}...")
            r = requests.get(f"{conf['url']}?date={hoy}", headers=conf['headers'], timeout=15)
            res = r.json()
            
            if res.get('response'):
                print("¡Conexión exitosa con la API de Fútbol!")
                for f in res['response']:
                    partidos_encontrados.append({
                        "liga": f['league']['name'],
                        "local": f['teams']['home']['name'],
                        "visitante": f['teams']['away']['name']
                    })
                if partidos_encontrados: break
            else:
                print(f"Intento fallido: {res.get('errors') or res.get('message')}")
        except Exception as e:
            print(f"Error de red: {e}")

    return partidos_encontrados[:40]

def analizar_con_ia(partidos):
    # Usamos la URL de Gemini v1 estable
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    prompt = f"""
    Analiza estos partidos para la app 'Pronosticos deportivos (IA)': {json.dumps(partidos)}
    Devuelve un JSON con: tip_05, tip_15, tip_1x2x, tip_btts, tip_as, tip_bonus.
    En 'puntos_actuales', pon solo el BENEFICIO (Total - 100).
    En 'analisis_tecnico', un resumen breve.
    Responde SOLO el JSON.
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
    print("--- INICIANDO PROCESO ---")
    datos = obtener_partidos()
    
    if not datos:
        print("No se pudieron obtener partidos. Revisa tu FOOTBALL_API_KEY.")
        return

    print(f"Enviando {len(datos)} partidos a Gemini...")
    resultado = analizar_con_ia(datos)
    
    if resultado:
        try:
            final_json = json.loads(resultado)
            with open("tips.json", "w", encoding="utf-8") as f:
                json.dump(final_json, f, indent=2, ensure_ascii=False)
            print("--- ¡ÉXITO! tips.json actualizado ---")
        except:
            print("Error al procesar el JSON final.")

if __name__ == "__main__":
    main()
