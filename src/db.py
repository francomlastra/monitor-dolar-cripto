"""Almacenamiento en SQLite y exportación a CSV.

El esquema es de serie temporal en formato largo y append-only: cada
corrida del pipeline agrega filas nuevas con su timestamp, nunca
actualiza ni borra. La historia completa queda en la base.
"""

import csv
import logging
import sqlite3
from pathlib import Path

log = logging.getLogger(__name__)

RUTA_RAIZ = Path(__file__).resolve().parents[1]
RUTA_DB = RUTA_RAIZ / "data" / "cotizaciones.db"
RUTA_EXPORTS = RUTA_RAIZ / "data" / "exports"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS cotizaciones_dolar (
    id            INTEGER PRIMARY KEY,
    timestamp_utc TEXT NOT NULL,   -- momento de la corrida (ISO 8601, UTC)
    tipo          TEXT NOT NULL,   -- oficial, blue, bolsa, contadoconliqui, ...
    compra        REAL,
    venta         REAL,
    fecha_fuente  TEXT             -- última actualización según DolarAPI
);

CREATE TABLE IF NOT EXISTS precios_cripto (
    id            INTEGER PRIMARY KEY,
    timestamp_utc TEXT NOT NULL,
    moneda        TEXT NOT NULL,   -- BTC, ETH, USDT
    precio_usd    REAL,
    precio_ars    REAL
);

CREATE INDEX IF NOT EXISTS idx_dolar_tipo_ts
    ON cotizaciones_dolar (tipo, timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_cripto_moneda_ts
    ON precios_cripto (moneda, timestamp_utc);
"""


def conectar(ruta: Path = RUTA_DB) -> sqlite3.Connection:
    """Abre la base (la crea si no existe) y asegura el esquema."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(ruta)
    conexion.executescript(ESQUEMA)
    return conexion


def guardar_dolares(
    conexion: sqlite3.Connection, cotizaciones: list[dict], timestamp_utc: str
) -> int:
    """Inserta las cotizaciones de una corrida. Devuelve filas insertadas."""
    filas = [
        (timestamp_utc, c["tipo"], c["compra"], c["venta"], c["fecha_fuente"])
        for c in cotizaciones
    ]
    with conexion:
        conexion.executemany(
            "INSERT INTO cotizaciones_dolar"
            " (timestamp_utc, tipo, compra, venta, fecha_fuente)"
            " VALUES (?, ?, ?, ?, ?)",
            filas,
        )
    log.info("SQLite: %d cotizaciones de dólar guardadas", len(filas))
    return len(filas)


def guardar_criptos(
    conexion: sqlite3.Connection, precios: list[dict], timestamp_utc: str
) -> int:
    """Inserta los precios cripto de una corrida. Devuelve filas insertadas."""
    filas = [
        (timestamp_utc, p["moneda"], p["precio_usd"], p["precio_ars"])
        for p in precios
    ]
    with conexion:
        conexion.executemany(
            "INSERT INTO precios_cripto"
            " (timestamp_utc, moneda, precio_usd, precio_ars)"
            " VALUES (?, ?, ?, ?)",
            filas,
        )
    log.info("SQLite: %d precios cripto guardados", len(filas))
    return len(filas)


def exportar_csv(
    conexion: sqlite3.Connection, carpeta: Path = RUTA_EXPORTS
) -> list[Path]:
    """Exporta cada tabla completa a un CSV en data/exports/.

    Los CSV se regeneran enteros en cada corrida: son una vista cómoda de
    la base para abrir en Excel/Sheets o cargar en otra herramienta,
    la fuente de verdad sigue siendo el .db.
    """
    carpeta.mkdir(parents=True, exist_ok=True)
    rutas = []

    for tabla in ("cotizaciones_dolar", "precios_cripto"):
        cursor = conexion.execute(f"SELECT * FROM {tabla} ORDER BY id")
        columnas = [desc[0] for desc in cursor.description]

        ruta = carpeta / f"{tabla}.csv"
        with open(ruta, "w", newline="", encoding="utf-8") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(columnas)
            escritor.writerows(cursor)
        rutas.append(ruta)

    log.info("CSV exportados a %s", carpeta)
    return rutas
