import pyaudio
import wave

# Environmental Vars
OUTPUT_FILE = "output.wav"
CHANNELS = 1  # Single channel for simplicity
SAMPLE_FORMAT = pyaudio.paInt16  # 16-bit integer samples
SAMPLE_RATE = 44100  # Audo samples per second (Hz)
CHUNK_SIZE = 1024  # Number of audio samples processed at a time
DURATION = 10  # Time to record (seconds)

if __name__ == "__main__":
    # Initialize audio class
    precord = pyaudio.PyAudio()

    # Open a stream
    stream = precord.open(
        format=SAMPLE_FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE,
    )

    print("Now recording...")

    frame_list = []

    # Record sound for the given duration
    for _ in range(0, int(SAMPLE_RATE / CHUNK_SIZE * DURATION)):
        data = stream.read(CHUNK_SIZE)
        frame_list.append(data)

    print(f"Finished recording. Saving to file: {OUTPUT_FILE}")

    # Stop and close the stream
    stream.stop_stream()
    stream.close()

    # Terminate class
    precord.terminate()

    # Save to output file
    with wave.open(OUTPUT_FILE, "wb") as f:
        f.setnchannels(CHANNELS)
        f.setsampwidth(precord.get_sample_size(SAMPLE_FORMAT))
        f.setframerate(SAMPLE_RATE)
        f.writeframes(b"".join(frame_list))

    print(f"Saved to file: {OUTPUT_FILE}")
