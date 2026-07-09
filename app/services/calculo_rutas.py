"""
Servicio para cálculo de rutas óptimas usando algoritmo de Dijkstra
Implementación adaptada para red de transporte público
"""

import heapq
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2 import WKTElement
from geoalchemy2.functions import ST_Distance, ST_Transform
from ..models import Punto, LineaRutaPunto, Transferencia, Ruta, Linea

from geoalchemy2.shape import to_shape

class NodoTransporte:
    """Representa un nodo en la red de transporte"""
    def __init__(self, punto_id: int, ruta_id: Optional[int] = None):
        self.punto_id = punto_id
        self.ruta_id = ruta_id  # Ruta actual (None si es punto de transferencia)
        
    def __lt__(self, other):
        return self.punto_id < other.punto_id

class CalculadorRutas:
    def __init__(self, db: Session):
        self.db = db
        self.graph = {}  # Grafo para Dijkstra
        self._build_graph()
    
    def _build_graph(self):
        """Construye el grafo de transporte público"""
        # Obtener todos los puntos de ruta
        puntos_ruta = self.db.query(LineaRutaPunto).all()
        
        for pr in puntos_ruta:
            # Nodo actual
            nodo_actual = NodoTransporte(pr.punto_id, pr.ruta_id)
            
            # Buscar el siguiente punto en la misma ruta
            siguiente = self.db.query(LineaRutaPunto).filter(
                LineaRutaPunto.ruta_id == pr.ruta_id,
                LineaRutaPunto.orden == pr.orden + 1
            ).first()
            
            if siguiente:
                # Calcular peso (tiempo entre puntos)
                peso = self._calculate_weight(pr, siguiente)
                
                # Agregar arista
                nodo_siguiente = NodoTransporte(siguiente.punto_id, pr.ruta_id)
                self._add_edge(nodo_actual, nodo_siguiente, peso)
            
            # Si es parada, considerar transferencias
            punto = self.db.query(Punto).filter(Punto.id == pr.punto_id).first()
            if punto and punto.stop:
                transferencias = self.db.query(Transferencia).filter(
                    Transferencia.punto_id == pr.punto_id,
                    Transferencia.ruta_origen_id == pr.ruta_id
                ).all()
                
                for trans in transferencias:
                    nodo_destino = NodoTransporte(pr.punto_id, trans.ruta_destino_id)
                    self._add_edge(nodo_actual, nodo_destino, trans.penalizacion_minutos)
    
    def _add_edge(self, origen: NodoTransporte, destino: NodoTransporte, peso: float):
        """Agrega una arista al grafo"""
        key = (origen.punto_id, origen.ruta_id)
        if key not in self.graph:
            self.graph[key] = []
        self.graph[key].append((destino, peso))
    
    def _calculate_weight(self, punto1: LineaRutaPunto, punto2: LineaRutaPunto) -> float:
        """Calcula el peso entre dos puntos consecutivos"""
        if punto2.tiempo_acumulado is not None and punto1.tiempo_acumulado is not None:
            tiempo = float(punto2.tiempo_acumulado - punto1.tiempo_acumulado)
            if tiempo > 0:
                return tiempo
        
        if punto2.distancia_acumulada is not None and punto1.distancia_acumulada is not None:
            distancia = float(punto2.distancia_acumulada - punto1.distancia_acumulada)
            if distancia > 0:
                velocidad_kmh = 20
                tiempo_minutos = (distancia / 1000) / velocidad_kmh * 60
                return max(tiempo_minutos, 1.0)
        
        return 1.0
    
    def encontrar_ruta_optima(self, punto_origen_id: int, punto_destino_id: int, 
                              max_rutas: int = 5) -> List[Dict]:
        """Encuentra las mejores rutas priorizando viajes directos y menor tiempo."""
        rutas_origen = self.db.query(LineaRutaPunto).filter(
            LineaRutaPunto.punto_id == punto_origen_id
        ).all()
        
        if not rutas_origen:
            return []
        
        resultados = self._encontrar_rutas_directas(punto_origen_id, punto_destino_id)
        distancias = {}
        previos = {}
        cola = []
        
        for ruta in rutas_origen:
            estado = (punto_origen_id, ruta.ruta_id)
            distancias[estado] = 0
            heapq.heappush(cola, (0, estado))
        
        while cola:
            dist_actual, (punto_id, ruta_id) = heapq.heappop(cola)
            
            if dist_actual > distancias.get((punto_id, ruta_id), float('inf')):
                continue
            
            key = (punto_id, ruta_id)
            for vecino, peso in self.graph.get(key, []):
                nueva_dist = dist_actual + peso
                estado_vecino = (vecino.punto_id, vecino.ruta_id)
                
                if nueva_dist < distancias.get(estado_vecino, float('inf')):
                    distancias[estado_vecino] = nueva_dist
                    previos[estado_vecino] = (punto_id, ruta_id)
                    heapq.heappush(cola, (nueva_dist, estado_vecino))
        
        destinos = [(k, v) for k, v in distancias.items() 
                   if k[0] == punto_destino_id]
        destinos.sort(key=lambda x: x[1])
        
        rutas_existentes = {
            tuple(resultado['pasos']) for resultado in resultados
        }

        for (dest_id, ruta_dest_id), tiempo_total in destinos:
            if tiempo_total == float('inf'):
                continue
                
            pasos = self._reconstruir_camino(previos, (dest_id, ruta_dest_id))
            if not pasos or pasos[0][0] != punto_origen_id:
                continue

            pasos_key = tuple(pasos)
            if pasos_key in rutas_existentes:
                continue

            rutas_existentes.add(pasos_key)
            
            resultado = {
                'tiempo_total_minutos': round(tiempo_total, 2),
                'pasos': pasos,
                'informacion_detallada': self._get_detalle_ruta(pasos)
            }
            resultados.append(resultado)

        resultados.sort(
            key=lambda ruta: (
                self._contar_transferencias(ruta['pasos']),
                ruta['tiempo_total_minutos'],
            )
        )
        
        return resultados[:max_rutas]

    def _encontrar_rutas_directas(self, punto_origen_id: int, punto_destino_id: int) -> List[Dict]:
        """Busca viajes en una sola ruta antes de evaluar transbordos."""
        origenes = self.db.query(LineaRutaPunto).filter(
            LineaRutaPunto.punto_id == punto_origen_id
        ).all()

        resultados = []
        for origen in origenes:
            destino = self.db.query(LineaRutaPunto).filter(
                LineaRutaPunto.ruta_id == origen.ruta_id,
                LineaRutaPunto.punto_id == punto_destino_id,
                LineaRutaPunto.orden > origen.orden,
            ).first()

            if not destino:
                continue

            puntos = self.db.query(LineaRutaPunto).filter(
                LineaRutaPunto.ruta_id == origen.ruta_id,
                LineaRutaPunto.orden >= origen.orden,
                LineaRutaPunto.orden <= destino.orden,
            ).order_by(LineaRutaPunto.orden).all()

            pasos = [(punto.punto_id, punto.ruta_id) for punto in puntos]
            tiempo_total = self._calcular_tiempo_tramo(origen, destino, puntos)

            resultados.append({
                'tiempo_total_minutos': round(tiempo_total, 2),
                'pasos': pasos,
                'informacion_detallada': self._get_detalle_ruta(pasos)
            })

        return resultados

    def _calcular_tiempo_tramo(
        self,
        origen: LineaRutaPunto,
        destino: LineaRutaPunto,
        puntos: List[LineaRutaPunto]
    ) -> float:
        """Calcula el tiempo de un tramo directo usando datos acumulados o pesos."""
        if destino.tiempo_acumulado is not None and origen.tiempo_acumulado is not None:
            tiempo = float(destino.tiempo_acumulado - origen.tiempo_acumulado)
            if tiempo > 0:
                return tiempo

        tiempo_total = 0.0
        for index in range(1, len(puntos)):
            tiempo_total += self._calculate_weight(puntos[index - 1], puntos[index])

        return tiempo_total if tiempo_total > 0 else 1.0
    
    def _reconstruir_camino(self, previos: Dict, fin: Tuple) -> List[Tuple]:
        """Reconstruye el camino desde previos"""
        camino = []
        actual = fin
        
        while actual is not None:
            camino.append(actual)
            if actual not in previos:
                break
            actual = previos[actual]

        camino.reverse()
        return camino

    def _contar_transferencias(self, pasos: List[Tuple]) -> int:
        return sum(
            1
            for index in range(1, len(pasos))
            if pasos[index][1] != pasos[index - 1][1]
        )
    
    def _get_detalle_ruta(self, pasos: List[Tuple]) -> List[Dict]:
        """Obtiene información detallada de cada paso de la ruta"""
        detalle = []
        
        for i, (punto_id, ruta_id) in enumerate(pasos):
            punto = self.db.query(Punto).filter(Punto.id == punto_id).first()
            ruta = self.db.query(Ruta).filter(Ruta.id == ruta_id).first()
            punto_ruta = self.db.query(LineaRutaPunto).filter(
                LineaRutaPunto.punto_id == punto_id,
                LineaRutaPunto.ruta_id == ruta_id,
            ).first()
            
            if punto and ruta:
                geom = to_shape(punto.geometria)

                detalle.append({
                    'orden': i + 1,
                    'punto_id': punto_id,
                    'descripcion': punto.descripcion or f"Punto {punto_id}",
                    'latitud': float(geom.y),
                    'longitud': float(geom.x),
                    'ruta_id': ruta_id,
                    'nombre_linea': ruta.linea.nombre_linea if ruta.linea else None,
                    'tipo_ruta': ruta.tipo_ruta,
                    'es_transferencia': (i > 0 and ruta_id != pasos[i-1][1]),
                    'stop': punto.stop,
                    'distancia_acumulada': float(punto_ruta.distancia_acumulada) if punto_ruta and punto_ruta.distancia_acumulada is not None else None,
                    'tiempo_acumulado': float(punto_ruta.tiempo_acumulado) if punto_ruta and punto_ruta.tiempo_acumulado is not None else None,
                })
        
        return detalle
    
    def encontrar_puntos_cercanos(self, lat: float, lon: float, radio_metros: int = 200) -> List[Dict]:
        """Encuentra puntos de parada cercanos a una ubicación"""
        point_wkt = f"POINT({lon} {lat})"
        
        puntos = self.db.query(Punto).filter(
            Punto.stop == True,
            ST_Distance(
                ST_Transform(Punto.geometria, 32720),
                ST_Transform(WKTElement(point_wkt, 4326), 32720)
            ) <= radio_metros
        ).all()
        
        resultados = []
        for p in puntos:
            # Calcular distancia
            distancia = self.db.query(
                ST_Distance(
                    ST_Transform(p.geometria, 32720),
                    ST_Transform(WKTElement(point_wkt, 4326), 32720)
                )
            ).scalar()
            
            geom = to_shape(p.geometria)

            resultados.append({
                'id': p.id,
                'descripcion': p.descripcion,
                'latitud': float(geom.y),
                'longitud': float(geom.x),
                'distancia': float(distancia) if distancia else 0,
                'lineas': self._get_lineas_punto(p.id)
            })
        
        return resultados
    
    def _get_lineas_punto(self, punto_id: int) -> List[str]:
        """Obtiene las líneas que pasan por un punto"""
        rutas = self.db.query(LineaRutaPunto).filter(
            LineaRutaPunto.punto_id == punto_id
        ).all()
        
        lineas_nombres = set()
        for ruta in rutas:
            ruta_info = self.db.query(Ruta).filter(Ruta.id == ruta.ruta_id).first()
            if ruta_info and ruta_info.linea:
                lineas_nombres.add(ruta_info.linea.nombre_linea)
        
        return sorted(list(lineas_nombres))
