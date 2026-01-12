import os
import requests
import google.generativeai as genai
import json

# Configuración
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def obtener_datos():
    # Pedimos 50 próximos partidos
    url = "https://v3.football.api-sports.io/fixtures?next=50"
    headers = {'x-rapidapi-key': FOOTBALL_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
    return requests.get(url, headers=headers).json()

def generar_tips(data):
    prompt = f"""
    Analiza estos partidos: {data}
    Genera un JSON con 6 claves: tip_05, tip_15, tip_1x2x, tip_btts, tip_as, tip_bonus.
    Cada clave debe tener 3 partidos con el icono ⚽.
    Añade la clave 'progression' con:
    - 'puntos_actuales': Calcula el progreso desde 100 puntos iniciales.
    - 'estado_hoy': lista de los 3 partidos del tip_bonus con el icono ⏳.
    Responde solo JSON puro.
    """
    response = model.generate_content(prompt)
    # Limpieza básica por si Gemini añade ```json
    texto = response.text.replace('```json', '').replace('```', '').strip()
    return texto

try:
    partidos = obtener_datos()
    nuevo_json = generar_tips(partidos)
    # Validamos que sea un JSON correcto antes de guardar
    json.loads(nuevo_json) 
    with open("tips.json", "w", encoding='utf-8') as f:
        f.write(nuevo_json)
    print("Tips actualizados correctamente")
except Exception as e:
    print(f"Error: {e}")
