import os
import requests
import json
import google.generativeai as genai
from datetime import datetime

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

# Configurar la IA
genai.configure(api_key=GEMINI_KEY)

def obtener_datos_futbol():
    headers = {
        'x-rapidapi-key': FOOTBALL_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    hoy = datetime.now().strftime("%Y-%m-%d")
    url = f"https://v3.football.api-sports.io/fixtures?date={hoy}"

    try:
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        partidos = []
        # Tomamos los primeros 40 partidos
        for f in data.get('response', [])[:40]:
            partidos.append({
                "liga": f['league']['name'],
                "local": f['teams']['home']['name'],
                "visitante": f['teams']['away']['name']
            })
        return partidos
    except Exception as e:
        print(f"Error API Futbol: {e}")
        return None

def generar_pronosticos_ia(datos_partidos):
    try:
        # Usamos el modelo flash-1.5 que es el más compatible
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Actúa como analista deportivo para 'Pronosticos deportivos (IA)'.
        Analiza estos partidos: {json.dumps(datos_partidos)}
        
        Genera un JSON con estas llaves:
        1. 'tip_05': 3 picks de +0.5 goles.
        2. 'tip_15': 3 picks de +1.5 goles.
        3. 'tip_1x2x': 3 picks de Doble Oportunidad.
        4. 'tip_btts': 3 picks de Ambos Marcan.
        5. 'tip_as': 3 picks de Handicap Asiatico.
        6. 'tip_bonus': Combinada de los 3 mejores.
        7. En 'puntos_actuales', indica SOLO el BENEFICIO (Total acumulado menos 100).
        
        Responde exclusivamente con el JSON puro.
        """

        # Generar contenido
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        return response.text
    except Exception as e:
        print(f"Error en Gemini SDK: {e}")
        return None

def main():
    print("Iniciando actualización con SDK Oficial...")
    datos = obtener_datos_futbol()
    if not datos:
        print("No hay datos de partidos.")
        return

    print(f"Procesando {len(datos)} partidos...")
    resultado = generar_pronosticos_ia(datos)
    
    if resultado:
        try:
            # Validar y limpiar
            json_dict = json.loads(resultado)
            with open("tips.json", "w", encoding='utf-8') as f:
                json.dump(json_dict, f, ensure_ascii=False, indent=2)
            print("¡EXITO! Archivo tips.json actualizado correctamente.")
        except Exception as e:
            print(f"Error al procesar JSON: {e}")
            print(f"Respuesta recibida: {resultado}")

if __name__ == "__main__":
    main()
