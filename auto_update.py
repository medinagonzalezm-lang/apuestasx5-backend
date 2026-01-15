import os
import requests
import json
from google import genai
from datetime import datetime

# Configuración de llaves
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

# Inicializar cliente forzando la versión estable v1
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
        # Enviamos 40 partidos para no saturar la memoria
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
        # Instrucciones claras en el prompt para evitar errores de configuración
        prompt = f"""
        Actúa como analista deportivo experto.
        Analiza estos partidos de hoy: {json.dumps(datos_partidos)}
        
        Genera un JSON con estas llaves exactas:
        1. 'tip_05': 3 picks de +0.5 goles.
        2. 'tip_15': 3 picks de +1.5 goles.
        3. 'tip_1x2x': 3 picks de 1X o 2X.
        4. 'tip_btts': 3 picks de Ambos Marcan.
        5. 'tip_as': 3 picks de Handicap Asiatico.
        6. 'tip_bonus': Los 3 mejores de los anteriores.
        7. 'puntos_actuales': Indica el BENEFICIO (Total acumulado menos 100). Solo el número.
        8. 'analisis_tecnico': Resumen breve de la jornada.

        IMPORTANTE: Responde ÚNICAMENTE con el código JSON puro, sin explicaciones ni bloques de texto.
        """

        # Eliminamos el bloque 'config' que causaba el Error 400
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        
        texto = response.text.strip()
        
        # Si la IA responde con bloques de código ```json ... ```, los limpiamos
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
            # Validamos que el JSON sea correcto antes de guardar
            datos_finales = json.loads(resultado_json)
            with open("tips.json", "w", encoding='utf-8') as f:
                json.dump(datos_finales, f, ensure_ascii=False, indent=2)
            print("¡ÉXITO! tips.json actualizado.")
        except Exception as e:
            print(f"Error parseando el JSON: {e}")
            print(f"Texto recibido: {resultado_json}")

if __name__ == "__main__":
    main()
