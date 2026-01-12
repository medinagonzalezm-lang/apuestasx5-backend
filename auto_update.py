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

def obtener_modelo_valido():
    """Pregunta a Google qué modelos puede usar esta API Key."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_KEY}"
    try:
        res = requests.get(url).json()
        for m in res.get('models', []):
            if 'generateContent' in m.get('supportedGenerationMethods', []):
                return m['name'] # Devuelve el primero compatible (ej: models/gemini-1.5-flash)
        return "models/gemini-pro" # Fallback
    except:
        return "models/gemini-pro"

def generar_pronosticos_ia(datos_partidos, modelo_nombre):
    url = f"https://generativelanguage.googleapis.com/v1beta/{modelo_nombre}:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    prompt_text = f"Analiza estos partidos y genera un JSON con tips de apuestas (0.5, 1.5, 1X2, BTTS, AS, BONUS) y progression (base 100): {datos_partidos}. Responde solo el JSON puro."
    
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
    try:
        response = requests.post(url, headers=headers, json=payload)
        res_json = response.json()
        texto = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
        if "```" in texto:
            texto = texto.split("```")[1].replace("json", "").strip()
        return texto
    except Exception as e:
        print(f"Error con modelo {modelo_nombre}: {e}")
        return None

def main():
    print("Buscando modelo disponible para tu cuenta...")
    modelo = obtener_modelo_valido()
    print(f"Usando modelo: {modelo}")
    
    datos = obtener_datos_futbol()
    if not datos: return

    json_final = generar_pronosticos_ia(datos, modelo)
    if not json_final: return

    try:
        json_dict = json.loads(json_final)
        with open("tips.json", "w", encoding='utf-8') as f:
            json.dump(json_dict, f, ensure_ascii=False, indent=2)
        print("¡ÉXITO TOTAL! tips.json actualizado.")
    except:
        print("Error en formato JSON")

if __name__ == "__main__":
    main()
