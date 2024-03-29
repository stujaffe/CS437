"""
Functions to display text and images on the LED screen.
"""

import sys
import time
import json
from PIL import Image, ImageDraw, ImageFont
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from typing import Tuple, List
from io import BytesIO

# Variables
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


FONT_SIZE = 15
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
DISPLAY_TEXT = "HELLO BODHI!"
TEXT_COLOR = (57, 255, 20)

ALBUM_TEXT_KEYS = ["Artist","Song","Album","Release Date","Duration"]
ALBUM_ART_KEY = "album_art_url"


def create_text_image(
    text: str, font_path: str, font_size: int, text_color: Tuple
) -> Image:
    """
    Function to create the text image.
    """
    font = ImageFont.truetype(font_path, font_size)
    bbox = font.getbbox(text)
    size = (bbox[2] - bbox[0], bbox[3] - bbox[1])
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.text((-bbox[0], -bbox[1]), text, font=font, fill=text_color)
    image.convert("RGB")

    return image


def create_led_matrx(
    rows: int,
    cols: int,
    chain_length: int,
    parallel: int,
    hardware_mapping: str,
    gpio_slowdown: int,
    multiplexing: int,
    pwm_bits: int,
    brightness: int,
    pwm_lsb_nanoseconds: int,
    led_rgb_sequence: str,
) -> RGBMatrix:
    """
    Function to create the LED screen (i.e. matrix) object
    """
    options = RGBMatrixOptions()
    options.rows = rows
    options.cols = cols
    options.chain_length = chain_length
    options.parallel = parallel
    options.hardware_mapping = hardware_mapping
    options.gpio_slowdown = gpio_slowdown
    options.multiplexing = multiplexing
    options.pwm_bits = pwm_bits
    options.brightness = brightness
    options.pwm_lsb_nanoseconds = pwm_lsb_nanoseconds
    options.led_rgb_sequence = led_rgb_sequence
    

    matrix = RGBMatrix(options=options)

    return matrix


def send_text_led(
    text_image: Image, matrix: RGBMatrix, x_cord: int, y_cord: int
) -> None:
    """
    Function to send a text image to the LED screen.
    """
    matrix.Clear()
    text_image = text_image.convert("RGB")
    matrix.SetImage(text_image, x_cord, y_cord)

def scroll_text_mid(text_image: Image, matrix: RGBMatrix, sleep_time: int=0.035) -> None:
    """
    Function to scroll the desired text in the middle of the LED screen.
    Note: Sleeping for a short time (e.g. 0.05 seconds) in the for loop is CRITICAL!!!
    Or else the text will display incorrectly.
    """
    # Get the text width and text height
    text_width, text_height = text_image.size
    # The y-axis position should be in the middle so that half the text is above and below
    # the center of the screen
    y_position = (ROWS - text_height) // 2
    
    # Initiate an loop to scroll the text once
    # Loop over the x-coordinates starting at the number of LED columns
    # and ending at the width of the text
    for x_position in range(COLS, -text_width, -1):
        send_text_led(
            text_image=text_image,
            matrix=matrix,
            x_cord=x_position,
            y_cord=y_position,
        )
        time.sleep(sleep_time)

def display_image_led(image_data: bytes, matrix: RGBMatrix, sleep_time: int=10) -> None:
    """
    Function to display an image on the LED matrix.
    """
    if image_data is not None:
        # Process and convert the image data
        image = Image.open(BytesIO(image_data))
        
        # Resize image to fit LED matrix dimensions
        image = image.resize((matrix.width, matrix.height))
        
        # Convert to the RGB format
        image = image.convert("RGB")
        
        # Display the image
        matrix.SetImage(image)
        
        time.sleep(sleep_time)
    
    return None

def gather_text(parsed_response: dict, target_keys: List[str]) -> str:
    """
    Function to create the scrolling text to display on the LED matrix, only
    if the values exist as strings.
    """
    text_to_display = ""
    for text_key in target_keys:
        if type(parsed_response.get(text_key)) == str:
            if len(text_to_display) > 0:
                # Spacer in between text data
                text_to_display += " | "
            text_to_display += text_key + ":" + parsed_response.get(text_key)
    
    return text_to_display
    

if __name__ == "__main__":
    pass
    
