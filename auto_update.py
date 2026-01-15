import os
import requests
import json
from google import genai
from datetime import datetime

# Configuración de llaves desde GitHub Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

# Inicializar el cliente de la forma más sencilla posible (v1 por defecto)
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
        # Seleccionamos los primeros 40 partidos para el análisis
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
        Actúa como experto analista de 'Pronosticos deportivos (IA)'. 
        Analiza estos partidos reales: {json.dumps(datos_partidos)}
        
        Genera un JSON con este formato exacto:
        1. 'tip_05': 3 picks de +0.5 goles.
        2. 'tip_15': 3 picks de +1.5 goles.
        3. 'tip_1x2x': 3 picks de doble oportunidad (1X o 2X).
        4. 'tip_btts': 3 picks de Ambos Marcan.
        5. 'tip_as': 3 picks de Hándicap Asiático.
        6. 'tip_bonus': Los 3 mejores de los anteriores.
        7. En 'puntos_actuales': Indica el BENEFICIO (Total acumulado menos 100). Ejemplo: si hay 120, pon 20.
        8. En 'analisis_tecnico': Resumen de 1 frase.

        Responde SOLO el JSON puro, sin bloques de código ni texto.
        """

        # Usamos el nombre corto del modelo sin prefijos de versión para evitar el 404
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        
        texto = response.text.strip()
        
        # Limpiamos posibles etiquetas markdown de la IA
        if texto.startswith("```"):
            texto = texto.split("```")[1]
            if texto.startswith("json"):
                texto = texto[4:]
        
        return texto.strip()
        
    except Exception as e:
        print(f"Error en el motor de IA: {e}")
        return None

def main():
    print("Iniciando proceso estable...")
    lista_partidos = obtener_partidos()
    
    if not lista_partidos:
        print("No se encontraron partidos.")
        return

    print(f"Analizando {len(lista_partidos)} partidos con Gemini...")
    resultado_json = analizar_con_ia(lista_partidos)
    
    if resultado_json:
        try:
            # Validamos el JSON
            datos_finales = json.loads(resultado_json)
            with open("tips.json", "w", encoding='utf-8') as f:
                json.dump(datos_finales, f, ensure_ascii=False, indent=2)
            print("¡EXITO! tips.json actualizado correctamente.")
        except Exception as e:
            print(f"Error al procesar JSON: {e}")
            print(f"Contenido recibido: {resultado_json}")

if __name__ == "__main__":
    main()
