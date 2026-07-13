#!/usr/bin/env python3
"""
generate_map.py

Consulta JPL Horizons por la posición heliocéntrica (X, Y en el plano
eclíptico) del Sol, los planetas y 3I/ATLAS, y genera un esquema en SVG
del sistema solar visto "desde arriba", con la posición real de cada
cuerpo en la fecha de ejecución.

Pensado para insertarse directo en 3i-atlas.html (es un <svg> standalone).

Fuente de datos: https://ssd-api.jpl.nasa.gov/doc/horizons.html
"""

import os
import re
import math
import requests
from datetime import datetime, timezone

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

# Cuerpos a graficar: (nombre visible, COMMAND de Horizons, color)
BODIES = [
    ("Mercurio", "199", "#9b9b9b"),
    ("Venus",    "299", "#d9a441"),
    ("Tierra",   "399", "#4a90d9"),
    ("Marte",    "499", "#c1440e"),
    ("Júpiter",  "599", "#d8b98a"),
    ("Saturno",  "699", "#e0d4a8"),
]

ATLAS_COMMAND = "DES=C/2025 N1;"
ATLAS_NAME = "3I/ATLAS"
ATLAS_COLOR = "#5ee6d0"


def fetch_heliocentric_xy(command: str, date: str) -> tuple[float, float]:
    """
    Pide a Horizons el vector de posición heliocéntrico (X, Y en AU,
    plano eclíptico J2000) de un cuerpo en una fecha dada.
    """
    params = {
        "format": "json",
        "COMMAND": f"'{command}'",
        "OBJ_DATA": "'NO'",
        "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'VECTORS'",
        "CENTER": "'500@10'",       # heliocéntrico (10 = Sol)
        "REF_PLANE": "'ECLIPTIC'",
        "VEC_TABLE": "'1'",         # solo posición (X,Y,Z), sin velocidad
        "OUT_UNITS": "'AU-D'",
        "START_TIME": f"'{date}'",
        "STOP_TIME": f"'{date} 01:00'",
        "STEP_SIZE": "'1h'",
    }
    response = requests.get(HORIZONS_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    if "result" not in data:
        raise RuntimeError(f"Respuesta inesperada de Horizons para {command}: {data}")

    raw = data["result"]

    match = re.search(
        r"X\s*=\s*([-\d.E+]+)\s*Y\s*=\s*([-\d.E+]+)\s*Z\s*=\s*([-\d.E+]+)",
        raw,
    )
    if not match:
        raise RuntimeError(
            f"No se pudo extraer vector X/Y/Z para {command}. "
            f"Respuesta cruda guardada para depurar."
        )

    x = float(match.group(1))
    y = float(match.group(2))
    return x, y


def build_svg(positions: dict, today_label: str) -> str:
    """
    Arma el SVG del esquema. `positions` es un dict:
    { nombre: {"x": ..., "y": ..., "color": ..., "es_atlas": bool} }
    """
    size = 600
    center = size / 2

    all_r = [math.hypot(p["x"], p["y"]) for p in positions.values()]
    max_r = max(all_r) * 1.12
    scale = (center - 40) / max_r

    def to_svg_coords(x, y):
        # Y invertido para que "arriba" sea eclíptica norte convencional
        return center + x * scale, center - y * scale

    svg_parts = [
        f'<svg viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="sans-serif">',
        f'<rect width="{size}" height="{size}" fill="#0a0a12"/>',
    ]

    # Anillos de referencia (distancia actual de cada planeta, no orbita real)
    for name, p in positions.items():
        if p.get("es_atlas"):
            continue
        r_px = math.hypot(p["x"], p["y"]) * scale
        svg_parts.append(
            f'<circle cx="{center}" cy="{center}" r="{r_px:.1f}" '
            f'fill="none" stroke="#2a2a3a" stroke-width="1" stroke-dasharray="2,3"/>'
        )

    # Sol
    svg_parts.append(
        f'<circle cx="{center}" cy="{center}" r="9" fill="#ffd35c"/>'
        f'<text x="{center}" y="{center - 14}" fill="#ffd35c" font-size="11" '
        f'text-anchor="middle">Sol</text>'
    )

    # Cuerpos
    for name, p in positions.items():
        cx, cy = to_svg_coords(p["x"], p["y"])
        radius = 7 if p.get("es_atlas") else 5
        svg_parts.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius}" fill="{p["color"]}"/>'
        )
        label_dy = -12 if p.get("es_atlas") else -9
        weight = "bold" if p.get("es_atlas") else "normal"
        svg_parts.append(
            f'<text x="{cx:.1f}" y="{cy + label_dy:.1f}" fill="{p["color"]}" '
            f'font-size="11" font-weight="{weight}" text-anchor="middle">{name}</text>'
        )

    # Título y nota de escala
    svg_parts.append(
        f'<text x="16" y="26" fill="#e8e8f0" font-size="14" font-weight="bold">'
        f'Sistema solar — posiciones del {today_label}</text>'
    )
    svg_parts.append(
        f'<text x="16" y="{size - 14}" fill="#6a6a7a" font-size="10">'
        f'Vista cenital · distancias a escala lineal · tamaños de cuerpos NO a escala · '
        f'Fuente: JPL Horizons (NASA)</text>'
    )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def main():
    os.makedirs("mapas", exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_label = datetime.now(timezone.utc).strftime("%d/%m/%Y")

    positions = {}

    for name, command, color in BODIES:
        x, y = fetch_heliocentric_xy(command, today)
        positions[name] = {"x": x, "y": y, "color": color, "es_atlas": False}
        print(f"{name}: X={x:.4f} AU, Y={y:.4f} AU")

    atlas_x, atlas_y = fetch_heliocentric_xy(ATLAS_COMMAND, today)
    positions[ATLAS_NAME] = {"x": atlas_x, "y": atlas_y, "color": ATLAS_COLOR, "es_atlas": True}
    print(f"{ATLAS_NAME}: X={atlas_x:.4f} AU, Y={atlas_y:.4f} AU")

    svg_content = build_svg(positions, today_label)

    # Versión "latest" que siempre se sobreescribe (para embeber en el sitio)
    with open("mapas/mapa_3iatlas.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)

    # Copia con fecha, para tener historial
    with open(f"mapas/mapa_3iatlas_{today}.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)

    print("Mapa generado: mapas/mapa_3iatlas.svg")


if __name__ == "__main__":
    main()
