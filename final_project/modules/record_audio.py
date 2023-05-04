"""
Functions to record, encode, and save audio files.
"""

import pyaudio
import io
from typing import List
from pydub import AudioSegment


def record_audio(
    audio_format,
    chunk: int = 1024,
    channels: int = 1,
    rate: int = 44100,
    duration: int = 10,
) -> List[bytes]:
    """
    Records audio according to various parameters, most of which have default values
    common to audio recording. Returns a list of chunked audio recordings in the form of bytes.
    """
    p = pyaudio.PyAudio()
    
    stream = p.open(format=audio_format,channels=channels,rate=rate,input=True,frames_per_buffer=chunk)
    
    print(f"Recording audio for {duration} seconds...")

    frame_list = []
    for _ in range(0, int(rate / chunk * duration)):
        data = stream.read(chunk)
        frame_list.append(data)

    print(f"Finished recording.")

    stream.stop_stream()
    stream.close()

    return frame_list


def encode_audio_mp3(
    frame_list: List[bytes], audio_format, channels: int = 1, rate: int = 44100
) -> bytes:
    """
    Encodes a list of byte audio data into MP3 format in the form of bytes.
    """
    p = pyaudio.PyAudio()

    raw_buffer = io.BytesIO(b"".join(frame_list))
    raw_audio = AudioSegment.from_file(
        raw_buffer,
        format="raw",
        sample_width=p.get_sample_size(audio_format),
        channels=channels,
        frame_rate=rate,
    )
    raw_buffer.close()

    mp3_buffer = io.BytesIO()
    raw_audio.export(mp3_buffer, format="mp3")
    mp3_buffer.seek(0)
    mp3_data = mp3_buffer.read()

    return mp3_data


if __name__ == "__main__":
    pass
