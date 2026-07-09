from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from geoalchemy2 import WKTElement
from geoalchemy2.functions import ST_Distance, ST_Transform
from ....core.database import SessionLocal
from ....models import Punto
from ....schemas.punto import PuntoResponse, PuntoCercanoResponse

from geoalchemy2.shape import to_shape

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[PuntoResponse])
async def get_puntos(
    stop_only: bool = False,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los puntos o solo paradas
    """
    query = db.query(Punto)
    if stop_only:
        query = query.filter(Punto.stop == True)
    
    puntos = query.limit(limit).all()
    ## print(type(puntos[0].geometria))
    ## print(puntos[0].geometria)
    # Convertir a diccionarios
    #return [
    #    {
    #        "id": p.id,
    #        "descripcion": p.descripcion,
    #        "stop": p.stop,
    #        "latitud": float(p.geometria.y),
    #        "longitud": float(p.geometria.x)
    #    }
    #    for p in puntos
    #]

    resultado = []

    for p in puntos:
        geom = to_shape(p.geometria)

        resultado.append({
            "id": p.id,
            "descripcion": p.descripcion,
            "stop": p.stop,
            "latitud": geom.y,
            "longitud": geom.x
        })

    return resultado

@router.get("/{punto_id}", response_model=PuntoResponse)
async def get_punto(
    punto_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene un punto por ID
    """
    punto = db.query(Punto).filter(Punto.id == punto_id).first()
    if not punto:
        raise HTTPException(status_code=404, detail="Punto no encontrado")
    
    #return {
    #    "id": punto.id,
    #    "descripcion": punto.descripcion,
    #    "stop": punto.stop,
    #    "latitud": float(punto.geometria.y),
    #    "longitud": float(punto.geometria.x)
    #}

    geom = to_shape(punto.geometria)

    return {
        "id": punto.id,
        "descripcion": punto.descripcion,
        "stop": punto.stop,
        "latitud": geom.y,
        "longitud": geom.x
    }

@router.get("/buscar/coordenadas")
async def buscar_por_coordenadas(
    lat: float,
    lon: float,
    radio: int = 500,
    db: Session = Depends(get_db)
):
    """
    Busca puntos cercanos a unas coordenadas dadas
    """
    point_wkt = f"POINT({lon} {lat})"
    
    puntos = db.query(Punto).filter(
        ST_Distance(
            ST_Transform(Punto.geometria, 32720),
            ST_Transform(WKTElement(point_wkt, 4326), 32720)
        ) < radio
    ).order_by(
        ST_Distance(
            ST_Transform(Punto.geometria, 32720),
            ST_Transform(WKTElement(point_wkt, 4326), 32720)
        )
    ).limit(10).all()
    
    resultados = []
    for p in puntos:
        distancia = db.query(
            ST_Distance(
                ST_Transform(p.geometria, 32720),
                ST_Transform(WKTElement(point_wkt, 4326), 32720)
            )
        ).scalar()
        
        geom = to_shape(p.geometria)

        resultados.append({
            "id": p.id,
            "descripcion": p.descripcion,
            ## "latitud": float(p.geometria.y),
            ## "longitud": float(p.geometria.x),
            "latitud": geom.y,
            "longitud": geom.x,
            "distancia": float(distancia) if distancia else 0,
            "stop": p.stop
        })
    
    return resultados