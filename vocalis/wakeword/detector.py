import numpy as np
import openwakeword
from openwakeword.model import Model


class WakeWordDetector:
    """
    Wake-Word Detector using OpenWakeWord (ONNX runtime).

    Evaluates streaming audio chunks to detect trigger keywords such as "hey_jarvis", "alexa", etc.

    Attributes:
        threshold (float): Detection confidence threshold between 0.0 and 1.0 (default: 0.5).
        target_model (str): Target wake-word model name to monitor (default: "hey_jarvis").
    """

    def __init__(self, threshold: float = 0.5, target_model: str = "hey_jarvis"):
        self.threshold = threshold
        self.target_model = target_model
        self.model = None
        self._init_model()

    def _init_model(self):
        """Loads pre-trained OpenWakeWord models in ONNX mode."""
        try:
            # Ensure model files are available locally
            openwakeword.utils.download_models()
            self.model = Model(inference_framework="onnx")
        except Exception as err:
            raise RuntimeError(
                f"Failed to initialize OpenWakeWord engine: {err}.\n"
                "Please check openwakeword installation."
            ) from err

    def is_wakeword_detected(self, audio_chunk: np.ndarray) -> tuple[bool, str, float]:
        """
        Evaluates an audio chunk and returns detection status.

        Args:
            audio_chunk (np.ndarray): 1D float32 NumPy array of audio samples (range -1.0 to 1.0).

        Returns:
            tuple: (is_detected: bool, model_name: str, confidence_score: float)
        """
        if self.model is None:
            return False, "", 0.0

        # Convert normalized float32 samples (-1.0 to 1.0) to int16 PCM amplitude scale
        pcm16_chunk = (audio_chunk * 32768.0).clip(-32768, 32767).astype(np.int16)

        # Run OpenWakeWord prediction
        predictions = self.model.predict(pcm16_chunk)

        # Check target model prediction score
        if self.target_model in predictions:
            score = float(predictions[self.target_model])
            is_detected = score >= self.threshold
            return is_detected, self.target_model, score
        else:
            # Fallback to maximum scoring model among loaded models
            max_model = max(predictions, key=predictions.get)
            max_score = float(predictions[max_model])
            is_detected = max_score >= self.threshold
            return is_detected, max_model, max_score
