# ui_controller.py
# -------------------------------------------------------
# Modern dark-themed Tkinter UI with live meters.
# -------------------------------------------------------

import tkinter as tk
from tkinter import filedialog


BG = "#1a1a2e"
FG = "#eaeaea"
ACCENT = "#a78bfa"
ACCENT2 = "#f472b6"
GREEN = "#4ade80"
RED = "#f87171"
BLUE = "#60a5fa"
PANEL = "#252540"


class UIController:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎆 Audio Visual Art — Controls")
        self.root.geometry("420x520")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.audio_path = None
        self.use_mic = False
        self.running = False
        self._switch_flag = False
        self._closed = False
        self._beat_flash_count = 0

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()

    def _build_ui(self):
        tk.Label(
            self.root,
            text="🎆 AUDIO VISUAL ART",
            font=("Helvetica", 16, "bold"),
            bg=BG,
            fg=ACCENT
        ).pack(pady=(15, 2))

        tk.Label(
            self.root,
            text="PRO Edition",
            font=("Helvetica", 9, "italic"),
            bg=BG,
            fg=ACCENT2
        ).pack(pady=(0, 12))

        src = tk.LabelFrame(
            self.root, text=" Audio Source ",
            bg=PANEL, fg=FG, bd=0,
            font=("Helvetica", 10, "bold")
        )
        src.pack(fill="x", padx=15, pady=5)

        self.file_label = tk.Label(
            src,
            text="No file selected",
            bg=PANEL,
            fg="#aaa",
            font=("Helvetica", 9),
            wraplength=370
        )
        self.file_label.pack(pady=6)

        btns = tk.Frame(src, bg=PANEL)
        btns.pack(pady=4)

        self._mk_button(btns, "📂 Upload WAV", self.upload_audio, BLUE).grid(row=0, column=0, padx=4)
        self._mk_button(btns, "🎤 Use Mic", self.use_microphone, ACCENT2).grid(row=0, column=1, padx=4)

        meters = tk.LabelFrame(
            self.root, text=" Live Audio ",
            bg=PANEL, fg=FG, bd=0,
            font=("Helvetica", 10, "bold")
        )
        meters.pack(fill="x", padx=15, pady=10)

        tk.Label(meters, text="Amplitude", bg=PANEL, fg=FG, font=("Helvetica", 9)).pack(anchor="w", padx=10, pady=(8, 0))
        self.amp_canvas = tk.Canvas(meters, width=370, height=18, bg="#0f0f1a", highlightthickness=0)
        self.amp_canvas.pack(padx=10, pady=2)
        self.amp_bar = self.amp_canvas.create_rectangle(0, 0, 0, 18, fill=GREEN, width=0)
        self.amp_value = tk.Label(meters, text="0.00", bg=PANEL, fg=GREEN, font=("Consolas", 10, "bold"))
        self.amp_value.pack(anchor="e", padx=10)

        tk.Label(meters, text="Frequency (Hz)", bg=PANEL, fg=FG, font=("Helvetica", 9)).pack(anchor="w", padx=10, pady=(8, 0))
        self.freq_canvas = tk.Canvas(meters, width=370, height=18, bg="#0f0f1a", highlightthickness=0)
        self.freq_canvas.pack(padx=10, pady=2)
        self.freq_bar = self.freq_canvas.create_rectangle(0, 0, 0, 18, fill=BLUE, width=0)
        self.freq_value = tk.Label(meters, text="0.00 Hz", bg=PANEL, fg=BLUE, font=("Consolas", 10, "bold"))
        self.freq_value.pack(anchor="e", padx=10)

        beat_frame = tk.Frame(meters, bg=PANEL)
        beat_frame.pack(pady=8)
        tk.Label(beat_frame, text="Beat:", bg=PANEL, fg=FG, font=("Helvetica", 10)).pack(side="left", padx=4)
        self.beat_dot = tk.Canvas(beat_frame, width=20, height=20, bg=PANEL, highlightthickness=0)
        self.beat_dot.pack(side="left")
        self.beat_circle = self.beat_dot.create_oval(2, 2, 18, 18, fill="#333", outline="")

        ctrl = tk.LabelFrame(
            self.root, text=" Controls ",
            bg=PANEL, fg=FG, bd=0,
            font=("Helvetica", 10, "bold")
        )
        ctrl.pack(fill="x", padx=15, pady=5)

        row = tk.Frame(ctrl, bg=PANEL)
        row.pack(pady=10)

        self._mk_button(row, "▶ Start", self.start, GREEN).grid(row=0, column=0, padx=4)
        self._mk_button(row, "⏹ Stop", self.stop, RED).grid(row=0, column=1, padx=4)
        self._mk_button(row, "🔄 Switch Mode", self.request_switch_mode, ACCENT).grid(row=0, column=2, padx=4)

        self.status_label = tk.Label(
            self.root,
            text="● Idle",
            bg=BG,
            fg="#888",
            font=("Helvetica", 9, "italic")
        )
        self.status_label.pack(pady=10)

    def _mk_button(self, parent, text, cmd, color):
        return tk.Button(
            parent,
            text=text,
            command=cmd,
            bg=color,
            fg="#1a1a2e",
            activebackground=color,
            font=("Helvetica", 9, "bold"),
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
            borderwidth=0
        )

    def upload_audio(self):
        path = filedialog.askopenfilename(
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")]
        )
        if path:
            self.audio_path = path
            self.use_mic = False
            short = path.split("/")[-1].split("\\")[-1]
            self.file_label.config(text=f"📄 {short}", fg=FG)

    def use_microphone(self):
        self.use_mic = True
        self.audio_path = None
        self.file_label.config(text="🎤 Microphone selected", fg=ACCENT2)

    def start(self):
        if self.audio_path or self.use_mic:
            self.running = True
            self.status_label.config(text="● Live", fg=GREEN)

    def stop(self):
        self.running = False
        self.status_label.config(text="● Stopped", fg=RED)

    def update_display(self, amplitude, frequency, beat=False):
        w = int(amplitude * 370)
        self.amp_canvas.coords(self.amp_bar, 0, 0, w, 18)
        self.amp_value.config(text=f"{amplitude:.2f}")

        norm = min(frequency / 2000.0, 1.0)
        w2 = int(norm * 370)
        self.freq_canvas.coords(self.freq_bar, 0, 0, w2, 18)
        self.freq_value.config(text=f"{frequency:.1f} Hz")

        if beat:
            self._beat_flash_count = 6

        if self._beat_flash_count > 0:
            self.beat_dot.itemconfig(self.beat_circle, fill=ACCENT2)
            self._beat_flash_count -= 1
        else:
            self.beat_dot.itemconfig(self.beat_circle, fill="#333")

    def request_switch_mode(self):
        self._switch_flag = True

    def consume_switch_request(self):
        if self._switch_flag:
            self._switch_flag = False
            return True
        return False

    def process_events(self):
        if self._closed:
            return False
        try:
            self.root.update_idletasks()
            self.root.update()
        except tk.TclError:
            self._closed = True
            return False
        return True

    def _on_close(self):
        self._closed = True
        self.running = False
        try:
            self.root.destroy()
        except Exception:
            pass