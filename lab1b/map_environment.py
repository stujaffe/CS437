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
LOCAL_MAP = np.zeros(shape=(X_LOCAL,Y_LOCAL))
GLOBAL_MAP = np.zeros(shape=(X_GLOBAL, Y_GLOBAL))
#################################

class PiCar:
    def __init__(self, start_loc: Coordinate, end_loc: Coordinate, power: int = 10,
        , direction: str ='N', angle_range: int = 140) -> None:
        self.start_loc = start_loc
        self.goal_loc = goal_loc
        self.current_loc = start_loc
        self.direction = direction
        self.distance_traveled = 0
        self.power = power
        self.angle_range = angle_range
        self.step = math.floor(angle_range/10)
        self.max_angle = angle_range/2
        self.min_angle = angle_ange/2*-1
        self.current_angle = 0
        self.speed_at_10 = 26.70
    
    
    # calculate the manhattan distance between two coordinates
    @staticmethod
    def calc_dist_mhtn(coord1: Coordinate, coord2: Coordinate) -> int:
        distance = abs(coord2.x - coord1.x) + abs(coord2.y - coord1.y)
        return distance
        
    # calculate the speed in cm/s for a given power
    def get_speed(self):
        if self.power == 10:
            return self.speed_at_10
        # extra speed is the power above 10 subtracted by 10
        # then divided by 10, multiplied by 2.5
        # During test I found for every 10 extra power above 10,
        # the car moved 2.5 cm/s faster. E.g. at 20 power the speed
        # is 26.7 + 2.5
        extra = (self.power - 10)/10*2.5
        self.speed = self.speed_at_10 + extra
        
        return self.speed
    
    # return the number of seconds needed to move along one axis (x or y) and the distance
    # given the current power and the two coordinates
    def calc_sec_dist(self, coord1: Coordinate, coord2: Coordinate, axis: str) -> Tuple[float, float]:
        axis = str(axis).lower()
        if axis not in ["x","y"]:
            raise Exception("Please specify axis on which to calculate seconds to move.")
        
        if axis == "x":
            dist_cm = abs(coord1.x - coord2.x)
        elif axis == "y":
            dist_cm = abs(coord1.y - coord2.y)
        else:
            dist_cm = 0
        
        seconds = dist_cm/self.get_speed(self.power)
        
        return dist_cm, seconds
    
    # scan the area in front of the car
    def scan_sweep(self) -> List[Tuple[float, int]]:
        scan_result = []
        for angle in range(self.min_angle, self.max_angle, self.step):
            fc.servo.set_angle(angle)
            self.current_angle = angle
            time.sleep(0.04)
            distance_to_obj = fc.us.get_distance()
            scan_result.append((distance_to_obj, angle))
        # returns a list of tuples (distance cm, angle degrees)
        return scan_result
    
    # convert angle and distance into caretisan coordinates
    @staticmethod
    def get_cartesian(angle: float, distance: float) -> Coordinate:
        # x can be negative (since the car is in the middle of the grid along the x plane)
        x = math.floor(math.sin(math.radians(angle))*distance)
        # y will always be >= 0 (since the car cannot detect objects behind with the servo and ultrasonic sensor)
        y = math.floor(math.cos(math.radians(angle))*distance)
        coord = Coordinate(x_cord, y_cord)

        return coord
    
    # calculate slope between two x,y points
    @staticmethod
    def get_slope(coord1: Coordinate, coord2: Coordinate) -> float:
        if abs(coord2.x - coord1.x) > 0:
            slope = (y2 - y1)/(x2 - x1)
        # account for infinite slope
        else:
            slope = float(-999)
        
        return slope
    
    # get all x,y points between two x,y points
    def get_points_inbtw(self, coord1: Coordinate, coord2: Coordinate) -> List[Coordinate]:
        points_inbtw = []
        # first get the slope
        slope = self.get_slope(coord1, coord2)
        # we know the equation of the line between two points is y=mx+b, where b is the y intercept
        # calculate the y intercept using either x,y pair
        b = coord2.y - slope*coord1.x
        if b == -999:
            return points_inbtw
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
        
        return points_inbtw
    
    def move_forward(self, distance, seconds):
        # move the car backwards for number of seconds based on the result
        # of self.calc_sec_dist()
        fc.forward(self.power)
        time.sleep(seconds)
        # save the current location
        prev_loc = self.current_loc
        # update the current location in the map
        if self.direction == 'N':
            self.current_loc.y += distance
        elif self.direction == 'E':
            self.current_loc.x += distance
        elif self.direction == 'S':
            self.current_loc.y -= distance
        elif self.direction == 'W':
            self.current_loc.x -= distance
        
        # calculate the total manhattan distance traveled
        # Note: this is not used to find where the car is on the map
        # but could be useful for some other purpose, so let's keep it for now
        self.distance_traveled += self.calc_dist_mhtn(prev_loc, self.current_loc)
    
    def move_backward(self, distance, seconds):
        # move the car backwards for number of seconds based on the result
        # of self.calc_sec_dist()
        fc.backward(self.power)
        time.sleep(seconds)
        # save the current location
        prev_loc = self.current_loc
        # update the current location in the map
        if self.direction == 'N':
            self.current_loc.y -= distance
        elif self.direction == 'E':
            self.current_loc.x -= distance
        elif self.direction == 'S':
            self.current_loc.y += distance
        elif self.direction == 'W':
            self.current_loc.x += distance
        
        # calculate the total manhattan distance traveled
        # Note: this is not used to find where the car is on the map
        # but could be useful for some other purpose, so let's keep it for now
        self.distance_traveled += self.calc_dist_mhtn(prev_loc, self.current_loc)
    
    def turn_left_90(self):
        # based on experimentation to get a 90 degree turn
        fc.turn_left(30)
        time.sleep(0.95)
        # update the car's absolute direction
        if self.direction == 'N':
            self.direction = 'W'
        elif self.direction == 'E':
            self.direction = 'N'
        elif self.direction == 'S':
            self.direction = 'E'
        elif self.direction == 'W':
            self.direction = 'S'
    
    def turn_right_90(self):
        # based on experimentation to get a 90 degree turn
        fc.turn_right(30)
        time.sleep(0.95)
        # update the car's absolute direction
        if self.direction == 'N':
            self.direction = 'E'
        elif self.direction == 'E':
            self.direction = 'S'
        elif self.direction == 'S':
            self.direction = 'W'
        elif self.direction == 'W':
            self.direction = 'N'


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


    
"""
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
"""

if __name__ == "__main__":
    pass
    
    



    
    
    





