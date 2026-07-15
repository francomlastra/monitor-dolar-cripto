"""Pipeline de ingesta: extrae de todas las fuentes y guarda en SQLite.

Se ejecuta con `python -m src.pipeline` (localmente o desde GitHub
Actions). Cada fuente se procesa de forma independiente: si una API está
caída, las demás se guardan igual. El pipeline solo falla (exit code 1)
si NINGUNA fuente pudo guardarse, para que el workflow avise.

Para agregar una fuente nueva alcanza con escribir su `obtener_*()` en
extract.py, su `guardar_*()` en db.py, y sumar una entrada a FUENTES.
"""

import logging
import sys
from datetime import datetime, timezone

from src import db, extract

# (nombre para el log, función que extrae, función que guarda)
FUENTES = [
    ("DolarAPI", extract.obtener_dolares, db.guardar_dolares),
    ("CoinGecko", extract.obtener_criptos, db.guardar_criptos),
]


def correr_pipeline() -> int:
    """Corre una ronda de extracción completa. Devuelve cuántas fuentes OK."""
    # Un único timestamp para toda la corrida, así las tablas se pueden
    # cruzar por corrida sin problemas de segundos de diferencia
    timestamp_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")

    conexion = db.conectar()
    fuentes_ok = 0

    for nombre, extraer, guardar in FUENTES:
        try:
            registros = extraer()
            guardar(conexion, registros, timestamp_utc)
            fuentes_ok += 1
        except Exception:
            # La falla de una fuente no debe impedir guardar las demás
            logging.exception("La fuente %s falló; se continúa con el resto", nombre)

    if fuentes_ok > 0:
        db.exportar_csv(conexion)

    conexion.close()
    logging.info(
        "Corrida %s: %d/%d fuentes OK", timestamp_utc, fuentes_ok, len(FUENTES)
    )
    return fuentes_ok


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    exitosas = correr_pipeline()
    if exitosas == 0:
        sys.exit(1)  # ninguna fuente respondió: que el workflow marque error
