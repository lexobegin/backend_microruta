# app/models/linea.py
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base

class Linea(Base):
    __tablename__ = "lineas"

    id = Column(Integer, primary_key=True, index=True)
    nombre_linea = Column(String(20), unique=True, nullable=False)
    color_linea = Column(String(7), nullable=False)
    imagen_microbus = Column(Text, nullable=True)  # URL o path a la imagen
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    rutas = relationship("Ruta", back_populates="linea")
