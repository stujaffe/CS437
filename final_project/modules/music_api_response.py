
"""
Functions to parse the response from the AUDD.IO music API
"""

import requests
import os
import json
from typing import Union, List
from json.decoder import JSONDecodeError

# Variables
ROWS = 64
COLS = 64

def delete_json(filename: str="latest_response.json", directory="api_responses") -> None:
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


def write_json(response: dict, filename: str="latest_response.json", directory="api_responses") -> None:
    """
    Saves JSON to disk
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    if directory[-1] != "/":
        directory = f"{directory}/"
    
    with open(f"{directory}{filename}", "w") as f:
        json.dump(response, f)
        print("Saved API response to disk.")
    
    return None

def read_json(filename: str="latest_response.json", directory="api_responses") -> dict:
    """
    Saves JSON to disk
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    if directory[-1] != "/":
        directory = f"{directory}/"
    
    response = None
    try:
        with open(f"{directory}{filename}", "r") as f:
            response = json.load(f)
            print("Read API response from disk.")
    except (JSONDecodeError, FileNotFoundError):
        pass
    
    return response


def convert_milliseconds(milliseconds: float) -> Union[None, str]:
    """
    Function to convert milliseconds into a readable length.
    E.g. 123456 milliseconds -> "2:03"
    """
    # Make sure milliseconds is valid
    if not type(milliseconds) in [int, float]:
        return None
        
    seconds_total = milliseconds // 1000
    minutes = seconds_total // 60
    seconds = seconds_total % 60
    
    result = "{:02d}:{:02d}".format(int(minutes), int(seconds))
    
    return result

def get_song_duration(response: dict) -> Union[None, float]:
    """
    Function to extract the song duration from Apple Music and/or Spotify data.
    Returned as a float in milliseconds.
    """
    try:
        dur_apple = response.get("result",{}).get("apple_music",{}).get("durationInMillis")
    except AttributeError:
        dur_apple = None
    try:
        dur_spotify = response.get("result", {}).get("spotify", {}).get("duration_ms")
    except AttributeError:
        dur_spotify = None
    
    dur_list = []
    # Calculate average of the two durations
    if dur_apple is not None:
        dur_list.append(dur_apple)
    if dur_spotify is not None:
        dur_list.append(dur_spotify)
    
    dur_avg = float(sum(dur_list)/len(dur_list)) if len(dur_list) > 0 else None
    
    return dur_avg

def get_apple_album_art_url(response: dict) -> Union[None, dict]:
    """
    Function to get the highest resolution album art URL from Apple Music
    """
    # Apple Music album art URL
    apple_data = response.get("result",{}).get("apple_music",{}).get("artwork",{})
    apple_width = apple_data.get("width")
    apple_height = apple_data.get("height")
    apple_url_raw = apple_data.get("url")
    # We need to insert the height and width into the Apple album URL since it looks
    # something like this: 
    # "https://is5-ssl.mzstatic.com/image/thumb/Music125/v4/9c/9b/93/9c9b931a-bf4d-f51b-def4-7d7ea41bfa29/5039060434796.png/{w}x{h}bb.jpg"
    if apple_width is not None and apple_height is not None and apple_url_raw is not None:
        apple_url_adj = apple_url_raw.format(w=apple_width, h=apple_height)
        result = {"url":apple_url_adj, "height":apple_height, "width":apple_width, "source":"apple_musc"}
    else:
        result = None
    
    return result
    

def get_spotify_album_art_url(response: dict) -> Union[None, List[Union[str,int]]]:
    """
    Function to get the highest resolution album art URL from Spotify
    """
    # Will grab a list of the possible album URLs from Spotify and their height/width
    spotify_data = response.get("result",{}).get("spotify",{}).get("album",{}).get("images")
    
    return spotify_data

def get_best_album_art_url(response: dict, height: int=ROWS, width: int=COLS) -> str:
    """
    Gets the best album art URL given the height and width (resolution). The goal
    is to get the album art with the closest resolution to the given height/width.
    """
    # Our target resolution
    target_res = height*width
    # Our starting difference
    best_diff = float("inf")
    # Our starting best album art URL
    best_url = None
    
    # Aggregate spotify and Apple URLs
    all_urls = []
    spotify_urls = get_spotify_album_art_url(response=response)
    apple_urls = get_apple_album_art_url(response=response)
    
    if type(spotify_urls) == list:
        all_urls.extend(spotify_urls)
    if type(apple_urls) == dict:
        all_urls.append(apple_urls)
    
    for item in all_urls:
        res = item.get("height",0)*item.get("width",0)
        url = item.get("url")
        # Make sure resolution exists 
        if res > 0:
            diff = res - target_res
        # The current resolution needs to be greater than or equal to target resolution
        if diff >= 0 and diff < best_diff and url is not None:
            best_diff = diff
            best_url = url
    
    return best_url
        

def download_album_art(url: str) -> Union[None, bytes]:
    """
    Function to download the album art image data.
    """
    result = None      
    if type(url) == str:
        response = requests.get(url)
        if response.status_code == 200:
            result = response.content
    
    return result

def parse_api_response(response: dict) -> dict:
    """
    Function to parse the JSON response from the API in send_audio.py and display certain
    text data from the response.
    """
    # Output dictionary with desired text data
    output_dict = {"Artist":None, "Song":None,
            "Album":None, "Release Date":None,
            "Duration":None, "album_art_url":None, "Lyrics":None}
            
    # First check to see the result exists
    response_data = response.get("result")
    if type(response_data) != dict:
        return output_dict
    
    # Get the basic song data
    artist = response_data.get("artist")
    song = response_data.get("title")
    album = response_data.get("album")
    release_date = response_data.get("release_date")
    
    # Get duration and convert to minutes:seconds for display
    duration_ms = get_song_duration(response=response)
    duration_str = convert_milliseconds(milliseconds=duration_ms)
    
    # Get the album art URL
    album_art_url = get_best_album_art_url(response=response)
    
    # Get the song preview URL (only Spotify works with the lyrics web app we have)
    song_preview_url = response_data.get("spotify",{}).get("preview_url")
    
    # Add to the parsed result. The text fields that we want to display
    # purposely have upper case names so they can display more micely on the lED Screen.
    output_dict["Artist"] = artist
    output_dict["Song"] = song
    output_dict["Album"] = album
    output_dict["Release Date"] = release_date
    output_dict["Duration"] = duration_str
    output_dict["album_art_url"] = album_art_url
    output_dict["preview_url"] = song_preview_url
    
    return output_dict
    
if __name__ == "__main__":
    pass
    
