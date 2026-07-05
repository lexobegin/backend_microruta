from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class LineaBase(BaseModel):
    nombre_linea: str
    color_linea: str
    imagen_microbus: Optional[str] = None

class LineaCreate(LineaBase):
    pass

class LineaResponse(LineaBase):
    id: int
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True

class LineaDetalleResponse(LineaResponse):
    rutas: Optional[List[dict]] = None