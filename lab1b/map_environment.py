# imports
import picar_4wd as fc
import numpy as np
import math
from typing import List, Tuple


# env vars
DEBUG = True
X_SIZE = 100
Y_SIZE = 100
ANGLE_RANGE = 120
STEP = 12
MAX_ANGLE = ANGLE_RANGE/2
MIN_ANGLE = ANGLE_RANGE/2*-1
GRID_MAP = np.zeros(shape=(X_SIZE,Y_SIZE))

# convert angle and distance into caretisan coordinates
def get_cartesian(angle: float, distance: float) -> Tuple[int, int]:
    # x can be negative (since the car is in the middle of the grid along the x plane)
    x_cord = math.floor(math.sin(math.radians(angle))*distance)
    # y will always be >= 0 (since the car cannot detect objects behind with the servo and ultrasonic sensor)
    y_cord = math.floor(math.cos(math.radians(angle))*distance)

    return x_cord, y_cord,

# calculate slope between two x,y points
def get_slope(x1: int, y1: int, x2: int, y2:int) -> float:
    if x2 - x1 > 0:
        slope = (y2 - y1)/(x2 - x1)
    # account for infinite slope
    else:
        slope = float(-999)
    
    return slope

# get all x,y points between two x,y points
def get_points_inbtw(x1: int, y1: int, x2: int, y2:int) -> List[Tuple[int, int]]:
    points_inbtw = []
    # first get the slope
    slope = get_slope(x1=x1, y1=y1, x2=x2, y2=y2)
    # we know the equation of the line between two points is y=mx+b, where b is the y intercept
    # calculate the y intercept using either x,y pair
    b = y2 - slope*x1
    # now loop from the lower to higher x coordinate and get the x,y points in between
    if x1 > x2:
        x_high = x1
        x_low = x2
    else:
        x_high = x2
        x_low = x1
    
    for x_cord in range(x_low, x_high):
        y_cord = slope*x_cord + b
        point = x_cord, y_cord,
        points_inbtw.append(point)
    
    return poinst_inbtw





