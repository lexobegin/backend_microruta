from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.router import api_router
from .core.database import engine, Base

# Crear las tablas en la base de datos (solo para desarrollo, usar Alembic en producción)
# Base.metadata.create_all(bind=engine)

app = FastAPI(title="MicroRuta API", version="1.0.0")

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, restringir a las URLs de tu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir el router de la API
app.include_router(api_router, prefix="/api/v1")