#!/usr/bin/env python3
"""mis_comprobaciones.py - EJERCICIO 3 de la practica autonoma: extiende la herramienta con TU comprobacion.

analiza_bag.py comprueba ritmos, huecos, latencia y reloj... pero es ciega a otros fallos. Prueba:
    python3 -c "import simulador_bags as s; s.generar('mi_rango', 'bags', fuera_de_rango=(10, 12, 9.9))"
    python3 analiza_bag.py bags/mi_rango --esperado /distancia=10        # dice TODO_OK ... pero el sensor
                                                                         # publico 9.9 m con max_range = 4 m
Tu tarea (elige al menos UNA; la segunda es ampliacion):
    1. comprobar_rangos : valores de `range` fuera de [min_range, max_range]            -> ERROR  RANGO_FUERA
    2. comprobar_frames : mas de un frame_id distinto en un topic                        -> WARN   FRAME_MIXTO
Reglas de la practica:
    - NO cambies los nombres ni las firmas de las funciones (las pruebas de test_mis_comprobaciones.py las usan).
    - Cada comprobacion devuelve una LISTA de Hallazgo (la clase de analiza_bag.py); lista vacia = sin problemas.
    - Escribe, ademas, al menos DOS pruebas propias nuevas en test_mis_comprobaciones.py (clase PruebasPropias).
    - Cuando funcione, integrala (opcional): anade la llamada en analiza_bag.analizar_ruta o usa `main` de este fichero.

Uso:  python3 mis_comprobaciones.py bags/mi_rango /distancia        # codigo de salida 1 si hay ERROR
"""
import sys
from pathlib import Path

from analiza_bag import Hallazgo


def leer_muestras_range(ruta_bag, topic):
    """(YA HECHA) Lee un topic sensor_msgs/Range del bag.

    Devuelve una lista de dicts: {'t': segundos desde el inicio del bag, 'range': float, 'min_range': float,
    'max_range': float, 'frame_id': str}, en orden de grabacion.
    """
    from rosbags.highlevel import AnyReader
    from rosbags.typesys import Stores, get_typestore
    ts = get_typestore(Stores.ROS2_JAZZY)
    out = []
    with AnyReader([Path(ruta_bag)], default_typestore=ts) as r:
        t0 = r.start_time / 1e9
        for conn, t_ns, raw in r.messages():
            if conn.topic != topic:
                continue
            m = r.deserialize(raw, conn.msgtype)
            out.append({'t': t_ns / 1e9 - t0, 'range': float(m.range), 'min_range': float(m.min_range),
                        'max_range': float(m.max_range), 'frame_id': m.header.frame_id})
    return out


def comprobar_rangos(muestras, topic='', margen=0.0):
    """Detecta muestras cuyo rango está fuera de los límites permitidos."""
    if not muestras:
        return []

    fuera = [
        muestra for muestra in muestras
        if muestra['range'] < muestra['min_range'] - margen
        or muestra['range'] > muestra['max_range'] + margen
    ]

    if not fuera:
        return []

    t_inicio = fuera[0]['t']
    t_fin = fuera[-1]['t']

    detalle = (
        f'{len(fuera)} de {len(muestras)} muestras fuera de rango. '
        f'Intervalo de tiempo: {t_inicio:.3f} s - {t_fin:.3f} s'
    )

    return [Hallazgo('ERROR', 'RANGO_FUERA', topic, detalle)]

def comprobar_frames(muestras, topic=''):
    """Detecta si un topic contiene varios frame_id distintos."""
    frames = list(dict.fromkeys(
        muestra['frame_id'] for muestra in muestras
    ))

    if len(frames) <= 1:
        return []

    detalle = f'Frames distintos encontrados: {", ".join(frames)}'

    return [Hallazgo('WARN', 'FRAME_MIXTO', topic, detalle)]
def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print('uso: mis_comprobaciones.py <carpeta_bag> <topic_range>')
        return 2
    muestras = leer_muestras_range(argv[0], argv[1])
    hallazgos = list(comprobar_rangos(muestras, argv[1]))
    try:
        hallazgos += comprobar_frames(muestras, argv[1])
    except NotImplementedError:
        pass
    if not hallazgos:
        print(f'[INFO ] {argv[1]}: sin problemas de rango ni de frame ({len(muestras)} muestras)')
    for h in hallazgos:
        print(f'[{h.severidad:5s}] {h.codigo:14s} {h.topic}  {h.detalle}')
    return 1 if any(h.severidad == 'ERROR' for h in hallazgos) else 0


if __name__ == '__main__':
    sys.exit(main())
