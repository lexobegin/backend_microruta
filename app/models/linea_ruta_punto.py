# app/models/linea_ruta_punto.py
from sqlalchemy import Column, Integer, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from ..core.database import Base

class LineaRutaPunto(Base):
    __tablename__ = "linea_ruta_puntos"

    id = Column(Integer, primary_key=True, index=True)
    ruta_id = Column(Integer, ForeignKey("rutas.id"), nullable=False)
    punto_id = Column(Integer, ForeignKey("puntos.id"), nullable=False)
    orden = Column(Integer, nullable=False)
    distancia_acumulada = Column(Numeric(10, 2), default=0)
    tiempo_acumulado = Column(Numeric(5, 2), default=0)

    # Relaciones
    ruta = relationship("Ruta", back_populates="puntos")
    punto = relationship("Punto")