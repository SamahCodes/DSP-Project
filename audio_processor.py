# audio_processor.py
# -------------------------------------------------------
# DSP: framing, FFT, RMS, beat detection.
# Supports WAV file or microphone.
# -------------------------------------------------------

import queue
from collections import deque

import numpy as np
from scipy.io import wavfile
from scipy.fft import rfft, rfftfreq

try:
    import sounddevice as sd
    HAS_SD = True
except ImportError:
    HAS_SD = False


class AudioProcessor:
    """
    Per-frame extraction:
        amplitude  : RMS energy (0 -> 1)
        frequency  : dominant frequency (Hz)
        spectrum   : compact log-band array (0 -> 1)
        beat       : True on detected onset
    """

    def __init__(self, source="mic", frame_size=1024, hop_size=512,
                 sample_rate=44100, n_bands=32):
        self.source = source
        self.frame_size = frame_size
        self.hop_size = hop_size
        self.sample_rate = sample_rate
        self.n_bands = n_bands

        # File mode
        self.audio_data = None
        self.position = 0

        # Mic mode
        self.mic_queue = queue.Queue(maxsize=32)
        self.mic_stream = None
        self.mic_buffer = np.zeros(0, dtype=np.float32)

        # Beat detection state
        self.energy_history = deque(maxlen=43)
        self.last_beat_frame = -999
        self.frame_counter = 0

        if source != "mic":
            self._load_file(source)

    # ---------------------------------------------------
    # File loading
    # ---------------------------------------------------
    def _load_file(self, path):
        sr, data = wavfile.read(path)
        self.sample_rate = sr

        # Convert stereo to mono
        if getattr(data, "ndim", 1) > 1:
            data = np.mean(data, axis=1)

        # Convert to float32 safely
        if np.issubdtype(data.dtype, np.integer):
            max_val = np.iinfo(data.dtype).max
            data = data.astype(np.float32) / max_val
        else:
            data = data.astype(np.float32)

        # Normalize
        peak = np.max(np.abs(data)) if len(data) > 0 else 0
        if peak > 0:
            data = data / peak

        self.audio_data = data
        self.position = 0

    # ---------------------------------------------------
    # Playback
    # ---------------------------------------------------
    def play(self):
        if self.source != "mic" and self.audio_data is not None and HAS_SD:
            sd.stop()
            sd.play(self.audio_data, self.sample_rate)

    def stop(self):
        self.stop_mic()
        if HAS_SD:
            sd.stop()

    # ---------------------------------------------------
    # Microphone
    # ---------------------------------------------------
    def start_mic(self):
        if self.source != "mic":
            return

        if not HAS_SD:
            raise RuntimeError("sounddevice is required for microphone input")

        if self.mic_stream is not None:
            return

        def callback(indata, frames, time_info, status):
            try:
                self.mic_queue.put_nowait(indata[:, 0].copy())
            except queue.Full:
                pass

        self.mic_stream = sd.InputStream(
            channels=1,
            samplerate=self.sample_rate,
            blocksize=self.hop_size,
            callback=callback
        )
        self.mic_stream.start()

    def stop_mic(self):
        if self.mic_stream is not None:
            self.mic_stream.stop()
            self.mic_stream.close()
            self.mic_stream = None

    # ---------------------------------------------------
    # Frame retrieval
    # ---------------------------------------------------
    def get_next_frame(self):
        if self.source == "mic":
            try:
                while len(self.mic_buffer) < self.frame_size:
                    chunk = self.mic_queue.get(timeout=0.05)
                    self.mic_buffer = np.concatenate([self.mic_buffer, chunk])
            except queue.Empty:
                return np.zeros(self.frame_size, dtype=np.float32)

            frame = self.mic_buffer[:self.frame_size]
            self.mic_buffer = self.mic_buffer[self.hop_size:]
            return frame

        # File mode
        if self.audio_data is None:
            return None

        end = self.position + self.frame_size
        if end > len(self.audio_data):
            return None

        frame = self.audio_data[self.position:end]
        self.position += self.hop_size
        return frame

    # ---------------------------------------------------
    # DSP
    # ---------------------------------------------------
    def process_frame(self, frame):
        """Return (amplitude, frequency, spectrum_bands, beat)."""
        if frame is None or len(frame) == 0:
            return 0.0, 0.0, np.zeros(self.n_bands), False

        # RMS amplitude
        amplitude = float(np.sqrt(np.mean(frame ** 2)))
        amplitude = float(np.clip(amplitude * 3.0, 0.0, 1.0))

        # FFT
        windowed = frame * np.hanning(len(frame))
        spectrum = np.abs(rfft(windowed))
        freqs = rfftfreq(len(frame), d=1.0 / self.sample_rate)

        # Dominant frequency
        if len(spectrum) > 1:
            peak_idx = np.argmax(spectrum[1:]) + 1
            frequency = float(freqs[peak_idx])
        else:
            frequency = 0.0

        bands = self._compute_bands(spectrum)
        beat = self._detect_beat(amplitude)

        self.frame_counter += 1
        return amplitude, frequency, bands, beat

    def _compute_bands(self, spectrum):
        n = len(spectrum)
        if n == 0:
            return np.zeros(self.n_bands)

        edges = np.logspace(0, np.log10(n), self.n_bands + 1).astype(int)
        edges = np.clip(edges, 0, n)

        bands = np.zeros(self.n_bands, dtype=np.float32)
        for i in range(self.n_bands):
            lo = edges[i]
            hi = max(lo + 1, edges[i + 1])
            hi = min(hi, n)
            bands[i] = np.mean(spectrum[lo:hi])

        m = np.max(bands)
        if m > 0:
            bands = bands / m
        return bands

    def _detect_beat(self, energy):
        self.energy_history.append(energy)

        if len(self.energy_history) < 10:
            return False

        avg = np.mean(self.energy_history)
        is_beat = (energy > avg * 1.5) and (energy > 0.15)

        if is_beat and (self.frame_counter - self.last_beat_frame) > 8:
            self.last_beat_frame = self.frame_counter
            return True

        return False

    # ---------------------------------------------------
    # Reset
    # ---------------------------------------------------
    def reset(self):
        self.position = 0
        self.frame_counter = 0
        self.last_beat_frame = -999
        self.energy_history.clear()
        self.mic_buffer = np.zeros(0, dtype=np.float32)

        while not self.mic_queue.empty():
            try:
                self.mic_queue.get_nowait()
            except Exception:
                break