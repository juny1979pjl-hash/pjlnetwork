# Recursos de producción: "Bukele en Haití: toda la historia"

Material audiovisual del especial. El guion completo está en [`haiti-bukele-voz-off.md`](haiti-bukele-voz-off.md).

## Video final (Descript)

| Recurso | Enlace |
|---|---|
| **Ver el reportaje final (15:28, 1080p)** | https://share.descript.com/view/O1Yj9W9xZzP |
| Proyecto editable en Descript (composición "REPORTAJE FINAL — Bukele en Haití") | https://web.descript.com/a009ca19-65f1-4d72-a690-55c37f088d2b/a4937 |
| Primera versión (fondo negro, solo rótulos) | https://share.descript.com/view/9EHeniyPdGc |

**Qué contiene el montaje final**

- **Voz off completa**, en cuatro tramos.
- **Apertura, tarjetas de capítulo y cierre con fuentes.**
- **Unas 70 escenas animadas y sincronizadas con la narración:**
  - Mapas de Centroamérica, el Caribe y Haití, con marcadores y rutas.
  - Contadores y gráficos de barras con las cifras.
  - Líneas de tiempo, citas a pantalla completa y la tarjeta de las cuatro siluetas.
- **18 rótulos** con fechas y datos.
- **Barra de titulares** que se desplaza en la parte inferior, con la marca "ESPECIAL · BUKELE EN HAITÍ".
- **Subtítulos en español** incrustados.
- **Música de fondo original**, que sube en la apertura, las pausas entre capítulos y el cierre.

Todo el material visual son gráficos y mapas ilustrativos: no hay imágenes de stock ni fotografías de personas reales.

### Cómo se produjo

La imagen se genera con los scripts de [`produccion/`](produccion/), escritos en Python con Pillow, OpenCV, CairoSVG y ffmpeg:

| Archivo | Qué hace |
|---|---|
| `scenes.py` | Define las escenas, los rótulos y la barra de titulares, con sus tiempos |
| `gfx.py` | Dibuja los mapas, los textos y los iconos |
| `render.py` | Anima las escenas (Ken Burns, fundidos, contadores) y codifica el video |
| `music.py` | Sintetiza la música de fondo |
| `subs.srt` | Subtítulos, sacados de la transcripción de Descript |

Después, en Descript, el video se combina con las cuatro pistas de voz.

## Voz off (Artlist)

Voz: **Alberto Rodríguez**, masculina, acento latinoamericano, tono serio y narrativo.

| Tramo | Contenido | Duración | Audio |
|---|---|---|---|
| 1 | Apertura, raíces de la crisis (2021–2024) y modelo Bukele | 3:51 | [MP3](https://cms-toolkit-artifacts.artlist.io/content/-t-e-x-t_-t-o_-s-p-e-e-c-h-v1/media__2/-t-e-x-t_-t-o_-s-p-e-e-c-h-55f1f22f-685f-4d45-bd3d-b21f2f0e3d82.mp3?Expires=2108694072&Key-Pair-Id=K2ZDLYDZI2R1DF&Signature=F8jf5Cs3Yxi9-uhWOv-H3p8w42GeFvOq83eLy5yPjFb2ONe5laESUqOShpb~OdRaOA15xMwNencsYS1Qdv-W0O3CsT5IUvPEebFyPRl5AxzI7ViClRUaSIAXIjfkSDF6RjzTb~41H5vT7HeCmOj7XF6BP4l5xmydCXAgg0it2rHezPQWIrVnvfy6nLRuSNozqiCfeNWv0zueRvIgpRC29HGkJviJ4i00cndi1nQBnLMPTMDdFCQBrfzlPe5iNtvrTaojgXLfhMvAjEhIBMbmIpbWOaKae2X6Z7ABnweYl-jVGezlPFJ~BJUYhIrLb7OnNW11FHivOznq-BR9WJI-FA__) |
| 2 | El Salvador llega a Haití, la fuerza de la ONU y la emboscada | 3:11 | [MP3](https://cms-toolkit-artifacts.artlist.io/content/-t-e-x-t_-t-o_-s-p-e-e-c-h-v1/media__10/-t-e-x-t_-t-o_-s-p-e-e-c-h-6b5cd921-da15-476f-8cd8-7790ebe53177.mp3?Expires=2108694054&Key-Pair-Id=K2ZDLYDZI2R1DF&Signature=Y2MOMbo9NYTrz4UfT6BABbuoUPg-iQr~Se11gxMCSfyuG9o9scKGSIAcNTT-YAcIsotrRVga6bIzpPdJVqoXC4vlGkQaB06N5feg0K8qwqJTB8rBJK9CbdE~XjdHmNFKlBXtvYcFiqHRCJecwhyDjiMZTXGHJoMgt-mUAyMWK4Uv~h4EmLrN5SULmapP56Dk6NY7ciLa28kEy9JzPUcUVyTEb6ONT5Ue7lzLfSTT34K8k-iB9a339gnf6Wvl6O-k99g40cAvzgBDU2JFqP4dOojElCyYJ1yIJyinTusZ9WSuZfXS66yG~Qj7xui2S8NW9-QN-dooYUctzHgF63~S2g__) |
| 3 | Respuesta de Bukele, los restos del aeropuerto y el despliegue | 3:37 | [MP3](https://cms-toolkit-artifacts.artlist.io/content/-t-e-x-t_-t-o_-s-p-e-e-c-h-v1/media__10/-t-e-x-t_-t-o_-s-p-e-e-c-h-ebac443e-2bf7-4d2a-91bd-d5716485ab55.mp3?Expires=2108694072&Key-Pair-Id=K2ZDLYDZI2R1DF&Signature=WsbELvGTvXZZGEw3JrDchpqpVNhnDXeQ2DPaMfo1xZLeNQT1APUq8U7eSogScehVXTDOhOmHJlG2J7TBaU9QSmEQx~rVpWMo9X~rHcLgDyqfvaXqTsxVRGoB~J~FOW-DfntpTB8jj7Xn2h8-BYYc~b0hWYQzqqwzVqV~o5pzAo3cS4PACyMmVS3r1s1PGgaP0lViMg6gixAc1mHgVF3ib5V~m7tNqjdqJ16zBPVx5Rq~x2qXEqlyNJhGidGq~1-IGyIxI4GxJMmywgKSHzMCpYNoAUFvypGqc8xa-T5kc9vnPAreb5nxfQB9IQa5hhVEnTjpCjSSEhFV3fiIxQEoWw__) |
| 4 | Las dudas, las voces de Haití, el día de hoy y el cierre | 3:54 | [MP3](https://cms-toolkit-artifacts.artlist.io/content/-t-e-x-t_-t-o_-s-p-e-e-c-h-v1/media__8/-t-e-x-t_-t-o_-s-p-e-e-c-h-ec27af76-1bc2-4fce-9ba4-45424c761edc.mp3?Expires=2108694078&Key-Pair-Id=K2ZDLYDZI2R1DF&Signature=x2FYgG6diLVXjOX-5qUQ4L43Nfk-JMEjf3IsNjFjdCRv~gq-tg7Yp996v69vKRf-8VYPb7JYyS9oAThygCmJZ71NbIcaUX~~YWDUYGNeNDW6z3EW7Uqk4yLTvzAdPU4SJg4p~90HslQo0pNgvkA5CQuMBWi3x36ObYYO-8DPeRrnSi9brLaB9i~CUbM5dB4OotTmJEEXnn8ov6~KJNZaYiVDdUJJ9RgQG3as8N0jv1xT4RZHu18TwD4g1Xmbf~QkcgwymVAapgzoNk3-gMNNg9~YOh5HgZS1so3PvyNkJEnML2z9HwqO6hIJfO8gHaRk5snl2Ifg1mAmhhu8Ch3ewg__) |

La voz off suma 14:33. Con la apertura, las pausas entre capítulos y el cierre, el video llega a 15:28.
