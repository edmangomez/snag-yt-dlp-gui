# Snag

GUI minimalista para yt-dlp en Windows. Descarga videos en MP4 y audio en MP3 con portada automática incrustada. Construida con Python, tkinter, yt-dlp y FFmpeg.

![Snag](snag.png)

## Descarga

Ve a [Releases](https://github.com/edmangomez/snag-yt-dlp-gui/releases) y descarga `Snag-Windows.zip` para Windows.

El ZIP es **portable**: extrae los 5 archivos en una carpeta y ejecuta `Snag.exe`. No requiere instalación de Python, yt-dlp ni FFmpeg.

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
python -m PyInstaller --onefile --windowed --icon snag.ico --add-data "snag.ico;." --name Snag descargador.py
```

Copia `yt-dlp.exe`, `ffmpeg.exe` y `ffprobe.exe` junto a `Snag.exe`.

## Modo de prueba (sin ventana)

```
python descargador.py --test --url "https://www.youtube.com/watch?v=jNQXAC9IVRw" --modo mp3 --dest "C:\ruta\destino"
```

Termina en `EXITO` (código 0) o `FALLO`.

## Notas

- Descarga solo contenido que tengas derecho a descargar, respetando los términos de cada sitio.
- Para actualizar yt-dlp, basta reemplazar `yt-dlp.exe` junto a `Snag.exe`.