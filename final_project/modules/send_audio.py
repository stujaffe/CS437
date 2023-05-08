"""
Functions to send audio data to AUDD.IO API and the Song Lyrics API.
"""

import requests
import json
from typing import Tuple, Union

def create_lyric_payload(audio_uri: str) -> dict:
    """
    Payload for lyrics uri.
    """
    
    payload = {
    "audio_uri": audio_uri,
    "audio_id": "01c34e28-515e-41bf-bf38-a01dc6efc3bf",
    "audio_type": "messages",
    }
    
    return payload

def send_lyric_api_request(audio_uri: str, 
    endpoint: str="https://us-central1-chats-58cde.cloudfunctions.net/openai-transcribe") -> Union[None,str]:
    """
    Gets song lyrics using an audio preview uri.
    """
    audio_transcript = None
    payload = create_lyric_payload(audio_uri=audio_uri)
    
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(endpoint, json=payload, headers=headers)
    
    if response.status_code == 200:
        response_json = response.json()
        audio_transcript = response_json.get("audio_transcript")
    else:
        print(f"Error in receiving audio transcript. Status code {response.status_code}.")
    
    if audio_transcript is not None:
        print("Received audio transcript.")
    
    return audio_transcript

def truncate_audio_transcript(audio_transcript: str, max_length: int=50) -> Union[None, str]:
    """
    Function to truncate the audio transcript so it doesn't scroll for so long.
    Will not cutoff words mid-word.
    """
    
    result = None
    if type(audio_transcript) == str:
        words = audio_transcript.split()
        result = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) > max_length:
                break
            result.append(word)
            current_length += len(word) + 1  # +1 accounts for the space between words
        result = " ".join(result)
        result = f"{result}..."
    
    return result
    

def create_auddio_payload(api_token: str, audio_data: bytes) -> Tuple[dict, dict]:
    """
    Creates payload for the audd.io API. docs.audd.io/#recognize
    audio_data can either be audio data in bytes form or a filepath to an encoded
    audio file, such as MP3.
    """

    data = {"api_token": api_token, "return": "apple_music,spotify"}

    file_data = None
    if type(audio_data) == str:
        file_data = open(audio_data, "rb")
    elif type(audio_data) == bytes:
        file_data = audio_data
    else:
        raise Exception(
            f"The 'audio_data' argument is of type {type(audio_data)} and needs \
			to be either a string filepath or encoded audio data in bytes."
        )

    files = {"file": file_data}

    return (
        data,
        files,
    )


def send_auddio_api_request(
    api_token: str, audio_data: bytes, endpoint: str = "https://api.audd.io/"
) -> dict:
    
    data, files = create_auddio_payload(api_token=api_token, audio_data=audio_data)
    
    response = requests.post(endpoint, data=data, files=files)

    result = json.loads(response.text)

    return result


if __name__ == "__main__":
    s = "So show me love if you wanna, I still gotta hang over You pick me up and put me down Here I am and it's over, look across and it's cool We used to build a tower for us But I'm still sleeping with a broken heart So I let you lay with me I can hide my tears from you in the dark But I'm lost in your body"

    print(truncate_audio_transcript(s))
