---
title: "Acerca de"
---

Esta página web es un registro de todas las películas, series y videojuegos que he consumido desde que hago seguimiento de ello.

## Historia y Motivación

Previamente usé Notion para hacer algo parecido. Creé una [plantilla](https://www.notion.com/templates/media-tracker-en) y se podía generar una [página web](https://christt105.notion.site/media-tracker) fácilmente, pero no me acababa de convencer. Desde que usé [Obsidian](https://obsidian.md/), migré todo el contenido a él.

El problema con [Obsidian](https://obsidian.md/) es que no tiene una opción para generar una página web fácilmente. Por eso decidí usar [Hugo](https://gohugo.io/). Hacerme mi propia página me permite hacerla a mi gusto aunque conlleve algo más de trabajo y yo no sea un programador web.

Toda la página está en castellano por el simple motivo que es un espacio personal más enfocado a mí que a otras personas, por lo que no creo que tenga prácticamente nada de tráfico y estoy más a gusto escribiendo en castellano.

## Cómo está hecha esta web

Esta página web está generada a partir de mis notas de [Obsidian](https://obsidian.md/) usando [Hugo](https://gohugo.io/). Es una página estática, sin servidor ni base de datos, publicada en GitHub Pages.

Tengo un script de Python que convierte las notas de mi vault de Obsidian al frontmatter de Hugo. Al hacer commit se genera la web automáticamente y se despliega. El contenido completo está en [este repositorio](https://github.com/christt105/MediaTracker).

Con el tiempo el proyecto ha crecido bastante. Empecé usando [hugo-blog-awesome](https://github.com/hugo-sid/hugo-blog-awesome) como base, pero acabé desarrollando mi propio tema de Hugo: [hugo-mediatracker-theme](https://github.com/christt105/hugo-mediatracker-theme). Es un módulo de Hugo reutilizable, y hay un [repositorio plantilla](https://github.com/christt105/mediatracker-starter) para que cualquiera pueda montar algo parecido sin partir de cero.

He escrito una serie de entradas en mi blog explicando todo el proceso:

- [Media Tracker: Orígenes](https://christt105.github.io/blog/media-tracker-origins/) — de Notion a Obsidian
- [Media Tracker: Obsidian](https://christt105.github.io/blog/media-tracker-obsidian/) — cómo organizo las notas y el script de conversión
- [Media Tracker: Hugo](https://christt105.github.io/blog/media-tracker-hugo/) — el tema, la arquitectura y el despliegue

## Funcionalidades

La página tiene bastante más de lo que parece a primera vista:

- **Filtros**: búsqueda por texto, tipo de contenido, estado, puntuación, plataforma y etiquetas. Los filtros se encadenan y la URL se actualiza para poder compartir una búsqueda concreta.
- **Estadísticas**: página de [stats](../stats) con distribución de puntuaciones, completadas por año (incluyendo repeticiones), géneros más vistos, y gráficos de plataformas, anime y cine vs. streaming. Se puede filtrar por año.
- **Collage**: generador de [collages](../collage) con las portadas de lo completado en un rango de fechas, exportable como PNG.
- **RSS**: feed de lo que voy terminando, para quien quiera seguirlo.
- **Repeticiones**: el campo `rewatches` registra cada vez que vuelvo a ver o jugar algo, y las stats lo tienen en cuenta.

Es un proyecto vivo que voy mejorando cuando tengo ganas o cuando algo me molesta. Si te parece útil o tienes algún comentario, hay una sección justo debajo y en cada elemento para ello.

## Sistema de puntuación

Todos los comentarios y notas de cada elemento son subjetivos bajo mis criterios y circunstancias a la hora de escribirlos. No pretendo que sea nada más que mis notas para poder hacer un seguimiento. No soy ningún experto en cine ni videojuegos ni pretendo serlo.

Las puntuaciones en general no suelen decir mucho, todo depende de tu estado actual de ánimo, tu contexto sobre el contenido multimedia y demás, no creo que haya mucha diferencia entre un 6 y un 7, entre un 2 y un 4, así que no quería notas numéricas. Me decanté por el sistema de [Steph Ango](https://stephango.com/about), actual CEO de [Obsidian](https://obsidian.md/).

[El sistema de puntuación de Steph Ango](https://stephango.com/vault#rating-system) se basa en una escala del 1 al 7 y me pareció un sistema interesante ya que permite más granularidad en los contenidos que te gustan, que serán la mayoría, a los que no te gusten. En la web no muestro el número, únicamente el nombre y el icono. Normalmente me trago todo lo que veo y no soy muy crítico, por lo que difícilmente pondré alguna nota por debajo del 3.

Esta es la escala de puntuación:

- **7 -- Obra Maestra.** La perfección absoluta (o casi). Algo que me ha marcado profundamente, que cambia mi forma de ver el género o que recordaré toda la vida.
- **6 -- Increíble.** Excelente en casi todos los apartados. Me ha encantado de principio a fin y no dudaría en recomendarlo a cualquiera. Muy cerca de ser perfecto.
- **5 -- Bueno.** Una experiencia sólida. Cumple lo que promete, es disfrutable. Tiene fallos, pero las virtudes pesan más. Un "buen rato" garantizado.
- **4 -- Decente.** Ni frío ni calor. Se deja ver o jugar, pero probablemente lo olvide la semana que viene. Entretenimiento de "comida rápida" o algo con potencial desperdiciado.
- **3 -- Malo.** Tiene problemas graves. Puede que tenga alguna idea buena, pero la ejecución falla. Aburrido, frustrante o técnicamente deficiente.
- **2 -- Terrible.** Una pérdida de tiempo. Falla en lo básico. Me ha costado terminarlo (si es que lo he hecho) y me arrepiento de haber empezado.
- **1 -- Abismal.** Lo peor de lo peor. Roto, ofensivo o insultante para la inteligencia. Huye sin mirar atrás.