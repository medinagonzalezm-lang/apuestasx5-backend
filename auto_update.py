import os
import requests
import json
from google import genai
from datetime import datetime

# Configuración de llaves
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

# Inicializar cliente forzando la versión estable de la API
# Esto evita que busque en v1beta y nos de el error 404
client = genai.Client(api_key=GEMINI_KEY, http_options={'api_version': 'v1'})

def obtener_partidos():
    headers = {
        'x-rapidapi-key': FOOTBALL_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    hoy = datetime.now().strftime("%Y-%m-%d")
    url = f"https://v3.football.api-sports.io/fixtures?date={hoy}"

    try:
        r = requests.get(url, headers=headers, timeout=15)
        res = r.json()
        partidos = []
        # Enviamos 40 partidos para no saturar
        for f in res.get('response', [])[:40]:
            partidos.append({
                "liga": f['league']['name'],
                "local": f['teams']['home']['name'],
                "visitante": f['teams']['away']['name']
            })
        return partidos
    except Exception as e:
        print(f"Error cargando partidos: {e}")
        return None

def analizar_con_ia(datos_partidos):
    try:
        prompt = f"""
        Actúa como analista deportivo experto.
        Analiza estos partidos: {json.dumps(datos_partidos)}
        
        Devuelve un JSON con:
        1. 'tip_05': 3 picks de +0.5 goles.
        2. 'tip_15': 3 picks de +1.5 goles.
        3. 'tip_1x2x': 3 picks de 1X o 2X.
        4. 'tip_btts': 3 picks de Ambos Marcan.
        5. 'tip_as': 3 picks de Handicap Asiatico.
        6. 'tip_bonus': Los 3 mejores picks.
        7. En 'puntos_actuales': Beneficio neto (Total - 100).
        8. En 'analisis_tecnico': Resumen breve.

        Responde SOLO el JSON puro.
        """

        # Llamada al modelo
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
                'temperature': 0.1
            }
        )
        return response.text
    except Exception as e:
        print(f"Error en el motor de IA: {e}")
        return None

def main():
    print("Iniciando proceso (Forzando API v1)...")
    lista_partidos = obtener_partidos()
    
    if not lista_partidos:
        print("No hay partidos.")
        return

    print(f"Analizando {len(lista_partidos)} partidos...")
    resultado_json = analizar_con_ia(lista_partidos)
    
    if resultado_json:
        try:
            datos_finales = json.loads(resultado_json)
            with open("tips.json", "w", encoding='utf-8') as f:
                json.dump(datos_finales, f, ensure_ascii=False, indent=2)
            print("¡EXITO! tips.json generado correctamente.")
        except Exception as e:
            print(f"Error parseando JSON: {e}")

if __name__ == "__main__":
    main()
