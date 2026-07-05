# app/models/punto.py
from sqlalchemy import Column, Integer, String, Boolean
from geoalchemy2 import Geometry
from ..core.database import Base

class Punto(Base):
    __tablename__ = "puntos"

    id = Column(Integer, primary_key=True, index=True)
    geometria = Column(Geometry('POINT', srid=4326), nullable=False)
    descripcion = Column(String(50), nullable=True)
    stop = Column(Boolean, default=False)