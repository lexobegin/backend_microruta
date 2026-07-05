# app/models/ruta.py
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from ..core.database import Base

class Ruta(Base):
    __tablename__ = "rutas"

    id = Column(Integer, primary_key=True, index=True)
    linea_id = Column(Integer, ForeignKey("lineas.id"), nullable=False)
    tipo_ruta = Column(String(20), nullable=False)  # 'Salida' o 'Retorno'
    distancia_total = Column(Numeric(10, 2), default=0)
    tiempo_total_minutos = Column(Numeric(5, 2), default=0)

    # Relaciones
    linea = relationship("Linea", back_populates="rutas")
    puntos = relationship("LineaRutaPunto", back_populates="ruta")