## NICKIBREEKI'S VIDEO COMPRESSION
# -----------------------------------------------------
## ORIGIN THIS PYTHON SCRIPT SEPERATED INTO MANY INDIVIDUAL FILE, BUT I DECIDED TO MAKE IT ALL IN ONE FILE
## BECAUSE I GOT NO IDEA WHY I DID THIS, EASY TO USE?
##
## I ALSO INCLUDED AUTO-INSTALLATION IN-CASE YOU GOT NO IDEA HOW TO USE OR INSTALL PACKAGE MANUALLY
## [Editted]: I found the updated version somewhere lol in my SSD, free to use, mostly just make it prettier format because old one a bit messy
##          incase you want to learn from my code

import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, ttk
import re
import json

## THIS IS AUTO PACKAGE INSTALLATION, REASON THIS EXISTED IT BECAUSE APPEAL ZERO-KNOWLEDGE USER
def _pip(*packages):
    subprocess.check_call(
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
    import pyperclip
except ImportError:
    _pip("pyperclip")
    import pyperclip


## LOOKING FOR "video_compressor_settings.json" if it does exist, If it exist it will pull the settings value from the file instead of use default settings
SETTINGS_PATH = os.path.join(
    os.path.expanduser("~"),
    ".video_compressor_settings.json"
)

DEFAULT_SETTINGS = {
    "audio_bitrate": 128,
    "cpu_preset": "fast",
    "min_video_bps": 100000,
    "copy_path": False,
    "open_folder": True,
    "preferred_encoder": "auto",
    "output_suffix": "_compressed",
    "two_pass": False,
}


def load_settings():
    try:
        with open(SETTINGS_PATH, "r") as settings_file:
            return {
                **DEFAULT_SETTINGS,
                **json.load(settings_file)
            }
    except Exception:
        return dict(DEFAULT_SETTINGS)


def save_settings(data):
    with open(SETTINGS_PATH, "w") as settings_file:
        json.dump(
            data,
            settings_file,
            indent = 2
        )

def detect_gpu_encoder():
    encoder_tests = [
        ("h264_nvenc", "NVIDIA NVENC"),
        ("h264_amf", "AMD AMF"),
        ("h264_qsv", "Intel QSV"),
    ]

    for encoder, label in encoder_tests:
        try:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-f", "lavfi",
                    "-i", "nullsrc",
                    "-t", "0.1",
                    "-c:v", encoder,
                    "-f", "null",
                    "-"
                ],
                capture_output = True,
                text = True
            )

            if result.returncode == 0:
                return encoder, label

        except FileNotFoundError:
            break

        except Exception:
            continue

    return "libx264", "CPU (libx264)"


def get_video_duration(path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path
        ],
        capture_output = True,
        text = True
    )

    return float(result.stdout.strip())


# Settings.py
# THIS IS SETTINGS WINDOW
class SettingsWindow(tk.Toplevel):

    PRESETS  = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow"]
    ENCODERS = ["auto", "libx264", "h264_nvenc", "h264_amf", "h264_qsv"]

    def __init__(self, parent, settings, on_save):
        super().__init__(parent)

        self.title("Settings")
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)

        self._s = dict(settings)
        self._on_save = on_save

        self._build_ui()

        self.update_idletasks()

        px = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2

        self.geometry(
            f"+{px}+{py}"
        )

    def _build_ui(self):
        ttk.Label(
            self,
            text = "Settings",
            font = ("Segoe UI", 13, "bold")
        ).pack(
            pady = (18, 10)
        )

        frame = ttk.Frame(self)
        frame.pack(
            fill = "x",
            padx = 28,
            pady = 4
        )

        frame.columnconfigure(1, weight = 1)

        LABEL_WIDTH = 22

        def row(row_index, label_text, widget_function):
            ttk.Label(
                frame,
                text = label_text,
                width = LABEL_WIDTH,
                anchor = "w"
            ).grid(
                row = row_index,
                column = 0,
                sticky = "w",
                pady = 7
            )
            widget_function(row_index)

        self._enc = tk.StringVar(value = self._s["preferred_encoder"])

        row(
            0,
            "Preferred Encoder",
            lambda r: ttk.Combobox(
                frame,
                textvariable = self._enc,
                values = self.ENCODERS,
                state = "readonly",
                width = 18
            ).grid(
                row = r,
                column = 1,
                sticky = "w"
            )
        )

        self._preset = tk.StringVar(value = self._s["cpu_preset"])

        row(
            1,
            "CPU Preset",
            lambda r: ttk.Combobox(
                frame,
                textvariable = self._preset,
                values = self.PRESETS,
                state = "readonly",
                width = 18
            ).grid(
                row = r,
                column = 1,
                sticky = "w"
            )
        )

        self._audio = tk.StringVar(value = str(self._s["audio_bitrate"]))

        number_validation = (
            self.register(lambda v: v.isdigit() or v == ""),
            "%P"
        )

        row(
            2,
            "Audio Bitrate (kbps)",
            lambda r: ttk.Entry(
                frame,
                textvariable = self._audio,
                width = 8,
                validate = "key",
                validatecommand = number_validation
            ).grid(
                row = r,
                column = 1,
                sticky = "w"
            )
        )

        self._suffix = tk.StringVar(value = self._s["output_suffix"])

        row(
            3,
            "Output Filename Suffix",
            lambda r: ttk.Entry(
                frame,
                textvariable = self._suffix,
                width = 18
            ).grid(
                row = r,
                column = 1,
                sticky = "w"
            )
        )

        self._twopass = tk.BooleanVar(value = self._s["two_pass"])

        ttk.Checkbutton(
            frame,
            text = "Two-Pass Encoding  (slower, more accurate size)",
            variable = self._twopass
        ).grid(
            row = 4,
            column = 0,
            columnspan = 2,
            sticky = "w",
            pady = 7
        )

        self._copy = tk.BooleanVar(value = self._s["copy_path"])

        ttk.Checkbutton(
            frame,
            text = "Copy output path to clipboard when done",
            variable = self._copy
        ).grid(
            row = 5,
            column = 0,
            columnspan = 2,
            sticky = "w",
            pady = 4
        )

        self._open = tk.BooleanVar(value = self._s["open_folder"])

        ttk.Checkbutton(
            frame,
            text = "Open output folder when done",
            variable = self._open
        ).grid(
            row = 6,
            column = 0,
            columnspan = 2,
            sticky = "w",
            pady = 4
        )

        ttk.Separator(
            self,
            orient = "horizontal"
        ).pack(
            fill = "x",
            padx = 28,
            pady = (14, 0)
        )

        button_row = ttk.Frame(self)
        button_row.pack(
            pady = 14
        )

        ttk.Button(
            button_row,
            text = "Cancel",
            width = 10,
            command = self.destroy
        ).pack(
            side = "left",
            padx = 6
        )

        ttk.Button(
            button_row,
            text = "Save",
            width = 10,
            style = "Accent.TButton",
            command = self._save
        ).pack(
            side = "left",
            padx = 6
        )

    def _save(self):
        try:
            bitrate = int(self._audio.get())
            if not (32 <= bitrate <= 320):
                raise ValueError
        except Exception:
            return

        self._s.update(
            {
                "preferred_encoder": self._enc.get(),
                "cpu_preset": self._preset.get(),
                "audio_bitrate": int(self._audio.get()),
                "output_suffix": self._suffix.get(),
                "two_pass": self._twopass.get(),
                "copy_path": self._copy.get(),
                "open_folder": self._open.get(),
            }
        )

        save_settings(self._s)

        self._on_save(self._s)
        self.destroy()


# main.py
# THIS IS MAIN PROGRAM
class VideoCompressorApp:
    def __init__(self, root):
        self.root = root
        self.settings = load_settings()

        self.root.title("Video Compressor")
        self.root.resizable(False, False)
        self.root.geometry("620x320")

        self._process = None
        self._thread = None
        self._cancel_flag = False
        self._duration = 0.0
        self._encoder = "libx264"

        sv_ttk.set_theme("dark")

        self._build_ui()
        self._detect_encoder_async()

    def _build_ui(self):
        top = ttk.Frame(self.root)
        top.pack(
            fill = "x",
            padx = 20,
            pady = (16, 2)
        )

        ttk.Label(
            top,
            text = "nickibreeki's Video Compressor",
            font = ("Segoe UI", 15, "bold")
        ).pack(
            side = "left"
        )

        ttk.Button(
            top,
            text = "Settings",
            width = 12,
            command = self._open_settings
        ).pack(
            side = "right"
        )

        self.gpu_var = tk.StringVar(
            value = "Detecting encoder…"
        )

        ttk.Label(
            self.root,
            textvariable = self.gpu_var,
            font = ("Segoe UI", 9),
            foreground = "#888"
        ).pack(
            anchor = "w",
            padx = 20
        )

        ttk.Separator(
            self.root,
            orient = "horizontal"
        ).pack(
            fill = "x",
            padx = 20,
            pady = (8, 4)
        )

        frame = ttk.Frame(self.root)
        frame.pack(
            fill = "x",
            padx = 20,
            pady = 8
        )

        frame.columnconfigure(1, weight = 1)

        BUTTON_WIDTH = 9
        LABEL_WIDTH  = 17

        ttk.Label(
            frame,
            text = "Target File",
            width = LABEL_WIDTH,
            anchor = "w"
        ).grid(
            row = 0,
            column = 0,
            sticky = "w",
            pady = 7
        )

        self.input_var = tk.StringVar()

        ttk.Entry(
            frame,
            textvariable = self.input_var
        ).grid(
            row = 0,
            column = 1,
            sticky = "ew",
            padx = (0, 6)
        )

        ttk.Button(
            frame,
            text = "Browse..",
            width = BUTTON_WIDTH,
            command = self._browse_input
        ).grid(
            row = 0,
            column = 2,
            sticky = "ew"
        )

        # Output directory
        ttk.Label(
            frame,
            text = "Output Directory",
            width = LABEL_WIDTH,
            anchor = "w"
        ).grid(
            row = 1,
            column = 0,
            sticky = "w",
            pady = 7
        )

        self.output_var = tk.StringVar(
            value = os.path.join(os.path.expanduser("~"), "Desktop")
        )

        ttk.Entry(
            frame,
            textvariable = self.output_var
        ).grid(
            row = 1,
            column = 1,
            sticky = "ew",
            padx = (0, 6)
        )

        ttk.Button(
            frame,
            text = "Browse..",
            width = BUTTON_WIDTH,
            command = self._browse_output
        ).grid(
            row = 1,
            column = 2,
            sticky = "ew"
        )

        ttk.Label(
            frame,
            text = "Target Size (MB)",
            width = LABEL_WIDTH,
            anchor = "w"
        ).grid(
            row = 2,
            column = 0,
            sticky = "w",
            pady = 7
        )

        size_row = ttk.Frame(frame)
        size_row.grid(
            row = 2,
            column = 1,
            columnspan = 2,
            sticky = "ew"
        )

        size_row.columnconfigure(1, weight = 1)

        number_validation = (
            self.root.register(self._validate_number),
            "%P"
        )

        self.size_var = tk.StringVar(value = "50")

        ttk.Entry(
            size_row,
            textvariable = self.size_var,
            width = 8,
            validate = "key",
            validatecommand = number_validation
        ).grid(
            row = 0,
            column = 0,
            sticky = "w",
            padx = (0, 10)
        )

        self.start_btn = ttk.Button(
            size_row,
            text = "Start Compression",
            style = "Accent.TButton",
            command = self._toggle_compression
        )

        self.start_btn.grid(
            row = 0,
            column = 1,
            sticky = "ew"
        )

        ttk.Separator(
            self.root,
            orient = "horizontal"
        ).pack(
            fill = "x",
            padx = 20,
            pady = (6, 0)
        )

        progress_frame = ttk.Frame(self.root)
        progress_frame.pack(
            fill = "x",
            padx = 20,
            pady = (10, 0)
        )

        progress_frame.columnconfigure(0, weight = 1)

        self.progress_var = tk.DoubleVar(value = 0)

        ttk.Progressbar(
            progress_frame,
            variable = self.progress_var,
            maximum = 100
        ).grid(
            row = 0,
            column = 0,
            sticky = "ew"
        )

        self.pct_var = tk.StringVar(value = "0%")

        ttk.Label(
            progress_frame,
            textvariable = self.pct_var,
            font = ("Segoe UI", 9),
            width = 6,
            anchor = "e"
        ).grid(
            row = 0,
            column = 1,
            padx = (8, 0)
        )

        self.status_var = tk.StringVar(value = "Ready.")

        ttk.Label(
            self.root,
            textvariable = self.status_var,
            font = ("Segoe UI", 9),
            foreground = "#aaa",
            wraplength = 580,
            justify = "left"
        ).pack(
            anchor = "w",
            padx = 20,
            pady = (8, 14)
        )

    def _detect_encoder_async(self):
        preferred = self.settings.get("preferred_encoder", "auto")

        def run_detection():

            if preferred != "auto":
                try:
                    result = subprocess.run(
                        [
                            "ffmpeg",
                            "-hide_banner",
                            "-f", "lavfi",
                            "-i", "nullsrc",
                            "-t", "0.1",
                            "-c:v", preferred,
                            "-f", "null",
                            "-"
                        ],
                        capture_output = True,
                        text = True
                    )

                    if result.returncode == 0:
                        encoder, label = preferred, preferred
                    else:
                        encoder, label = detect_gpu_encoder()

                except Exception:
                    encoder, label = detect_gpu_encoder()

            else:
                encoder, label = detect_gpu_encoder()

            self._encoder = encoder

            self.root.after(
                0,
                lambda: self.gpu_var.set(f"Encoder: {label}")
            )

        threading.Thread(
            target = run_detection,
            daemon = True
        ).start()

    def _open_settings(self):
        def apply_changes(new_settings):
            self.settings = new_settings
            self._detect_encoder_async()

        SettingsWindow(
            self.root,
            self.settings,
            apply_changes
        )

    @staticmethod
    def _validate_number(value):
        return (
            value == "" or
            re.fullmatch(r"\d*\.?\d*", value) is not None
        )

    def _browse_input(self):
        path = filedialog.askopenfilename(
            title = "Select Video",
            filetypes = [
                (
                    "Video files",
                    "*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm *.ts"
                ),
                ("All files", "*.*")
            ]
        )

        if path:
            self.input_var.set(path)
            self.output_var.set(os.path.dirname(path))

    def _browse_output(self):
        path = filedialog.askdirectory(
            title = "Select Output Directory"
        )

        if path:
            self.output_var.set(path)

    def _toggle_compression(self):
        if self._thread and self._thread.is_alive():

            self._cancel_flag = True

            if self._process:
                self._process.terminate()

            self.start_btn.config(text = "Start Compression")
            self.status_var.set("Cancelled.")

        else:
            self._start_compression()

    def _start_compression(self):
        video_path = self.input_var.get().strip().strip('"')
        output_dir = self.output_var.get().strip()
        size_str   = self.size_var.get().strip()

        if not os.path.isfile(video_path):
            self.status_var.set("[ERROR]: Input file not found.")
            return

        if not os.path.isdir(output_dir):
            self.status_var.set("[ERROR]: Output directory not found.")
            return

        if not size_str:
            self.status_var.set("[ERROR]: Enter a target size.")
            return

        suffix = self.settings.get("output_suffix", "_compressed")

        base_name, ext = os.path.splitext(os.path.basename(video_path))

        output_path = os.path.join(
            output_dir,
            f"{base_name}{suffix}{ext}"
        )

        self._cancel_flag = False

        self.progress_var.set(0)
        self.pct_var.set("0%")

        self.start_btn.config(text = "Cancel Compression")
        self.status_var.set("[STATUS]: Compressing…")

        self._thread = threading.Thread(
            target = self._compress_worker,
            args = (video_path, output_path, float(size_str)),
            daemon = True
        )

        self._thread.start()

    def _compress_worker(self, video_path, output_path, target_mb):

        try:
            duration = get_video_duration(video_path)

            audio_bitrate_kbps = self.settings.get("audio_bitrate", 128)
            audio_bps          = audio_bitrate_kbps * 1000

            min_video_bps = self.settings.get("min_video_bps", 100_000)

            preset   = self.settings.get("cpu_preset", "fast")
            two_pass = self.settings.get("two_pass", False)

            # Compute target bitrate
            video_bps = max(
                int(
                    target_mb * 8 * 1024 * 1024 / duration - audio_bps
                ),
                min_video_bps
            )

            import multiprocessing

            threads = max(
                1,
                multiprocessing.cpu_count() - 1
            )

            encoder = self._encoder

            def build_command(pass_number = None):

                cmd = [
                    "ffmpeg",
                    "-y",
                    "-i", video_path,
                    "-c:v", encoder,
                    "-b:v", str(video_bps),
                    "-progress", "pipe:1",
                    "-nostats"
                ]

                if encoder == "libx264":
                    cmd.extend(
                        [
                            "-threads", str(threads),
                            "-preset",  preset
                        ]
                    )

                if pass_number == 1:

                    cmd.extend(
                        [
                            "-pass", "1",
                            "-an",
                            "-f", "null",
                            "NUL" if sys.platform == "win32" else "/dev/null"
                        ]
                    )

                elif pass_number == 2:

                    cmd.extend(
                        [
                            "-pass", "2",
                            "-c:a", "aac",
                            "-b:a", f"{audio_bitrate_kbps}k",
                            output_path
                        ]
                    )

                else:

                    cmd.extend(
                        [
                            "-c:a", "aac",
                            "-b:a", f"{audio_bitrate_kbps}k",
                            output_path
                        ]
                    )

                return cmd

            def run_ffmpeg(cmd, start_progress = 0.0, end_progress = 1.0):

                self._process = subprocess.Popen(
                    cmd,
                    stdout = subprocess.PIPE,
                    stderr = subprocess.STDOUT,
                    text = True,
                    bufsize = 1
                )

                for line in self._process.stdout:
                    if self._cancel_flag:
                        break

                    line = line.strip()

                    if line.startswith("out_time_ms="):

                        try:
                            elapsed = int(line.split("=")[1]) / 1_000_000
                            fraction = min(elapsed / duration, 1.0)

                            percent = (
                                start_progress +
                                fraction * (end_progress - start_progress)
                            ) * 100

                            self.root.after(
                                0,
                                lambda p = percent: (
                                    self.progress_var.set(p),
                                    self.pct_var.set(f"{p:.1f}%")
                                )
                            )

                        except Exception:
                            pass

                self._process.wait()

            if two_pass:

                run_ffmpeg(
                    build_command(pass_number = 1),
                    0.0,
                    0.5
                )

                if not self._cancel_flag:

                    run_ffmpeg(
                        build_command(pass_number = 2),
                        0.5,
                        1.0
                    )

            else:

                run_ffmpeg(
                    build_command(),
                    0.0,
                    1.0
                )

            if self._cancel_flag:

                try:
                    os.remove(output_path)
                except FileNotFoundError:
                    pass

                return

            if os.path.isfile(output_path):

                message = f"[STATUS]: FINISHED!   >   {output_path}"

                if self.settings.get("copy_path", True):

                    pyperclip.copy(output_path)
                    message += "  📋 Path copied."

                if self.settings.get("open_folder", False):

                    folder = os.path.dirname(output_path)

                    if sys.platform == "win32":
                        os.startfile(folder)
                    elif sys.platform == "darwin":
                        subprocess.Popen(["open", folder])
                    else:
                        subprocess.Popen(["xdg-open", folder])

                self.root.after(
                    0,
                    lambda: (
                        self.progress_var.set(100),
                        self.pct_var.set("100%"),
                        self.status_var.set(message)
                    )
                )

            else:

                self.root.after(
                    0,
                    lambda: self.status_var.set(
                        "[STATUS]: Compression failed. Is ffmpeg installed?"
                    )
                )

        except Exception as error:

            self.root.after(
                0,
                lambda: self.status_var.set(f"[ERROR]: {error}")
            )

        finally:

            self.root.after(
                0,
                lambda: self.start_btn.config(text = "Start Compression")
            )

            self._process = None

def main():
    root = tk.Tk()
    VideoCompressorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()