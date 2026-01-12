import os
import requests
import google.generativeai as genai
import json

# 1. CONFIGURACIÓN DE APIS
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

# Configurar Gemini con el modelo correcto para evitar Error 404
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def obtener_datos_futbol():
    """Obtiene los próximos 50 partidos reales de la API."""
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
    """Envía los partidos a Gemini y formatea la respuesta en JSON."""
    prompt = f"""
    Eres un experto en apuestas y probabilidad para la app 'Pronosticos deportivos (IA)'.
    Analiza estos partidos reales: {datos_partidos}
    
    TAREA:
    Genera un JSON con estas 6 categorías:
    1. tip_05: 3 partidos con +1.5 goles.
    2. tip_15: 3 partidos con +1.5 goles (diferentes a los anteriores).
    3. tip_1x2x: 3 partidos donde el equipo local gana/empata (1X) o visitante gana/empata (2X).
    4. tip_btts: 3 partidos donde Ambos marcan (BTTS) o No marcan.
    5. tip_as: Combinado de 3 partidos muy fiables.
    6. tip_bonus: Los 3 partidos con mayor probabilidad estadística de éxito hoy.

    REGLA DE ORO:
    - Incluye la clave 'progression' con:
      - 'puntos_actuales': Realiza un seguimiento partiendo de 100 puntos iniciales (excluyendo el depósito).
      - 'estado_hoy': Muestra los 3 partidos del 'tip_bonus' con el icono ⏳.
    - Cada partido debe llevar el icono ⚽.
    - Responde EXCLUSIVAMENTE con el JSON puro, sin explicaciones ni bloques de código markdown.
    """
    
    try:
        response = model.generate_content(prompt)
        texto = response.text.strip()
        
        # Limpieza de posibles etiquetas de markdown
        if "```json" in texto:
            texto = texto.split("```json")[1].split("```")[0].strip()
        elif "```" in texto:
            texto = texto.split("```")[1].split("```")[0].strip()
            
        return texto
    except Exception as e:
        print(f"Error en Gemini: {e}")
        return None

# --- PROCESO PRINCIPAL ---
def main():
    print("Iniciando actualización diaria...")
    
    datos = obtener_datos_futbol()
    if not datos:
        return

    json_final = generar_pronosticos_ia(datos)
    if not json_final:
        return

    # Validar que es un JSON correcto antes de guardar
    try:
        json.loads(json_final)
        with open("tips.json", "w", encoding='utf-8') as f:
            f.write(json_final)
        print("¡ÉXITO! El archivo tips.json ha sido actualizado localmente.")
    except Exception as e:
        print(f"Error al validar el JSON final: {e}")
        print("Contenido recibido de la IA:", json_final)

if __name__ == "__main__":
    main()
