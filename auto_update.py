import os
import requests
import google.generativeai as genai
import json

# 1. CONFIGURACIÓN DE APIS
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

# Configuración mejorada para evitar el Error 404
genai.configure(api_key=GEMINI_KEY)

# Cambiamos a 'gemini-1.5-flash-latest' o 'models/gemini-1.5-flash'
model = genai.GenerativeModel('models/gemini-1.5-flash')

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
        print(f"Error al obtener datos de fútbol: {e}")
        return None

def generar_pronosticos_ia(datos_partidos):
    prompt = f"""
    Eres un experto en apuestas. Analiza estos partidos reales: {datos_partidos}
    Genera un JSON con estas claves: tip_05, tip_15, tip_1x2x, tip_btts, tip_as, tip_bonus.
    Cada una con 3 partidos reales y el icono ⚽.
    Añade 'progression' con:
    - 'puntos_actuales': Seguimiento desde 100 puntos iniciales.
    - 'estado_hoy': Los 3 partidos del 'tip_bonus' con el icono ⏳.
    Responde EXCLUSIVAMENTE el JSON puro.
    """
    
    try:
        # Forzamos la generación sin usar funciones beta que den 404
        response = model.generate_content(prompt)
        texto = response.text.strip()
        
        # Limpieza de markdown
        if "```" in texto:
            texto = texto.split("```")[1]
            if texto.startswith("json"):
                texto = texto[4:]
        return texto.strip()
    except Exception as e:
        print(f"Error en Gemini: {e}")
        return None

def main():
    print("Iniciando actualización diaria...")
    datos = obtener_datos_futbol()
    if not datos:
        print("No se obtuvieron datos de fútbol.")
        return

    json_final = generar_pronosticos_ia(datos)
    if not json_final:
        print("Gemini no devolvió resultados.")
        return

    try:
        # Validar JSON
        json_dict = json.loads(json_final)
        with open("tips.json", "w", encoding='utf-8') as f:
            json.dump(json_dict, f, ensure_ascii=False, indent=2)
        print("¡ÉXITO! El archivo tips.json ha sido actualizado.")
    except Exception as e:
        print(f"Error al validar JSON: {e}")
        print("Contenido:", json_final)

if __name__ == "__main__":
    main()
