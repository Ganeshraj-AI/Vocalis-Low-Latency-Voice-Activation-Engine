import numpy as np
import torch
import silero_vad


class VADDetector:
    """
    Voice Activity Detector (VAD) powered by Silero VAD.

    Determines whether a given real-time audio chunk contains human speech.

    Attributes:
        sample_rate (int): Audio sample rate in Hz (default: 16000).
        threshold (float): Decision probability threshold between 0.0 and 1.0 (default: 0.5).
    """

    def __init__(self, sample_rate: int = 16000, threshold: float = 0.5):
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.model = None
        self._init_vad()

    def _init_vad(self):
        """Loads the pre-trained Silero VAD model locally."""
        try:
            self.model = silero_vad.load_silero_vad()
        except Exception as err:
            raise RuntimeError(
                f"Failed to initialize Silero VAD engine: {err}.\n"
                "Please verify that silero-vad package is installed correctly."
            ) from err

    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """
        Evaluates an audio chunk and returns True if speech is detected.

        Args:
            audio_chunk (np.ndarray): 1D float32 NumPy array of audio samples.

        Returns:
            bool: True if voice activity is detected, False otherwise.
        """
        if self.model is None:
            return False

        # Convert NumPy float32 array to PyTorch Tensor expected by Silero VAD
        tensor_chunk = torch.from_numpy(audio_chunk)

        # Silero VAD returns a confidence probability (0.0 to 1.0)
        speech_probability = self.model(tensor_chunk, self.sample_rate).item()

        return speech_probability >= self.threshold
