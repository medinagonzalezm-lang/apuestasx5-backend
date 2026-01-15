import os
import requests

FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")

def diagnostico():
    # Probamos los dos túneles posibles
    intentos = [
        {
            "nombre": "Conexión Directa API-SPORTS",
            "url": "https://v3.football.api-sports.io/status",
            "headers": {"x-apisports-key": FOOTBALL_KEY}
        },
        {
            "nombre": "Conexión vía RAPID-API",
            "url": "https://api-football-v1.p.rapidapi.com/v3/status",
            "headers": {
                "x-rapidapi-key": FOOTBALL_KEY,
                "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
            }
        }
    ]

    for i in intentos:
        print(f"--- Probando: {i['nombre']} ---")
        try:
            r = requests.get(i['url'], headers=i['headers'], timeout=10)
            print(f"Código de estado: {r.status_code}")
            print(f"Respuesta: {r.text}")
        except Exception as e:
            print(f"Error de red: {e}")
        print("\n")

if __name__ == "__main__":
    diagnostico()
