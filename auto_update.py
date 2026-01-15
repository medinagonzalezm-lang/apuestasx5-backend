import os
import requests
import json
from google import genai
from datetime import datetime

# Configuración de llaves desde el entorno de GitHub
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

# Inicializar el nuevo cliente oficial de Google 2026
client = genai.Client(api_key=GEMINI_KEY)

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
        # Enviamos 40 partidos para análisis de calidad
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
        Como experto analista de 'Pronosticos deportivos (IA)', analiza estos partidos: {json.dumps(datos_partidos)}
        
        Debes devolver un JSON estrictamente con este formato:
        1. 'tip_05': 3 partidos para más de 0.5 goles.
        2. 'tip_15': 3 partidos para más de 1.5 goles.
        3. 'tip_1x2x': 3 partidos de doble oportunidad (1X o 2X).
        4. 'tip_btts': 3 partidos de Ambos Marcan.
        5. 'tip_as': 3 partidos de Hándicap Asiático.
        6. 'tip_bonus': Los 3 mejores pronósticos de todos los anteriores.
        7. En 'puntos_actuales': Calcula el beneficio neto (Beneficio Total - 100). Solo el número.
        8. En 'analisis_tecnico': Un resumen breve de la jornada.

        Responde SOLO el JSON, sin texto adicional ni comillas de bloque.
        """

        # Uso del nuevo SDK google-genai
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
    print("Iniciando proceso de IA...")
    lista_partidos = obtener_partidos()
    
    if not lista_partidos:
        print("No hay partidos para analizar.")
        return

    print(f"Analizando {len(lista_partidos)} partidos con Gemini 1.5 Flash...")
    resultado_json = analizar_con_ia(lista_partidos)
    
    if resultado_json:
        try:
            # Limpieza básica por si la IA añade caracteres extra
            datos_finales = json.loads(resultado_json)
            with open("tips.json", "w", encoding='utf-8') as f:
                json.dump(datos_finales, f, ensure_ascii=False, indent=2)
            print("¡LISTO! tips.json actualizado con éxito.")
        except Exception as e:
            print(f"Error parseando el resultado: {e}")
            print(f"Recibido: {resultado_json}")

if __name__ == "__main__":
    main()
