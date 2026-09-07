import queue
import sounddevice as sd
import numpy as np


class MicrophoneStream:
    """
    Manages audio capture from the system's default microphone.

    Attributes:
        sample_rate (int): Sampling frequency in Hz (default: 16000 Hz).
        chunk_size (int): Number of audio samples per chunk (default: 512 samples = ~32ms).
        audio_queue (queue.Queue): Thread-safe queue containing incoming audio chunks.
    """

    def __init__(self, sample_rate: int = 16000, chunk_size: int = 512):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio_queue = queue.Queue()
        self.stream = None

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        """
        Callback function executed by sounddevice in a background thread
        whenever a new block of audio samples is captured by the hardware.
        """
        if status:
            # Drop/overflow status warnings can be checked here if needed
            pass
        
        # indata has shape (frames, channels), e.g. (512, 1).
        # We flatten it to a 1D float32 NumPy array of 512 numbers.
        chunk = indata.copy().flatten()
        
        # Put the chunk into the queue for the main loop to process
        self.audio_queue.put(chunk)

    def start(self):
        """
        Initializes and starts the real-time audio input stream.
        """
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,            # Mono audio stream
                dtype="float32",        # Normalized sample values (-1.0 to 1.0)
                blocksize=self.chunk_size,
                callback=self._audio_callback
            )
            self.stream.start()
        except sd.PortAudioError as err:
            raise RuntimeError(
                f"Failed to access microphone stream: {err}.\n"
                "Please check if a microphone is connected and authorized."
            ) from err

    def get_chunk(self, timeout: float = 1.0) -> np.ndarray:
        """
        Retrieves the next available audio chunk from the queue.
        Blocks until a chunk is available or until timeout seconds elapse.
        """
        return self.audio_queue.get(timeout=timeout)

    def stop(self):
        """
        Stops and releases the microphone audio stream resources cleanly.
        """
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
