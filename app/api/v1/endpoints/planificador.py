"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ....core.database import SessionLocal
from ....models import Punto
from ....services.calculo_rutas import CalculadorRutas
from ....schemas.ruta import RutaOptimaRequest, RutaOptimaResponse

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/calcular")
async def calcular_plan_viaje(
    request: RutaOptimaRequest,
    db: Session = Depends(get_db)
) -> List[RutaOptimaResponse]:

    ## Calcula el plan de viaje óptimo entre dos puntos
    
    ## Args:
    ##    request: Origen y destino

    # Validar puntos
    origen = db.query(Punto).filter(Punto.id == request.origen_id).first()
    destino = db.query(Punto).filter(Punto.id == request.destino_id).first()
    
    if not origen:
        raise HTTPException(status_code=404, detail="Punto de origen no encontrado")
    if not destino:
        raise HTTPException(status_code=404, detail="Punto de destino no encontrado")
    
    # Validar que sean paradas
    if not origen.stop:
        raise HTTPException(
            status_code=400,
            detail="El punto de origen debe ser una parada"
        )
    if not destino.stop:
        raise HTTPException(
            status_code=400,
            detail="El punto de destino debe ser una parada"
        )
    
    # Calcular rutas
    calculador = CalculadorRutas(db)
    rutas = calculador.encontrar_ruta_optima(
        request.origen_id,
        request.destino_id,
        max_rutas=5
    )
    
    if not rutas:
        raise HTTPException(
            status_code=404,
            detail="No se encontraron rutas entre los puntos seleccionados"
        )
    
    return rutas

@router.get("/puntos-cercanos")
async def obtener_puntos_cercanos(
    lat: float,
    lon: float,
    radio: int = 200,
    db: Session = Depends(get_db)
):
    
    ## Obtiene puntos de parada cercanos a una ubicación
    
    calculador = CalculadorRutas(db)
    puntos = calculador.encontrar_puntos_cercanos(lat, lon, radio)
    
    if not puntos:
        raise HTTPException(
            status_code=404,
            detail="No se encontraron paradas cercanas"
        )
    
    return puntos
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ....core.database import SessionLocal
from ....models import Punto
from ....services.calculo_rutas import CalculadorRutas
from ....schemas.ruta import RutaOptimaRequest

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/calcular")
async def calcular_plan_viaje(
    request: RutaOptimaRequest,
    db: Session = Depends(get_db)
):
    """
    Calcula el plan de viaje óptimo entre dos puntos
    """
    # Validar puntos
    origen = db.query(Punto).filter(Punto.id == request.origen_id).first()
    destino = db.query(Punto).filter(Punto.id == request.destino_id).first()
    
    if not origen:
        raise HTTPException(status_code=404, detail="Punto de origen no encontrado")
    if not destino:
        raise HTTPException(status_code=404, detail="Punto de destino no encontrado")
    
    # Validar que sean paradas
    if not origen.stop:
        raise HTTPException(
            status_code=400,
            detail="El punto de origen debe ser una parada"
        )
    if not destino.stop:
        raise HTTPException(
            status_code=400,
            detail="El punto de destino debe ser una parada"
        )
    
    # Calcular rutas
    calculador = CalculadorRutas(db)
    rutas = calculador.encontrar_ruta_optima(
        request.origen_id,
        request.destino_id,
        max_rutas=5
    )
    
    if not rutas:
        raise HTTPException(
            status_code=404,
            detail="No se encontraron rutas entre los puntos seleccionados"
        )
    
    # Enriquecer la respuesta con información adicional
    resultados = []
    for idx, ruta in enumerate(rutas):
        # Calcular número de transbordos
        num_transbordos = sum(1 for paso in ruta['informacion_detallada'] if paso['es_transferencia'])
        
        # Obtener líneas utilizadas
        lineas_utilizadas = list(set(
            paso['nombre_linea'] for paso in ruta['informacion_detallada'] 
            if paso['nombre_linea'] is not None
        ))
        
        # Calcular distancia total usando diferencias de acumulado por cada ruta.
        distancia_total = 0
        paso_anterior = None
        for paso in ruta['informacion_detallada']:
            if (
                paso_anterior
                and paso['ruta_id'] == paso_anterior['ruta_id']
                and paso.get('distancia_acumulada') is not None
                and paso_anterior.get('distancia_acumulada') is not None
            ):
                distancia_total += max(
                    paso['distancia_acumulada'] - paso_anterior['distancia_acumulada'],
                    0,
                )

            paso_anterior = paso
        
        resultados.append({
            "plan": idx + 1,
            "tiempo_total_minutos": ruta['tiempo_total_minutos'],
            "distancia_total_metros": round(distancia_total, 2),
            "numero_transbordos": num_transbordos,
            "lineas_utilizadas": lineas_utilizadas,
            "pasos": ruta['informacion_detallada']
        })
    
    return resultados

@router.get("/puntos-cercanos")
async def obtener_puntos_cercanos(
    lat: float,
    lon: float,
    radio: int = 200,
    db: Session = Depends(get_db)
):
    """
    Obtiene puntos de parada cercanos a una ubicación
    """
    calculador = CalculadorRutas(db)
    puntos = calculador.encontrar_puntos_cercanos(lat, lon, radio)
    
    if not puntos:
        raise HTTPException(
            status_code=404,
            detail="No se encontraron paradas cercanas"
        )
    
    return puntos
