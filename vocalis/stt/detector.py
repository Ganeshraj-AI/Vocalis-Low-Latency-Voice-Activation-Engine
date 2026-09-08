import logging
import numpy as np
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)


class STTDetector:
    """
    Local Speech-to-Text (STT) Detector powered by faster-whisper (CTranslate2).

    Transcribes accumulated PCM audio chunks into text locally on CPU without cloud APIs.

    Attributes:
        model_size (str): Whisper model variant (default: "tiny.en").
        device (str): Inference device ("cpu").
        compute_type (str): Quantization strategy ("int8" for CPU efficiency).
    """

    def __init__(self, model_size: str = "tiny.en", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        self._init_model()

    def _init_model(self):
        """
        Loads the faster-whisper model locally.
        Falls back to float32 compute_type if int8 quantized inference is unsupported.
        """
        try:
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
        except Exception as primary_err:
            # Fallback to float32 compute type if int8 fails on specific CPU architectures
            if self.compute_type != "float32":
                try:
                    logger.warning(
                        f"Failed int8 quantization init ({primary_err}). Retrying with float32..."
                    )
                    self.compute_type = "float32"
                    self.model = WhisperModel(
                        self.model_size,
                        device=self.device,
                        compute_type="float32"
                    )
                    return
                except Exception as fallback_err:
                    raise RuntimeError(
                        f"Failed to initialize faster-whisper engine ({self.model_size}): {fallback_err}.\n"
                        "Please check faster-whisper installation and internet connection for model download."
                    ) from fallback_err
            else:
                raise RuntimeError(
                    f"Failed to initialize faster-whisper engine ({self.model_size}): {primary_err}.\n"
                    "Please check faster-whisper installation."
                ) from primary_err

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Transcribes a 1D float32 audio NumPy array (-1.0 to +1.0) into text.

        Args:
            audio_data (np.ndarray): 1D array of float32 mono audio samples.
            sample_rate (int): Sampling rate of the audio (default: 16000 Hz).

        Returns:
            str: Transcribed text string, or empty string if no speech recognized.
        """
        if self.model is None:
            return ""

        if audio_data is None or len(audio_data) == 0:
            return ""

        # Ensure float32 array dtype
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        # Minimum duration check (e.g. at least 0.2s of audio)
        min_samples = int(sample_rate * 0.2)
        if len(audio_data) < min_samples:
            return ""

        try:
            # faster-whisper accepts float32 numpy array directly
            segments, _ = self.model.transcribe(
                audio_data,
                beam_size=1,
                language="en",
                vad_filter=False
            )

            text_pieces = [segment.text.strip() for segment in segments if segment.text.strip()]
            full_text = " ".join(text_pieces)
            return full_text
        except Exception as err:
            logger.error(f"STT transcription error: {err}")
            return ""
