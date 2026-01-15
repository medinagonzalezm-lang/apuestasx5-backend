import os
import requests
import json
from datetime import datetime, timedelta

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

def obtener_partidos():
    # Formato de cabeceras estándar para API-Sports
    headers = {
        'x-apisports-key': FOOTBALL_KEY,
        'Content-Type': 'application/json'
    }
    
    hoy = datetime.now().strftime("%Y-%m-%d")
    mañana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    partidos_totales = []
    
    # Intentamos con la URL de API-Sports que es más estable
    for fecha in [hoy, mañana]:
        url = f"https://v3.football.api-sports.io/fixtures?date={fecha}"
        try:
            print(f"Consultando fecha: {fecha}...")
            r = requests.get(url, headers=headers, timeout=20)
            res = r.json()
            
            # Verificación de errores en la respuesta
            if res.get('errors'):
                print(f"Aviso de API Fútbol: {res['errors']}")
                # Si falla el primer nombre de cabecera, intentamos con el alternativo de RapidAPI
                headers_alt = {'x-rapidapi-key': FOOTBALL_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
                r = requests.get(url, headers=headers_alt, timeout=20)
                res = r.json()

            datos = res.get('response', [])
            if not datos:
                print(f"No se encontraron partidos para la fecha {fecha}.")
                continue
                
            for f in datos:
                partidos_totales.append({
                    "liga": f['league']['name'],
                    "local": f['teams']['home']['name'],
                    "visitante": f['teams']['away']['name']
                })
        except Exception as e:
            print(f"Error de conexión: {e}")
            
    return partidos_totales[:45]

def analizar_con_ia(datos_partidos):
    # Usamos el endpoint estable v1
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    prompt = f"""
    Eres analista experto de 'Pronosticos deportivos (IA)'. 
    Analiza: {json.dumps(datos_partidos)}
    Genera un JSON: tip_05, tip_15, tip_1x2x, tip_btts, tip_as, tip_bonus (3 c/u).
    'puntos_actuales': BENEFICIO NETO (Total acumulado - 100).
    'analisis_tecnico': Resumen breve.
    Responde SOLO JSON puro.
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, json=payload, timeout=30)
        res_json = response.json()
        if 'candidates' in res_json:
            texto = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
            if "```" in texto:
                texto = texto.split("```")[1].replace("json", "").strip()
            return texto
        return None
    except Exception as e:
        print(f"Error IA: {e}")
        return None

def main():
    print("Iniciando proceso...")
    partidos = obtener_partidos()
    
    if not partidos:
        print("CRÍTICO: No se recibieron datos. Verifica tu clave en Dashboard API-Football.")
        return

    print(f"Procesando {len(partidos)} partidos con Gemini...")
    resultado = analizar_con_ia(partidos)
    
    if resultado:
        try:
            json_data = json.loads(resultado)
            with open("tips.json", "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print("¡ACTUALIZACIÓN COMPLETADA!")
        except:
            print("Error al parsear el JSON de la IA.")

if __name__ == "__main__":
    main()
