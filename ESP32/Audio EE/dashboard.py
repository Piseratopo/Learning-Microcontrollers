# pip install matplotlib sounddevice
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import numpy as np
import serial
import serial.tools.list_ports
import sounddevice as sd
from ctypes import windll
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from m16kHz_input import (
    apply_noise_reduction,
    flush_serial_input,
    sample_noise,
    save_wav,
)

BAUD = 460800
FLUSH_DURATION = 2
NOISE_SAMPLE_DURATION = 2
FILE_NAME = "manual_recording_cleaned.wav"
WAVEFORM_WINDOW = 6000  # samples shown in real-time view


class AudioRecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ghi Âm RS485")
        self.root.configure(bg="#f4f4f9")
        self.root.resizable(True, True)
        self.root.minsize(700, 400)

        self.recording = False
        self.rec_buffer = bytearray()
        self.noise_buffer = bytearray()
        self.sample_rate = 8000
        self.start_time = None
        self.ser = None
        self.is_playing = False

        self._build_ui()
        self._refresh_ports()
        self._tick()

    # ------------------------------------------------------------------ UI --
    def _build_ui(self):
        BG = "#1e1e2e"
        PANEL = "#2a2a3e"
        FG = "#cdd6f4"
        GREEN = "#a6e3a1"
        RED = "#f38ba8"
        BLUE = "#89b4fa"
        YELLOW = "#f9e2af"

        # ── Top bar ──
        top = tk.Frame(self.root, bg=PANEL, pady=10)
        top.pack(fill=tk.X, padx=0, pady=(0, 2))

        tk.Label(top, text="Cổng COM:", bg=PANEL, fg=FG, font=("Segoe UI", 10)).pack(
            side=tk.LEFT, padx=(14, 4)
        )
        self.port_var = tk.StringVar(value="COM7")
        self.port_combo = ttk.Combobox(
            top, textvariable=self.port_var, width=9, font=("Segoe UI", 10)
        )
        self.port_combo.pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(
            top,
            text="↻",
            bg=PANEL,
            fg=FG,
            relief=tk.FLAT,
            font=("Segoe UI", 11),
            cursor="hand2",
            command=self._refresh_ports,
        ).pack(side=tk.LEFT, padx=(0, 16))

        self.btn_start = tk.Button(
            top,
            text="▶  Bắt đầu",
            bg=GREEN,
            fg="#1e1e2e",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=14,
            pady=4,
            cursor="hand2",
            command=self._start,
        )
        self.btn_start.pack(side=tk.LEFT, padx=4)

        self.btn_stop = tk.Button(
            top,
            text="■  Dừng",
            bg=RED,
            fg="#1e1e2e",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=14,
            pady=4,
            cursor="hand2",
            state=tk.DISABLED,
            command=self._stop,
        )
        self.btn_stop.pack(side=tk.LEFT, padx=4)

        self.btn_play = tk.Button(
            top,
            text="▷  Phát lại",
            bg=BLUE,
            fg="#1e1e2e",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=14,
            pady=4,
            cursor="hand2",
            state=tk.DISABLED,
            command=self._toggle_playback,
        )
        self.btn_play.pack(side=tk.LEFT, padx=4)

        # Timer (right side)
        self.timer_var = tk.StringVar(value="00:00")
        tk.Label(
            top,
            textvariable=self.timer_var,
            bg=PANEL,
            fg=YELLOW,
            font=("Courier New", 22, "bold"),
        ).pack(side=tk.RIGHT, padx=18)

        # ── Waveform ──
        fig = Figure(figsize=(8, 2.8), dpi=100, facecolor=BG)
        self.ax = fig.add_subplot(111)
        self.ax.set_facecolor("#11111b")
        self.ax.set_ylim(0, 255)
        self.ax.set_xlim(0, WAVEFORM_WINDOW)
        self.ax.tick_params(colors="#9399b2", labelsize=9)
        self.ax.set_ylabel("Biên độ", color="#9399b2", fontsize=9)
        for spine in self.ax.spines.values():
            spine.set_edgecolor("#45475a")
        fig.tight_layout(pad=0.6)

        (self.waveform_line,) = self.ax.plot([], [], color=GREEN, linewidth=1.0)

        self.canvas = FigureCanvasTkAgg(fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # ── Status bar ──
        bot = tk.Frame(self.root, bg=PANEL, pady=6)
        bot.pack(fill=tk.X)

        self.status_var = tk.StringVar(
            value="Sẵn sàng — chọn cổng COM và nhấn Bắt đầu."
        )
        tk.Label(
            bot,
            textvariable=self.status_var,
            bg=PANEL,
            fg=FG,
            font=("Segoe UI", 9),
            anchor=tk.W,
        ).pack(side=tk.LEFT, padx=12)

        self.info_var = tk.StringVar(value="")
        tk.Label(
            bot,
            textvariable=self.info_var,
            bg=PANEL,
            fg="#585b70",
            font=("Segoe UI", 9),
        ).pack(side=tk.RIGHT, padx=12)

    # -------------------------------------------------------- port helpers --
    def _refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo["values"] = ports
        if "COM7" in ports:
            self.port_var.set("COM7")
        elif ports:
            self.port_var.set(ports[0])

    # --------------------------------------------------------- timer / UI --
    def _tick(self):
        if self.recording and self.start_time:
            elapsed = int(time.time() - self.start_time)
            m, s = divmod(elapsed, 60)
            self.timer_var.set(f"{m:02d}:{s:02d}")
            self._redraw_waveform_realtime()
        self.root.after(120, self._tick)

    def _redraw_waveform_realtime(self):
        if len(self.rec_buffer) < 2:
            return
        data = np.frombuffer(self.rec_buffer[-WAVEFORM_WINDOW:], dtype=np.uint8)
        self.waveform_line.set_data(np.arange(len(data)), data)
        self.ax.set_xlim(0, max(WAVEFORM_WINDOW, len(data)))
        self.canvas.draw_idle()

    def _redraw_waveform_full(self, data: np.ndarray):
        n = len(data)
        # Downsample for display if too many points
        if n > 40000:
            step = n // 40000
            data = data[::step]
        self.waveform_line.set_data(np.arange(len(data)), data)
        self.ax.set_xlim(0, len(data))
        self.canvas.draw_idle()

    def _set_status(self, msg):
        self.root.after(0, lambda: self.status_var.set(msg))

    # ------------------------------------------------------------ actions --
    def _start(self):
        port = self.port_var.get().strip()
        if not port:
            messagebox.showerror("Lỗi", "Vui lòng chọn cổng COM.")
            return
        self.rec_buffer = bytearray()
        self.noise_buffer = bytearray()
        self.timer_var.set("00:00")
        self.info_var.set("")
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.DISABLED)
        self.btn_play.config(state=tk.DISABLED)
        threading.Thread(target=self._worker, args=(port,), daemon=True).start()

    def _worker(self, port):
        try:
            self.ser = serial.Serial(port, BAUD, timeout=0.1)

            # 1. Flush
            self._set_status(f"[1/3] Đang xả nhiễu phần cứng ({FLUSH_DURATION}s)...")
            flush_serial_input(self.ser, FLUSH_DURATION)

            # 2. Noise sample
            self._set_status(
                f"[2/3] Đang lấy mẫu tiếng ồn nền ({NOISE_SAMPLE_DURATION}s) — giữ im lặng!"
            )
            noise_data = sample_noise(self.ser, NOISE_SAMPLE_DURATION)
            self.noise_buffer = noise_data.tobytes()

            # 3. Record
            self._set_status("[3/3] Đang ghi âm... Nhấn  ■ Dừng  khi xong.")
            self.recording = True
            self.start_time = time.time()
            self.root.after(0, lambda: self.btn_stop.config(state=tk.NORMAL))

            while self.recording:
                if self.ser.in_waiting:
                    self.rec_buffer.extend(self.ser.read(self.ser.in_waiting))

        except Exception as exc:
            self.root.after(
                0, lambda: messagebox.showerror("Lỗi kết nối Serial", str(exc))
            )
            self.root.after(0, self._reset_ui)
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()

    def _stop(self):
        self.recording = False
        self.btn_stop.config(state=tk.DISABLED)
        self._set_status("Đang xử lý âm thanh...")
        threading.Thread(target=self._process, daemon=True).start()

    def _process(self):
        try:
            duration = time.time() - self.start_time
            n = len(self.rec_buffer)
            self.sample_rate = max(1, int(n / duration))

            noise = np.frombuffer(self.noise_buffer, dtype=np.uint8)
            signal = np.frombuffer(self.rec_buffer, dtype=np.uint8)
            cleaned = apply_noise_reduction(signal, noise)
            save_wav(FILE_NAME, cleaned, self.sample_rate)

            self.root.after(0, lambda: self._on_saved(n, duration, cleaned))
        except Exception as exc:
            self.root.after(0, lambda: messagebox.showerror("Lỗi xử lý", str(exc)))
            self.root.after(0, self._reset_ui)

    def _on_saved(self, n, duration, cleaned):
        self.status_var.set(f"Đã lưu → {FILE_NAME}   |   Nhấn ▷ Phát lại để nghe.")
        self.info_var.set(
            f"Số mẫu: {n:,}   Tần số lấy mẫu: {self.sample_rate:,} Hz   Thời lượng: {duration:.1f}s"
        )
        self._redraw_waveform_full(cleaned)
        self.btn_start.config(state=tk.NORMAL)
        self.btn_play.config(state=tk.NORMAL)

    def _reset_ui(self):
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.btn_play.config(state=tk.DISABLED)

    # ---------------------------------------------------------- playback --
    def _toggle_playback(self):
        if self.is_playing:
            sd.stop()
            self.is_playing = False
            self.btn_play.config(text="▷  Phát lại")
            self.status_var.set("Đã dừng phát.")
        else:
            if not self.rec_buffer:
                return
            raw = np.frombuffer(self.rec_buffer, dtype=np.uint8).astype(np.float32)
            raw = (raw - 127.0) / 128.0
            self.is_playing = True
            self.btn_play.config(text="◼  Dừng phát")
            self.status_var.set("Đang phát lại âm thanh gốc...")
            sd.play(raw, self.sample_rate)
            threading.Thread(target=self._wait_playback_end, daemon=True).start()

    def _wait_playback_end(self):
        sd.wait()
        self.root.after(0, self._on_playback_end)

    def _on_playback_end(self):
        self.is_playing = False
        self.btn_play.config(text="▷  Phát lại")
        self.status_var.set("Phát lại hoàn tất.")


if __name__ == "__main__":
    try:

        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    AudioRecorderApp(root)
    root.mainloop()
