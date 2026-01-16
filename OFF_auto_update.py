import os
import requests
import json
from google import genai
from datetime import datetime

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

def obtener_partidos():
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": FOOTBALL_KEY}
    hoy = datetime.now().strftime("%Y-%m-%d")
    
    try:
        r = requests.get(f"{url}?date={hoy}", headers=headers, timeout=15)
        res = r.json()
        if res.get('response'):
            # Filtramos los 70 partidos más relevantes para ahorrar tokens
            partidos = res['response'][:70]
            return [f"{p['teams']['home']['name']} vs {p['teams']['away']['name']}" for p in partidos]
        return None
    except Exception as e:
        print(f"Error Fútbol: {e}")
        return None

def main():
    print("--- INICIANDO ACTUALIZACIÓN ÚNICA DIARIA ---")
    datos = obtener_partidos()
    
    if not datos:
        return

    try:
        client = genai.Client(api_key=GEMINI_KEY)
        
        # Un solo prompt maestro, muy directo para no gastar cuota
        prompt = f"""
        Actúa como el experto de 'Pronosticos deportivos (IA)'. 
        Analiza estos partidos: {json.dumps(datos)}
        Genera un JSON con 3 picks para: tip_05, tip_15, tip_1x2x, tip_btts, tip_bonus.
        puntos_actuales: Beneficio neto mensual (Total acumulado - 100).
        analisis_tecnico: Resumen de 15 palabras.
        Responde SOLO JSON.
        """
        
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        
        # Limpieza y guardado
        resultado = response.text.replace("```json", "").replace("```", "").strip()
        final_json = json.loads(resultado)
        
        with open("tips.json", "w", encoding="utf-8") as f:
            json.dump(final_json, f, indent=2, ensure_ascii=False)
        print("--- ÉXITO: tips.json actualizado por hoy ---")
        
    except Exception as e:
        print(f"Error de cuota o sistema: {e}. Mañana se reintentará automáticamente.")

if __name__ == "__main__":
    main()
