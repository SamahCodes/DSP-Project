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