# Snag

GUI minimalista para yt-dlp en Windows. Descarga videos en MP4 y audio en MP3 con portada automática incrustada. Construida con Python, tkinter, yt-dlp y FFmpeg.

![Snag](snag.png)

## Descarga

Ve a [Releases](https://github.com/edmangomez/snag-yt-dlp-gui/releases) y elige una de estas dos opciones para Windows:

- **`Snag-Setup.exe`** — instalador oficial (Inno Setup): instala Snag en Program Files con accesos directos.
- **`Snag-Portable.zip`** — versión portable: descomprime y ejecuta `Snag.exe` directamente.

Ambas son **auto-contenidas**: incluyen yt-dlp y FFmpeg incrustados; no requieren instalación de Python, yt-dlp ni FFmpeg ni depender de archivos externos.

> ⚠️ Windows SmartScreen puede mostrarte un aviso porque el ejecutable no está firmado. Pulsa "Más información" → "Ejecutar de todas formas".

## Funciones

- **Video (MP4)** — descarga el mejor video + mejor audio y los fusiona en MP4 con FFmpeg.
- **MP3 (audio)** — extrae el mejor audio a MP3 en máxima calidad y **incrusta la portada** automáticamente.
- **Metadatos**: antes de guardar un MP3 se muestra un diálogo para confirmar **Artista** y **Título**; el archivo se guarda con el título confirmado.
- Barra de progreso con porcentaje y velocidad en tiempo real.
- Elige la carpeta de destino; por defecto `Descargas`.
- Portable y sin consola: el progreso se ve en la propia ventana.

## Uso

1. Abre `Snag.exe`.
2. Pega la URL del video.
3. Elige **Video** o **MP3**.
4. Pulsa **Descargar** y espera el aviso con la ruta del archivo guardado.

## Estructura

| Archivo | Descripción |
|---|---|
| `descargador.py` | Aplicación completa (GUI tkinter + lógica de descarga) |
| `abrir.bat` | Lanzador en desarrollo con `pythonw` (sin consola) |
| `snag.ico` / `snag.png` | Icono de la aplicación |
| `snag.iss` | Script de Inno Setup para generar el instalador (opcional) |

## Compilar desde el código

Requisitos: Python 3.10+, [yt-dlp](https://github.com/yt-dlp/yt-dlp), [FFmpeg](https://ffmpeg.org/), PyInstaller.

```
pip install pyinstaller
python -m PyInstaller --onefile --noconsole --icon snag.ico --add-data "snag.ico;." --add-binary "dist/yt-dlp.exe;." --add-binary "dist/ffmpeg.exe;." --add-binary "dist/ffprobe.exe;." --name Snag descargador.py
```

Los binarios de yt-dlp, ffmpeg y ffprobe quedan **incrustados** en `Snag.exe` (también se usan desde `_MEIPASS`); no hace falta copiarlos aparte. Para usar una versión distinta de yt-dlp, coloca un `yt-dlp.exe` junto al ejecutable y tendrá prioridad.

## Modo de prueba (sin ventana)

```
python descargador.py --test --url "https://www.youtube.com/watch?v=jNQXAC9IVRw" --modo mp3 --dest "C:\ruta\destino"
```

Termina en `EXITO` (código 0) o `FALLO`.

## Notas

- Descarga solo contenido que tengas derecho a descargar, respetando los términos de cada sitio.
- Para actualizar yt-dlp, basta reemplazar `yt-dlp.exe` junto a `Snag.exe`.