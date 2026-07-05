"""
from pydantic import BaseModel
from typing import List, Optional

class RutaPaso(BaseModel):
    orden: int
    punto_id: int
    descripcion: str
    latitud: float
    longitud: float
    ruta_id: int
    nombre_linea: Optional[str]
    tipo_ruta: str
    es_transferencia: bool

class RutaOptimaRequest(BaseModel):
    origen_id: int
    destino_id: int

class RutaOptimaResponse(BaseModel):
    tiempo_total_minutos: float
    pasos: List[tuple]
    informacion_detallada: List[RutaPaso]
"""

from pydantic import BaseModel
from typing import List, Optional

class PuntoRuta(BaseModel):
    orden: int
    punto_id: int
    descripcion: str
    latitud: float
    longitud: float
    stop: bool
    distancia_acumulada: Optional[float] = 0
    tiempo_acumulado: Optional[float] = 0

class RutaBase(BaseModel):
    tipo_ruta: str
    distancia_total: float
    tiempo_total_minutos: float

class RutaResponse(RutaBase):
    id: int
    linea_id: int
    puntos: Optional[List[PuntoRuta]] = None
    
    class Config:
        from_attributes = True

class RutaOptimaRequest(BaseModel):
    origen_id: int
    destino_id: int

class PasoRuta(BaseModel):
    orden: int
    punto_id: int
    descripcion: str
    latitud: float
    longitud: float
    ruta_id: int
    nombre_linea: Optional[str] = None
    tipo_ruta: str
    es_transferencia: bool
    tiempo_acumulado: Optional[float] = None
    distancia_acumulada: Optional[float] = None

class DetalleViaje(BaseModel):
    tiempo_total_minutos: float
    distancia_total_metros: Optional[float] = 0
    numero_transbordos: int
    lineas_utilizadas: List[str]
    pasos: List[PasoRuta]

class RutaOptimaResponse(BaseModel):
    tiempo_total_minutos: float
    distancia_total_metros: Optional[float] = 0
    pasos: List[tuple]
    informacion_detallada: List[PasoRuta]
