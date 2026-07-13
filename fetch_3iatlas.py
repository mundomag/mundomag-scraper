#!/usr/bin/env python3
"""
fetch_3iatlas.py

Consulta la API pública de JPL Horizons (NASA) para obtener datos
actualizados del objeto interestelar 3I/ATLAS (designación C/2025 N1)
y genera un reporte en Markdown con los datos clave para la sección
fija "3I/ATLAS" de Mundo Maravilloso.

Fuente de datos: https://ssd-api.jpl.nasa.gov/doc/horizons.html
No requiere API key.
"""

import requests
import json
import re
from datetime import datetime, timezone

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

# Designación oficial del objeto en el catálogo JPL.
# 3I/ATLAS también se conoce como C/2025 N1.
OBJECT_DESIGNATION = "DES=C/2025_N1;"


def build_ephemeris_params(start_date: str, stop_date: str) -> dict:
    """
    Arma los parámetros de consulta para pedir datos de efemérides
    (posición observada desde la Tierra) para 3I/ATLAS.

    QUANTITIES elegidas:
      1  -> Ascensión recta / Declinación
      20 -> Distancia a la Tierra (delta) y tasa de cambio
      19 -> Distancia heliocéntrica (al Sol) y tasa de cambio
      9  -> Magnitud visual e intensidad de brillo superficial
    """
    return {
        "format": "json",
        "COMMAND": f"'{OBJECT_DESIGNATION}'",
        "OBJ_DATA": "'YES'",
        "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'OBSERVER'",
        "CENTER": "'500@399'",  # geocéntrico (desde el centro de la Tierra)
        "START_TIME": f"'{start_date}'",
        "STOP_TIME": f"'{stop_date}'",
        "STEP_SIZE": "'1d'",
        "QUANTITIES": "'1,9,19,20'",
    }


def fetch_horizons_data(start_date: str, stop_date: str) -> str:
    """Hace la consulta a la API y devuelve el texto crudo de resultado."""
    params = build_ephemeris_params(start_date, stop_date)
    response = requests.get(HORIZONS_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    if "result" not in data:
        raise RuntimeError(f"Respuesta inesperada de Horizons: {data}")

    return data["result"]


def parse_ephemeris_block(raw_text: str) -> list[dict]:
    """
    Extrae las filas de datos entre las marcas $$SOE y $$EOE
    que Horizons usa para delimitar la tabla de resultados.
    """
    match = re.search(r"\$\$SOE(.*?)\$\$EOE", raw_text, re.DOTALL)
    if not match:
        raise RuntimeError(
            "No se encontró bloque de datos ($$SOE/$$EOE) en la respuesta. "
            "Revisar si cambió el formato de la API o el objeto no fue encontrado."
        )

    lines = [l.strip() for l in match.group(1).strip().splitlines() if l.strip()]

    rows = []
    for line in lines:
        # Formato típico de una fila (columnas separadas por espacios,
        # el orden depende de las QUANTITIES pedidas):
        # Fecha__(UT)__HR:MN  R.A.  DEC  APmag  S-brt  delta  deldot  r  rdot
        rows.append({"raw": line})

    return rows


def extract_object_summary(raw_text: str) -> dict:
    """Extrae metadatos generales del objeto desde el encabezado de Horizons."""
    summary = {}

    name_match = re.search(r"Target body name:\s*(.+?)\{", raw_text)
    if name_match:
        summary["nombre"] = name_match.group(1).strip()

    epoch_match = re.search(r"Epoch:\s*([\d.]+)", raw_text)
    if epoch_match:
        summary["epoch_jd"] = epoch_match.group(1)

    return summary


def build_report(raw_text: str, rows: list[dict], summary: dict) -> str:
    """Genera el contenido del reporte en Markdown."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"# Reporte 3I/ATLAS — {now}",
        "",
        "> Generado automáticamente desde JPL Horizons (NASA).",
        "> Este es un REPORTE de datos crudos, no un artículo. Revisar antes de publicar.",
        "",
        "## Resumen del objeto",
        "",
    ]

    if summary:
        for key, value in summary.items():
            lines.append(f"- **{key}**: {value}")
    else:
        lines.append("- (No se pudo extraer resumen del encabezado; revisar raw_response.txt)")

    lines.append("")
    lines.append("## Datos de efemérides (crudos, últimos días consultados)")
    lines.append("")
    lines.append("```")
    for row in rows:
        lines.append(row["raw"])
    lines.append("```")
    lines.append("")
    lines.append("## Notas para la redacción")
    lines.append("")
    lines.append("- [ ] Confirmar distancia actual al Sol (UA) contra este reporte")
    lines.append("- [ ] Confirmar distancia actual a la Tierra contra este reporte")
    lines.append("- [ ] Revisar si hubo novedades de misiones observadoras (buscar manualmente)")
    lines.append("- [ ] Actualizar `3i-atlas.html` si hay cambios relevantes respecto al reporte anterior")

    return "\n".join(lines)


def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Pedimos un rango corto: hoy y mañana, un solo paso de 1 día.
    tomorrow = datetime.now(timezone.utc)
    stop = tomorrow.replace(day=tomorrow.day + 1) if tomorrow.day < 28 else tomorrow
    stop_date = stop.strftime("%Y-%m-%d")

    raw_text = fetch_horizons_data(today, stop_date)

    rows = parse_ephemeris_block(raw_text)
    summary = extract_object_summary(raw_text)
    report_md = build_report(raw_text, rows, summary)

    # Guardar el reporte del día
    filename = f"reportes/3iatlas_{today}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_md)

    # Guardar también la respuesta cruda por si hay que depurar
    with open(f"reportes/3iatlas_{today}_raw.txt", "w", encoding="utf-8") as f:
        f.write(raw_text)

    print(f"Reporte generado: {filename}")


if __name__ == "__main__":
    main()
