import os
import requests
import google.generativeai as genai
import json

# CONFIGURACIÓN
GEMINI_KEY = "AIzaSyCL_YB0HI27QKXdk0_K8dorUtuzPBOUgQE"
FOOTBALL_KEY = "ace74b368016e12059d2a44bc893d69d"

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def obtener_partidos_reales():
    # Consultamos los próximos 50 partidos de las ligas top y secundarias
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {'x-rapidapi-key': FOOTBALL_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
    params = {"next": "50"} 
    
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json()['response']
    except:
        return []

def generar_json_automatizado(datos):
    # Prompt maestro para que Gemini genere el JSON perfecto
    prompt = f"""
    Eres el analista de 'Pronósticos Deportivos (IA)'. 
    Usa estos datos reales de partidos: {datos}
    
    Genera un JSON con: tip_05, tip_15, tip_1x2x, tip_btts, tip_as, tip_bonus.
    
    REGLAS ESTRICTAS:
    - 3 partidos por categoría con el icono ⚽.
    - Calcula 'cuota_final' multiplicando las 3 cuotas.
    - Para 'tip_bonus', elige los 3 más fiables del día.
    - 'explicacion' técnica y profesional.
    - Incluye una sección 'progression' con: 'puntos_actuales', 'mes' (ENERO), y 'hoy' (lista de partidos con ⏳).
    
    IMPORTANTE: Si no tienes partidos suficientes de ligas top, usa ligas de cualquier parte del mundo pero que sean reales para hoy/mañana.
    Responde SOLO el JSON.
    """
    
    response = model.generate_content(prompt)
    # Limpiamos la respuesta para asegurarnos de que sea JSON puro
    raw_json = response.text.replace('```json', '').replace('```', '').strip()
    return raw_json

# Ejecución y guardado
partidos = obtener_partidos_reales()
nuevo_tips_json = generar_json_automatizado(partidos)

with open("tips.json", "w", encoding='utf-8') as f:
    f.write(nuevo_tips_json)
