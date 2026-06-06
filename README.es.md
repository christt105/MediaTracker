# Media Tracker

[Read in English](README.md)

**Media Tracker** es mi registro personal de películas, series y videojuegos — un
sitio Hugo generado a partir de mi bóveda de Obsidian.

> **¿Quieres crear el tuyo?**
> Este repositorio es mi contenido privado, no una plantilla.
> Usa [**mediatracker-starter**](https://github.com/christt105/mediatracker-starter)
> para crear tu propio sitio en un clic, o consulta la documentación del
> [**hugo-mediatracker-theme**](https://github.com/christt105/hugo-mediatracker-theme)
> para todas las opciones de configuración.

## Cómo funciona

El contenido vive en Obsidian. Un script de migración (`scripts/migration.py`)
convierte las notas de Obsidian en page bundles de Hugo bajo `content/`. El
directorio `content/` es por tanto **generado** — los cambios manuales se
sobreescriben en la próxima ejecución.

```
Bóveda de Obsidian
      │
      ▼
scripts/migration.py
      │
      ▼
content/  ←── generado, no editar a mano
      │
      ▼
hugo build → GitHub Actions → GitHub Pages
```

## Stack

| Herramienta | Función |
|-------------|---------|
| [Hugo](https://gohugo.io/) | Generador de sitio estático |
| [hugo-mediatracker-theme](https://github.com/christt105/hugo-mediatracker-theme) | Tema (Hugo Module) |
| [Obsidian](https://obsidian.md/) | Edición de notas / fuente de verdad |
| GitHub Actions | Build y despliegue a Pages |

## Ejecución local

```bash
hugo server
```

Requiere Hugo extended + Go (para módulos). El tema se descarga automáticamente
via `go.mod`.

## Feeds RSS

| Feed | URL |
|------|-----|
| Todo el contenido | `/index.xml` |
| Elementos acabados | `/finished.xml` |
