import os
import requests
import google.generativeai as genai
import json
import base64

# CONFIGURACIÓN (Render leerá estas variables de las casillas Name/Value que pusiste)
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "medinagonzalezm-lang/apuestasx5-backend"  # Tu repo confirmado

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def obtener_partidos_reales():
    # Consultamos los próximos 50 partidos disponibles en la API
    url = "https://v3.football.api-sports.io/fixtures?next=50"
    headers = {
        'x-rapidapi-key': FOOTBALL_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    try:
        response = requests.get(url, headers=headers)
        return response.json()
    except:
        return "No se pudieron obtener datos de la API"

def generar_nuevo_json(datos_futbol):
    # El "Prompt" maestro para Gemini
    prompt = f"""
    Eres el analista jefe de 'Pronósticos Deportivos (IA)'. 
    Analiza estos datos reales: {datos_futbol}
    
    Genera un archivo JSON con este formato exacto:
    1. Secciones: tip_05, tip_15, tip_1x2x, tip_btts, tip_as, tip_bonus.
    2. Cada sección con 3 partidos reales usando el icono ⚽.
    3. Muy importante la sección 'progression':
       - 'mes': "ENERO 2026"
       - 'puntos_actuales': (Calcula el progreso partiendo de 100 puntos iniciales. Si el Bonus Tip de ayer fue acierto, suma; si no, resta).
       - 'hoy': (Lista de los partidos del Bonus Tip de hoy con el icono ⏳ si no han empezado o ☑️ si son claros favoritos).
    
    Regla de oro: No inventes partidos, usa solo los que están en los datos.
    Responde solo el código JSON puro.
    """
    
    response = model.generate_content(prompt)
    # Limpiamos la respuesta por si Gemini añade comillas de código
    limpio = response.text.replace('```json', '').replace('```', '').strip()
    return limpio

def subir_a_github(contenido_json):
    url = f"https://api.github.com/repos/{REPO}/contents/tips.json"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 1. Obtener el SHA del archivo actual para poder sobrescribirlo
    res_get = requests.get(url, headers=headers)
    sha = res_get.json().get("sha") if res_get.status_code == 200 else None
    
    # 2. Preparar la subida
    payload = {
        "message": "🔄 Actualización automática IA - Pronósticos y Bankroll",
        "content": base64.b64encode(contenido_json.encode('utf-8')).decode('utf-8'),
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha
        
    res_put = requests.put(url, json=payload, headers=headers)
    return res_put.status_code

# EJECUCIÓN DEL PROCESO
print("Iniciando actualización diaria...")
datos = obtener_partidos_reales()
nuevo_json = generar_nuevo_json(datos)
estado = subir_a_github(nuevo_json)

if estado in [200, 201]:
    print("✅ ¡Éxito! tips.json actualizado en GitHub y Render.")
else:
    print(f"❌ Error al subir a GitHub. Código: {estado}")
