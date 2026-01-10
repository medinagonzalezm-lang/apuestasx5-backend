from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI(
    title="Pronósticos Deportivos (IA)",
    description="Backend optimizado para servir predicciones diarias",
    version="2.0"
)

# Configuración CORS para permitir conexiones desde la App móvil
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Función segura para cargar el JSON
def cargar_tips():
    file_path = "tips.json"
    if not os.path.exists(file_path):
        # Retornamos una estructura por defecto si el archivo no existe
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error leyendo tips.json: {e}")
        return {}

@app.get("/")
def root():
    return {
        "status": "online", 
        "app": "Pronósticos Deportivos (IA)",
        "message": "Servidor listo para enviar predicciones"
    }

@app.get("/tip/{tip_id}")
def obtener_tip(tip_id: str):
    tips = cargar_tips()
    
    # Verificamos si el ID solicitado existe en nuestro JSON
    if tip_id not in tips:
        raise HTTPException(
            status_code=404, 
            detail=f"El pronóstico '{tip_id}' aún no ha sido publicado hoy."
        )
    
    return tips[tip_id]

# Endpoint adicional para ver todos los tips de una vez (útil para debug)
@app.get("/all_tips")
def ver_todo():
    return cargar_tips()
