# Vocalis — Low-Latency Voice Activation Engine (V1)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![VAD: Silero](https://img.shields.io/badge/VAD-Silero%20VAD-orange.svg)](https://github.com/snakers4/silero-vad)

**Vocalis** is a lightweight, software-only voice activation engine built for low-latency real-time processing on edge devices and local hardware.

---

## 1. What is Vocalis?

Vocalis is a local audio processing engine designed to continuously monitor microphone input and detect voice activity with minimal latency, CPU overhead, and memory footprint. It operates entirely offline without sending audio data to external cloud services.

---

## 2. Connection to SIH26172

This project is inspired by **Smart India Hackathon (SIH) Problem Statement SIH26172: Low Latency and Efficient Voice Activator for Edge Devices**. 

While SIH26172 aims to build full-stack embedded voice activation systems for microcontrollers and edge chips, **Vocalis V1** focuses on building the foundational first layer: **Real-Time Voice Activity Detection (VAD)** in software to understand streaming audio pipelines, sample chunking, and low-latency inference.

---

## 3. What V1 Does

Vocalis V1 executes a continuous streaming pipeline:

```text
Microphone
    ↓
Audio Stream (16 kHz, Mono)
    ↓
Small Audio Chunk (512 samples / 32 ms)
    ↓
Voice Activity Detection (Silero VAD)
    ↓
┌───────────────┐
│               │
Voice           Silence
│               │
↓               ↓
Speaking        Listening
```

It renders a live, non-flickering terminal dashboard:

```text
╔══════════════════════════════╗
║          VOCALIS V1          ║
║   Voice Activity Detection   ║
╚══════════════════════════════╝

Microphone: Active
VAD: Active

Status: 🔊 Voice detected

Latency: 4.2 ms
CPU: 3.1%
Memory: 82.4 MB
```

---

## 4. What V1 Does NOT Do

V1 is strictly focused on mastering real-time audio chunking and VAD. It intentionally **does NOT include**:

* ❌ Wake-word detection ("Hey Vocalis")
* ❌ Speech-to-Text (STT) or speech recognition
* ❌ LLMs or AI assistants
* ❌ Cloud APIs or network communication
* ❌ Web / GUI frontends or mobile apps
* ❌ Embedded hardware / Microcontrollers (ESP32, Raspberry Pi)
* ❌ Databases or authentication

These capabilities are reserved for future iterations in the project roadmap.

---

## 5. System Architecture

```text
[ Microphone Hardware ]
          │
          ▼  (16 kHz Mono Audio Stream)
[ microphone.py ] ──(Pushes 512-sample float32 arrays)──► [ Thread-Safe Queue ]
                                                                 │
                                                          (Pulls Chunks)
                                                                 │
                                                                 ▼
                                                       [ detector.py ]
                                                    (Silero VAD Inference)
                                                                 │
                                                    ┌────────────┴────────────┐
                                                    ▼                         ▼
                                             Speech (True)             Silence (False)
                                                    │                         │
                                                    └────────────┬────────────┘
                                                                 │
                                                                 ▼
                                                       [ metrics.py ]
                                                  (Latency, CPU, Memory)
                                                                 │
                                                                 ▼
                                                          [ app.py ]
                                                  (Terminal Status Output)
```

---

## 6. Audio Concepts for Beginners

* **Audio Sample**: A single numerical value representing sound pressure amplitude measured at one instant. Values range between `-1.0` and `+1.0`.
* **Sampling Rate**: How many audio samples are measured per second. Vocalis uses **16,000 Hz** (16,000 samples per second), standard for speech processing.
* **Audio Chunk**: A small slice of consecutive audio samples (e.g., 512 samples = $512 / 16000 = 0.032$ seconds or 32 milliseconds).
* **Microphone Stream**: A continuous background stream opened via `sounddevice` that captures audio blocks from your computer microphone.
* **Voice Activity Detection (VAD)**: A binary model that classifies whether a short audio chunk contains human voice or background noise.
* **Latency**: The time (in milliseconds) taken by the VAD model to process a single audio chunk. Lower latency means faster system response.
* **CPU & Memory Usage**: Hardware resource consumption measured using `psutil` to ensure low-power execution suitable for edge hardware.

---

## 7. Installation

### Prerequisites
* Python 3.10 or higher
* Working microphone connected to your computer

### Setup Virtual Environment

```bash
# Clone or navigate to the repository
cd "Vocalis — Low-Latency Voice Activation Engine"

# Create a virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (CMD):
.venv\Scripts\activate.bat
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 8. Running Vocalis

To start the real-time Voice Activity Detection engine:

```bash
python app.py
```

Speak into your microphone to observe real-time state transitions between `Status: 🔇 Silence` and `Status: 🔊 Voice detected`.

Press `Ctrl+C` in the terminal to cleanly terminate Vocalis.

---

## 9. Future Roadmap

```text
Vocalis V1
↓
Voice Activity Detection

Vocalis V2
↓
Wake-Word Detection

Vocalis V3
↓
Speech-to-Text

Vocalis V4
↓
Command Recognition

Vocalis V5
↓
Latency + CPU + Memory Optimization

Vocalis V6
↓
Train / Fine-Tune Lightweight Wake-Word Model

Vocalis V7
↓
Optional Edge Hardware
(Raspberry Pi / ESP32-class device)
```

---

## 10. License

Licensed under the MIT License.
