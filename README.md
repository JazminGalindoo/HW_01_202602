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
