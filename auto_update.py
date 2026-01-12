import os
import requests
import json

# CONFIGURACIÓN
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

def obtener_datos_futbol():
    url = "https://v3.football.api-sports.io/fixtures?next=50"
    headers = {
        'x-rapidapi-key': FOOTBALL_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    try:
        response = requests.get(url, headers=headers)
        return response.json()
    except Exception as e:
        print(f"Error API Futbol: {e}")
        return None

def generar_pronosticos_ia(datos_partidos):
    # Usamos gemini-1.0-pro que es el modelo con la ruta más estable para evitar el 404
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.0-pro:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    prompt_text = f"""
    Eres el experto de 'Pronosticos deportivos (IA)'. 
    Analiza estos partidos reales: {datos_partidos}
    Genera un JSON con las claves: tip_05, tip_15, tip_1x2x, tip_btts, tip_as, tip_bonus.
    Añade 'progression' con 'puntos_actuales' (base 100) y 'estado_hoy'.
    Responde SOLAMENTE el JSON puro.
    """

    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        res_json = response.json()
        
        # Si este falla, es que la Key tiene un problema de activación
        if 'error' in res_json:
            print(f"Error definitivo de Google: {res_json['error']['message']}")
            return None

        texto = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
        if "```" in texto:
            texto = texto.split("```")[1].replace("json", "").strip()
        return texto
    except Exception as e:
        print(f"Error en el proceso: {e}")
        return None

def main():
    print("Iniciando con modelo universal gemini-1.0-pro...")
    datos = obtener_datos_futbol()
    if not datos: return

    json_final = generar_pronosticos_ia(datos)
    if not json_final: return

    try:
        json_dict = json.loads(json_final)
        with open("tips.json", "w", encoding='utf-8') as f:
            json.dump(json_dict, f, ensure_ascii=False, indent=2)
        print("¡ÉXITO TOTAL! tips.json actualizado.")
    except Exception as e:
        print(f"Error JSON: {e}")

if __name__ == "__main__":
    main()
