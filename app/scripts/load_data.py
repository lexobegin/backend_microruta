"""
Script para cargar datos desde el archivo Excel a la base de datos.
Uso: python -m app.scripts.load_data
"""

import pandas as pd
from sqlalchemy import create_engine
from geoalchemy2 import WKTElement
from ..core.database import SessionLocal
from ..models import Linea, Punto, Ruta, LineaRutaPunto, Transferencia
import sys
import os

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_excel_data(excel_path: str):
    """Carga los datos del Excel a la base de datos"""
    
    # Leer el archivo Excel
    lineas_df = pd.read_excel(excel_path, sheet_name='Lineas')
    puntos_df = pd.read_excel(excel_path, sheet_name='Puntos')
    lineas_rutas_df = pd.read_excel(excel_path, sheet_name='LineaRuta')
    lineas_puntos_df = pd.read_excel(excel_path, sheet_name='LineasPuntos')
    transbordos_df = pd.read_excel(excel_path, sheet_name='PuntosTrasbordos')
    
    # Configurar sesión de DB
    db = SessionLocal()
    
    try:
        # 1. Cargar Líneas
        for _, row in lineas_df.iterrows():
            linea = Linea(
                id=int(row['IdLinea']),
                nombre_linea=row['NombreLinea'],
                color_linea=row['ColorLinea'],
                imagen_microbus=row['ImagenMicrobus']
            )
            db.merge(linea)
        db.commit()
        print("✅ Líneas cargadas correctamente")
        
        # 2. Cargar Puntos (con geometría)
        for _, row in puntos_df.iterrows():
            # Crear punto geográfico en formato WKT
            point_wkt = f"POINT({row['Longitud']} {row['Latitud']})"
            punto = Punto(
                id=int(row['IdPunto']),
                geometria=WKTElement(point_wkt, srid=4326),
                descripcion=row['Descripcion'],
                stop=(row['Stop'] == 'S')  # S = True, N = False
            )
            db.merge(punto)
        db.commit()
        print("✅ Puntos cargados correctamente")
        
        # 3. Cargar Rutas
        for _, row in lineas_rutas_df.iterrows():
            ruta = Ruta(
                id=int(row['IdLineaRuta']),
                linea_id=int(row['IdLinea']),
                tipo_ruta='Salida' if row['IdRuta'] == 1 else 'Retorno',
                distancia_total=float(row['Distancia']),
                tiempo_total_minutos=float(row['Tiempo'])
                #distancia_total=row['Distancia'],
                #tiempo_total_minutos=row['Tiempo']
            )
            db.merge(ruta)
        db.commit()
        print("✅ Rutas cargadas correctamente")
        
        # 4. Cargar Puntos de Ruta (LineaRutaPunto)
        for _, row in lineas_puntos_df.iterrows():
            if row['IdPuntoDest'] != 0:
                linea_ruta_punto = LineaRutaPunto(
                    id=int(row['IdLineaPunto']),
                    ruta_id=int(row['IdLineaRuta']),
                    punto_id=int(row['IdPunto']),
                    orden=int(row['Orden']),
                    distancia_acumulada=float(row['Distancia']) if not pd.isna(row['Distancia']) else 0.0,
                    tiempo_acumulado=float(row['Tiempo']) if not pd.isna(row['Tiempo']) else 0.0
                    #distancia_acumulada=row['Distancia'],
                    #tiempo_acumulado=row['Tiempo']
                )
                db.merge(linea_ruta_punto)
        db.commit()
        print("✅ Puntos de ruta cargados correctamente")
        
        # 5. Cargar Transferencias
        for _, row in transbordos_df.iterrows():
            transferencia = Transferencia(
                id=int(row['IdTrasbordo']),
                punto_id=int(row['IdPunto']),
                ruta_origen_id=int(row['IdLineaOrigen']),
                ruta_destino_id=int(row['IdLineaDestino']),
                penalizacion_minutos=int(row['PenalizacionMin'])
            )
            db.merge(transferencia)
        db.commit()
        print("✅ Transferencias cargadas correctamente")
        
        print("🎉 ¡Todos los datos cargados exitosamente!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error al cargar datos: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    # Ruta al archivo Excel
    excel_file = "DatosLineas.xls"  # Ajusta la ruta según sea necesario
    
    if not os.path.exists(excel_file):
        print(f"❌ Archivo no encontrado: {excel_file}")
        print("Por favor, especifica la ruta correcta al archivo Excel")
        sys.exit(1)
    
    load_excel_data(excel_file)