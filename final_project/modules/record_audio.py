"""
Functions to record, encode, and save audio files.
"""

import pyaudio
import io
import os
import sys
from typing import List
from pydub import AudioSegment
from typing import Union


def record_audio(
    audio_format,
    chunk: int = 1024,
    channels: int = 2,
    rate: int = 48000,
    duration: int = 10,
) -> List[bytes]:
    """
    Records audio according to various parameters, most of which have default values
    common to audio recording. Returns a list of chunked audio recordings in the form of bytes.
    """
    p = pyaudio.PyAudio()

    stream = p.open(
        format=audio_format,
        channels=channels,
        rate=rate,
        input=True,
        frames_per_buffer=chunk,
    )

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
    frame_list: List[bytes], audio_format, channels: int = 2, rate: int = 48000
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
    
    print(f"Size in bytes of MP3 encoding: {sys.getsizeof(mp3_data)}")

    return mp3_data

def write_mp3_encoding(mp3_data: bytes, filename: str="latest_recording.mp3", directory="recordings") -> None:
    """
    Saves MP3 encoded audio to disk.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    if directory[-1] != "/":
        directory = f"{directory}/"
    
    with open(f"{directory}{filename}", "wb") as f:
        f.write(mp3_data)
        print("Saved recording to disk.")
    
    return None

def read_mp3_encoding(filename: str="latest_recording.mp3", directory="recordings") -> Union[None,bytes]:
    """
    Reads MP3 encoded audio from disk.
    """
    mp3_data = None
    if directory[-1] != "/":
        directory = f"{directory}/"
    
    try:
        with open(f"{directory}{filename}", "rb") as f:
            mp3_data = f.read()
            print("Read recording from disk.")
    except FileNotFoundError:
        pass
    
    return mp3_data

def delete_mp3_encoding(filename: str="latest_recording.mp3", directory="recordings") -> None:
    # Check if the file exists before trying to delete it
    if directory[-1] != "/":
        directory = f"{directory}/"
    file_path = f"{directory}{filename}"
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"File '{file_path}' has been deleted.")
        except OSError as e:
            print(f"Error deleting file '{file_path}': {e}")



if __name__ == "__main__":
    pass
