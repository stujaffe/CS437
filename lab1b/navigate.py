
"""
Picar navigation and mapping of surrounding area.
"""

import picar_4wd as fc
import numpy as np
import logging
import math
import time
from typing import List, Tuple, Union
from helper_classes import Coordinate, Direction, Maze
    

class PiCar(object):
    def __init__(
        self,
        start_loc: Coordinate,
        goal_loc: Coordinate,
        power: int = 10,
        direction: str = Direction.north.name,
        angle_range: int = 140,
        threshold: int = 15, # object clearance in cm
    ) -> None:
        self.start_loc = start_loc
        self.goal_loc = goal_loc
        self.current_loc = start_loc
        self.direction = direction
        self.distance_traveled = 0
        self.power = power
        self.angle_range = angle_range
        self.step = math.floor(angle_range / 10)
        self.max_angle = int(angle_range / 2)
        self.min_angle = int(angle_range / 2 * -1)
        self.current_angle = 0
        self.speed_at_10 = 26.70
        self.threshold = threshold
        self.logger = logging.getLogger()
        logging.basicConfig(format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                datefmt='%Y-%m-%d:%H:%M:%S',
                level=logging.DEBUG)

    
    # calculate the angle (in degrees) between two coordinates on x,y plane given our 45 degree increment constraint
    @staticmethod
    def calc_angle_btwn(coord1: Coordinate, coord2: Coordinate) -> float:
        y_delta = coord2.y - coord1.y
        x_delta = coord2.x - coord1.x
        # usually arctan is calculated with y as the first argument, but that gives the angle between two
        # points along the x-axis. we are assuming north (along the y-axis) is 0 degrees so we want to swap
        # the arguments and have the x-axis delta be the first argument. we could just "rotate" the xy plane
        # so that north is along the x-axis, but it's more intuitive to visualize north along the y-axis.
        # in addition, we multiply by -1 since in our Direction class, we specify east as -90 degrees and the
        # arctan function with the x and y swapped will return 90 degrees for a point directly "east" of another point
        # on the x-axis but we need that point to be -90 degrees.
        angle_degrees = math.degrees(math.atan2(x_delta, y_delta))*-1
        # round the closest 45 degree increment
        angle_degrees = round(angle_degrees/45)*45

        return angle_degrees
    
    # get the turn direction (left/right) and how long to engage the turn
    def get_turn_data(self, angle_btwn: float) -> dict:
        # get angle associated with current direction N/W/E/S
        angle_direction = Direction[self.direction].value
        # get the angle the car needs to turn
        # e.g. for a -90 degree angle between coordindates and the car is going southwest, angle_turn = -90 - 135 = -225
        angle_turn = angle_btwn - angle_direction
        
        # if the value of angle_turn is negative, the car turns right. if positive, the car turns left.
        # this is based on how we oriented the angles and directions

        # if the angle_turn value is greater than 180, then we can swap the turn direction to save time/power
        # e.g. the example above a car needs to turn -225 degrees (i.e. 225 degrees right), but we can have the
        # car turn 135 degrees (i.e. 135 degrees left)
        if angle_turn < -180:
            angle_turn = angle_turn + 360
        elif angle_turn > 180:
            angle_turn = angle_turn - 360
        
        # calculate the time to turn. assumes power=30 when turning (from experimentation)
        turn_sec = 0
        if abs(angle_turn) == 45:
            turn_sec = 0.51
        elif abs(angle_turn) == 90:
            turn_sec = 1
        elif abs(angle_turn) == 135:
            turn_sec = 1.45
        elif abs(angle_turn) == 180:
            turn_sec = 2.02
        
        if angle_turn > 0:
            turn_command = "left"
        elif angle_turn < 0: 
            turn_command = "right"
        else:
            turn_command = "no_turn"
        
        turn_data = {"turn_direction":turn_command, "seconds":turn_sec, "angle":angle_turn}
        
        return turn_data

    def get_movement_data(self, coord1: Coordinate, coord2: Coordinate) -> dict:

        # angle between coordinates in 45 degree increments
        angle_btwn = self.calc_angle_btwn(coord1=coord1, coord2=coord2)
        # now adjust for the direction the car is heading. for example, the points (1,0) and (2,0) will have
        # an angle_btwn value of -90 because that assumes that is facing north (degree=0) but if it is
        # facing east (degree=-90), then there is no angle between them.
        angle_btwn_adj = angle_btwn - Direction[self.direction].value

        # now calculate the distance between the coordiantes using the law of cosines to generalize
        a = (coord1.x**2 + coord1.y**2)**0.5
        b = (coord2.x**2 + coord2.y**2)**0.5
        c = math.radians(angle_btwn_adj)
        distance = (a**2 + b**2 - 2*a*b*math.cos(c))**0.5

        # calculate the seconds to move
        seconds = distance / self.get_speed()

        movement_data = {"distance": distance, "seconds": seconds}

        return movement_data


    # calculate the speed in cm/s for a given power
    def get_speed(self):
        if self.power == 10:
            return self.speed_at_10
        # extra speed is the power above 10 subtracted by 10 then divided by 10, multiplied by 2.5
        # During test I found for every 10 extra power above 10, the car moved 2.5 cm/s faster. E.g. at 20 power the speed is 26.7 + 2.5
        extra = (self.power - 10) / 10 * 2.5
        self.speed = self.speed_at_10 + extra

        return self.speed

    # scan the area in front of the car. set for_map=True when you want
    # to return the results, otherwise when for_map=False, this will scan
    # for objects so the car can stop and not hit them.
    def scan_sweep(self, for_map: bool=False) -> Union[List[Tuple[float, int]], None]:
        scan_result = []
        # ensure the sensor gets readings going in both directions depending upon
        # the current angle of the sensor.
        if self.current_angle > 0:
            start_angle = self.max_angle
            end_angle = self.min_angle - self.step
            step = abs(self.step)*-1
        else:
            start_angle = self.min_angle
            end_angle = self.max_angle + self.step
            step = abs(self.step)
        for angle in range(start_angle, end_angle, step):
            fc.servo.set_angle(angle)
            self.current_angle = angle
            time.sleep(0.04)
            distance_to_obj = fc.us.get_distance()
            if for_map == False and distance_to_obj <= self.threshold:
                self.avoid_object()
                return None
            scan_result.append((distance_to_obj, angle))
        # returns a list of tuples (distance cm, angle degrees)
        return scan_result

    # convert angle and distance into caretisan coordinates
    def get_cartesian(self, angle: float, distance: float) -> Coordinate:
        # we need to adjust the angle based on the direction of the car
        # if the car is going north (0 degrees) then the angle from the ultrasonic
        # sensor does not need to be adjusted. However, if the car is, for example,
        # traveling southwest at 135 degrees, we need to get the correct cartesian
        # coordinates on an absolute basis on the map. That is, relative to north being
        # 0 degrees along the y-axis. Otherwise, incorrect cells will be calculated.
        angle_adj = Direction[self.direction].value + angle
        # x is usually calculated using cosine and y from sine but that is from the perspective
        # of the x-axis and in this case the car has 0 degrees on the y-axis
        # x can be negative (since the car is in the middle of the grid along the x plane)
        # we want to multiply x by -1
        x = math.sin(math.radians(angle_adj)) * distance*-1
        # y will always be >= 0 (since the car cannot detect objects behind with the servo and ultrasonic sensor)
        y = math.cos(math.radians(angle_adj)) * distance
        # relative coordinate
        coord_rel = Coordinate(x, y)
        # absolute coorindate, taking into account where the car is
        coord_abs = Coordinate(self.current_loc.x + x, self.current_loc.y + y)
        self.logger.info(f"Calculated abs point {coord_abs} from current loc {self.current_loc}, rel point {coord_rel}, {angle} angle, {distance} distance")

        return coord_abs

    # calculate slope between two x,y points
    @staticmethod
    def get_slope(coord1: Coordinate, coord2: Coordinate) -> float:
        if abs(coord2.x - coord1.x) > 0:
            slope = (coord2.y - coord1.y) / (coord2.x - coord1.x)
        # account for infinite slope
        else:
            slope = float(-999)

        return slope

    # get all x,y points between two x,y points
    def get_points_inbtwn(
        self, coord1: Coordinate, coord2: Coordinate
    ) -> List[Coordinate]:
        points_inbtwn = []
        # first get the slope
        slope = self.get_slope(coord1, coord2)
        # we know the equation of the line between two points is y=mx+b, where b is the y intercept
        # calculate the y intercept using either x,y pair
        b = coord1.y - slope * coord1.x
        if b == -999:
            return points_inbtwn
        # now loop from the lower to higher x coordinate and get the x,y points in between
        if coord1.x > coord2.x:
            x_high = coord1.x
            x_low = coord2.x
        else:
            x_high = coord2.x
            x_low = coord1.x

        for x in range(x_low+1, x_high):
            y_calc = slope * x + b
            point = Coordinate(x, y_calc)
            if point not in points_inbtwn:
                points_inbtwn.append(point)

        return points_inbtwn
    
    def avoid_object(self):
        self.logger.info(f"Detected potential object with threshold of {self.threshold}cm. Stopping.")
        fc.stop()

    def move_forward(self, distance, seconds):
        self.logger.info(f"Moving FORWARD at {self.power} power for {seconds} seconds for a distance of {distance}cm")
        # move the car forwards for a number of seconds
        fc.forward(self.power)
        time.sleep(seconds)
        fc.stop()

        # save the current location
        prev_loc = Coordinate(self.current_loc.x, self.current_loc.y)
        # update the current location in the x,y plane
        # swap the cosine and sine function again since the car's perspective is along
        # the y-axis. also multiply by -1 since going along the positive a-axis is "east" and that is -90 degree direction
        self.current_loc.x = prev_loc.x + math.floor(distance*math.sin(math.radians(Direction[self.direction].value)))*-1
        self.current_loc.y = prev_loc.y + math.floor(distance*math.cos(math.radians(Direction[self.direction].value)))
        self.logger.info(f"After moving forward, new location: {self.current_loc}, previous location: {prev_loc}")

        # keep track of the distance traveled
        self.distance_traveled += distance

    def turn_left(self, seconds: float, turn_angle: float):
        self.logger.info(f"Turning LEFT for {seconds} seconds at an angle of {turn_angle}")
        fc.turn_left(30)
        time.sleep(seconds)
        # update the car's absolute direction
        prev_direction_angle = Direction[self.direction].value
        new_direction_angle = prev_direction_angle + turn_angle
        self.logger.info(f"After turning LEFT, new direction angle: {new_direction_angle}, previous direction angle: {prev_direction_angle}")
        try:
            self.direction = Direction(new_direction_angle).name
        except:
            fc.stop()
            raise Exception(f"New direction angle of {new_direction_angle} is not valid. Current direction angle: {Direction[self.direction]} \
                                and turn angle: {turn_angle}. Angle changes should be in increments of 45 degrees.")
            
    def turn_right(self, seconds: float, turn_angle: float):
        self.logger.info(f"Turning RIGHT for {seconds} seconds at an angle of {turn_angle}")
        fc.turn_right(30)
        time.sleep(seconds)
        # update the car's absolute direction
        prev_direction_angle = Direction[self.direction].value
        new_direction_angle = prev_direction_angle + turn_angle
        self.logger.info(f"After turning RIGHT, new direction angle: {new_direction_angle}, previous direction angle: {prev_direction_angle}")
        try:
            self.direction = Direction(new_direction_angle).name
        except:
            fc.stop()
            raise Exception(f"New direction angle of {new_direction_angle} is not valid. Current direction angle: {Direction[self.direction]} \
                                and turn angle: {turn_angle}. Angle changes should be in increments of 45 degrees.")
    
    def stop_car(self):
        fc.stop()


if __name__ == "__main__":
    # various testing, debugging
    point1 = Coordinate(0,0)
    point2 = Coordinate(0,9)
    
    angle1 = 45
    distance1 = 10
    
    start = Coordinate(9,9)
    end = Coordinate(9,0)
    picar = PiCar(start_loc=start, goal_loc=end)
    print(f"Current direction : {picar.direction}")
    
    movement_data = picar.get_movement_data(point1, point2)
    print(movement_data)
    angle_btwn = picar.calc_angle_btwn(point1, point2)
    print(angle_btwn)
    turn_data = picar.get_turn_data(angle_btwn)
    print(turn_data)
    points_inbtwn = picar.get_points_inbtwn(point1, point2)
    [print(x) for x in points_inbtwn]
    
    """
    # empty map
    global_map = Maze(20,20)
    print(global_map)
    
    # mark objects
    for coord in points_inbtwn:
        global_map.mark_object(coord)
        
    print(global_map)
    
    scan_sweep = picar.scan_sweep()
    print(scan_sweep)
    """
    
