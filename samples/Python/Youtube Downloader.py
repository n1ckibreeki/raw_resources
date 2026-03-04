## NICKIBREEKI'S YOUTUBE DOWNLOADER
import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog
import re

## THIS IS AUTO PACKAGE INSTALLATION, REASON THIS EXISTED IS BECAUSE APPEAL ZERO-KNOWLEDGE USER
def _pip(*packages):
    subprocess.call(
        [
            sys.executable, "-m", "pip", "install", *packages
        ],
        stdout = subprocess.DEVNULL,
        stderr = subprocess.DEVNULL
    )

try:
    import sv_ttk
except ImportError:
    _pip("sv-ttk")
    import sv_ttk

try:
    import yt_dlp
except ImportError:
    _pip("yt-dlp")
    import yt_dlp

class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.resizable(False, False)
        self.root.geometry("640x275")
        self._cancel_flag = False
        self._downloading = False
        sv_ttk.set_theme("dark")
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self.root)
        top.pack(fill = "x", padx = 20, pady = (16, 2))

        ttk.Label(
            top,
            text = "nickibreeki's YouTube Downloader",
            font = ("Segoe UI", 15, "bold")
        ).pack(side = "left")

        ttk.Separator(self.root, orient = "horizontal").pack(
            fill = "x", padx = 20, pady = (8, 6)
        )

        frame = ttk.Frame(self.root)
        frame.pack(fill = "x", padx = 20)

        LABEL_WIDTH = 17

        ## URL
        ttk.Label(
            frame,
            text = "URL",
            width = LABEL_WIDTH,
            anchor = "w"
        ).grid(row = 0, column = 0, sticky = "w", pady = 4)

        self.url_var = tk.StringVar()
        ttk.Entry(
            frame,
            textvariable = self.url_var
        ).grid(row = 0, column = 1, columnspan = 2, sticky = "ew", padx = (0, 0))

        frame.columnconfigure(1, weight = 1)

        ## OUTPUT DIRECTORY
        ttk.Label(
            frame,
            text = "Output Directory",
            width = LABEL_WIDTH,
            anchor = "w"
        ).grid(row = 1, column = 0, sticky = "w", pady = 4)

        self.output_var = tk.StringVar(
            value = os.path.join(os.path.expanduser("~"), "Desktop")
        )
        ttk.Entry(
            frame,
            textvariable = self.output_var
        ).grid(row = 1, column = 1, sticky = "ew", padx = (0, 6))

        ttk.Button(
            frame,
            text = "Browse..",
            width = 9,
            command = self._browse_output
        ).grid(row = 1, column = 2, sticky = "ew")

        ## FORMAT TYPE + CODEC/BITRATE (inline, no label for codec)
        ttk.Label(
            frame,
            text = "Format Type",
            width = LABEL_WIDTH,
            anchor = "w"
        ).grid(row = 2, column = 0, sticky = "w", pady = 4)

        self.format_var = tk.StringVar(value = "[VIDEO]: mp4")
        self.format_box = ttk.Combobox(
            frame,
            textvariable = self.format_var,
            state = "readonly",
            width = 14,
            values = [
                "[VIDEO]: mp4",
                "[VIDEO]: webm",
                "[VIDEO]: mkv",
                "[AUDIO]: mp3",
                "[AUDIO]: ogg",
                "[AUDIO]: wav"
            ]
        )
        self.format_box.grid(row = 2, column = 1, sticky = "w", padx = (0, 6))
        self.format_box.bind("<<ComboboxSelected>>", self._format_changed)

        self.codec_var = tk.StringVar(value = "h264 and aac")
        self.codec_box = ttk.Combobox(
            frame,
            textvariable = self.codec_var,
            state = "readonly",
            width = 12,
            values = ["h264 and aac"]
        )
        self.codec_box.grid(row = 2, column = 2, sticky = "w")

        self.bitrate_var = tk.StringVar(value = "128kb/s")
        self.bitrate_box = ttk.Combobox(
            frame,
            textvariable = self.bitrate_var,
            state = "readonly",
            width = 12,
            values = ["320kb/s", "256kb/s", "128kb/s", "96kb/s", "64kb/s", "8kb/s"]
        )
        self.bitrate_box.grid(row = 2, column = 2, sticky = "w")
        self.bitrate_box.grid_remove()

        self.start_btn = ttk.Button(
            frame,
            text = "Download",
            style = "Accent.TButton",
            command = self._toggle_download
        )
        self.start_btn.grid(row = 3, column = 1, columnspan = 2, sticky = "ew", pady = (10, 2))

        ttk.Separator(self.root).pack(
            fill = "x", padx = 20, pady = (10, 6)
        )

        progress_frame = ttk.Frame(self.root)
        progress_frame.pack(fill = "x", padx = 20)
        progress_frame.columnconfigure(0, weight = 1)

        self.progress_var = tk.DoubleVar(value = 0)
        ttk.Progressbar(
            progress_frame,
            variable = self.progress_var,
            maximum = 100
        ).grid(row = 0, column = 0, sticky = "ew")

        self.pct_var = tk.StringVar(value = "0%")
        ttk.Label(
            progress_frame,
            textvariable = self.pct_var,
            width = 6,
            anchor = "e"
        ).grid(row = 0, column = 1, padx = (8, 0))

        self.status_var = tk.StringVar(value = "Ready.")
        ttk.Label(
            self.root,
            textvariable = self.status_var,
            font = ("Segoe UI", 9),
            foreground = "#aaa",
            wraplength = 580,
            justify = "left"
        ).pack(anchor = "w", padx = 20, pady = (8, 14))

    def _format_changed(self, event = None):
        fmt = self.format_var.get()
        if fmt.startswith("[VIDEO]"):
            self.codec_box.grid()
            self.bitrate_box.grid_remove()
        else:
            self.codec_box.grid_remove()
            self.bitrate_box.grid()

    def _browse_output(self):
        path = filedialog.askdirectory(title = "Select Output Directory")
        if path:
            self.output_var.set(path)

    def _toggle_download(self):
        if self._downloading:
            self._cancel_flag = True
            self.status_var.set("Cancelling…")
            return
        self._start_download()

    def _start_download(self):
        url = self.url_var.get().strip()
        out_dir = self.output_var.get().strip()
        fmt_sel = self.format_var.get().strip()

        if not url:
            self.status_var.set("[ERROR]: URL is empty.")
            return

        ext = fmt_sel.split(":")[1].strip()
        bitrate = None

        if fmt_sel.startswith("[AUDIO]"):
            bitrate = self.bitrate_var.get().replace("kb/s", "")

        self._cancel_flag = False
        self._downloading = True
        self.start_btn.config(text = "Cancel Download")
        self.status_var.set("[STATUS]: Downloading…")
        self.progress_var.set(0)
        self.pct_var.set("0%")

        thread = threading.Thread(
            target = self._download_worker,
            args = (url, out_dir, ext, fmt_sel.startswith("[AUDIO]"), bitrate),
            daemon = True
        )
        thread.start()

    def _download_worker(self, url, out_dir, ext, is_audio, bitrate):
        opts = {
            "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
            "noplaylist": True,
            "progress_hooks": [self._progress_hook]
        }

        if is_audio:
            opts["format"] = "bestaudio"
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": ext,
                    "preferredquality": bitrate
                }
            ]
        else:
            opts["format"] = "bestvideo+bestaudio/best"
            opts["postprocessors"] = [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": ext
                }
            ]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            if not self._cancel_flag:
                self.root.after(0, self.status_var.set, "[STATUS]: FINISHED!")
                self.root.after(0, self.progress_var.set, 100)
                self.root.after(0, self.pct_var.set, "100%")
        except Exception as e:
            if self._cancel_flag:
                self.root.after(0, self.status_var.set, "[STATUS]: Cancelled.")
            else:
                self.root.after(0, self.status_var.set, f"[ERROR]: {e}")
        finally:
            self._downloading = False
            self.root.after(0, self.start_btn.config, {"text": "Download"})

    def _progress_hook(self, d):
        if self._cancel_flag:
            raise Exception("cancelled")

        if d["status"] == "downloading":
            percent = d.get("_percent_str", "0%").replace("%", "").strip()
            try:
                pct = float(percent)
                self.root.after(0, self.progress_var.set, pct)
                self.root.after(0, self.pct_var.set, f"{pct:.1f}%")
            except:
                pass
        elif d["status"] == "finished":
            self.root.after(0, self.status_var.set, "[STATUS]: Processing…")

def main():
    root = tk.Tk()
    YouTubeDownloaderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()