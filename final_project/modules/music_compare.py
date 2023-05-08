"""
Functions to compare two audio signals.
"""

import numpy as np
from pydub import AudioSegment
from scipy import signal
from io import BytesIO

def load_audio_file(file_path: str) -> np.ndarray:
    audio = AudioSegment.from_file(file_path)
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    
    if audio.channels == 2:
        samples = samples.reshape((-1, 2))
        samples = samples.mean(axis=1)
    
    return samples / (2**15)  # Normalize to range -1 to 1

def load_audio(audio_data: bytes, audio_format="mp3") -> np.ndarray:
    audio_buffer = BytesIO(audio_data)
    audio = AudioSegment.from_file(audio_buffer, format=audio_format)
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    
    if audio.channels == 2:
        samples = samples.reshape((-1, 2))
        samples = samples.mean(axis=1)
    
    return samples / (2**15)  # Normalize to range -1 to 1

def compute_spectrogram(audio: np.ndarray, sample_rate: int, window: str = 'hann', nperseg: int = 256) -> np.ndarray:
    f, _, Sxx = signal.spectrogram(audio, fs=sample_rate, window=window, nperseg=nperseg)
    return Sxx

def compare_spectrograms(Sxx1: np.ndarray, Sxx2: np.ndarray) -> float:
    correlation = np.corrcoef(Sxx1.flatten(), Sxx2.flatten())[0, 1]
    print("Spectrogram correlation:", correlation)
    
    return correlation

if __name__ == "__main__":
    pass
