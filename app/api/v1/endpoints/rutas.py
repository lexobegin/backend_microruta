from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from geoalchemy2.shape import to_shape

from ....core.database import SessionLocal
from ....models import LineaRutaPunto, Ruta, Punto, Linea
from ....services.calculo_rutas import CalculadorRutas
from ....schemas.ruta import RutaResponse, RutaOptimaRequest, RutaOptimaResponse, PuntoRuta


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/linea/{linea_id}")
async def get_rutas_linea(
    linea_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las rutas de una línea
    """
    # Verificar que la línea existe
    linea = db.query(Linea).filter(Linea.id == linea_id).first()
    if not linea:
        raise HTTPException(status_code=404, detail="Línea no encontrada")
    
    rutas = db.query(Ruta).filter(Ruta.linea_id == linea_id).all()
    
    resultados = []
    for ruta in rutas:
        puntos = db.query(LineaRutaPunto).filter(
            LineaRutaPunto.ruta_id == ruta.id
        ).order_by(LineaRutaPunto.orden).all()
        
        puntos_data = []
        for pr in puntos:
            punto = db.query(Punto).filter(Punto.id == pr.punto_id).first()
            if punto:
                geom = to_shape(punto.geometria)

                puntos_data.append({
                    "orden": pr.orden,
                    "punto_id": pr.punto_id,
                    "descripcion": punto.descripcion or f"Punto {pr.punto_id}",
                    "latitud": float(geom.y),
                    "longitud": float(geom.x),
                    "stop": punto.stop,
                    "distancia_acumulada": float(pr.distancia_acumulada) if pr.distancia_acumulada else 0,
                    "tiempo_acumulado": float(pr.tiempo_acumulado) if pr.tiempo_acumulado else 0
                })
        
        resultados.append({
            "id": ruta.id,
            "tipo_ruta": ruta.tipo_ruta,
            "distancia_total": float(ruta.distancia_total) if ruta.distancia_total else 0,
            "tiempo_total_minutos": float(ruta.tiempo_total_minutos) if ruta.tiempo_total_minutos else 0,
            "linea_id": ruta.linea_id,
            "puntos": puntos_data
        })
    
    return resultados

@router.post("/optimizar")
async def calcular_ruta_optima(
    request: RutaOptimaRequest,
    db: Session = Depends(get_db)
):
    """
    Calcula la ruta óptima entre dos puntos
    """
    calculador = CalculadorRutas(db)
    
    # Validar que los puntos existen
    origen = db.query(Punto).filter(Punto.id == request.origen_id).first()
    destino = db.query(Punto).filter(Punto.id == request.destino_id).first()
    
    if not origen:
        raise HTTPException(status_code=404, detail="Punto de origen no encontrado")
    if not destino:
        raise HTTPException(status_code=404, detail="Punto de destino no encontrado")
    
    # Encontrar rutas óptimas
    rutas = calculador.encontrar_ruta_optima(
        request.origen_id, 
        request.destino_id,
        max_rutas=5
    )
    
    if not rutas:
        raise HTTPException(status_code=404, detail="No se encontraron rutas")
    
    return rutas

@router.get("/puntos/cercanos")
async def obtener_puntos_cercanos(
    lat: float = Query(..., description="Latitud"),
    lon: float = Query(..., description="Longitud"),
    radio: int = Query(200, description="Radio en metros"),
    db: Session = Depends(get_db)
):
    """
    Obtiene puntos de parada cercanos a una ubicación
    """
    calculador = CalculadorRutas(db)
    resultados = calculador.encontrar_puntos_cercanos(lat, lon, radio)
    
    if not resultados:
        raise HTTPException(
            status_code=404, 
            detail="No se encontraron puntos cercanos"
        )
    
    return resultados

@router.get("/punto/{punto_id}/lineas")
async def obtener_lineas_punto(
    punto_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene las líneas que pasan por un punto
    """
    # Verificar que el punto existe
    punto = db.query(Punto).filter(Punto.id == punto_id).first()
    if not punto:
        raise HTTPException(status_code=404, detail="Punto no encontrado")
    
    calculador = CalculadorRutas(db)
    lineas = calculador._get_lineas_punto(punto_id)
    
    if not lineas:
        raise HTTPException(
            status_code=404,
            detail="No se encontraron líneas para este punto"
        )
    
    return {
        "punto_id": punto_id,
        "descripcion": punto.descripcion,
        "lineas": lineas
    }