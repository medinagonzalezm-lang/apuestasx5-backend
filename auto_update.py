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
    hoy = datetime.now().strftime("%Y-%m-%d")
    url = f"https://v3.football.api-sports.io/fixtures?date={hoy}"
    try:
        r = requests.get(url, headers=headers, timeout=15)
        res = r.json()
        partidos = []
        # Tomamos 40 partidos para el análisis
        for f in res.get('response', [])[:40]:
            partidos.append({
                "liga": f['league']['name'],
                "local": f['teams']['home']['name'],
                "visitante": f['teams']['away']['name']
            })
        return partidos
    except Exception as e:
        print(f"Error Football API: {e}")
        return None

def analizar_con_ia(datos_partidos):
    # Usamos v1beta que es la más flexible con las claves nuevas
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    prompt = f"""
    Eres un analista experto para 'Pronosticos deportivos (IA)'. 
    Analiza estos partidos: {json.dumps(datos_partidos)}
    
    Genera un JSON con este formato:
    - 'tip_05', 'tip_15', 'tip_1x2x', 'tip_btts', 'tip_as', 'tip_bonus' (3 picks cada uno).
    - 'puntos_actuales': Beneficio neto (Total - 100).
    - 'analisis_tecnico': Resumen breve.

    Responde SOLO el JSON puro.
    """

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        res_json = response.json()
        
        if 'candidates' in res_json:
            texto = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
            # Limpiar markdown si existe
            if "```" in texto:
                texto = texto.split("```")[1].replace("json", "").strip()
            return texto
        else:
            print(f"Error de Google: {res_json}")
            return None
    except Exception as e:
        print(f"Error de red: {e}")
        return None

def main():
    print("Iniciando IA con clave renovada...")
    partidos = obtener_partidos()
    if not partidos:
        print("No se pudieron obtener partidos.")
        return

    print(f"Analizando {len(partidos)} partidos...")
    resultado = analizar_con_ia(partidos)
    if resultado:
        try:
            json_data = json.loads(resultado)
            with open("tips.json", "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print("¡ACTUALIZACIÓN COMPLETADA EXITOSAMENTE!")
        except Exception as e:
            print(f"Error al procesar JSON: {e}")
            print(f"Texto recibido: {resultado}")

if __name__ == "__main__":
    main()
