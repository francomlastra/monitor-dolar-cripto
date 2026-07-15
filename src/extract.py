"""Extracción de datos desde las APIs públicas.

Cada fuente tiene su propia función `obtener_*()` que devuelve una lista
de dicts ya normalizados (listos para insertar en la base). Si una API
falla después de los reintentos, la función lanza la excepción: es el
pipeline el que decide que la caída de una fuente no frene a las demás.
"""

import logging
import os
import time

import requests

log = logging.getLogger(__name__)

URL_DOLARES = "https://dolarapi.com/v1/dolares"
URL_COINGECKO = "https://api.coingecko.com/api/v3/simple/price"

# id de CoinGecko -> ticker que guardamos en la base
CRIPTOS = {"bitcoin": "BTC", "ethereum": "ETH", "tether": "USDT"}

TIMEOUT_SEGUNDOS = 15
REINTENTOS = 3
ESPERA_BASE = 5  # segundos; se duplica en cada reintento (5, 10, 20)


def _get_json(url: str, params: dict | None = None, headers: dict | None = None):
    """GET con timeout y reintentos con backoff exponencial.

    Reintenta ante cualquier error de red o HTTP (incluido el 429 de
    rate limit). Si el último intento también falla, propaga la excepción.
    """
    for intento in range(1, REINTENTOS + 1):
        try:
            respuesta = requests.get(
                url, params=params, headers=headers, timeout=TIMEOUT_SEGUNDOS
            )
            respuesta.raise_for_status()
            return respuesta.json()
        except requests.RequestException as error:
            log.warning(
                "Intento %d/%d falló para %s: %s", intento, REINTENTOS, url, error
            )
            if intento == REINTENTOS:
                raise
            time.sleep(ESPERA_BASE * 2 ** (intento - 1))


def obtener_dolares() -> list[dict]:
    """Consulta DolarAPI y devuelve todas las cotizaciones del dólar.

    Cada elemento tiene: tipo (oficial, blue, bolsa, contadoconliqui,
    cripto, tarjeta, mayorista), compra, venta y la fecha de última
    actualización que informa la propia fuente.
    """
    datos = _get_json(URL_DOLARES)

    cotizaciones = [
        {
            "tipo": casa["casa"],
            "compra": casa.get("compra"),
            "venta": casa.get("venta"),
            "fecha_fuente": casa.get("fechaActualizacion"),
        }
        for casa in datos
    ]

    log.info("DolarAPI: %d cotizaciones obtenidas", len(cotizaciones))
    return cotizaciones


def obtener_criptos() -> list[dict]:
    """Consulta CoinGecko y devuelve precios de BTC, ETH y USDT en USD y ARS.

    Usa el endpoint público sin key (alcanza de sobra: 3 llamadas por día).
    Si existe la variable de entorno COINGECKO_API_KEY (plan Demo gratuito),
    se envía como header — útil si la IP compartida del runner de GitHub
    Actions llegara a toparse con el rate limit del acceso sin key.
    """
    params = {"ids": ",".join(CRIPTOS), "vs_currencies": "usd,ars"}

    headers = {}
    api_key = os.getenv("COINGECKO_API_KEY")
    if api_key:
        headers["x-cg-demo-api-key"] = api_key

    datos = _get_json(URL_COINGECKO, params=params, headers=headers)

    precios = [
        {
            "moneda": ticker,
            "precio_usd": datos[id_coingecko].get("usd"),
            "precio_ars": datos[id_coingecko].get("ars"),
        }
        for id_coingecko, ticker in CRIPTOS.items()
        if id_coingecko in datos
    ]

    log.info("CoinGecko: %d monedas obtenidas", len(precios))
    return precios
