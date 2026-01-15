import os
import requests
import json
import time
from google import genai
from datetime import datetime

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

client = genai.Client(api_key=GEMINI_KEY)

def obtener_partidos():
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": FOOTBALL_KEY}
    hoy = datetime.now().strftime("%Y-%m-%d")
    
    try:
        r = requests.get(f"{url}?date={hoy}", headers=headers, timeout=15)
        res = r.json()
        if res.get('response'):
            partidos = res['response']
            # Filtramos solo ligas importantes para asegurar calidad y reducir tamaño
            # O simplemente tomamos los primeros 100 para no saturar la cuota
            seleccion = partidos[:100]
            print(f"Procesando los {len(seleccion)} partidos principales de la jornada.")
            return [f"{p['teams']['home']['name']} vs {p['teams']['away']['name']}" for p in seleccion]
        return None
    except Exception as e:
        print(f"Error Fútbol: {e}")
        return None

def main():
    print("--- MODO SUPERVIVENCIA: PROCESANDO JORNADA EN 1 LLAMADA ---")
    datos = obtener_partidos()
    
    if not datos:
        return

    # Prompt único para ahorrar cuota de API
    prompt_maestro = f"""
    Analiza esta lista de partidos de fútbol para hoy: {json.dumps(datos)}
    
    Actúa como el experto de 'Pronosticos deportivos (IA)'. 
    Selecciona estadísticamente y genera un JSON con este formato:
    - 'tip_05' y 'tip_15': 3 picks OVER 1.5 goles.
    - 'tip_1x2x': 3 picks de 1X o 2X.
    - 'tip_btts': 3 picks de Ambos Marcan.
    - 'tip_bonus': Los 3 más fiables del día.
    - 'puntos_actuales': Beneficio neto (Total acumulado menos 100). Solo número.
    - 'analisis_tecnico': Resumen de 15 palabras.

    Responde SOLO el JSON puro, sin texto adicional.
    """

    try:
        # Hacemos el único intento del día
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt_maestro
        )
        
        resultado = response.text
        if resultado:
            limpio = resultado.replace("```json", "").replace("```", "").strip()
            json_data = json.loads(limpio)
            with open("tips.json", "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print("--- ¡ÉXITO! tips.json generado con 1 sola llamada ---")
            
    except Exception as e:
        print(f"Fallo crítico de cuota: {e}")
        print("Sugerencia: Espera 1 hora o cambia la API KEY en GitHub Secrets.")

if __name__ == "__main__":
    main()
