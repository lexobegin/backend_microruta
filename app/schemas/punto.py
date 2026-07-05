"""
from pydantic import BaseModel
from typing import Optional

class PuntoResponse(BaseModel):
    id: int
    descripcion: Optional[str]
    latitud: float
    longitud: float
    stop: bool
    
    class Config:
        from_attributes = True
"""

from pydantic import BaseModel
from typing import Optional, List

class PuntoBase(BaseModel):
    descripcion: Optional[str] = None
    stop: bool = False

class PuntoResponse(PuntoBase):
    id: int
    latitud: float
    longitud: float
    
    class Config:
        from_attributes = True

class PuntoDetalleResponse(PuntoResponse):
    lineas: Optional[List[str]] = None

class PuntoCercanoResponse(BaseModel):
    id: int
    descripcion: str
    latitud: float
    longitud: float
    distancia: float
    lineas: Optional[List[str]] = None