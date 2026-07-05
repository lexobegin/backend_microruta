# app/models/transferencia.py
from sqlalchemy import Column, Integer, ForeignKey
from ..core.database import Base

class Transferencia(Base):
    __tablename__ = "transferencias"

    id = Column(Integer, primary_key=True, index=True)
    punto_id = Column(Integer, ForeignKey("puntos.id"), nullable=False)
    ruta_origen_id = Column(Integer, ForeignKey("rutas.id"), nullable=False)
    ruta_destino_id = Column(Integer, ForeignKey("rutas.id"), nullable=False)
    penalizacion_minutos = Column(Integer, default=5)