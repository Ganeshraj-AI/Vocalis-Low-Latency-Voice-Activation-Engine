import os
import sys
import time
import queue

from vocalis.audio.microphone import MicrophoneStream
from vocalis.vad.detector import VADDetector
from vocalis.wakeword.detector import WakeWordDetector
from vocalis.monitoring.metrics import MetricsMonitor


def render_dashboard(
    is_speaking: bool,
    ww_detected: bool,
    ww_model_name: str,
    ww_score: float,
    vad_latency_ms: float,
    ww_latency_ms: float,
    cpu_percent: float,
    memory_mb: float,
    target_model: str
):
    """
    Renders a real-time, non-flickering V2 dashboard in the terminal.
    """
    status_text = "🔊 Voice detected" if is_speaking else "🔇 Silence"
    
    if ww_detected:
        ww_text = f"⚡ WAKE WORD DETECTED! [{ww_model_name}] ({ww_score:.2f})"
    else:
        ww_text = f"💤 Listening for target trigger..."

    # \033[H repositions terminal cursor to row 1, col 1 (overwriting in-place)
    dashboard = (
        "\033[H"
        "╔══════════════════════════════╗\n"
        "║          VOCALIS V2          ║\n"
        "║     Wake-Word Detection      ║\n"
        "╚══════════════════════════════╝\n\n"
        "Microphone: Active              \n"
        "VAD: Active                     \n"
        f"Wake-Word Engine: Active (Target: {target_model})          \n\n"
        f"Status: {status_text:<30}\n"
        f"Wake-Word: {ww_text:<40}\n\n"
        f"VAD Latency: {vad_latency_ms:.1f} ms             \n"
        f"Wake-Word Latency: {ww_latency_ms:.1f} ms        \n"
        f"CPU: {cpu_percent:.1f}%                 \n"
        f"Memory: {memory_mb:.1f} MB              \n"
    )
    sys.stdout.write(dashboard)
    sys.stdout.flush()


def main():
    # Reconfigure stdout to UTF-8 to prevent Windows charmap encoding errors
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    # Enable ANSI VT100 processing in Windows console
    os.system("")
    
    # Clear screen once on startup
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()
    print("Initializing Vocalis V2 Engine (VAD + Wake-Word)...")

    mic = None
    try:
        # 1. Initialize performance monitoring
        monitor = MetricsMonitor()

        # 2. Initialize VAD detector (Silero VAD)
        vad_detector = VADDetector(sample_rate=16000, threshold=0.5)

        # 3. Initialize Wake-Word detector (OpenWakeWord)
        target_keyword = "hey_jarvis"
        ww_detector = WakeWordDetector(threshold=0.5, target_model=target_keyword)

        # 4. Initialize microphone input stream (16kHz, 512 samples/chunk = ~32ms)
        mic = MicrophoneStream(sample_rate=16000, chunk_size=512)
        mic.start()

        # Clear screen again after initializing resources
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

        # Trigger event state tracking (hold trigger display for 1.5 seconds)
        last_trigger_time = 0.0
        last_trigger_model = ""
        last_trigger_score = 0.0

        # 5. Continuous hierarchical audio processing loop
        while True:
            try:
                # Retrieve audio chunk from queue (timeout allows checking Ctrl+C)
                chunk = mic.get_chunk(timeout=0.5)
            except queue.Empty:
                continue

            # Stage 1: VAD evaluation
            is_speaking, vad_latency_ms = monitor.measure_latency(vad_detector.is_speech, chunk)

            # Stage 2: Wake-Word evaluation (fed continuously to update rolling feature window)
            (is_ww, model_name, score), ww_latency_ms = monitor.measure_latency(
                ww_detector.is_wakeword_detected, chunk
            )

            # Record trigger event if detected
            current_time = time.time()
            if is_ww:
                last_trigger_time = current_time
                last_trigger_model = model_name
                last_trigger_score = score

            # Check if trigger state should still be displayed (within 1.5s window)
            display_ww = (current_time - last_trigger_time) < 1.5

            # Get system CPU and Memory metrics
            system_metrics = monitor.get_system_metrics()

            # Render updated status dashboard
            render_dashboard(
                is_speaking=is_speaking,
                ww_detected=display_ww,
                ww_model_name=last_trigger_model,
                ww_score=last_trigger_score,
                vad_latency_ms=vad_latency_ms,
                ww_latency_ms=ww_latency_ms,
                cpu_percent=system_metrics["cpu_percent"],
                memory_mb=system_metrics["memory_mb"],
                target_model=target_keyword
            )

    except KeyboardInterrupt:
        sys.stdout.write("\n\n\033[KStopping Vocalis V2... Goodbye!\n")
        sys.stdout.flush()
    except Exception as err:
        sys.stdout.write(f"\n\nError: {err}\n")
        sys.stdout.flush()
        sys.exit(1)
    finally:
        if mic is not None:
            mic.stop()


if __name__ == "__main__":
    main()
