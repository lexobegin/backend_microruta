from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ....core.database import SessionLocal
from ....models import Transferencia, Punto, Ruta, Linea

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/punto/{punto_id}")
async def get_transferencias_punto(
    punto_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las transferencias disponibles en un punto
    """
    punto = db.query(Punto).filter(Punto.id == punto_id).first()
    if not punto:
        raise HTTPException(status_code=404, detail="Punto no encontrado")
    
    transferencias = db.query(Transferencia).filter(
        Transferencia.punto_id == punto_id
    ).all()
    
    resultados = []
    for trans in transferencias:
        ruta_origen = db.query(Ruta).filter(Ruta.id == trans.ruta_origen_id).first()
        ruta_destino = db.query(Ruta).filter(Ruta.id == trans.ruta_destino_id).first()
        
        if ruta_origen and ruta_destino:
            linea_origen = db.query(Linea).filter(Linea.id == ruta_origen.linea_id).first()
            linea_destino = db.query(Linea).filter(Linea.id == ruta_destino.linea_id).first()
            
            resultados.append({
                "id": trans.id,
                "punto_id": trans.punto_id,
                "punto_descripcion": punto.descripcion,
                "ruta_origen": {
                    "id": ruta_origen.id,
                    "tipo": ruta_origen.tipo_ruta,
                    "linea_id": ruta_origen.linea_id,
                    "linea_nombre": linea_origen.nombre_linea if linea_origen else None
                },
                "ruta_destino": {
                    "id": ruta_destino.id,
                    "tipo": ruta_destino.tipo_ruta,
                    "linea_id": ruta_destino.linea_id,
                    "linea_nombre": linea_destino.nombre_linea if linea_destino else None
                },
                "penalizacion_minutos": trans.penalizacion_minutos
            })
    
    return resultados
