# mundomag-scraper

Scraper automático para generar reportes de datos que alimentan las
secciones fijas de Mundo Maravilloso (mundomag.fyi). Corre en GitHub
Actions — no depende de tu PC ni de tu hosting actual.

**Importante:** este repo NO publica nada directo a tu sitio. Solo genera
reportes en `reportes/` para que vos los revises y los conviertas en
artículo con la plantilla del sitio.

## Qué hace ahora mismo

- `scripts/fetch_3iatlas.py`: consulta la API pública de JPL Horizons
  (NASA) y genera un reporte diario en Markdown con distancia al Sol,
  distancia a la Tierra y magnitud del objeto interestelar 3I/ATLAS.

## Cómo se configura (una sola vez)

1. Crear un repositorio nuevo en GitHub (puede ser privado), por ejemplo
   `mundomag-scraper`.
2. Subir el contenido de esta carpeta a ese repo:
   ```bash
   cd mundomag-scraper
   git init
   git add .
   git commit -m "Setup inicial del scraper"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/mundomag-scraper.git
   git push -u origin main
   ```
3. No hace falta configurar ningún secret/API key — JPL Horizons es
   pública y gratuita.
4. El workflow (`.github/workflows/update-3iatlas.yml`) va a correr
   solo todos los días a las 09:00 UTC. También podés dispararlo a mano
   desde la pestaña "Actions" del repo en GitHub, botón "Run workflow".

## Cómo se prueba manualmente (antes de dejarlo en automático)

```bash
pip install -r requirements.txt
python scripts/fetch_3iatlas.py
```

Esto va a crear un archivo como `reportes/3iatlas_2026-07-12.md` con los
datos del día.

## Próximos pasos (para cuando este esté validado)

- Sumar `scripts/fetch_uap.py` para UAP Watch (fuente por confirmar)
- Sumar `scripts/fetch_pursue.py` para PURSUE (fuente por confirmar)
- Evaluar si conviene que el workflow también genere un borrador de HTML
  usando la plantilla del skill, o si preferís seguir pasando el reporte
  a Claude manualmente para redactar el artículo
