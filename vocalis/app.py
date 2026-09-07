import os
import sys
import time
import queue

from vocalis.audio.microphone import MicrophoneStream
from vocalis.vad.detector import VADDetector
from vocalis.monitoring.metrics import MetricsMonitor


def render_dashboard(is_speaking: bool, latency_ms: float, cpu_percent: float, memory_mb: float):
    """
    Renders a non-flickering, real-time dashboard in the terminal using ANSI escape codes.
    """
    status_text = "🔊 Voice detected" if is_speaking else "🔇 Silence"
    
    # \033[H repositions terminal cursor to row 1, col 1 (overwriting in-place)
    dashboard = (
        "\033[H"
        "╔══════════════════════════════╗\n"
        "║          VOCALIS V1          ║\n"
        "║   Voice Activity Detection   ║\n"
        "╚══════════════════════════════╝\n\n"
        "Microphone: Active              \n"
        "VAD: Active                     \n\n"
        f"Status: {status_text:<25}\n\n"
        f"Latency: {latency_ms:.1f} ms             \n"
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
    print("Initializing Vocalis V1 Voice Activation Engine...")

    mic = None
    try:
        # 1. Initialize performance monitoring
        monitor = MetricsMonitor()

        # 2. Initialize VAD detector (Silero VAD)
        detector = VADDetector(sample_rate=16000, threshold=0.5)

        # 3. Initialize microphone input stream (16kHz, 512 samples/chunk = ~32ms)
        mic = MicrophoneStream(sample_rate=16000, chunk_size=512)
        mic.start()

        # Clear screen again after initializing resources
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

        # 4. Continuous audio processing loop
        while True:
            try:
                # Retrieve audio chunk from queue (timeout allows checking Ctrl+C)
                chunk = mic.get_chunk(timeout=0.5)
            except queue.Empty:
                continue

            # Send chunk to VAD and measure processing latency
            is_speaking, latency_ms = monitor.measure_latency(detector.is_speech, chunk)

            # Get system CPU and Memory metrics
            system_metrics = monitor.get_system_metrics()

            # Render updated status dashboard
            render_dashboard(
                is_speaking=is_speaking,
                latency_ms=latency_ms,
                cpu_percent=system_metrics["cpu_percent"],
                memory_mb=system_metrics["memory_mb"]
            )

    except KeyboardInterrupt:
        sys.stdout.write("\n\n\033[KStopping Vocalis... Goodbye!\n")
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
