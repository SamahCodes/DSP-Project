
# Audio Visual Art Project — Full Beginner Study Guide

## For absolute beginners

This guide explains the final project using these 4 files:

- `main.py`
- `audio_processor.py`
- `visualizer.py`
- `ui_controller.py`

The goal is to explain the project as if you are seeing:

- Python
- DSP
- GUI
- visualization

for the **first time**.

---

# Table of Contents

1. [What this project does](#what-this-project-does)
2. [How the 4 files work together](#how-the-4-files-work-together)
3. [Big-picture flow of the program](#big-picture-flow-of-the-program)
4. [File 1: `main.py` explained line by line](#file-1-mainpy-explained-line-by-line)
5. [File 2: `audio_processor.py` explained line by line](#file-2-audio_processorpy-explained-line-by-line)
6. [File 3: `visualizer.py` explained line by line](#file-3-visualizerpy-explained-line-by-line)
7. [File 4: `ui_controller.py` explained line by line](#file-4-ui_controllerpy-explained-line-by-line)
8. [Important concepts you must understand](#important-concepts-you-must-understand)
9. [How to explain this project in a viva or presentation](#how-to-explain-this-project-in-a-viva-or-presentation)
10. [Common mistakes and bugs](#common-mistakes-and-bugs)
11. [Quick revision notes](#quick-revision-notes)

---

# What this project does

This project creates an **audio visualizer**.

That means:

- it takes sound from either:
  - a `.wav` file, or
  - the microphone
- it analyzes the sound
- it extracts useful features like:
  - amplitude
  - dominant frequency
  - spectrum
  - beat
- it sends these features to a visualizer
- the visualizer draws animated art based on the sound
- there is also a control panel UI where the user can:
  - choose a WAV file
  - use the microphone
  - start
  - stop
  - switch visualization mode

So this is a project combining:

- **audio signal processing**
- **graphics**
- **real-time interactivity**
- **GUI programming**

---

# How the 4 files work together

## 1. `main.py`
This is the **manager** of the whole project.

It:
- creates the UI
- creates the visualizer
- creates the audio processor
- keeps the program loop running
- connects everything together

Think of it as the **brain** or **controller**.

---

## 2. `audio_processor.py`
This file handles the **sound analysis**.

It:
- reads audio from file or mic
- cuts audio into frames
- calculates:
  - RMS amplitude
  - dominant frequency
  - spectrum bands
  - beat detection

Think of it as the **ears + analysis engine**.

---

## 3. `visualizer.py`
This file handles the **graphics**.

It:
- opens the Pygame window
- draws the particles, bars, mandala, ribbon, or nebula
- updates the animation using audio data

Think of it as the **artist**.

---

## 4. `ui_controller.py`
This file builds the **control panel window** using Tkinter.

It:
- shows buttons
- lets the user choose mic/file
- shows meters for amplitude and frequency
- shows beat indicator
- sends commands like start/stop/switch mode

Think of it as the **dashboard**.

---

# Big-picture flow of the program

Here is the full flow in simple words:

1. `main.py` starts
2. It creates:
   - UI window
   - visualizer window
3. The user chooses:
   - microphone, or
   - WAV file
4. The user clicks **Start**
5. `main.py` creates an `AudioProcessor`
6. `AudioProcessor` starts reading sound
7. `main.py` repeatedly:
   - gets audio frames
   - processes them
   - smooths values
   - sends them to the visualizer
   - updates the UI meters
8. The visualizer draws art
9. If the user clicks stop or closes windows:
   - mic/file playback stops
   - windows close cleanly

---

# File 1: `main.py` explained line by line

## Full code

```python
# main.py
# -------------------------------------------------------
# Integration: connect audio -> visualizer + UI.
# -------------------------------------------------------

import time
from audio_processor import AudioProcessor
from visualizer import Visualizer
from ui_controller import UIController


def main():
    ui = UIController()
    visualizer = Visualizer()

    audio_processor = None
    active_source = None
    was_running = False

    # Visual smoothing
    smooth_amp = 0.0
    smooth_freq = 0.0
    AMP_S = 0.30
    FREQ_S = 0.15

    # For file playback timing
    file_time_accumulator = 0.0
    seconds_per_hop = 0.0

    # Keep last spectrum for drawing between file-frame updates
    last_spectrum = [0.0] * 32

    print("🎆 Audio Visual Art — PRO Edition started")
    print("Tip: Press SPACE in the visualizer to switch modes.")

    last_tick = time.perf_counter()

    def stop_current_source():
        nonlocal audio_processor, active_source
        if audio_processor is not None:
            audio_processor.stop()
        active_source = None

    def start_current_source(source):
        nonlocal audio_processor, active_source, file_time_accumulator, seconds_per_hop, last_spectrum

        if not source:
            return False

        # Recreate processor if source changed or processor doesn't exist
        if audio_processor is None or active_source != source:
            if audio_processor is not None:
                audio_processor.stop()
            audio_processor = AudioProcessor(source)
        else:
            audio_processor.reset()

        if source == "mic":
            audio_processor.start_mic()
        else:
            audio_processor.play()

        active_source = source
        file_time_accumulator = 0.0
        seconds_per_hop = audio_processor.hop_size / audio_processor.sample_rate
        last_spectrum = [0.0] * audio_processor.n_bands
        return True

    while visualizer.running:
        now = time.perf_counter()
        dt = now - last_tick
        last_tick = now

        # 1) Process Tkinter UI
        if not ui.process_events():
            break

        # 2) Determine source
        current_source = "mic" if ui.use_mic else ui.audio_path

        # 3) Handle Start / Stop / Source-change transitions
        if ui.running and not was_running:
            # Just pressed Start
            try:
                if not start_current_source(current_source):
                    ui.stop()
            except Exception as e:
                print(f"[Error starting source] {e}")
                ui.stop()
                stop_current_source()

        elif ui.running and was_running and current_source != active_source:
            # Source changed while running
            try:
                if not start_current_source(current_source):
                    ui.stop()
            except Exception as e:
                print(f"[Error switching source] {e}")
                ui.stop()
                stop_current_source()

        elif not ui.running and was_running:
            # Just pressed Stop
            stop_current_source()
            if audio_processor is not None:
                audio_processor.reset()

        # 4) Audio processing
        if ui.running and audio_processor is not None and active_source is not None:
            if active_source == "mic":
                # Real-time mic mode
                frame = audio_processor.get_next_frame()
                amp, freq, spectrum, beat = audio_processor.process_frame(frame)

                smooth_amp = AMP_S * amp + (1 - AMP_S) * smooth_amp
                smooth_freq = FREQ_S * freq + (1 - FREQ_S) * smooth_freq
                last_spectrum = spectrum.tolist() if hasattr(spectrum, "tolist") else list(spectrum)

                visualizer.update(smooth_amp, smooth_freq, last_spectrum, beat)
                ui.update_display(smooth_amp, smooth_freq, beat)

            else:
                # File mode: advance frames according to real time
                file_time_accumulator += dt
                beat_flag = False
                processed_any = False

                while file_time_accumulator >= seconds_per_hop:
                    frame = audio_processor.get_next_frame()

                    if frame is None:
                        # End of file
                        ui.stop()
                        audio_processor.stop()
                        audio_processor.reset()
                        active_source = None
                        break

                    amp, freq, spectrum, beat = audio_processor.process_frame(frame)
                    smooth_amp = AMP_S * amp + (1 - AMP_S) * smooth_amp
                    smooth_freq = FREQ_S * freq + (1 - FREQ_S) * smooth_freq
                    last_spectrum = spectrum.tolist() if hasattr(spectrum, "tolist") else list(spectrum)
                    beat_flag = beat_flag or beat
                    processed_any = True

                    file_time_accumulator -= seconds_per_hop

                if active_source is not None:
                    visualizer.update(smooth_amp, smooth_freq, last_spectrum, beat_flag if processed_any else False)
                    ui.update_display(smooth_amp, smooth_freq, beat_flag if processed_any else False)

        else:
            # Idle decay
            smooth_amp *= 0.90
            smooth_freq *= 0.95
            visualizer.update(smooth_amp, smooth_freq, last_spectrum, False)
            ui.update_display(smooth_amp, smooth_freq, False)

        # 5) Mode switch from UI
        if ui.consume_switch_request():
            visualizer.switch_mode()

        # 6) Draw pygame window
        visualizer.draw()

        was_running = ui.running
        time.sleep(0.005)

    # Cleanup
    if audio_processor is not None:
        audio_processor.stop()

    visualizer.quit()
    print("✅ Closed cleanly.")


if __name__ == "__main__":
    main()
```

---

## Line-by-line explanation

### Lines 1–4
```python
# main.py
# -------------------------------------------------------
# Integration: connect audio -> visualizer + UI.
# -------------------------------------------------------
```

- These are comments.
- They do not execute.
- They tell us this file is the integration point.
- "Integration" means this file connects all the parts together.

---

### Line 6
```python
import time
```

- This imports Python’s built-in `time` module.
- We use it for timing the loop.
- It helps us know how much real time passed between frames.

---

### Line 7
```python
from audio_processor import AudioProcessor
```

- This imports the `AudioProcessor` class from `audio_processor.py`.
- That class handles sound analysis.

---

### Line 8
```python
from visualizer import Visualizer
```

- This imports the `Visualizer` class from `visualizer.py`.
- That class draws the graphics.

---

### Line 9
```python
from ui_controller import UIController
```

- This imports the `UIController` class from `ui_controller.py`.
- That class manages the Tkinter control window.

---

### Line 12
```python
def main():
```

- This defines the main function.
- A function is a reusable block of code.
- This one runs the whole application.

---

### Line 13
```python
ui = UIController()
```

- Creates an object from the `UIController` class.
- This opens the Tkinter control panel.

---

### Line 14
```python
visualizer = Visualizer()
```

- Creates an object from the `Visualizer` class.
- This opens the Pygame visualization window.

---

### Line 16
```python
audio_processor = None
```

- This variable will later hold an `AudioProcessor`.
- It starts as `None`, meaning “nothing yet”.

---

### Line 17
```python
active_source = None
```

- This stores what source is currently being used.
- It may later become:
  - `"mic"`
  - or a file path string

---

### Line 18
```python
was_running = False
```

- This helps detect changes in state.
- It remembers whether the UI was running in the previous loop.
- Useful for detecting:
  - just started
  - just stopped

---

### Line 21
```python
smooth_amp = 0.0
```

- This stores a smoothed amplitude value.
- Smoothed means less jumpy.

---

### Line 22
```python
smooth_freq = 0.0
```

- Same idea, but for frequency.

---

### Line 23
```python
AMP_S = 0.30
```

- This is the smoothing factor for amplitude.
- 0.30 means use 30% of the new value and keep 70% of the old one.

---

### Line 24
```python
FREQ_S = 0.15
```

- Smoothing factor for frequency.
- Smaller smoothing factor = smoother/slower changes.

---

### Line 27
```python
file_time_accumulator = 0.0
```

- Used only in file mode.
- It accumulates real elapsed time.
- This helps keep visualization synchronized with file playback.

---

### Line 28
```python
seconds_per_hop = 0.0
```

- This will later store how long one audio hop takes.
- Hop = step size between frames.

---

### Line 31
```python
last_spectrum = [0.0] * 32
```

- Creates a list of 32 zeros.
- This stores the last known spectrum values.
- We keep them so visuals still have something to draw even between updates.

---

### Lines 33–34
```python
print("🎆 Audio Visual Art — PRO Edition started")
print("Tip: Press SPACE in the visualizer to switch modes.")
```

- These print messages to the terminal.
- Good for debugging and user feedback.

---

### Line 36
```python
last_tick = time.perf_counter()
```

- Gets a high-precision time value.
- `perf_counter()` is good for measuring elapsed time accurately.

---

## Nested helper function: `stop_current_source`

### Line 38
```python
def stop_current_source():
```

- Defines a helper function inside `main()`.
- This function stops whatever audio source is active.

---

### Line 39
```python
nonlocal audio_processor, active_source
```

- `nonlocal` means:
  - “I want to modify variables from the enclosing function (`main`)”
- Without `nonlocal`, Python would think these are new local variables.

---

### Lines 40–41
```python
if audio_processor is not None:
    audio_processor.stop()
```

- If an audio processor exists, stop it.
- This may stop mic streaming or audio playback.

---

### Line 42
```python
active_source = None
```

- Mark that no source is active anymore.

---

## Nested helper function: `start_current_source`

### Line 44
```python
def start_current_source(source):
```

- This helper starts a new source.
- `source` can be:
  - `"mic"`
  - or a path to a WAV file

---

### Line 45
```python
nonlocal audio_processor, active_source, file_time_accumulator, seconds_per_hop, last_spectrum
```

- We want this nested function to modify variables defined in `main()`.

---

### Lines 47–48
```python
if not source:
    return False
```

- If `source` is empty or invalid, fail.
- `False` means start did not succeed.

---

### Lines 51–55
```python
if audio_processor is None or active_source != source:
    if audio_processor is not None:
        audio_processor.stop()
    audio_processor = AudioProcessor(source)
```

- If:
  - no processor exists yet, or
  - the source changed
- then create a new `AudioProcessor`.
- Before creating a new one, stop the old one if it exists.

---

### Lines 56–57
```python
else:
    audio_processor.reset()
```

- If we are using the same source again, just reset it.
- No need to recreate the object.

---

### Lines 59–62
```python
if source == "mic":
    audio_processor.start_mic()
else:
    audio_processor.play()
```

- If the source is microphone:
  - start mic capture
- otherwise:
  - it must be a file
  - so start playback

---

### Line 64
```python
active_source = source
```

- Remember what source is currently active.

---

### Line 65
```python
file_time_accumulator = 0.0
```

- Reset timing counter for file playback.

---

### Line 66
```python
seconds_per_hop = audio_processor.hop_size / audio_processor.sample_rate
```

- Calculates how long one hop lasts in seconds.
- Example:
  - hop size = 512
  - sample rate = 44100
  - duration = 512 / 44100 seconds

---

### Line 67
```python
last_spectrum = [0.0] * audio_processor.n_bands
```

- Reset stored spectrum to zeros.
- Number of bands comes from the processor.

---

### Line 68
```python
return True
```

- Starting succeeded.

---

## Main loop

### Line 70
```python
while visualizer.running:
```

- This is the main loop of the program.
- It keeps running as long as the visualizer window is still open.

---

### Line 71
```python
now = time.perf_counter()
```

- Get current precise time.

---

### Line 72
```python
dt = now - last_tick
```

- `dt` means delta time.
- It is the amount of time that passed since the previous loop iteration.

---

### Line 73
```python
last_tick = now
```

- Update the previous time marker.

---

### Lines 76–77
```python
if not ui.process_events():
    break
```

- Ask the Tkinter UI to process its events.
- Events include:
  - button clicks
  - window close
- If the UI says it is closed, exit loop.

---

### Line 80
```python
current_source = "mic" if ui.use_mic else ui.audio_path
```

- This is a Python conditional expression.
- If the user selected mic:
  - current source is `"mic"`
- otherwise:
  - use the selected audio file path

---

## Start/Stop/Source change logic

### Line 83
```python
if ui.running and not was_running:
```

- Means:
  - user is running now
  - but was not running in previous loop
- So the user **just pressed Start**

---

### Line 85
```python
try:
```

- Start a `try` block.
- This means:
  - “run this code, and if an error happens, catch it”

---

### Lines 86–87
```python
if not start_current_source(current_source):
    ui.stop()
```

- Try to start the selected source.
- If starting fails, stop the UI running state.

---

### Lines 88–91
```python
except Exception as e:
    print(f"[Error starting source] {e}")
    ui.stop()
    stop_current_source()
```

- If any error happens:
  - print the error
  - stop UI state
  - stop any source cleanly

---

### Line 93
```python
elif ui.running and was_running and current_source != active_source:
```

- Means:
  - user is running
  - user was already running
  - but selected source changed
- Example:
  - switched from mic to file while app is live

---

### Lines 95–101
```python
try:
    if not start_current_source(current_source):
        ui.stop()
except Exception as e:
    print(f"[Error switching source] {e}")
    ui.stop()
    stop_current_source()
```

- Same logic as start, but for changing source during runtime.

---

### Line 103
```python
elif not ui.running and was_running:
```

- Means:
  - user is not running now
  - but was running in previous loop
- So the user **just pressed Stop**

---

### Lines 105–107
```python
stop_current_source()
if audio_processor is not None:
    audio_processor.reset()
```

- Stop whatever was active.
- Reset processor state.

---

## Audio processing section

### Line 110
```python
if ui.running and audio_processor is not None and active_source is not None:
```

- Only process audio if:
  - user pressed Start
  - processor exists
  - and a source is active

---

## Microphone mode

### Line 111
```python
if active_source == "mic":
```

- If the active source is microphone, use real-time mode.

---

### Line 113
```python
frame = audio_processor.get_next_frame()
```

- Ask processor for the next chunk of audio samples.

---

### Line 114
```python
amp, freq, spectrum, beat = audio_processor.process_frame(frame)
```

- Process this frame.
- Returns four features:
  - `amp`
  - `freq`
  - `spectrum`
  - `beat`

---

### Line 116
```python
smooth_amp = AMP_S * amp + (1 - AMP_S) * smooth_amp
```

- This smooths amplitude.
- It mixes:
  - some of the new value
  - some of the old value
- This reduces sudden jumps.

---

### Line 117
```python
smooth_freq = FREQ_S * freq + (1 - FREQ_S) * smooth_freq
```

- Same smoothing idea, but for frequency.

---

### Line 118
```python
last_spectrum = spectrum.tolist() if hasattr(spectrum, "tolist") else list(spectrum)
```

- Convert spectrum into a normal Python list.
- Some arrays are NumPy arrays and have `.tolist()`.
- If not, use `list()`.

---

### Lines 120–121
```python
visualizer.update(smooth_amp, smooth_freq, last_spectrum, beat)
ui.update_display(smooth_amp, smooth_freq, beat)
```

- Send processed audio features to:
  - visualizer
  - UI meters

---

## File mode

### Line 124
```python
file_time_accumulator += dt
```

- Add elapsed real time to the file accumulator.
- This helps keep file processing synced with audio playback.

---

### Line 125
```python
beat_flag = False
```

- This will remember whether any processed frame had a beat.

---

### Line 126
```python
processed_any = False
```

- This tells us whether we actually processed any frames in this loop.

---

### Line 128
```python
while file_time_accumulator >= seconds_per_hop:
```

- If enough time passed for one or more audio hops, process that many frames.
- This allows visualization to catch up correctly.

---

### Line 129
```python
frame = audio_processor.get_next_frame()
```

- Read next frame from the WAV file.

---

### Line 131
```python
if frame is None:
```

- If no frame exists, file ended.

---

### Lines 133–137
```python
ui.stop()
audio_processor.stop()
audio_processor.reset()
active_source = None
break
```

- Stop everything related to the file.
- Reset processor.
- Clear active source.
- Exit the inner while loop.

---

### Lines 139–144
```python
amp, freq, spectrum, beat = audio_processor.process_frame(frame)
smooth_amp = AMP_S * amp + (1 - AMP_S) * smooth_amp
smooth_freq = FREQ_S * freq + (1 - FREQ_S) * smooth_freq
last_spectrum = spectrum.tolist() if hasattr(spectrum, "tolist") else list(spectrum)
beat_flag = beat_flag or beat
processed_any = True
```

- Process frame.
- Smooth amplitude and frequency.
- Save spectrum.
- Update beat flag.
- Mark that at least one frame was processed.

`beat_flag = beat_flag or beat` means:
- if any frame had a beat, keep `beat_flag` as `True`

---

### Line 146
```python
file_time_accumulator -= seconds_per_hop
```

- Since one hop has been processed, subtract that amount of time.

---

### Lines 148–150
```python
if active_source is not None:
    visualizer.update(smooth_amp, smooth_freq, last_spectrum, beat_flag if processed_any else False)
    ui.update_display(smooth_amp, smooth_freq, beat_flag if processed_any else False)
```

- If file is still active:
  - update visualizer and UI
- If no frames were processed, beat becomes `False`

---

## Idle mode

### Line 153
```python
else:
```

- This means:
  - app is not running, or
  - no valid source exists

---

### Lines 155–156
```python
smooth_amp *= 0.90
smooth_freq *= 0.95
```

- Slowly fade old values toward zero.
- This gives a gentle decay effect.

---

### Lines 157–158
```python
visualizer.update(smooth_amp, smooth_freq, last_spectrum, False)
ui.update_display(smooth_amp, smooth_freq, False)
```

- Update visuals and UI using the faded values.

---

## Mode switching

### Lines 161–162
```python
if ui.consume_switch_request():
    visualizer.switch_mode()
```

- If the user requested a mode switch in the UI:
  - tell the visualizer to go to the next mode

---

## Drawing

### Line 165
```python
visualizer.draw()
```

- Draw one full visual frame on screen.

---

### Line 167
```python
was_running = ui.running
```

- Save current running state for next loop.
- Needed to detect transitions.

---

### Line 168
```python
time.sleep(0.005)
```

- Pause for 5 milliseconds.
- This slightly reduces CPU usage.

---

## Cleanup

### Line 171
```python
if audio_processor is not None:
```

- If processor exists, clean it up.

---

### Line 172
```python
audio_processor.stop()
```

- Stop playback or mic stream.

---

### Line 174
```python
visualizer.quit()
```

- Close Pygame cleanly.

---

### Line 175
```python
print("✅ Closed cleanly.")
```

- Print a success message.

---

## Program entry point

### Lines 178–179
```python
if __name__ == "__main__":
    main()
```

- This is a very important Python pattern.
- It means:
  - if this file is run directly, call `main()`
- If imported by another file, do not run automatically.

---

# File 2: `audio_processor.py` explained line by line

## Full code

```python
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

    def _load_file(self, path):
        sr, data = wavfile.read(path)
        self.sample_rate = sr

        if getattr(data, "ndim", 1) > 1:
            data = np.mean(data, axis=1)

        if np.issubdtype(data.dtype, np.integer):
            max_val = np.iinfo(data.dtype).max
            data = data.astype(np.float32) / max_val
        else:
            data = data.astype(np.float32)

        peak = np.max(np.abs(data)) if len(data) > 0 else 0
        if peak > 0:
            data = data / peak

        self.audio_data = data
        self.position = 0

    def play(self):
        if self.source != "mic" and self.audio_data is not None and HAS_SD:
            sd.stop()
            sd.play(self.audio_data, self.sample_rate)

    def stop(self):
        self.stop_mic()
        if HAS_SD:
            sd.stop()

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

        if self.audio_data is None:
            return None

        end = self.position + self.frame_size
        if end > len(self.audio_data):
            return None

        frame = self.audio_data[self.position:end]
        self.position += self.hop_size
        return frame

    def process_frame(self, frame):
        if frame is None or len(frame) == 0:
            return 0.0, 0.0, np.zeros(self.n_bands), False

        amplitude = float(np.sqrt(np.mean(frame ** 2)))
        amplitude = float(np.clip(amplitude * 3.0, 0.0, 1.0))

        windowed = frame * np.hanning(len(frame))
        spectrum = np.abs(rfft(windowed))
        freqs = rfftfreq(len(frame), d=1.0 / self.sample_rate)

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
```

---

## Line-by-line explanation

### Header comments
```python
# audio_processor.py
# -------------------------------------------------------
# DSP: framing, FFT, RMS, beat detection.
# Supports WAV file or microphone.
# -------------------------------------------------------
```

- These comments explain the purpose of the file.
- DSP = Digital Signal Processing.

---

### Imports
```python
import queue
from collections import deque

import numpy as np
from scipy.io import wavfile
from scipy.fft import rfft, rfftfreq
```

#### `import queue`
- Imports Python’s queue module.
- A queue is a data structure where data waits in order.
- Used for microphone chunks.

#### `from collections import deque`
- Imports `deque`, a fast double-ended queue.
- Used for beat history.

#### `import numpy as np`
- Imports NumPy and gives it alias `np`.
- NumPy is used for numeric arrays and math.

#### `from scipy.io import wavfile`
- Used to read WAV files.

#### `from scipy.fft import rfft, rfftfreq`
- `rfft` = FFT for real-valued input
- `rfftfreq` = frequency values corresponding to FFT bins

---

### Optional sounddevice import
```python
try:
    import sounddevice as sd
    HAS_SD = True
except ImportError:
    HAS_SD = False
```

- Try to import `sounddevice`.
- If available:
  - `HAS_SD = True`
- If not:
  - `HAS_SD = False`

Why do this?
- Because mic and playback need `sounddevice`.
- This prevents program crash during import if it is missing.

---

## Class definition
```python
class AudioProcessor:
```

- Defines the class.
- A class is like a blueprint for making objects.

---

### Docstring
```python
"""
Per-frame extraction:
    amplitude  : RMS energy (0 -> 1)
    frequency  : dominant frequency (Hz)
    spectrum   : compact log-band array (0 -> 1)
    beat       : True on detected onset
"""
```

- This is a class docstring.
- It explains what the processor returns for each frame.

---

## Constructor

### Function start
```python
def __init__(self, source="mic", frame_size=1024, hop_size=512,
             sample_rate=44100, n_bands=32):
```

- Constructor function.
- Runs automatically when object is created.
- Parameters:
  - `source`: `"mic"` or file path
  - `frame_size`: number of samples in one frame
  - `hop_size`: how far to move for next frame
  - `sample_rate`: samples per second
  - `n_bands`: how many spectrum bands to produce

---

### Store settings
```python
self.source = source
self.frame_size = frame_size
self.hop_size = hop_size
self.sample_rate = sample_rate
self.n_bands = n_bands
```

- Save constructor inputs into the object.

---

### File mode state
```python
self.audio_data = None
self.position = 0
```

- `audio_data` will store full WAV data.
- `position` tells where we are in the file.

---

### Mic mode state
```python
self.mic_queue = queue.Queue(maxsize=32)
self.mic_stream = None
self.mic_buffer = np.zeros(0, dtype=np.float32)
```

- `mic_queue` stores chunks coming from the mic callback.
- `mic_stream` will hold the active microphone stream.
- `mic_buffer` stores collected mic samples until enough data exists for one frame.

---

### Beat state
```python
self.energy_history = deque(maxlen=43)
self.last_beat_frame = -999
self.frame_counter = 0
```

- `energy_history` stores recent amplitude values.
- `maxlen=43` means keep only the latest 43 values.
- `last_beat_frame` remembers when the last beat happened.
- `frame_counter` counts how many frames have been processed.

---

### File loading decision
```python
if source != "mic":
    self._load_file(source)
```

- If source is not mic, then source must be a file path.
- Load file immediately.

---

## `_load_file`

### Start
```python
def _load_file(self, path):
```

- Private helper function.
- Loads and prepares WAV file.

---

### Read WAV file
```python
sr, data = wavfile.read(path)
```

- Reads the WAV file.
- Returns:
  - sample rate
  - raw audio data

---

### Save sample rate
```python
self.sample_rate = sr
```

- Update object sample rate to match file.

---

### Convert stereo to mono
```python
if getattr(data, "ndim", 1) > 1:
    data = np.mean(data, axis=1)
```

- `ndim` means number of dimensions.
- If data has more than 1 dimension, it likely has multiple channels.
- `np.mean(..., axis=1)` averages channels into one mono signal.

---

### Convert integer audio to float
```python
if np.issubdtype(data.dtype, np.integer):
    max_val = np.iinfo(data.dtype).max
    data = data.astype(np.float32) / max_val
else:
    data = data.astype(np.float32)
```

- WAV files are often stored as integers like `int16`.
- We convert them to `float32`.
- If integer:
  - divide by maximum possible value to scale into roughly `[-1, 1]`
- If already float:
  - just cast to `float32`

---

### Normalize peak
```python
peak = np.max(np.abs(data)) if len(data) > 0 else 0
if peak > 0:
    data = data / peak
```

- `np.abs(data)` makes all samples positive in magnitude.
- `np.max(...)` finds largest absolute value.
- If peak is nonzero:
  - divide all samples by peak
- This normalizes the signal so max amplitude becomes 1.

---

### Save file data
```python
self.audio_data = data
self.position = 0
```

- Store normalized audio in object.
- Start reading from the beginning.

---

## Playback methods

### `play`
```python
def play(self):
    if self.source != "mic" and self.audio_data is not None and HAS_SD:
        sd.stop()
        sd.play(self.audio_data, self.sample_rate)
```

- Only valid for file mode.
- Stops any previous sound first.
- Plays current audio data at the correct sample rate.

---

### `stop`
```python
def stop(self):
    self.stop_mic()
    if HAS_SD:
        sd.stop()
```

- General-purpose stop function.
- Stops microphone stream if active.
- Stops audio playback if sounddevice exists.

---

## Microphone methods

### `start_mic`
```python
def start_mic(self):
```

- Starts live microphone input.

---

```python
if self.source != "mic":
    return
```

- If this processor is not mic-based, do nothing.

---

```python
if not HAS_SD:
    raise RuntimeError("sounddevice is required for microphone input")
```

- If `sounddevice` is missing, raise an error.

---

```python
if self.mic_stream is not None:
    return
```

- If mic stream already started, do nothing.

---

### Callback function
```python
def callback(indata, frames, time_info, status):
    try:
        self.mic_queue.put_nowait(indata[:, 0].copy())
    except queue.Full:
        pass
```

- This function runs automatically whenever mic audio arrives.
- `indata` contains incoming audio samples.
- `indata[:, 0]` means first channel.
- `.copy()` makes a separate copy.
- Put it into the queue.
- If queue is full, ignore the chunk.

---

### Create stream
```python
self.mic_stream = sd.InputStream(
    channels=1,
    samplerate=self.sample_rate,
    blocksize=self.hop_size,
    callback=callback
)
```

- Open microphone stream.
- Use:
  - 1 channel
  - object sample rate
  - block size equal to hop size
  - callback function for receiving data

---

### Start stream
```python
self.mic_stream.start()
```

- Begin live microphone capture.

---

### `stop_mic`
```python
def stop_mic(self):
    if self.mic_stream is not None:
        self.mic_stream.stop()
        self.mic_stream.close()
        self.mic_stream = None
```

- Stops and closes microphone stream safely.
- Then clears the variable.

---

## `get_next_frame`

### Start
```python
def get_next_frame(self):
```

- Returns the next frame of audio samples.

---

### Microphone branch
```python
if self.source == "mic":
```

- If source is microphone, use mic buffer logic.

---

```python
try:
    while len(self.mic_buffer) < self.frame_size:
        chunk = self.mic_queue.get(timeout=0.05)
        self.mic_buffer = np.concatenate([self.mic_buffer, chunk])
except queue.Empty:
    return np.zeros(self.frame_size, dtype=np.float32)
```

- Keep taking chunks from queue until we have enough samples for one frame.
- Append them into `mic_buffer`.
- If queue is empty for too long:
  - return a silent frame of zeros

---

```python
frame = self.mic_buffer[:self.frame_size]
self.mic_buffer = self.mic_buffer[self.hop_size:]
return frame
```

- Take first `frame_size` samples as the frame.
- Remove only `hop_size` samples from the buffer.
- This creates overlapping frames.

Why overlap?
- Better signal analysis.
- Common in audio DSP.

---

### File branch
```python
if self.audio_data is None:
    return None
```

- If no file loaded, no frame is available.

---

```python
end = self.position + self.frame_size
if end > len(self.audio_data):
    return None
```

- Compute end index of requested frame.
- If it goes past file length, file is done.

---

```python
frame = self.audio_data[self.position:end]
self.position += self.hop_size
return frame
```

- Extract frame from current position.
- Move position forward by hop size.
- Return frame.

---

## `process_frame`

### Start
```python
def process_frame(self, frame):
```

- Takes one frame and computes audio features.

---

```python
if frame is None or len(frame) == 0:
    return 0.0, 0.0, np.zeros(self.n_bands), False
```

- If frame is invalid:
  - amplitude = 0
  - frequency = 0
  - spectrum = zeros
  - beat = False

---

### RMS amplitude
```python
amplitude = float(np.sqrt(np.mean(frame ** 2)))
amplitude = float(np.clip(amplitude * 3.0, 0.0, 1.0))
```

- `frame ** 2`: square samples
- `np.mean(...)`: average power
- `np.sqrt(...)`: root mean square = RMS
- Then multiply by 3.0 to make visualization stronger
- Clip between 0 and 1

---

### Windowing and FFT
```python
windowed = frame * np.hanning(len(frame))
spectrum = np.abs(rfft(windowed))
freqs = rfftfreq(len(frame), d=1.0 / self.sample_rate)
```

- `np.hanning(...)` creates a Hann window
- Multiplying frame by window reduces FFT edge artifacts
- `rfft` computes frequency content
- `np.abs(...)` gets magnitude spectrum
- `rfftfreq(...)` gives actual frequency values in Hz

---

### Dominant frequency
```python
if len(spectrum) > 1:
    peak_idx = np.argmax(spectrum[1:]) + 1
    frequency = float(freqs[peak_idx])
else:
    frequency = 0.0
```

- Find index of largest spectral magnitude
- `spectrum[1:]` skips bin 0 (DC component)
- `+1` fixes index after skipping
- Convert peak index into Hz
- If spectrum too small, use 0 Hz

---

### Spectrum bands and beat
```python
bands = self._compute_bands(spectrum)
beat = self._detect_beat(amplitude)
```

- Reduce full spectrum into 32 bands
- Detect whether current frame is a beat

---

### Update frame count
```python
self.frame_counter += 1
return amplitude, frequency, bands, beat
```

- Increase processed frame count
- Return results

---

## `_compute_bands`

### Start
```python
def _compute_bands(self, spectrum):
```

- Converts full FFT into smaller number of bands.

---

```python
n = len(spectrum)
if n == 0:
    return np.zeros(self.n_bands)
```

- If empty spectrum, return zeros.

---

```python
edges = np.logspace(0, np.log10(n), self.n_bands + 1).astype(int)
edges = np.clip(edges, 0, n)
```

- Create logarithmically spaced band edges.
- Log spacing gives more detail in lower frequencies.

---

```python
bands = np.zeros(self.n_bands, dtype=np.float32)
for i in range(self.n_bands):
    lo = edges[i]
    hi = max(lo + 1, edges[i + 1])
    hi = min(hi, n)
    bands[i] = np.mean(spectrum[lo:hi])
```

- Create array for band values.
- For each band:
  - get lower edge
  - get upper edge
  - make sure at least one bin is included
  - compute mean magnitude for that band

---

```python
m = np.max(bands)
if m > 0:
    bands = bands / m
return bands
```

- Normalize band values by their max.
- This keeps values between 0 and 1.

---

## `_detect_beat`

### Start
```python
def _detect_beat(self, energy):
```

- Detect whether current energy level looks like a beat.

---

```python
self.energy_history.append(energy)
```

- Add current amplitude to recent energy history.

---

```python
if len(self.energy_history) < 10:
    return False
```

- Need enough history first.
- If too few frames, do not detect beats yet.

---

```python
avg = np.mean(self.energy_history)
is_beat = (energy > avg * 1.5) and (energy > 0.15)
```

- Compute average recent energy.
- Consider this frame a beat if:
  - energy is 1.5 times bigger than average
  - and energy is above 0.15 absolute threshold

---

```python
if is_beat and (self.frame_counter - self.last_beat_frame) > 8:
    self.last_beat_frame = self.frame_counter
    return True
```

- Prevent too many beat detections too close together.
- If enough frames passed since last beat:
  - record this beat
  - return `True`

---

```python
return False
```

- Otherwise not a beat.

---

## `reset`

### Start
```python
def reset(self):
```

- Reset processor state.

---

```python
self.position = 0
self.frame_counter = 0
self.last_beat_frame = -999
self.energy_history.clear()
self.mic_buffer = np.zeros(0, dtype=np.float32)
```

- Reset file reading position
- Reset frame counter
- Reset beat tracking
- Clear energy history
- Clear microphone buffer

---

```python
while not self.mic_queue.empty():
    try:
        self.mic_queue.get_nowait()
    except Exception:
        break
```

- Empty anything still left in mic queue.
- This prevents old audio chunks from mixing with new session.

---

# File 3: `visualizer.py` explained line by line

## Full code

```python
import pygame
import math
import random
import colorsys
import os
import time


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "size", "color")

    def __init__(self, x, y, vx, vy, life, size, color):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = life
        self.max_life = life
        self.size = size
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.98
        self.vy *= 0.98
        self.life -= 1

    def alive(self):
        return self.life > 0


class Visualizer:
    """
    Modes:
        0 -> Particle Burst
        1 -> Spectrum Bars
        2 -> Mandala
        3 -> Waveform Ribbon
        4 -> Nebula
    """

    MODE_NAMES = [
        "Particle Burst",
        "Spectrum Bars",
        "Mandala",
        "Waveform Ribbon",
        "Nebula"
    ]

    def __init__(self, width=1000, height=700):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height), pygame.DOUBLEBUF)
        pygame.display.set_caption("Audio Visual Art — PRO")
        self.clock = pygame.time.Clock()

        self.amplitude = 0.0
        self.frequency = 0.0
        self.spectrum = [0.0] * 32
        self.beat = False

        self.mode = 0
        self.running = True
        self.fullscreen = False
        self.angle = 0.0
        self.hue = 0.0
        self.particles = []
        self.waveform_history = []
        self.beat_flash = 0.0

        self.fade_layer = pygame.Surface((width, height), pygame.SRCALPHA)
        self.fade_layer.fill((10, 10, 20, 35))

        self.font = pygame.font.SysFont("Arial", 18, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 13)

    def update(self, amplitude, frequency, spectrum=None, beat=False):
        self.amplitude = amplitude
        self.frequency = frequency
        if spectrum is not None:
            self.spectrum = spectrum
        self.beat = beat

        target_hue = min(frequency / 2000.0, 1.0)
        self.hue += (target_hue - self.hue) * 0.05
        self.angle += 0.01 + amplitude * 0.05

        self.waveform_history.append(amplitude)
        if len(self.waveform_history) > self.width // 2:
            self.waveform_history.pop(0)

        if beat:
            self.beat_flash = 1.0
            self._spawn_beat_particles()

        self.beat_flash *= 0.9

    def switch_mode(self, mode=None):
        if mode is None:
            self.mode = (self.mode + 1) % len(self.MODE_NAMES)
        else:
            self.mode = mode % len(self.MODE_NAMES)

    def draw(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.switch_mode()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_f:
                    self._toggle_fullscreen()
                elif event.key == pygame.K_s:
                    self._screenshot()
                elif pygame.K_1 <= event.key <= pygame.K_5:
                    self.switch_mode(event.key - pygame.K_1)

        self.screen.blit(self.fade_layer, (0, 0))

        if self.beat_flash > 0.05:
            flash = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            alpha = int(40 * self.beat_flash)
            flash.fill((255, 255, 255, alpha))
            self.screen.blit(flash, (0, 0))

        color = self._hue_color(self.hue)

        if self.mode == 0:
            self._draw_particles(color)
        elif self.mode == 1:
            self._draw_spectrum_bars(color)
        elif self.mode == 2:
            self._draw_mandala(color)
        elif self.mode == 3:
            self._draw_waveform_ribbon(color)
        elif self.mode == 4:
            self._draw_nebula(color)

        self._draw_hud()
        pygame.display.flip()
        self.clock.tick(60)

    def quit(self):
        pygame.quit()

    def _hue_color(self, h, s=0.85, v=1.0):
        r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
        return (int(r * 255), int(g * 255), int(b * 255))

    def _spawn_beat_particles(self):
        cx, cy = self.width // 2, self.height // 2
        count = int(30 + self.amplitude * 80)

        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(2, 8) * (1 + self.amplitude)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life = random.randint(40, 80)
            size = random.randint(2, 5)
            hue = (self.hue + random.uniform(-0.1, 0.1)) % 1.0
            color = self._hue_color(hue)
            self.particles.append(Particle(cx, cy, vx, vy, life, size, color))

        if len(self.particles) > 800:
            self.particles = self.particles[-800:]

    def _draw_particles(self, color):
        if self.amplitude > 0.05:
            cx, cy = self.width // 2, self.height // 2
            for _ in range(int(self.amplitude * 6)):
                a = random.uniform(0, math.tau)
                s = random.uniform(1, 4)
                self.particles.append(
                    Particle(
                        cx, cy,
                        math.cos(a) * s,
                        math.sin(a) * s,
                        random.randint(30, 60),
                        random.randint(2, 4),
                        color
                    )
                )

        new_particles = []
        for p in self.particles:
            p.update()
            if p.alive():
                alpha_ratio = p.life / p.max_life
                r = int(p.color[0] * alpha_ratio)
                g = int(p.color[1] * alpha_ratio)
                b = int(p.color[2] * alpha_ratio)
                pygame.draw.circle(self.screen, (r, g, b), (int(p.x), int(p.y)), p.size)
                new_particles.append(p)

        self.particles = new_particles

    def _draw_spectrum_bars(self, color):
        n = len(self.spectrum)
        if n == 0:
            return

        bar_w = self.width / n
        cy = self.height // 2

        for i, val in enumerate(self.spectrum):
            h = int(val * self.height * 0.45)
            x = int(i * bar_w)
            hue = (self.hue + i / n * 0.3) % 1.0
            c = self._hue_color(hue)

            pygame.draw.rect(self.screen, c, (x + 2, cy - h, max(1, int(bar_w - 4)), h))
            pygame.draw.rect(self.screen, c, (x + 2, cy, max(1, int(bar_w - 4)), h))

    def _draw_mandala(self, color):
        cx, cy = self.width // 2, self.height // 2
        layers = 6
        spikes = 12
        base_r = 50 + self.amplitude * 200

        for L in range(layers):
            r_outer = base_r + L * 25
            r_inner = r_outer * 0.5
            pts = []

            for i in range(spikes * 2):
                rr = r_outer if i % 2 == 0 else r_inner
                theta = self.angle * (1 + L * 0.2) + i * math.pi / spikes
                x = cx + rr * math.cos(theta)
                y = cy + rr * math.sin(theta)
                pts.append((x, y))

            hue = (self.hue + L * 0.08) % 1.0
            c = self._hue_color(hue)
            pygame.draw.polygon(self.screen, c, pts, width=2)

    def _draw_waveform_ribbon(self, color):
        if len(self.waveform_history) < 2:
            return

        cy = self.height // 2
        pts_top, pts_bot = [], []

        for i, v in enumerate(self.waveform_history):
            x = i * (self.width / max(1, len(self.waveform_history)))
            offset = v * self.height * 0.4
            pts_top.append((x, cy - offset))
            pts_bot.append((x, cy + offset))

        if len(pts_top) >= 2:
            pygame.draw.lines(self.screen, color, False, pts_top, 3)
            pygame.draw.lines(self.screen, color, False, pts_bot, 3)

    def _draw_nebula(self, color):
        cx, cy = self.width // 2, self.height // 2
        max_r = int(80 + self.amplitude * 350)
        layers = 25

        for i in range(layers, 0, -1):
            r = int(max_r * i / layers)
            ratio = i / layers
            hue = (self.hue + ratio * 0.2) % 1.0
            c = self._hue_color(hue, s=0.8, v=ratio)
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            alpha = int(30 * (1 - ratio) + 10)
            pygame.draw.circle(surf, (*c, alpha), (r, r), r)
            self.screen.blit(surf, (cx - r, cy - r), special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_hud(self):
        mode_text = f"Mode {self.mode + 1}/5: {self.MODE_NAMES[self.mode]}"
        info = self.font.render(mode_text, True, (255, 255, 255))
        self.screen.blit(info, (15, 12))

        hint = self.small_font.render(
            "SPACE: next  |  1-5: select  |  F: fullscreen  |  S: screenshot  |  ESC: quit",
            True,
            (180, 180, 200)
        )
        self.screen.blit(hint, (15, self.height - 22))

        if self.beat_flash > 0.3:
            beat_text = self.font.render("BEAT", True, (255, 80, 120))
            self.screen.blit(beat_text, (self.width - 90, 12))

    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        flags = pygame.FULLSCREEN if self.fullscreen else pygame.DOUBLEBUF
        self.screen = pygame.display.set_mode((self.width, self.height), flags)

    def _screenshot(self):
        os.makedirs("screenshots", exist_ok=True)
        path = f"screenshots/art_{int(time.time())}.png"
        pygame.image.save(self.screen, path)
        print(f"Saved: {path}")
```

---

## Important overview before line-by-line

This file has **2 classes**:

1. `Particle`
2. `Visualizer`

### `Particle`
Used for visual effects like sparks.

### `Visualizer`
Used to:
- open Pygame window
- receive audio values
- draw one of 5 modes

---

## Imports

```python
import pygame
import math
import random
import colorsys
import os
import time
```

- `pygame`: drawing and window management
- `math`: sin, cos, pi, tau
- `random`: random particles
- `colorsys`: convert HSV to RGB
- `os`: create screenshot folder
- `time`: timestamp filenames

---

## `Particle` class

### Class line
```python
class Particle:
```

- Defines a particle object.

---

### `__slots__`
```python
__slots__ = ("x", "y", "vx", "vy", "life", "max_life", "size", "color")
```

- `__slots__` restricts allowed attributes.
- Saves memory.
- This is useful when many particles exist.

---

### Constructor
```python
def __init__(self, x, y, vx, vy, life, size, color):
```

- A particle needs:
  - position: `x`, `y`
  - velocity: `vx`, `vy`
  - lifespan: `life`
  - size
  - color

---

```python
self.x, self.y = x, y
self.vx, self.vy = vx, vy
self.life = life
self.max_life = life
self.size = size
self.color = color
```

- Save all particle properties.
- `max_life` keeps original lifespan for fading.

---

### `update`
```python
def update(self):
    self.x += self.vx
    self.y += self.vy
    self.vx *= 0.98
    self.vy *= 0.98
    self.life -= 1
```

- Move particle by velocity.
- Reduce velocity a little for friction/drag.
- Decrease lifetime each frame.

---

### `alive`
```python
def alive(self):
    return self.life > 0
```

- Returns `True` if particle still exists.

---

## `Visualizer` class

### Class docstring
Explains the 5 modes:
- 0: Particle Burst
- 1: Spectrum Bars
- 2: Mandala
- 3: Waveform Ribbon
- 4: Nebula

---

### `MODE_NAMES`
```python
MODE_NAMES = [
    "Particle Burst",
    "Spectrum Bars",
    "Mandala",
    "Waveform Ribbon",
    "Nebula"
]
```

- A class-level list of mode names.
- Used for HUD display.

---

## Constructor

### Start
```python
def __init__(self, width=1000, height=700):
```

- Builds visualizer window.
- Default size = 1000 x 700.

---

### Pygame init
```python
pygame.init()
```

- Initialize Pygame.

---

### Window setup
```python
self.width = width
self.height = height
self.screen = pygame.display.set_mode((width, height), pygame.DOUBLEBUF)
self.screen = pygame.display.set_mode((width, height), pygame.DOUBLEBUF)
pygame.display.set_caption("Audio Visual Art — PRO")
self.clock = pygame.time.Clock()
```

- Save window width and height.
- Create display surface.
- `DOUBLEBUF` helps smooth rendering.
- Set window title.
- `clock` helps control frame rate.

Note: only one `set_mode` line is needed; conceptually that line creates the drawing surface.

---

### Audio state
```python
self.amplitude = 0.0
self.frequency = 0.0
self.spectrum = [0.0] * 32
self.beat = False
```

- Stores latest audio values received from main program.

---

### Visual state
```python
self.mode = 0
self.running = True
self.fullscreen = False
self.angle = 0.0
self.hue = 0.0
self.particles = []
self.waveform_history = []
self.beat_flash = 0.0
```

- `mode`: which visualization mode is active
- `running`: whether window should stay open
- `fullscreen`: fullscreen state
- `angle`: used for rotation
- `hue`: color value in HSV
- `particles`: list of particles
- `waveform_history`: stores previous amplitudes
- `beat_flash`: flash effect strength

---

### Fade layer
```python
self.fade_layer = pygame.Surface((width, height), pygame.SRCALPHA)
self.fade_layer.fill((10, 10, 20, 35))
```

- Create transparent surface for fading trails.
- Alpha = 35 means partially transparent.
- Each frame this layer darkens the previous drawing a bit instead of hard-clearing the screen.

---

### Fonts
```python
self.font = pygame.font.SysFont("Arial", 18, bold=True)
self.small_font = pygame.font.SysFont("Arial", 13)
```

- Fonts for HUD text.

---

## `update`

```python
def update(self, amplitude, frequency, spectrum=None, beat=False):
```

- Receives new audio information.

---

```python
self.amplitude = amplitude
self.frequency = frequency
if spectrum is not None:
    self.spectrum = spectrum
self.beat = beat
```

- Save new incoming values.

---

```python
target_hue = min(frequency / 2000.0, 1.0)
```

- Convert frequency into a hue value between 0 and 1.
- Any value above 2000 Hz is clamped to 1.0.

---

```python
self.hue += (target_hue - self.hue) * 0.05
```

- Smoothly move current hue toward target hue.

---

```python
self.angle += 0.01 + amplitude * 0.05
```

- Increase angle each frame.
- Louder sound increases rotation speed.

---

```python
self.waveform_history.append(amplitude)
if len(self.waveform_history) > self.width // 2:
    self.waveform_history.pop(0)
```

- Add current amplitude to history.
- If history gets too long, remove oldest item.

---

```python
if beat:
    self.beat_flash = 1.0
    self._spawn_beat_particles()
```

- On beat:
  - trigger flash
  - spawn particles

---

```python
self.beat_flash *= 0.9
```

- Beat flash fades every frame.

---

## `switch_mode`

```python
def switch_mode(self, mode=None):
```

- Changes active visualization mode.

---

```python
if mode is None:
    self.mode = (self.mode + 1) % len(self.MODE_NAMES)
else:
    self.mode = mode % len(self.MODE_NAMES)
```

- If no mode given:
  - go to next mode
- If mode given:
  - use that specific mode
- `%` keeps mode inside valid range

---

## `draw`

This is the most important visual function.

### Event loop
```python
for event in pygame.event.get():
```

- Get all Pygame events like key presses and window close.

---

```python
if event.type == pygame.QUIT:
    self.running = False
```

- If user closes window, stop loop.

---

```python
elif event.type == pygame.KEYDOWN:
```

- If a key is pressed, check which one.

---

```python
if event.key == pygame.K_SPACE:
    self.switch_mode()
```

- Space bar = next mode.

---

```python
elif event.key == pygame.K_ESCAPE:
    self.running = False
```

- Escape = quit.

---

```python
elif event.key == pygame.K_f:
    self._toggle_fullscreen()
```

- `F` key toggles fullscreen.

---

```python
elif event.key == pygame.K_s:
    self._screenshot()
```

- `S` key saves screenshot.

---

```python
elif pygame.K_1 <= event.key <= pygame.K_5:
    self.switch_mode(event.key - pygame.K_1)
```

- Number keys 1 to 5 select a specific mode.

---

### Fade old frame
```python
self.screen.blit(self.fade_layer, (0, 0))
```

- Draw the fade layer over the whole screen.
- This creates trailing effects.

---

### Beat flash overlay
```python
if self.beat_flash > 0.05:
    flash = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
    alpha = int(40 * self.beat_flash)
    flash.fill((255, 255, 255, alpha))
    self.screen.blit(flash, (0, 0))
```

- If beat flash is still strong enough:
  - create translucent white overlay
  - brightness depends on beat flash value
  - draw it on screen

---

### Main drawing color
```python
color = self._hue_color(self.hue)
```

- Convert current hue into RGB color.

---

### Mode selection
```python
if self.mode == 0:
    self._draw_particles(color)
elif self.mode == 1:
    self._draw_spectrum_bars(color)
elif self.mode == 2:
    self._draw_mandala(color)
elif self.mode == 3:
    self._draw_waveform_ribbon(color)
elif self.mode == 4:
    self._draw_nebula(color)
```

- Call drawing function based on current mode.

---

### HUD and screen update
```python
self._draw_hud()
pygame.display.flip()
self.clock.tick(60)
```

- Draw text overlay
- Show rendered frame on screen
- Limit to 60 FPS

---

## `quit`
```python
def quit(self):
    pygame.quit()
```

- Close Pygame safely.

---

## `_hue_color`
```python
def _hue_color(self, h, s=0.85, v=1.0):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))
```

- Convert HSV to RGB.
- Hue wraps using `% 1.0`.
- Multiply by 255 because Pygame uses RGB values 0–255.

---

## `_spawn_beat_particles`

```python
cx, cy = self.width // 2, self.height // 2
count = int(30 + self.amplitude * 80)
```

- Center of screen.
- Number of particles depends on amplitude.

---

```python
for _ in range(count):
```

- Create that many particles.

---

```python
angle = random.uniform(0, math.tau)
speed = random.uniform(2, 8) * (1 + self.amplitude)
vx = math.cos(angle) * speed
vy = math.sin(angle) * speed
```

- Random direction.
- Random speed scaled by amplitude.
- Convert polar direction to x/y velocity.

---

```python
life = random.randint(40, 80)
size = random.randint(2, 5)
hue = (self.hue + random.uniform(-0.1, 0.1)) % 1.0
color = self._hue_color(hue)
```

- Random lifetime
- Random size
- Slightly varied