from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.router import api_router
from .core.database import engine, Base
import os

# Crear las tablas en la base de datos (solo para desarrollo, usar Alembic en producción)
# Base.metadata.create_all(bind=engine)

app = FastAPI(title="MicroRuta API", version="1.0.0")

# Configurar CORS para permitir peticiones desde el frontend
# Obtener origins de entorno o usar defaults
origins = [
    "https://micro-ruta-nine.vercel.app",  # Tu frontend en Vercel
    "https://microruta.duckdns.org",       # El mismo backend
    "http://localhost:3000",               # Desarrollo local
    "http://localhost:5173",               # Vite desarrollo
]

# Si hay variable de entorno CORS_ORIGINS, agregarlos
if os.getenv("CORS_ORIGINS"):
    extra_origins = os.getenv("CORS_ORIGINS").split(",")
    origins.extend(extra_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Restringido a los dominios especificados
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Incluir el router de la API
app.include_router(api_router, prefix="/api/v1")

# Endpoint de health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "microruta-backend"}