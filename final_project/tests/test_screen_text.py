"""
Functions to draw text on the LED screen.
"""

import sys
import time
from PIL import Image, ImageDraw, ImageFont
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from typing import Tuple
from io import BytesIO

# Variables
ROWS = 64
COLS = 64
CHAIN_LENGTH = 1
PARALLEL = 1
HARDWARE_MAPPING = "adafruit-hat"
GPIO_SLOWDOWN = 4

FONT_SIZE = 16
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
DISPLAY_TEXT = "HELLO BODHI!"
TEXT_COLOR = (57, 255, 20)
X_CORD = 10
Y_CORD = 20


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

def scroll_text_mid(display_text: str, text_image: Image, matrix: RGBMatrix, sleep_sec: int=0.05) -> None:
    """
    Function to scroll the desired text in the middle of the LED screen.
    """
    # Get the text width and text height
    text_width, text_height = text_image.size
    # The y-axis position should be in the middle so that half the text is above and below
    # the center of the screen
    y_position = (ROWS - text_height) // 2
    
    # Initiate an infinite loop to scroll until there is a keyboard interrupt
    while True:
        try:
            # Loop over the x-coordinates starting at the number of LED columns
            # and ending at the width of the text
            for x_position in range(COLS, -text_width, -1):
                send_text_led(
                    text_image=text_image,
                    matrix=matrix,
                    x_cord=x_position,
                    y_cord=y_position,
                )
                time.sleep(0.05)
        except KeyboardInterrupt:
            sys.exit(0)

        


if __name__ == "__main__":
    text_image = create_text_image(
        text=DISPLAY_TEXT,
        font_path=FONT_PATH,
        font_size=FONT_SIZE,
        text_color=TEXT_COLOR,
    )
    matrix = create_led_matrx(
        rows=ROWS,
        cols=COLS,
        chain_length=CHAIN_LENGTH,
        parallel=PARALLEL,
        hardware_mapping=HARDWARE_MAPPING,
        gpio_slowdown=GPIO_SLOWDOWN,
    )

    scroll_text_mid(display_text=DISPLAY_TEXT, text_image=text_image, matrix=matrix)
    