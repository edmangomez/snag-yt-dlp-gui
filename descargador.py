import argparse
import os
import queue
import re
import shutil
import subprocess
import sys
import threading

URL_TESTO = "https://www.youtube.com/watch?v=BaW_jenozKc"

RE_PCT = re.compile(r"\[download\]\s+(\d+\.?\d*)%")
RE_SPEED = re.compile(r"\bat\s+([\d.,]+)\s*([KMGTP]i?B/s)", re.IGNORECASE)
RE_DEST = re.compile(r"Destination:\s+(.+)", re.IGNORECASE)
RE_MERGE = re.compile(r'Merging formats into "(.+)"', re.IGNORECASE)


def esta_empaquetado():
    return getattr(sys, "frozen", False)


def carpeta_app():
    if esta_empaquetado():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def localizar_ytdlp():
    if esta_empaquetado():
        ruta = os.path.join(carpeta_app(), "yt-dlp.exe")
        return ruta if os.path.isfile(ruta) else None
    return shutil.which("yt-dlp")


def localizar_ffmpeg():
    if esta_empaquetado():
        ruta = os.path.join(carpeta_app(), "ffmpeg.exe")
        return ruta if os.path.isfile(ruta) else None
    return shutil.which("ffmpeg")


def localizar_ffprobe():
    if esta_empaquetado():
        ruta = os.path.join(carpeta_app(), "ffprobe.exe")
        return ruta if os.path.isfile(ruta) else None
    return shutil.which("ffprobe")


class Descargador:
    def __init__(self, url, modo, destino, callbacks=None):
        self.url = url.strip()
        self.modo = modo
        self.destino = destino
        self.callbacks = callbacks or {}
        self.regex_progreso = re.compile(
            r"\[download\]\s+(\d+\.?\d*)%\s+of\s+~?([\d.,]+)([KMGTP]i?B)"
            r"(?:\s+at\s+([\d.,]+)([KMGTP]i?B/s))?",
            re.IGNORECASE,
        )

    def _notificar(self, nombre, *args):
        cb = self.callbacks.get(nombre)
        if cb:
            cb(*args)

    def descargar(self):
        ytdlp = localizar_ytdlp()
        if not ytdlp:
            self._notificar("error", "No se encontró yt-dlp.exe junto al programa.")
            return False, None

        ffmpeg = localizar_ffmpeg()
        if not ffmpeg:
            self._notificar(
                "error",
                "No se encontró ffmpeg.exe. Colócalo junto al programa y vuelve a intentarlo.",
            )
            return False, None

        ffprobe = localizar_ffprobe()
        if not ffprobe:
            self._notificar(
                "error",
                "No se encontró ffprobe.exe. Colócalo junto al programa y vuelve a intentarlo.",
            )
            return False, None

        os.makedirs(self.destino, exist_ok=True)

        args = [
            ytdlp,
            "--newline",
            "--no-playlist",
            "--no-mtime",
            "-f" if self.modo == "video" else "--extract-audio",
        ]
        if self.modo == "video":
            args += ["bestvideo+bestaudio/best", "--merge-output-format", "mp4"]
        else:
            args += [
                "--audio-format",
                "mp3",
                "--audio-quality",
                "0",
                "--embed-thumbnail",
                "--embed-metadata",
                "--replace-in-metadata",
                "title",
                r"(?i)\s*\([Oo]fficial\s+[Mm]usic\s+[Vv]ideo[^)]*\)",
                "",
                "--replace-in-metadata",
                "title",
                r"(?i)\s*\([Oo]fficial\s+[Vv]ideo[^)]*\)",
                "",
                "--replace-in-metadata",
                "title",
                r"(?i)\s*\([Oo]fficial\s+[Aa]udio[^)]*\)",
                "",
                "--replace-in-metadata",
                "title",
                r"(?i)\s*\[[Ll]yrics[^\]]*\]",
                "",
                "--replace-in-metadata",
                "title",
                r"(?i)\s*\([Ll]yrics\s+[Vv]ideo[^)]*\)",
                "",
                "--replace-in-metadata",
                "title",
                r"(?i)\s*\[HD[^\]]*\]",
                "",
                "--replace-in-metadata",
                "title",
                r"(?i)\s*\(HD[^)]*\)",
                "",
                "--replace-in-metadata",
                "title",
                r"(?i)\s*\|\s*[Pp]romo",
                "",
                "--replace-in-metadata",
                "title",
                r"(?i)\s*\([Rr]emastered[^)]*\)",
                "",
                "--replace-in-metadata",
                "artist",
                r"\s*-\s*Topic\s*$",
                "",
                "--replace-in-metadata",
                "artist",
                r"\s+[Oo]fficial\s*$",
                "",
            ]

        args += [
            "--ffmpeg-location",
            os.path.dirname(ffmpeg),
            "-o",
            os.path.join(self.destino, "%(title)s.%(ext)s"),
            self.url,
        ]

        self._notificar("inicio", args)
        try:
            proceso = subprocess.Popen(
                args,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except OSError as e:
            self._notificar("error", f"No se pudo ejecutar yt-dlp: {e}")
            return False, None

        lineas = queue.Queue()

        def lector(stream):
            try:
                for linea in stream:
                    lineas.put(linea)
            except (ValueError, OSError):
                pass

        hilo_stdout = threading.Thread(
            target=lector, args=(proceso.stdout,), daemon=True
        )
        hilo_stderr = threading.Thread(
            target=lector, args=(proceso.stderr,), daemon=True
        )
        hilo_stdout.start()
        hilo_stderr.start()

        ultimo_destino = None
        salida_error = []
        while True:
            try:
                linea = lineas.get(timeout=0.2)
            except queue.Empty:
                if proceso.poll() is not None and lineas.empty():
                    break
                continue
            linea = linea.rstrip("\n\r")
            if not linea:
                continue
            m = self.regex_progreso.search(linea)
            if m:
                pct = float(m.group(1))
                velocidad = ""
                if m.group(4) and m.group(5):
                    velocidad = f"{m.group(4)}{m.group(5)}"
                self._notificar("progreso", pct, velocidad)
                continue
            m = RE_DEST.search(linea)
            if m:
                ultimo_destino = m.group(1).strip()
                continue
            m = RE_MERGE.search(linea)
            if m:
                ultimo_destino = m.group(1).strip().strip('"')
                continue
            if linea.startswith("ERROR"):
                salida_error.append(linea)

        returncode = proceso.wait()
        if returncode != 0 or salida_error:
            mensaje = " ".join(salida_error) or f"yt-dlp terminó con código {returncode}"
            mensaje += "\n\nVuelve a intentar la descarga."
            self._notificar("error", mensaje)
            return False, None

        ruta = ultimo_destino
        if not ruta:
            ruta = _archivo_mas_reciente(self.destino)

        # Confirmación de metadatos para MP3 (solo si hay callback "metadatos" registrado, es decir, en GUI)
        if self.modo == "mp3" and ruta and "metadatos" in self.callbacks:
            metadatos = _leer_metadatos_mp3(ruta, ffprobe)
            # Limpieza defensiva: quitar prefijo "NA - " dejado por yt-dlp cuando no detecta artista
            metadatos["title"] = _limpiar_prefijo_na(metadatos.get("title", ""))
            metadatos["artist"] = _limpiar_prefijo_na(metadatos.get("artist", ""))
            # Respaldo: si ffprobe no devolvió título, usar el nombre del archivo
            if not metadatos.get("title"):
                metadatos["title"] = _limpiar_prefijo_na(
                    os.path.splitext(os.path.basename(ruta))[0]
                )

            evento = getattr(self, "_metadatos_evento", None)
            pendiente = getattr(self, "_metadatos_pendiente", None)
            if evento is not None and pendiente is not None:
                self._notificar("metadatos", ruta, metadatos)
                evento.wait()
                resultado = pendiente.get("resultado")
            else:
                resultado = {
                    "artist": metadatos.get("artist", ""),
                    "title": metadatos.get("title", ""),
                }

            if resultado is None:
                # Usuario canceló: borrar archivo
                try:
                    os.remove(ruta)
                except OSError:
                    pass
                return False, None
            
            # Usuario guardó: reescribir metadatos si cambiaron
            if (resultado["artist"] != metadatos["artist"] or 
                resultado["title"] != metadatos["title"]):
                temp_final = ruta + "_meta.mp3"
                try:
                    _escribir_metadatos_mp3(ruta, temp_final, resultado, ffmpeg)
                    os.replace(temp_final, ruta)
                except subprocess.CalledProcessError:
                    if os.path.isfile(temp_final):
                        try: os.remove(temp_final)
                        except OSError: pass

            # Renombrar archivo al título confirmado (formato "Artista - Título")
            titulo_limpio = _sanitizar_nombre_archivo(_limpiar_prefijo_na(resultado["title"]))
            if titulo_limpio:
                nueva_ruta = os.path.join(os.path.dirname(ruta), f"{titulo_limpio}.mp3")
                if nueva_ruta != ruta:
                    try:
                        if os.path.isfile(nueva_ruta):
                            os.remove(nueva_ruta)
                        os.replace(ruta, nueva_ruta)
                        ruta = nueva_ruta
                    except OSError:
                        pass

        self._notificar("fin", ruta)
        return True, ruta


def _limpiar_prefijo_na(nombre):
    """Quita el prefijo 'NA - ' que deja yt-dlp cuando no detecta artista."""
    if not nombre:
        return nombre or ""
    return re.sub(r"(?i)^\s*NA\s*-\s*", "", nombre)


def _sanitizar_nombre_archivo(nombre):
    """Elimina caracteres inválidos para nombres de archivo en Windows."""
    if not nombre:
        return ""
    # Caracteres no permitidos en Windows: \ / : * ? " < > |
    invalidos = r'[\\/:*?"<>|]'
    nombre = re.sub(invalidos, "", nombre)
    # Eliminar espacios al inicio/final y puntos finales
    nombre = nombre.strip().rstrip(".")
    # Limitar longitud (255 es límite NTFS, pero dejamos margen)
    if len(nombre) > 240:
        nombre = nombre[:240].rstrip()
    return nombre


def _archivo_mas_reciente(destino):
    try:
        archivos = [
            os.path.join(destino, f)
            for f in os.listdir(destino)
            if os.path.isfile(os.path.join(destino, f))
        ]
    except OSError:
        return None
    if not archivos:
        return None
    return max(archivos, key=os.path.getmtime)


def _leer_metadatos_mp3(ruta, ffprobe_path):
    """Lee artist y title del MP3 usando ffprobe."""
    try:
        if not ffprobe_path or not os.path.isfile(ffprobe_path):
            return {"artist": "", "title": ""}
        
        resultado = subprocess.run([
            ffprobe_path, "-v", "error", "-show_entries",
            "format_tags=artist,title", "-of", "default=noprint_wrappers=1:nokey=0",
            ruta
        ], capture_output=True, text=True, encoding="utf-8", errors="replace",
           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        
        metadatos = {"artist": "", "title": ""}
        for linea in resultado.stdout.strip().split("\n"):
            if "=" in linea:
                clave, valor = linea.split("=", 1)
                # ffprobe puede devolver "TAG:artist=..." o "artist=..."
                clave = clave.replace("TAG:", "")
                if clave in metadatos:
                    metadatos[clave] = valor
        return metadatos
    except Exception:
        return {"artist": "", "title": ""}


def _escribir_metadatos_mp3(ruta_entrada, ruta_salida, metadatos, ffmpeg_path):
    """Reescribe metadatos del MP3 usando ffmpeg (-c copy, sin recodificar)."""
    args = [ffmpeg_path, "-y", "-i", ruta_entrada]
    if metadatos.get("artist"):
        args += ["-metadata", f"artist={metadatos['artist']}"]
    if metadatos.get("title"):
        args += ["-metadata", f"title={metadatos['title']}"]
    args += ["-c", "copy", "-id3v2_version", "3", ruta_salida]
    
    subprocess.run(args, check=True, capture_output=True,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


class MetadatosDialog:
    def __init__(self, parent, metadatos_iniciales):
        import tkinter as tk
        from tkinter import ttk
        
        self.resultado = None
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Confirmar metadatos")
        self.ventana.geometry("520x180")
        self.ventana.resizable(False, False)
        self.ventana.transient(parent)
        self.ventana.grab_set()
        self.ventana.protocol("WM_DELETE_WINDOW", self._cancelar)
        
        # Centrar en parent
        self.ventana.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 260
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 90
        self.ventana.geometry(f"+{x}+{y}")
        
        # Artista
        tk.Label(self.ventana, text="Artista:").grid(row=0, column=0, padx=10, pady=12, sticky="w")
        self.entry_artist = ttk.Entry(self.ventana, width=55)
        self.entry_artist.grid(row=0, column=1, padx=10, pady=12, sticky="ew")
        self.entry_artist.insert(0, metadatos_iniciales.get("artist", ""))
        
        # Título
        tk.Label(self.ventana, text="Título:").grid(row=1, column=0, padx=10, pady=12, sticky="w")
        self.entry_title = ttk.Entry(self.ventana, width=55)
        self.entry_title.grid(row=1, column=1, padx=10, pady=12, sticky="ew")
        self.entry_title.insert(0, metadatos_iniciales.get("title", ""))
        
        self.ventana.columnconfigure(1, weight=1)
        
        # Botones
        frame_btns = tk.Frame(self.ventana)
        frame_btns.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(frame_btns, text="Guardar", command=self._guardar, width=15).pack(side="left", padx=8)
        ttk.Button(frame_btns, text="Cancelar", command=self._cancelar, width=15).pack(side="left", padx=8)
        
        self.entry_artist.focus_set()
        self.ventana.wait_window()
    
    def _guardar(self):
        self.resultado = {
            "artist": self.entry_artist.get().strip(),
            "title": self.entry_title.get().strip()
        }
        self.ventana.destroy()
    
    def _cancelar(self):
        self.resultado = None
        self.ventana.destroy()
    
    def obtener_resultado(self):
        return self.resultado


def _descarga_control(url, modo, destino, log_archivo=None):
    def on_progreso(pct, velocidad):
        linea = f"{pct:.1f}%"
        if velocidad:
            linea += f" - {velocidad}"
        print(linea, flush=True)

    def on_error(msg):
        print(f"ERROR: {msg}", flush=True)

    d = Descargador(
        url,
        modo,
        destino,
        callbacks={
            "progreso": on_progreso,
            "error": on_error,
            "fin": lambda ruta: print(f"OK: {ruta}", flush=True),
        },
    )
    ok, ruta = d.descargar()
    if not ok:
        print("FALLO", flush=True)
        return 1
    print("EXITO", flush=True)
    return 0


def modo_test_log_abierto():
    if sys.stdout is None:
        try:
            ruta_log = os.path.join(carpeta_app(), "descargador_test.log")
            sys.stdout = open(ruta_log, "w", encoding="utf-8")
        except OSError:
            pass


def main_prueba():
    modo_test_log_abierto()
    parser = argparse.ArgumentParser(description="Descargador yt-dlp (modo prueba)")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--url", default=URL_TESTO)
    parser.add_argument("--modo", choices=["video", "mp3"], default="video")
    parser.add_argument("--dest", required=True)
    args = parser.parse_args()
    if not args.test:
        return 2
    return _descarga_control(args.url, args.modo, args.dest)


def interfaz():
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    raiz = tk.Tk()
    raiz.title("Snag")
    raiz.geometry("640x300")
    raiz.resizable(False, False)
    raiz.configure(padx=14, pady=12)

    icono_ruta = os.path.join(carpeta_app(), "snag.ico")
    if esta_empaquetado():
        ruta_meipass = os.path.join(getattr(sys, "_MEIPASS", ""), "snag.ico")
        if os.path.isfile(ruta_meipass):
            icono_ruta = ruta_meipass
    if os.path.isfile(icono_ruta):
        try:
            raiz.iconbitmap(icono_ruta)
        except tk.TclError:
            pass

    carpeta_descargas = os.path.join(os.path.expanduser("~"), "Downloads")
    cola_ui = queue.Queue()

    def nuevo_descargador(url, modo, destino):
        evento_metadatos = threading.Event()
        pendiente_metadatos = {}
        d = Descargador(
            url,
            modo,
            destino,
            callbacks={
                "inicio": lambda _args: None,
                "progreso": lambda pct, vel: cola_ui.put(("progreso", pct, vel)),
                "error": lambda msg: cola_ui.put(("error", msg)),
                "fin": lambda ruta: cola_ui.put(("fin", ruta)),
                "metadatos": lambda ruta, metadatos: cola_ui.put(
                    ("metadatos", ruta, metadatos, evento_metadatos, pendiente_metadatos)
                ),
            },
        )
        d._metadatos_evento = evento_metadatos
        d._metadatos_pendiente = pendiente_metadatos
        return d

    def procesar_cola():
        try:
            while True:
                evento = cola_ui.get_nowait()
                nombre = evento[0]
                if nombre == "progreso":
                    actualizar_progreso(evento[1], evento[2])
                elif nombre == "error":
                    mostrar_error(evento[1])
                elif nombre == "fin":
                    mostrar_fin(evento[1])
                elif nombre == "metadatos":
                    mostrar_dialogo_metadatos(
                        evento[1], evento[2], evento[3], evento[4]
                    )
        except queue.Empty:
            pass
        raiz.after(100, procesar_cola)

    def actualizar_progreso(pct, velocidad):
        barra["value"] = pct
        texto = f"{pct:.1f}%"
        if velocidad:
            texto += f"  -  {velocidad}"
        estado.set(texto)
        estado_etiqueta.configure(fg="#0a0a0a")

    def mostrar_error(msg):
        barra["value"] = 0
        estado.set("Error")
        boton_descargar["state"] = "normal"
        messagebox.showerror("Error de descarga", msg[:2000])

    def mostrar_fin(ruta):
        estado.set("Descarga completada")
        boton_descargar["state"] = "normal"
        if ruta:
            messagebox.showinfo(
                "Descarga completada",
                f"Archivo guardado en:\n{ruta}",
            )

    def mostrar_dialogo_metadatos(ruta, metadatos, evento, pendiente):
        dialogo = MetadatosDialog(raiz, metadatos)
        resultado = dialogo.obtener_resultado()
        pendiente["resultado"] = resultado
        evento.set()

        if resultado is None:
            # Usuario canceló: borrar archivo y re-habilitar botón
            try:
                if os.path.isfile(ruta):
                    os.remove(ruta)
            except OSError:
                pass
            barra["value"] = 0
            estado.set("Descarga cancelada")
            boton_descargar["state"] = "normal"

    tk.Label(raiz, text="URL del video:").pack(anchor="w")

    entrada_url = ttk.Entry(raiz, width=78)
    entrada_url.pack(fill="x", pady=(2, 10))

    fila_modo = tk.Frame(raiz)
    fila_modo.pack(anchor="w", pady=(0, 10))
    modo_seleccion = tk.StringVar(value="video")
    tk.Radiobutton(
        fila_modo,
        text="Video (máxima calidad)",
        variable=modo_seleccion,
        value="video",
    ).pack(side="left")
    tk.Radiobutton(
        fila_modo,
        text="MP3 (solo audio)",
        variable=modo_seleccion,
        value="mp3",
    ).pack(side="left", padx=(16, 0))

    fila_carpeta = tk.Frame(raiz)
    fila_carpeta.pack(fill="x", pady=(0, 10))
    entrada_carpeta = ttk.Entry(fila_carpeta, width=62)
    entrada_carpeta.insert(0, carpeta_descargas)
    entrada_carpeta.pack(side="left", fill="x", expand=True)
    ttk.Button(
        fila_carpeta,
        text="Examinar...",
        command=lambda: seleccionar_carpeta(),
    ).pack(side="left", padx=(6, 0))

    def seleccionar_carpeta():
        elegida = filedialog.askdirectory(initialdir=entrada_carpeta.get() or None)
        if elegida:
            entrada_carpeta.delete(0, "end")
            entrada_carpeta.insert(0, elegida)

    def descargar():
        url = entrada_url.get().strip()
        if not url:
            messagebox.showwarning("Falta la URL", "Introduce la URL del video.")
            return
        destino = entrada_carpeta.get().strip()
        if not destino:
            destino = carpeta_descargas
        boton_descargar["state"] = "disabled"
        estado.set("Iniciando descarga...")
        barra["value"] = 0
        d = nuevo_descargador(url, modo_seleccion.get(), destino)
        hilo = threading.Thread(target=d.descargar, daemon=True)
        hilo.start()

    fila_boton = tk.Frame(raiz)
    fila_boton.pack(anchor="e", pady=(0, 10))
    boton_descargar = ttk.Button(
        fila_boton,
        text="Descargar",
        command=descargar,
        width=16,
    )
    boton_descargar.pack(side="right")

    barra = ttk.Progressbar(raiz, maximum=100)
    barra.pack(fill="x", pady=(0, 6))

    estado = tk.StringVar(value="Listo")
    estado_etiqueta = tk.Label(raiz, textvariable=estado, anchor="w", fg="#0a0a0a")
    estado_etiqueta.pack(fill="x")

    raiz.after(100, procesar_cola)
    raiz.mainloop()


if __name__ == "__main__":
    if "--test" in sys.argv:
        sys.exit(main_prueba())
    interfaz()