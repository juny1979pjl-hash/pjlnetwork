# Short diario de mapas: instrucciones

Cada día se hace **un** short vertical (1080×1920, 45–60 s) en español, con el mismo estilo que `ejemplos/alaska` y `ejemplos/haiti`. Luego se programa en YouTube a través de Make.

## 1. Elegir el tema
- Lee `temas.json`. El día N se cuenta desde `inicio` (día 0, en fecha UTC) y su tema es `temas[N % len(temas)]`.
- Es un cálculo fijo según la fecha, así que no hace falta llevar ningún estado.

## 2. Preparar el entorno
```bash
bash mapas-shorts/engine/setup.sh "$SCRATCH/hoy"
```
Esto instala las dependencias de npm, descarga Kokoro (la voz) desde las releases de GitHub y copia `render.js` y `tts.py`.

**Red disponible:** npm, PyPI y GitHub funcionan. Hugging Face, Natural Earth, edge-tts y Higgsfield están bloqueados.

## 3. Guion (`scenes.json`)
- Escribe entre 7 y 9 escenas con los campos `id`, `say` y `cap`:
  - `say` es el texto que lee la voz. Escribe los años con letras ("mil ochocientos cuatro").
  - `cap` es el subtítulo. Marca con `*palabra*` las palabras que deben salir en dorado.
- Estructura:
  1. Gancho con una pregunta en los primeros 3 s.
  2. Contexto, causa, giro y consecuencia.
  3. Cierre con una pregunta para los comentarios.
- **Comprueba cada dato:** fechas, cifras y nombres. Si un dato está en disputa, dilo con matices. Nada inventado.
- Luego ejecuta `python3 tts.py`. Genera `s0.wav`… y `durs.json` con la voz `em_alex`, `lang="es"` y velocidad 1.12.
- Une las pistas:
```bash
ffmpeg -f concat -safe 0 -i list.txt -af loudnorm=I=-14:TP=-1.5 -ar 48000 voice.wav
```

## 4. Animación (`page.html`)
- Copia `ejemplos/haiti/page.html`; es el que tiene los subtítulos con `*palabra*`.
- Adapta al tema:
  - `CAM`: una cámara `[lon, lat, escala]` por escena.
  - Colores de países: usa sus códigos ISO numéricos de world-atlas.
  - Superposiciones por `sceneId`.
- Revisa las vistas previas:
```bash
node render.js preview
```
  Mira los `prev*.jpg`. No debe haber textos solapados ni etiquetas cortadas, y nada debe tapar la caja de subtítulos (y > 1500).
- Renderiza:
```bash
node render.js full short.mp4
```
  Tarda unos 10 min. Lánzalo en segundo plano y espera a que termine.
- Verifica con `ffprobe` la duración, que haya audio y que sea 1080×1920.

## 5. Alojar el vídeo
- Copia el MP4 a `shorts/AAAA-MM-DD-<slug>.mp4`.
- Haz commit y push a la rama de la sesión. El repo es público, así que la URL será:
  `https://raw.githubusercontent.com/juny1979pjl-hash/pjlnetwork/<rama>/shorts/<archivo>.mp4`
- Comprueba con `curl -I` que la URL devuelve 200.
- **No abras ninguna PR** por estos vídeos diarios.

## 6. Programar en YouTube (Make)
- Lanza el escenario de Make **6890445** («Shorts Mapas - Subir a YouTube programado»), equipo 2442310, con `scenarios_run` (`responsive: true`). Datos:
  - `video_url`: la URL raw.
  - `title`: hasta 100 caracteres, sin `<` ni `>`. Termina en `#shorts`.
  - `description`: 2–3 frases, 3–5 hashtags y la línea "Mapa: Natural Earth (dominio público)."
  - `publish_at`: hoy a las **01:00:00Z** del día siguiente, es decir, las 19:00 de Ciudad de México. Formato ISO, por ejemplo `2026-11-05T01:00:00.000Z`.
- El escenario sube el vídeo como privado con publicación programada. Si falla, revisa `executions_get-detail` antes de reintentar. Reintenta como mucho una vez.

## 6b. TikTok (borrador)
- Importa el vídeo en Higgsfield con `media_import_url`. Usa la URL de jsDelivr con el **hash del commit**, porque la URL raw de GitHub se rechaza (llega como octet-stream):
  `https://cdn.jsdelivr.net/gh/juny1979pjl-hash/pjlnetwork@<hash>/shorts/<archivo>.mp4`
- Con `show_medias` (tipo video) obtén la URL de cloudfront de ese media_id.
- Llama a `tiktok_prepare_publish` con `connector_id` 6c15e3eb-b4fe-49bb-beda-5f0e6b4a1073, modo `UPLOAD_TO_DRAFT`, un título corto con emoji y una descripción con hashtags.
- El usuario confirma el formulario. **Nunca** llames a `tiktok_publish` tú. El formulario caduca en 1 h; si caduca, prepáralo de nuevo cuando el usuario lo pida.

## 7. Informe
Termina con un resumen corto: tema, título, hora de publicación, URL del vídeo y el resultado de la ejecución de Make.
