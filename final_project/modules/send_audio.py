"""
Functions to send audio data to AUDD.IO API.
"""

import requests
import json
from typing import Tuple, Union


def create_payload(api_token: str, audio_data: Union[str, bytes]) -> Tuple[dict, dict]:
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


def send_api_request(
    data: dict, files: dict, url: str = "https://api.audd.io/"
) -> dict:
    response = requests.post(url, data=data, files=files)

    result = json.loads(response.text)

    return result


if __name__ == "__main__":
    pass
