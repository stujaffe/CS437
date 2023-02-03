# imports
import picar_4wd as fc
import numpy as np
import math
import time
from typing import List, Tuple


# global vars
DEBUG = True
X_LOCAL = 100
Y_LOCAL = 100
X_GLOBAL = 1000
Y_GLOBAL = 1000
ANGLE_RANGE = 140
STEP = 14
CURRENT_ANGLE = 0
POWER = 20
SPEED_AT_10 = 26.70
#################################
# Calculated global vars
MAX_ANGLE = ANGLE_RANGE/2
MIN_ANGLE = ANGLE_RANGE/2*-1
LOCAL_MAP = np.zeros(shape=(X_LOCAL,Y_LOCAL))
GLOBAL_MAP = np.zeros(shape=(X_GLOBAL, Y_GLOBAL))
#################################
# Dictionary to keep track of the number of seconds traveled
# in each direction
DIRECTION_TIME = {"north":0,"east":0,"west":0,"south":0}

class Coordinate(object):
    def __init__(self, x: int, y: int) -> None:
        self.x = int(x)
        self.y = int(y)
    
    def __eq__(self, other):
        isequal = False
        if other is not None and self.x == other.x and self.y == other.y:
            isequal = True
        else:
            isequal = False
        return isequal
    
    def __add__(self, other):
        new_point = Coordinate(self.x + other.x, self.y + other.y)
        return new_point

# convert angle and distance into caretisan coordinates
def get_cartesian(angle: float, distance: float) -> Coordinate:
    # x can be negative (since the car is in the middle of the grid along the x plane)
    x = math.floor(math.sin(math.radians(angle))*distance)
    # y will always be >= 0 (since the car cannot detect objects behind with the servo and ultrasonic sensor)
    y = math.floor(math.cos(math.radians(angle))*distance)
    coord = Coordinate(x_cord, y_cord)

    return coord

# calculate slope between two x,y points
def get_slope(coord1: Coordinate, coord2: Coordinate) -> float:
    if coord2.x - coord1.x > 0:
        slope = (y2 - y1)/(x2 - x1)
    # account for infinite slope
    else:
        slope = float(-999)
    
    return slope

# get all x,y points between two x,y points
def get_points_inbtw(coord1: Coordinate, coord2: Coordinate) -> List[Coordinate]:
    points_inbtw = []
    # first get the slope
    slope = get_slope(coord1, coord2)
    # we know the equation of the line between two points is y=mx+b, where b is the y intercept
    # calculate the y intercept using either x,y pair
    b = coord2.y - slope*coord1.x
    # now loop from the lower to higher x coordinate and get the x,y points in between
    if coord1.x > coord2.x:
        x_high = coord1.x
        x_low = coord2.x
    else:
        x_high = coord2.x
        x_low = coord1.x
    
    for x in range(x_low, x_high):
        y_calc = slope*x + b
        point = Coordinate(x, y_calc)
        points_inbtw.append(point)
    
    return poinst_inbtw

# scan the area in front of the car
def scan_sweep() -> List[Tuple[float, int]]:
    
    scan_result = []
    for angle in range(MIN_ANGLE, MAX_ANGLE, STEP):
        fc.servo.set_angle(angle)
        CURRENT_ANGLE = angle
        time.sleep(0.04)
        distance_to_obj = fc.us.get_distance()
        scan_result.append((distance_to_obj, angle))
    # returns a list of tuples (distance cm, angle degrees)
    return scan_result

# calculate the speed in cm/s for a given power
def get_speed(power: int) -> float:
    speed_10 = SPEED_AT_10
    if power == 10:
        return speed_10
    # extra speed is the power above 10 subtracted by 10
    # then divided by 10, multiplied by 2.5
    # During test I found for every 10 extra power above 10,
    # the car moved 2.5 cm/s faster. E.g. at 20 power the speed
    # is 26.7 + 2.5
    extra = (power - 10)/10*2.5
    speed = speed_10 + extra
    
    return speed

def right_turn_90() -> None:
    fc.turn_right(30)
    time.sleep(0.95)

def left_turn_90() -> None:
    fc.turn_left(30)
    time.sleep(0.95)

# returns the location of the car in the global map
def get_global_location(start: Coordinate) -> Coordinate:
    pass
    

def navigate_to_goal(start: Coordinate, goal: Coordinate) -> None:
    x_cm = goal.x - start.x
    y_cm = goal.y - start.y
    
    print(x_cm)
    print(y_cm)

    # orient the car so the goal is in front of the car
    if y_cm < 0:
        left_turn_90()
        left_turn_90()
        # reverse polarity of x coordinate since we turned around
        x_cm = x_cm*-1
        
    # goal y coordinate should be in front of the car
    sec_forward = y_cm/get_speed(POWER)
    # drive forward for the number of seconds in takes to cover the y_cm at current power
    fc.forward(POWER)
    time.sleep(sec_forward)
    fc.stop()
    if x_cm < 0:
        left_turn_90()
        sec_forward = abs(x_cm)/get_speed(POWER)
        fc.forward(POWER)
        time.sleep(sec_forward)
        fc.stop()
    elif x_cm > 0:
        right_turn_90()
        sec_forward = abs(x_cm)/get_speed(POWER)
        fc.forward(POWER)
        time.sleep(sec_forward)
        fc.stop()
    else:
        fc.stop()

    fc.stop()


if __name__ == "__main__":
    
    start = Coordinate(50,50)
    goal = Coordinate(25, 100)
    
    navigate_to_goal(start, goal)
    
    



    
    
    





