import os
import sys
import time
import queue
from enum import Enum
import numpy as np

# Ensure vocalis root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vocalis.audio.microphone import MicrophoneStream
from vocalis.vad.detector import VADDetector
from vocalis.wakeword.detector import WakeWordDetector
from vocalis.stt.detector import STTDetector
from vocalis.monitoring.metrics import MetricsMonitor
from vocalis.commands.parser import CommandParser, ParsedCommand
from vocalis.commands.executor import CommandExecutor, ExecutionResult
from vocalis.commands.registry import CommandIntent


class SystemState(Enum):
    IDLE = "🎧 Listening for wake word"
    WAKE_WORD_DETECTED = "⚡ Wake word detected!"
    LISTENING = "👂 Active listening..."
    RECORDING = "🎙️ Recording speech..."
    TRANSCRIBING = "🧠 Transcribing speech..."
    UNDERSTANDING = "🔍 Understanding command..."
    EXECUTING = "⚙️ Executing action..."
    RESULT = "📝 Result ready"


def render_dashboard(
    state: SystemState,
    is_speaking: bool,
    ww_detected: bool,
    ww_model_name: str,
    ww_score: float,
    transcribed_text: str,
    intent_str: str,
    target_str: str,
    action_str: str,
    result_str: str,
    vad_latency_ms: float,
    ww_latency_ms: float,
    stt_latency_ms: float,
    parse_latency_ms: float,
    exec_latency_ms: float,
    total_activation_time_ms: float,
    speech_duration_s: float,
    cpu_percent: float,
    memory_mb: float,
    target_model: str,
    stt_model_name: str
):
    """
    Renders a real-time, non-flickering V4 dashboard in the terminal.
    """
    vad_text = "🔊 Speech detected" if is_speaking else "🔇 Silence"
    
    if ww_detected:
        ww_status = f"⚡ DETECTED [{ww_model_name}] ({ww_score:.2f})"
    else:
        ww_status = f"💤 Target: {target_model} ({ww_score:.2f})"

    if state == SystemState.TRANSCRIBING:
        stt_status = "🧠 Transcribing audio..."
    elif state in (SystemState.UNDERSTANDING, SystemState.EXECUTING, SystemState.RESULT) or transcribed_text:
        stt_status = "✅ Completed"
    else:
        stt_status = f"⚡ Ready ({stt_model_name})"

    text_display = f'"{transcribed_text}"' if transcribed_text else "(None)"
    intent_display = intent_str if intent_str else "--"
    target_display = target_str if target_str else "--"
    action_display = action_str if action_str else "--"
    result_display = result_str if result_str else "--"

    stt_lat_str = f"{stt_latency_ms:.1f} ms" if stt_latency_ms > 0 else "-- ms"
    parse_lat_str = f"{parse_latency_ms:.1f} ms" if parse_latency_ms > 0 else "-- ms"
    exec_lat_str = f"{exec_latency_ms:.1f} ms" if exec_latency_ms > 0 else "-- ms"
    total_lat_str = f"{total_activation_time_ms:.1f} ms" if total_activation_time_ms > 0 else "-- ms"
    speech_dur_str = f"{speech_duration_s:.2f} s" if speech_duration_s > 0 else "-- s"

    # \033[H repositions terminal cursor to row 1, col 1 (overwriting in-place)
    dashboard = (
        "\033[H"
        "╔════════════════════════════════════════════════════════════╗\n"
        "║                         VOCALIS V4                         ║\n"
        "║       Local Voice Command Assistant (VAD+WW+STT)           ║\n"
        "╚════════════════════════════════════════════════════════════╝\n\n"
        f"Microphone:   Active (16 kHz Mono)                           \n"
        f"Engine State: {state.value:<45}\n\n"
        f"VAD Status:   {vad_text:<25} [Latency: {vad_latency_ms:.1f} ms]        \n"
        f"Wake-Word:    {ww_status:<30} [Latency: {ww_latency_ms:.1f} ms]   \n"
        f"STT Engine:   {stt_status:<45}\n\n"
        "──────────────────────────────────────────────────────────────\n"
        f"Transcribed:  {text_display:<45}\n"
        f"Intent:       {intent_display:<45}\n"
        f"Target:       {target_display:<45}\n"
        f"Action:       {action_display:<45}\n"
        f"Result:       {result_display:<45}\n"
        "──────────────────────────────────────────────────────────────\n"
        f"STT Latency:          {stt_lat_str:<25}\n"
        f"Command Parsing:      {parse_lat_str:<25}\n"
        f"Execution Latency:    {exec_lat_str:<25}\n"
        f"Total Activation Time:{total_lat_str:<25}\n"
        f"Speech Duration:      {speech_dur_str:<25}\n"
        "──────────────────────────────────────────────────────────────\n"
        f"CPU Usage:            {cpu_percent:.1f}%                      \n"
        f"Memory Usage:         {memory_mb:.1f} MB                     \n"
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
    print("Initializing Vocalis V4 Engine (VAD + Wake-Word + Local STT + Commands)...")

    mic = None
    try:
        # 1. Initialize performance monitoring
        monitor = MetricsMonitor()

        # 2. Initialize VAD detector (Silero VAD)
        print("  - Loading Silero VAD detector...")
        vad_detector = VADDetector(sample_rate=16000, threshold=0.5)

        # 3. Initialize Wake-Word detector (OpenWakeWord)
        target_keyword = "hey_jarvis"
        print(f"  - Loading OpenWakeWord detector (Target: {target_keyword})...")
        ww_detector = WakeWordDetector(threshold=0.5, target_model=target_keyword)

        # 4. Initialize Local Speech-to-Text detector (faster-whisper)
        stt_model_name = "tiny.en"
        print(f"  - Loading Local Speech-to-Text engine ({stt_model_name})...")
        stt_detector = STTDetector(model_size=stt_model_name, device="cpu", compute_type="int8")

        # 5. Initialize Command Parser and Executor
        print("  - Loading Command Parser & Executor...")
        parser = CommandParser()
        executor = CommandExecutor()

        # 6. Initialize microphone input stream (16kHz, 512 samples/chunk = ~32ms)
        print("  - Accessing microphone input stream...")
        mic = MicrophoneStream(sample_rate=16000, chunk_size=512)
        mic.start()

        # Clear screen after resource initialization
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

        state = SystemState.IDLE
        audio_buffer = []
        silence_chunks = 0
        
        activation_start_time = 0.0
        listening_start_time = 0.0
        speech_start_time = 0.0
        result_start_time = 0.0

        last_ww_model = ""
        last_ww_score = 0.0
        last_ww_detected_time = 0.0

        transcribed_text = ""
        intent_str = ""
        target_str = ""
        action_str = ""
        result_str = ""

        stt_latency_ms = 0.0
        parse_latency_ms = 0.0
        exec_latency_ms = 0.0
        total_activation_time_ms = 0.0
        speech_duration_s = 0.0

        should_exit_app = False

        # Continuous state-driven audio processing loop
        while True:
            try:
                chunk = mic.get_chunk(timeout=0.5)
            except queue.Empty:
                continue

            # Measure Stage 1: VAD evaluation
            is_speaking, vad_latency_ms = monitor.measure_latency(vad_detector.is_speech, chunk)

            # Measure Stage 2: Wake-Word evaluation
            (is_ww, model_name, score), ww_latency_ms = monitor.measure_latency(
                ww_detector.is_wakeword_detected, chunk
            )

            current_time = time.time()

            if is_ww:
                last_ww_model = model_name
                last_ww_score = score
                last_ww_detected_time = current_time

            display_ww = (current_time - last_ww_detected_time) < 2.0

            # State Machine Transitions
            if state == SystemState.IDLE:
                if is_ww:
                    state = SystemState.WAKE_WORD_DETECTED
                    activation_start_time = current_time
                    listening_start_time = current_time

            elif state == SystemState.WAKE_WORD_DETECTED:
                state = SystemState.LISTENING

            elif state == SystemState.LISTENING:
                if is_speaking:
                    state = SystemState.RECORDING
                    audio_buffer = [chunk]
                    silence_chunks = 0
                    speech_start_time = current_time
                elif current_time - listening_start_time > 5.0:
                    # Timeout if no speech detected after wake word
                    state = SystemState.IDLE

            elif state == SystemState.RECORDING:
                audio_buffer.append(chunk)
                if is_speaking:
                    silence_chunks = 0
                else:
                    silence_chunks += 1
                    # ~32ms per chunk (512 / 16000). 1.0s silence threshold = ~31 chunks
                    silence_duration = silence_chunks * (len(chunk) / 16000.0)
                    if silence_duration >= 1.0:
                        speech_duration_s = max(0.0, (current_time - speech_start_time) - silence_duration)
                        state = SystemState.TRANSCRIBING

            elif state == SystemState.TRANSCRIBING:
                # Render dashboard immediately so user sees "Transcribing..." state
                system_metrics = monitor.get_system_metrics()
                render_dashboard(
                    state=state,
                    is_speaking=is_speaking,
                    ww_detected=display_ww,
                    ww_model_name=last_ww_model,
                    ww_score=last_ww_score,
                    transcribed_text=transcribed_text,
                    intent_str=intent_str,
                    target_str=target_str,
                    action_str=action_str,
                    result_str=result_str,
                    vad_latency_ms=vad_latency_ms,
                    ww_latency_ms=ww_latency_ms,
                    stt_latency_ms=stt_latency_ms,
                    parse_latency_ms=parse_latency_ms,
                    exec_latency_ms=exec_latency_ms,
                    total_activation_time_ms=total_activation_time_ms,
                    speech_duration_s=speech_duration_s,
                    cpu_percent=system_metrics["cpu_percent"],
                    memory_mb=system_metrics["memory_mb"],
                    target_model=target_keyword,
                    stt_model_name=stt_model_name
                )

                if len(audio_buffer) > 0:
                    recorded_audio = np.concatenate(audio_buffer)
                    text_result, stt_latency_ms = monitor.measure_latency(
                        stt_detector.transcribe, recorded_audio, 16000
                    )
                    transcribed_text = text_result
                else:
                    transcribed_text = ""
                    stt_latency_ms = 0.0

                audio_buffer = []
                state = SystemState.UNDERSTANDING

            elif state == SystemState.UNDERSTANDING:
                # Render dashboard so user sees "Understanding..." state
                system_metrics = monitor.get_system_metrics()
                render_dashboard(
                    state=state,
                    is_speaking=is_speaking,
                    ww_detected=display_ww,
                    ww_model_name=last_ww_model,
                    ww_score=last_ww_score,
                    transcribed_text=transcribed_text,
                    intent_str=intent_str,
                    target_str=target_str,
                    action_str=action_str,
                    result_str=result_str,
                    vad_latency_ms=vad_latency_ms,
                    ww_latency_ms=ww_latency_ms,
                    stt_latency_ms=stt_latency_ms,
                    parse_latency_ms=parse_latency_ms,
                    exec_latency_ms=exec_latency_ms,
                    total_activation_time_ms=total_activation_time_ms,
                    speech_duration_s=speech_duration_s,
                    cpu_percent=system_metrics["cpu_percent"],
                    memory_mb=system_metrics["memory_mb"],
                    target_model=target_keyword,
                    stt_model_name=stt_model_name
                )

                parsed_cmd, parse_latency_ms = monitor.measure_latency(parser.parse, transcribed_text)
                intent_str = parsed_cmd.intent.value
                target_str = parsed_cmd.target
                action_str = parsed_cmd.action_description

                state = SystemState.EXECUTING

            elif state == SystemState.EXECUTING:
                # Render dashboard so user sees "Executing..." state
                system_metrics = monitor.get_system_metrics()
                render_dashboard(
                    state=state,
                    is_speaking=is_speaking,
                    ww_detected=display_ww,
                    ww_model_name=last_ww_model,
                    ww_score=last_ww_score,
                    transcribed_text=transcribed_text,
                    intent_str=intent_str,
                    target_str=target_str,
                    action_str=action_str,
                    result_str=result_str,
                    vad_latency_ms=vad_latency_ms,
                    ww_latency_ms=ww_latency_ms,
                    stt_latency_ms=stt_latency_ms,
                    parse_latency_ms=parse_latency_ms,
                    exec_latency_ms=exec_latency_ms,
                    total_activation_time_ms=total_activation_time_ms,
                    speech_duration_s=speech_duration_s,
                    cpu_percent=system_metrics["cpu_percent"],
                    memory_mb=system_metrics["memory_mb"],
                    target_model=target_keyword,
                    stt_model_name=stt_model_name
                )

                exec_result, exec_latency_ms = monitor.measure_latency(executor.execute, parsed_cmd)
                result_str = exec_result.result_message
                should_exit_app = exec_result.should_exit
                total_activation_time_ms = (time.time() - activation_start_time) * 1000.0

                state = SystemState.RESULT
                result_start_time = time.time()

            elif state == SystemState.RESULT:
                # Hold RESULT state for 2 seconds before returning to IDLE
                if current_time - result_start_time >= 2.0:
                    if should_exit_app:
                        break
                    state = SystemState.IDLE

            system_metrics = monitor.get_system_metrics()
            render_dashboard(
                state=state,
                is_speaking=is_speaking,
                ww_detected=display_ww,
                ww_model_name=last_ww_model,
                ww_score=last_ww_score,
                transcribed_text=transcribed_text,
                intent_str=intent_str,
                target_str=target_str,
                action_str=action_str,
                result_str=result_str,
                vad_latency_ms=vad_latency_ms,
                ww_latency_ms=ww_latency_ms,
                stt_latency_ms=stt_latency_ms,
                parse_latency_ms=parse_latency_ms,
                exec_latency_ms=exec_latency_ms,
                total_activation_time_ms=total_activation_time_ms,
                speech_duration_s=speech_duration_s,
                cpu_percent=system_metrics["cpu_percent"],
                memory_mb=system_metrics["memory_mb"],
                target_model=target_keyword,
                stt_model_name=stt_model_name
            )

    except KeyboardInterrupt:
        sys.stdout.write("\n\n\033[KStopping Vocalis V4... Goodbye!\n")
        sys.stdout.flush()
    except Exception as err:
        sys.stdout.write(f"\n\nError initializing/running Vocalis V4: {err}\n")
        sys.stdout.flush()
        sys.exit(1)
    finally:
        if mic is not None:
            mic.stop()


if __name__ == "__main__":
    main()
