# Herramientas de contenido con IA

Scripts en Python para producir videos verticales (9:16) con voz en off y armar ebooks en HTML.

| Script | Qué hace |
|---|---|
| `voz.py` | Genera la voz en off de un guion con ElevenLabs, con tiempos por palabra. |
| `plan_broll.py` | Arma la lista de clips de b-roll a partir de las líneas `[B: ...]` de un guion. |
| `montaje.py` | Junta voz, b-roll, subtítulos por palabra (la activa en amarillo) y textos en pantalla en un video final con ffmpeg. |
| `diseccionar_video.py` | Saca una tira de fotogramas y la transcripción de un video. |
| `ebook.py` | Convierte un archivo de recetas en un ebook HTML A4 listo para pasar a PDF. |

## Requisitos

- Python 3.9 o superior (solo usa la librería estándar).
- [ffmpeg](https://ffmpeg.org/) en el PATH, para `montaje.py` y `diseccionar_video.py`.
- Una clave de ElevenLabs en la variable de entorno `ELEVENLABS_API_KEY`, para `voz.py` y `diseccionar_video.py`.

Las claves se leen siempre del entorno: nunca se escriben en el código.

## Formato del guion

`voz.py`, `plan_broll.py` y `montaje.py` leen un guion en Markdown con estas secciones:

```markdown
## HOOK
Primera frase que frena el scroll.
[B: descripción del clip de fondo]

## RE-HOOK
Segunda frase.

## CUERPO
Desarrollo, una frase por línea.
[T: Texto en pantalla con *palabra resaltada*]

## CTA
Llamado a la acción.

## VARIANTE H02
Otro hook alternativo.
```

## Uso rápido

```bash
python voz.py guion.md voz/ <voice_id> 1.1
python plan_broll.py guion.md videos/ v1- "Nombre" "cinematic, natural light"
python montaje.py montaje.json
python diseccionar_video.py video.mp4
python ebook.py recetas.txt meta.json ebook.html
```

Cada script explica sus parámetros al principio del archivo.

## Licencia

MIT
