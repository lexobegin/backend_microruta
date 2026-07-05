from fastapi import APIRouter
from .endpoints import lineas, puntos, rutas, planificador, transferencias

api_router = APIRouter()

# Endpoints de líneas
api_router.include_router(lineas.router, prefix="/lineas", tags=["Líneas"])

# Endpoints de puntos
api_router.include_router(puntos.router, prefix="/puntos", tags=["Puntos"])

# Endpoints de rutas
api_router.include_router(rutas.router, prefix="/rutas", tags=["Rutas"])

# Endpoints del planificador
api_router.include_router(planificador.router, prefix="/planificador", tags=["Planificador"])

# Endpoints de transferencias
api_router.include_router(transferencias.router, prefix="/transferencias", tags=["Transferencias"])