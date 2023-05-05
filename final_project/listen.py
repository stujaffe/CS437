import pyaudio
import os
import json
import sys

from modules import record_audio as record
from modules import send_audio as send

FORMAT = pyaudio.paInt16

# Load variables from .env file
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.environ.get("AUDDIO_API_TOKEN")

if __name__ == "__main__":
    frame_list = record.record_audio(audio_format=FORMAT, duration=15)

    mp3_encoding = record.encode_audio_mp3(frame_list=frame_list, audio_format=FORMAT)

    data, files = send.create_payload(api_token=API_TOKEN, audio_data=mp3_encoding)

    result = send.send_api_request(data=data, files=files)

    print(result)
    
    with open("sample_response.json","w") as f:
        json.dump(result, f, indent=4)
    
    
