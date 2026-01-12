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
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    prompt_text = f"""
    Eres el experto de 'Pronosticos deportivos (IA)'. 
    Analiza estos partidos: {datos_partidos}
    Genera un JSON con las claves: tip_05, tip_15, tip_1x2x, tip_btts, tip_as, tip_bonus.
    Añade 'progression' con 'puntos_actuales' (base 100) y 'estado_hoy'.
    Responde SOLAMENTE el JSON puro.
    """

    # Añadimos configuración para saltar filtros de seguridad por palabras de "apuestas"
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        res_json = response.json()
        
        # Si hay un error de API (ej: clave inválida), nos lo dirá aquí
        if 'error' in res_json:
            print(f"Error de la API de Google: {res_json['error']['message']}")
            return None

        # Si el filtro bloqueó la respuesta
        if 'candidates' not in res_json or not res_json['candidates'][0].get('content'):
            print("Gemini bloqueó la respuesta por seguridad o devolvió vacío.")
            print("Respuesta completa para debug:", res_json)
            return None

        texto = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
        if "```" in texto:
            texto = texto.split("```")[1].replace("json", "").strip()
        return texto
    except Exception as e:
        print(f"Error detallado: {e}")
        return None

def main():
    print("Iniciando actualización con bypass de filtros...")
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
