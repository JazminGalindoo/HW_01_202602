# HW_01_202602 — RPA, Web Scraping y Automatización de API

Proyecto integrador del curso Python para Data Science. Tres proyectos independientes:

| Parte | Proyecto | Tecnología | Estado |
|---|---|---|---|
| 1 | PeopleSync — registro RPA de empleados | Python + Selenium | 🔶 estructura lista, en pruebas |
| 2 | SUNAT — scraping del tipo de cambio | Python + Selenium | 🔶 estructura lista, faltan selectores finales |
| 3 | Lichess — análisis de partidas (API) | Python + requests + pandas + matplotlib | ✅ funcionando |

## Instalación

```
pip install -r requirements.txt
```

Se necesita tener Google Chrome instalado para las Partes 1 y 2 (Selenium controla el navegador).

## Estructura

```
part1_peoplesync_rpa/   script RPA para el formulario de PeopleSync
part2_sunat_scraping/   script de scraping del tipo de cambio SUNAT
part3_lichess/          script de análisis de partidas de Lichess
output/                 archivos CSV y gráficos generados por los scripts
```

## Cómo correr cada parte

**Parte 3 — Lichess (funcionando):**
```
cd part3_lichess
python lichess_analysis.py --username TU_USUARIO --max-games 50
```

**Parte 2 — SUNAT:**
```
cd part2_sunat_scraping
python sunat_scraper.py
```

**Parte 1 — PeopleSync:**
```
cd part1_peoplesync_rpa
python peoplesync_rpa.py
```

## Notas

Este proyecto está en desarrollo activo. Las Partes 1 y 2 tienen la lógica de automatización completa, pero requieren ajuste de selectores contra el HTML real de cada sitio antes de la ejecución final y la configuración del Programador de Tareas de Windows.
