import os
import requests
import json

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

def obtener_datos_futbol():
    url = "https://v3.football.api-sports.io/fixtures?next=50"
    headers = {'x-rapidapi-key': FOOTBALL_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
    try:
        response = requests.get(url, headers=headers)
        return response.json()
    except: return None

def generar_pronosticos_ia(datos_partidos):
    # Forzamos el uso del modelo que el sistema detectó: gemini-2.5-flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    prompt_text = f"""
    Eres el analista de 'Pronosticos deportivos (IA)'. 
    Analiza estos partidos reales y genera pronósticos estadísticos: {datos_partidos}
    
    REQUISITO: Genera un JSON con:
    - tip_05, tip_15, tip_1x2x, tip_btts, tip_as, tip_bonus (3 partidos cada uno con ⚽).
    - progression: 'puntos_actuales' (empieza en 100) y 'estado_hoy'.
    
    Responde UNICAMENTE el JSON. No digas nada más.
    """
    
    # Configuración de seguridad para que Gemini 2.5 no bloquee contenido de fútbol/apuestas
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ],
        "generationConfig": {
            "temperature": 0.7,
            "responseMimeType": "application/json"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        res_json = response.json()
        
        # Log para ver si Google nos manda un error de seguridad
        if 'candidates' not in res_json:
            print("Error de seguridad o respuesta vacía de Gemini 2.5")
            print("Respuesta de la API:", res_json)
            return None

        texto = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
        return texto
    except Exception as e:
        print(f"Error en Gemini 2.5: {e}")
        return None

def main():
    print("Iniciando con Gemini 2.5 Flash...")
    datos = obtener_datos_futbol()
    if not datos: return

    json_final = generar_pronosticos_ia(datos)
    if not json_final: return

    try:
        # Limpiamos posibles caracteres raros
        json_dict = json.loads(json_final)
        with open("tips.json", "w", encoding='utf-8') as f:
            json.dump(json_dict, f, ensure_ascii=False, indent=2)
        print("¡ÉXITO TOTAL! tips.json actualizado con Gemini 2.5.")
    except Exception as e:
        print(f"Error al procesar el JSON final: {e}")

if __name__ == "__main__":
    main()
