
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
        threshold: int = 15, # object avoidance clearance in cm
        car_width_cm: int = 25,
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
        self.distance_to_obj = -2
        self.car_width_cm = car_width_cm
        self.logger = logging.getLogger()
        logging.basicConfig(format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                datefmt='%Y-%m-%d:%H:%M:%S',
                level=logging.DEBUG)
        fc.servo.set_angle(self.current_angle)

    
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
            turn_sec = 0.48
        elif abs(angle_turn) == 90:
            turn_sec = 0.92
        elif abs(angle_turn) == 135:
            turn_sec = 1.35
        elif abs(angle_turn) == 180:
            turn_sec = 1.75
        
        if angle_turn > 0:
            turn_command = "left"
        elif angle_turn < 0: 
            turn_command = "right"
        else:
            turn_command = "no_turn"
        
        turn_data = {"turn_direction":turn_command, "seconds":turn_sec, "angle":angle_turn}
        
        return turn_data

    def get_movement_data(self, coord1: Coordinate, coord2: Coordinate) -> dict:

        # euclidean distance
        distance = ((coord1.x - coord2.x)**2 + (coord1.y - coord2.y)**2)**0.5

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

   
   # scan the area in front of the car for obstacle avoidance purposes
    def scan_sweep_avoid(self):
        self.current_angle += self.step
        if self.current_angle >= self.max_angle:
            self.current_angle = self.max_angle
            self.step = abs(self.step)*-1
        elif self.current_angle <= self.min_angle:
            self.current_angle = self.min_angle
            self.step = abs(self.step)

        fc.servo.set_angle(self.current_angle)
        self.distance_to_obj = fc.us.get_distance()
        time.sleep(0.04)


    # scan the area in front of the car for mapping purposes
    # you can set a max distance (cm) for which the scan will return (distance, angle)
    # since the ultrasonic sensor can be unreliable from too far
    def scan_sweep_map(self, max_dist: int=50) -> Union[List[Tuple[float, int]], None]:
        scan_result = []
        # ensure the sensor gets readings going in both directions depending upon
        # the current angle of the sensor.
        if self.current_angle > 0:
            start_angle = self.max_angle
            end_angle = self.min_angle
            step = abs(self.step)*-1
        else:
            start_angle = self.min_angle
            end_angle = self.max_angle
            step = abs(self.step)

        for angle in range(start_angle, end_angle+step, step):
            fc.servo.set_angle(angle)
            self.current_angle = angle
            time.sleep(0.04)
            distance_to_obj = fc.us.get_distance()
            if distance_to_obj > -2 and distance_to_obj <= max_dist:
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
        angle_adj = angle + Direction[self.direction].value
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
        self, coord1: Coordinate, coord2: Coordinate, dist_threshold: float = 25.0
    ) -> List[Coordinate]:
        
        points_inbtwn = []
        
        # calculate euclidean distance between points to see if we should interpolate them
        dist = ((coord1.x - coord2.x)**2 + (coord1.y - coord2.y)**2)**0.5
        
        if dist <= dist_threshold:
            # first get the slope
            slope = self.get_slope(coord1, coord2)
            # we know the equation of the line between two points is y=mx+b, where b is the y intercept
            # calculate the y intercept using either x,y pair
            b = coord1.y - slope * coord1.x
            if b == -999:
                return points_inbtwn
            # now loop from the lower to higher x coordinate and get the x,y points in between
            x_sorted = sorted([coord1.x, coord2.x])
            
            for x in range(x_sorted[0], x_sorted[1]):
                y_calc = slope * x + b
                point = Coordinate(x, y_calc)
                if point not in points_inbtwn:
                    points_inbtwn.append(point)

        return points_inbtwn
    
    def avoid_object(self):
        self.logger.info(f"Detected potential object {self.distance_to_obj}cm away, within threshold of {self.threshold}cm. Stopping.")
        fc.stop()

    def move_forward(self, distance, seconds):
        self.logger.info(f"Moving FORWARD at {self.power} power for {seconds} seconds for a distance of {distance}cm")
        # move the car forwards for a number of seconds
        curr_time = time.time()
        stop_time = curr_time + seconds
        # while the car is moving forward for the given number of seconds, scan the surroundings for object detection
        # and if an object is found via self.scan_sweep_avoid(), a -999 return value results, so avoid object and break the loop..
        while curr_time < stop_time:
            fc.forward(self.power)
            self.scan_sweep_avoid()
            if self.distance_to_obj > -2 and self.distance_to_obj <= self.threshold:
                self.avoid_object()
                # need a new distance since the car didn't travel the whole original distance
                distance = max(0,(stop_time-curr_time)/seconds*distance)
                self.logger.info(f"Stopped early due to object detection, traveled {distance}cm.")
                break
            curr_time = time.time()
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
        if new_direction_angle < -180:
            new_direction_angle = new_direction_angle + 360
        elif new_direction_angle > 180:
            new_direction_angle = new_direction_angle - 360
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
        if new_direction_angle < -180:
            new_direction_angle = new_direction_angle + 360
        elif new_direction_angle > 180:
            new_direction_angle = new_direction_angle - 360
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
    
    from astar import astar

    start = Coordinate(0,0)
    end = Coordinate(0,20)

    picar = PiCar(start_loc=start, goal_loc=end)
    
    global_map = Maze(50,50)
    
    path1 = astar(maze = global_map, start=start, end=end)

    scan = picar.scan_sweep_map()
    
    print(scan)
    

    points = []
    last_point = None
    for item in scan:
        curr_point = picar.get_cartesian(angle=item[1], distance=item[0])
        points.append(curr_point)
        if last_point is not None:
            points_inbtwn = picar.get_points_inbtwn(last_point, curr_point)
            for point in points_inbtwn:
                points.append(point)
        last_point = curr_point
    
    # dedup points
    points = list(set(points))
    print(points)
    
    for point in points:
        global_map.mark_object(point)
    
    path2 = astar(maze = global_map, start=start, end=end)
    
    print(path1)
    print(path2)
    
        
    
        





