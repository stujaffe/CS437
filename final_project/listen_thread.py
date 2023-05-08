"""
Main entry point into the program.
"""

import pyaudio
import os
import json
import sys
import threading
import time
from queue import Queue

from modules import record_audio as record
from modules import send_audio as send
from modules import display_led as led
from modules import music_api_response as mapi
from modules import music_compare as mcomp

# Audio variables
FORMAT = pyaudio.paInt16
RECORD_TIME_SEC = 15
SIM_THRESHOLD = 0.80
# RGB Matrix variables
ROWS = 64
COLS = 64
CHAIN_LENGTH = 1
PARALLEL = 1
HARDWARE_MAPPING = "adafruit-hat"
GPIO_SLOWDOWN = 4
LED_MULTIPLEXING = 0
LED_PWM_BITS = 11
LED_BRIGHTNESS = 100
PWM_LSB_NANOSECONDS = 130
LED_RGB_SEQUENCE = "RGB"
# Text display variables
FONT_SIZE = 15
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
TEXT_COLOR = (57, 255, 20)
# Song info variables
ALBUM_TEXT_KEYS = ["Artist","Song","Album","Release Date","Duration"]
ALBUM_ART_KEY = "album_art_url"

# Load variables from .env file
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.environ.get("AUDDIO_API_TOKEN")

# Queue to hold api responses
api_response_queue = Queue()

def record_and_process_audio():
    global api_response_parsed

    while True:
        # Listen for surrounding audio and record
        frame_list = record.record_audio(audio_format=FORMAT, duration=RECORD_TIME_SEC)

        # Encode to MP3 format for processing
        mp3_encoding = record.encode_audio_mp3(frame_list=frame_list, audio_format=FORMAT)
        
        # Compare the current mp3 econding to the latest recording to see if they are the same
        prev_encoding = record.read_mp3_encoding()
        
        correlation = 0
        if prev_encoding is not None:
        
            mp3_encoding_arr = mcomp.load_audio(audio_data=mp3_encoding)
            prev_encoding_arr = mcomp.load_audio(audio_data=prev_encoding)
            sxx_cur = mcomp.compute_spectrogram(audio=mp3_encoding_arr, sample_rate=48000)
            sxx_prev = mcomp.compute_spectrogram(audio=prev_encoding_arr, sample_rate=48000)
            
            correlation = mcomp.compare_spectrograms(sxx_cur, sxx_prev)
        
        if correlation < SIM_THRESHOLD:
            print("New recording is sufficiently different to ping the music API again.")
        
            # Save the encoded audio data to disk so we can refer to it later
            record.write_mp3_encoding(mp3_data=mp3_encoding)
            
            # Prepare the payload for the AUDD.IO API call
            data, files = send.create_payload(api_token=API_TOKEN, audio_data=mp3_encoding)

            # Send the payload to the AUDD.IO API
            api_response = send.send_api_request(data=data, files=files)
            
            # Parse the API response to extract the data we are interested in
            api_response_parsed = mapi.parse_api_response(response=api_response)
            
            # Save current API response parsed to disk
            mapi.write_json(response=api_response_parsed)
            
            print("API RESPONSE:")
            print(api_response_parsed)
        
        else:
            print("New recording is NOT sufficiently different to ping the music API again.")
            
            print("EXISTING API RESPONSE:")
            api_response_parsed = mapi.read_json()


def display_text_and_image(api_response_parsed):
    while True:
        print("ENTERING IMAGE")
        # We only have the album art URL in the api_response_parsed, so we need to get the actual byte data of the image.
        image_data = mapi.download_album_art(url=api_response_parsed.get(ALBUM_ART_KEY))
        
        # Create the text string to display
        text_to_display = led.gather_text(parsed_response=api_response_parsed, target_keys=ALBUM_TEXT_KEYS)
        
        # Create the text image that will be sent to the LED matrix
        text_image = led.create_text_image(
            text=text_to_display,
            font_path=FONT_PATH,
            font_size=FONT_SIZE,
            text_color=TEXT_COLOR,
        )
        
        # Create the LED matrix object that will display the text and images
        matrix = led.create_led_matrx(
            rows=ROWS,
            cols=COLS,
            chain_length=CHAIN_LENGTH,
            parallel=PARALLEL,
            hardware_mapping=HARDWARE_MAPPING,
            gpio_slowdown=GPIO_SLOWDOWN,
            multiplexing=LED_MULTIPLEXING,
            pwm_bits=LED_PWM_BITS,
            brightness=LED_BRIGHTNESS,
            pwm_lsb_nanoseconds=PWM_LSB_NANOSECONDS,
            led_rgb_sequence=LED_RGB_SEQUENCE
        )
        
        # Scroll the text across the LED matrix
        led.scroll_text_mid(text_image=text_image, matrix=matrix)
        
        # Display album art image if it exists
        led.display_image_led(image_data=image_data, matrix=matrix)

        # Sleep for a short duration between updates to avoid excessive resource usage
        time.sleep(1)
            
if __name__ == "__main__":
    
    
    # Create a global variable to store the parsed API response
    api_response_parsed = None
    
    # Create threads for audio recording and LED matrix display
    audio_thread = threading.Thread(target=record_and_process_audio)
    display_thread = threading.Thread(target=display_text_and_image)

    # Start the threads
    audio_thread.start()
    display_thread.start()

    # Keep the main thread running while the audio and display threads are running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping the program.")
