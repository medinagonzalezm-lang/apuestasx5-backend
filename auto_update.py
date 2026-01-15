import os
import requests
import json
from datetime import datetime, timedelta

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

def obtener_partidos():
    headers = {
        'x-rapidapi-key': FOOTBALL_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    
    # Intentamos obtener partidos de hoy y de mañana para asegurar datos
    hoy = datetime.now().strftime("%Y-%m-%d")
    mañana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    partidos_totales = []
    
    for fecha in [hoy, mañana]:
        url = f"https://v3.football.api-sports.io/fixtures?date={fecha}"
        try:
            r = requests.get(url, headers=headers, timeout=15)
            res = r.json()
            
            # Si hay error en la API de fútbol, lo imprimimos para saber qué pasa
            if res.get('errors'):
                print(f"Error de API Fútbol ({fecha}): {res['errors']}")
                continue
                
            datos = res.get('response', [])
            for f in datos:
                partidos_totales.append({
                    "liga": f['league']['name'],
                    "local": f['teams']['home']['name'],
                    "visitante": f['teams']['away']['name']
                })
        except Exception as e:
            print(f"Error de conexión en fecha {fecha}: {e}")
            
    return partidos_totales[:50] # Máximo 50 partidos para no saturar

def analizar_con_ia(datos_partidos):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    prompt = f"""
    Eres un analista experto para 'Pronosticos deportivos (IA)'. 
    Analiza estos partidos: {json.dumps(datos_partidos)}
    
    Genera un JSON con este formato:
    - 'tip_05', 'tip_15', 'tip_1x2x', 'tip_btts', 'tip_as', 'tip_bonus' (3 picks cada uno).
    - 'puntos_actuales': Beneficio neto (Total acumulado menos 100).
    - 'analisis_tecnico': Resumen breve de la jornada.

    Responde SOLO el JSON puro, sin bloques de código.
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
        else:
            print(f"Error de Gemini: {res_json}")
            return None
    except Exception as e:
        print(f"Error IA: {e}")
        return None

def main():
    print("Iniciando IA...")
    partidos = obtener_partidos()
    
    if not partidos:
        print("CRÍTICO: Sigue sin haber partidos. Revisa tu FOOTBALL_API_KEY en Secrets.")
        return

    print(f"Analizando {len(partidos)} partidos encontrados...")
    resultado = analizar_con_ia(partidos)
    
    if resultado:
        try:
            json_data = json.loads(resultado)
            with open("tips.json", "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print("¡ACTUALIZACIÓN COMPLETADA!")
        except:
            print("Error al procesar el JSON final.")

if __name__ == "__main__":
    main()
