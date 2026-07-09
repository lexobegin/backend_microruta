from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ....core.database import SessionLocal
from ....models import Linea, Ruta, LineaRutaPunto, Punto
from ....schemas.linea import LineaResponse, LineaDetalleResponse
from ....schemas.ruta import RutaResponse, PuntoRuta

from geoalchemy2.shape import to_shape

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[LineaResponse])
async def get_lineas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las líneas de microbús
    
    Args:
        skip: Número de registros a saltar (paginación)
        limit: Número máximo de registros a retornar
        search: Búsqueda por nombre de línea (opcional)
    """
    query = db.query(Linea)
    
    if search:
        query = query.filter(Linea.nombre_linea.ilike(f"%{search}%"))
    
    lineas = query.offset(skip).limit(limit).all()
    
    # Convertir a diccionario para Pydantic
    return [
        {
            "id": l.id,
            "nombre_linea": l.nombre_linea,
            "color_linea": l.color_linea,
            "imagen_microbus": l.imagen_microbus,
            "fecha_creacion": l.fecha_creacion
        }
        for l in lineas
    ]

@router.get("/{linea_id}", response_model=LineaDetalleResponse)
async def get_linea_by_id(
    linea_id: int,
    incluir_rutas: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Obtiene una línea específica por su ID
    
    Args:
        linea_id: ID de la línea
        incluir_rutas: Si incluye las rutas (ida/retorno)
    """
    linea = db.query(Linea).filter(Linea.id == linea_id).first()
    
    if not linea:
        raise HTTPException(status_code=404, detail="Línea no encontrada")
    
    resultado = {
        "id": linea.id,
        "nombre_linea": linea.nombre_linea,
        "color_linea": linea.color_linea,
        "imagen_microbus": linea.imagen_microbus,
        "fecha_creacion": linea.fecha_creacion
    }
    
    if incluir_rutas:
        rutas = db.query(Ruta).filter(Ruta.linea_id == linea_id).all()
        rutas_data = []
        
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
            
            rutas_data.append({
                "id": ruta.id,
                "tipo_ruta": ruta.tipo_ruta,
                "distancia_total": float(ruta.distancia_total) if ruta.distancia_total else 0,
                "tiempo_total_minutos": float(ruta.tiempo_total_minutos) if ruta.tiempo_total_minutos else 0,
                "linea_id": ruta.linea_id,
                "puntos": puntos_data
            })
        
        resultado["rutas"] = rutas_data
    
    return resultado

@router.get("/buscar/nombre")
async def buscar_linea_por_nombre(
    nombre: str,
    db: Session = Depends(get_db)
):
    """
    Busca líneas por nombre (búsqueda parcial)
    """
    lineas = db.query(Linea).filter(
        Linea.nombre_linea.ilike(f"%{nombre}%")
    ).all()
    
    if not lineas:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron líneas con el nombre: {nombre}"
        )
    
    return [
        {
            "id": l.id,
            "nombre_linea": l.nombre_linea,
            "color_linea": l.color_linea,
            "imagen_microbus": l.imagen_microbus
        }
        for l in lineas
    ]

@router.get("/{linea_id}/recorrido")
async def get_recorrido_linea(
    linea_id: int,
    tipo_ruta: Optional[str] = Query(None, description="'Salida' o 'Retorno'"),
    db: Session = Depends(get_db)
):
    """
    Obtiene el recorrido completo de una línea
    
    Args:
        linea_id: ID de la línea
        tipo_ruta: Filtrar por tipo de ruta (Salida/Retorno)
    """
    query = db.query(Ruta).filter(Ruta.linea_id == linea_id)
    
    if tipo_ruta:
        query = query.filter(Ruta.tipo_ruta == tipo_ruta)
    
    rutas = query.all()
    
    if not rutas:
        raise HTTPException(
            status_code=404,
            detail="No se encontraron rutas para esta línea"
        )
    
    recorridos = []
    for ruta in rutas:
        puntos = db.query(LineaRutaPunto).filter(
            LineaRutaPunto.ruta_id == ruta.id
        ).order_by(LineaRutaPunto.orden).all()
        
        puntos_coords = []
        paradas = []
        
        for pr in puntos:
            punto = db.query(Punto).filter(Punto.id == pr.punto_id).first()
            if punto:
                geom = to_shape(punto.geometria)

                coord = {
                    "lat": float(geom.y),
                    "lon": float(geom.x),
                    "orden": pr.orden,
                    "descripcion": punto.descripcion,
                    "stop": punto.stop
                }
                puntos_coords.append(coord)
                
                if punto.stop:
                    paradas.append(coord)
        
        recorridos.append({
            "id": ruta.id,
            "tipo": ruta.tipo_ruta,
            "distancia_total": float(ruta.distancia_total) if ruta.distancia_total else 0,
            "tiempo_total": float(ruta.tiempo_total_minutos) if ruta.tiempo_total_minutos else 0,
            "puntos": puntos_coords,
            "paradas": paradas,
            "punto_inicio": puntos_coords[0] if puntos_coords else None,
            "punto_fin": puntos_coords[-1] if puntos_coords else None
        })
    
    return recorridos