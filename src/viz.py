"""Estilo visual del proyecto: paleta, estilo de matplotlib y helpers.

Un color fijo por tipo de dólar, usado en todos los gráficos, así el
lector aprende la asociación una sola vez. La paleta fue verificada por
separación para daltonismo (deuteranopia/protanopia, ΔE mínimo entre
pares 13.5, objetivo >=12).
"""

from pathlib import Path

import matplotlib.pyplot as plt

RUTA_FIGURAS = Path(__file__).resolve().parents[1] / "reports" / "figures"

# Un color fijo por tipo de dólar (el color sigue a la entidad)
PALETA_DOLARES = {
    "oficial": "#2a78d6",  # azul
    "blue": "#e34948",  # rojo
    "bolsa": "#1baf7a",  # aqua  (MEP)
    "contadoconliqui": "#4a3aa7",  # violeta (CCL)
    "cripto": "#eda100",  # amarillo
    "mayorista": "#008300",  # verde
    "tarjeta": "#e87ba4",  # magenta
}

# Nombres cortos para ejes y leyendas
NOMBRES_DOLARES = {
    "oficial": "Oficial",
    "blue": "Blue",
    "bolsa": "MEP",
    "contadoconliqui": "CCL",
    "cripto": "Cripto",
    "mayorista": "Mayorista",
    "tarjeta": "Tarjeta",
}

AZUL = "#2a78d6"

# Tinta y chrome
SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
TINTA_TENUE = "#898781"
GRILLA = "#e1e0d9"
EJE = "#c3c2b7"


def aplicar_estilo() -> None:
    """Configura matplotlib con el estilo del proyecto (llamar una vez)."""
    plt.rcParams.update(
        {
            "figure.facecolor": SUPERFICIE,
            "axes.facecolor": SUPERFICIE,
            "savefig.facecolor": SUPERFICIE,
            "font.family": ["Segoe UI", "DejaVu Sans"],
            "text.color": TINTA,
            "axes.labelcolor": TINTA_SECUNDARIA,
            "axes.titlecolor": TINTA,
            "axes.titlesize": 13,
            "axes.titleweight": "semibold",
            "axes.titlelocation": "left",
            "axes.labelsize": 10,
            "xtick.color": TINTA_TENUE,
            "ytick.color": TINTA_TENUE,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "axes.edgecolor": EJE,
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": GRILLA,
            "grid.linewidth": 0.6,
            "axes.axisbelow": True,
            "legend.frameon": False,
            "legend.fontsize": 9,
            "figure.dpi": 100,
            "savefig.dpi": 150,
            "savefig.bbox": "tight",
        }
    )


def guardar_figura(fig: plt.Figure, nombre: str) -> Path:
    """Guarda la figura en reports/figures/ y devuelve la ruta."""
    RUTA_FIGURAS.mkdir(parents=True, exist_ok=True)
    ruta = RUTA_FIGURAS / f"{nombre}.png"
    fig.savefig(ruta)
    return ruta


def etiqueta_directa(ax: plt.Axes, x, y, texto: str, color: str) -> None:
    """Etiqueta al final de una línea, en el color de la serie."""
    ax.annotate(
        texto,
        xy=(x, y),
        xytext=(6, 0),
        textcoords="offset points",
        va="center",
        fontsize=9,
        fontweight="semibold",
        color=color,
    )
