import os
import requests
import json

# CONFIGURACIÓN
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

def obtener_datos_futbol():
    """Trae 50 partidos reales de la API de Fútbol."""
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
    """Llamada directa a la API REST de Gemini para evitar errores 404."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    prompt_text = f"""
    Eres el experto de 'Pronosticos deportivos (IA)'. 
    Analiza estos partidos reales: {datos_partidos}
    
    Genera un JSON con estas 6 claves:
    tip_05, tip_15, tip_1x2x, tip_btts, tip_as, tip_bonus.
    Cada clave debe contener 3 partidos reales con el icono ⚽.
    
    Añade la clave 'progression' con:
    - 'puntos_actuales': Seguimiento excluyendo los 100€ iniciales.
    - 'estado_hoy': Los 3 partidos del 'tip_bonus' con el icono ⏳.
    
    Responde SOLAMENTE el JSON puro, sin bloques de código ni texto extra.
    """

    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        res_json = response.json()
        texto = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
        
        # Limpiar posible formato Markdown
        if "```" in texto:
            texto = texto.split("```")[1].replace("json", "").strip()
        return texto
    except Exception as e:
        print(f"Error Gemini: {e}")
        return None

def main():
    print("Iniciando actualización...")
    datos = obtener_datos_futbol()
    if not datos: return

    json_final = generar_pronosticos_ia(datos)
    if not json_final: return

    try:
        # Validar y guardar
        json_dict = json.loads(json_final)
        with open("tips.json", "w", encoding='utf-8') as f:
            json.dump(json_dict, f, ensure_ascii=False, indent=2)
        print("¡ÉXITO TOTAL! tips.json actualizado.")
    except Exception as e:
        print(f"Error validando JSON: {e}")

if __name__ == "__main__":
    main()
