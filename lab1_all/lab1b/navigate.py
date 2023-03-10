
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
        us_offset: int = 8 # offset for ultasonic distance readings in cm, the larger the more buffer
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
        self.avoid_obstacle_time = None
        self.us_offset = us_offset
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

        return angle_degrees
    
    # get the turn direction (left/right) and how long to engage the turn
    def get_turn_data(self, angle_btwn: float) -> dict:
        
        # get the angle the car needs to turn
        angle_turn = angle_btwn - Direction[self.direction].value
        angle_turn = round(angle_turn/45)*45
        
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
    
    @staticmethod
    def calc_euclid_dist(coord1: Coordinate, coord2: Coordinate) -> float:
        distance = ((coord1.x - coord2.x)**2 + (coord1.y - coord2.y)**2)**0.5

        return distance

    def get_movement_data(self, coord1: Coordinate, coord2: Coordinate) -> dict:

        # euclidean distance
        distance = self.calc_euclid_dist(coord1, coord2)

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
        self.distance_to_obj = fc.us.get_distance() - self.us_offset
        time.sleep(0.02)

    # is the point within the boundaries of the map
    # note this only works when the car is stationary and knows its current location
    @ staticmethod
    def is_point_in_map(coord1: Coordinate, x_lower: int, x_upper: int, y_lower: int, y_upper: int) -> bool:
        result = False
        if coord1.x >= x_lower and coord1.x < x_upper and coord1.y >= y_lower and coord1.y < y_upper:
            result = True
        
        return result

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
            distance_to_obj = fc.us.get_distance() - self.us_offset
            if distance_to_obj > -2 and distance_to_obj <= max_dist:
                scan_result.append((distance_to_obj, angle))
        # returns a list of tuples (distance cm, angle degrees)
        return scan_result

    # convert angle and distance into caretisan coordinates
    def get_cartesian(self, angle: float, distance: float, adjust_for_car: bool = True) -> Coordinate:
        # we need to adjust the angle based on the direction of the car
        # if the car is going north (0 degrees) then the angle from the ultrasonic
        # sensor does not need to be adjusted. However, if the car is, for example,
        # traveling southwest at 135 degrees, we need to get the correct cartesian
        # coordinates on an absolute basis on the map. That is, relative to north being
        # 0 degrees along the y-axis. Otherwise, incorrect cells will be calculated.
        angle_adj = (angle + Direction[self.direction].value) % 360
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
        if adjust_for_car:
            coord_abs = Coordinate(self.current_loc.x + x, self.current_loc.y + y)
        else:
            coord_abs = coord_rel

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
    
    # find all the points with a certain radius of a given point
    def within_radius(self, coord1, radius):
        points = []
        for x2 in range(coord1.x - radius, coord1.x + radius + 1):
            for y2 in range(coord1.y - radius, coord1.y + radius + 1):
                points.append(Coordinate(x2,y2))
        return points
    
    # get all the points "behind" the car so that an obstacles marked as 1, especially via buffer points,
    # are not behind the car, causing erroroneous maps
    # the area_dim (x,y) arugment will determine which part of the sub for which we want the behind coordinates
    # otherwise, this calculation can take a long time
    @staticmethod
    def get_coordinates_behind(arr: Maze, position: Coordinate, angle: float, area_dim: tuple,
                            x_lower: int, x_upper: int, y_lower: int, y_upper: int):
        
        arr_sub = arr.maze[min(position.x-area_dim[0],x_lower):max(position.x+area_dim[0],x_upper),
                    min(position.y-area_dim[1],y_lower):max(position.y+area_dim[1],y_upper)]
        angle = angle - 90
        angle = np.radians(-angle)
        x, y = position.x, position.y
        x = int(x)
        y = int(y)
        indices = np.where(arr_sub == 0)
        x_indices = indices[0]
        y_indices = indices[1]
        coords = np.stack([x_indices, y_indices], axis=-1)
        # results in a 2D array with shape (N, 1) where N is the number of zero elements in the maze. 
        # the result is then used to determine which points are behind the car by checking if the first element of each row is greater than zero
        behind = (coords - [x, y]) @ np.array([[np.cos(angle)], [-np.sin(angle)]])
        behind_indices = coords[behind[:, 0] > 0]
        behind_coordinates = [Coordinate(*coord) for coord in behind_indices]
        
        return behind_coordinates

    
    # calculate the points between two coordinates with a supercover line that catches
    # all the coordinates in between
    # from this website: https://www.redblobgames.com/grids/line-drawing.html
    @staticmethod
    def supercover_line(coord1: Coordinate, coord2: Coordinate, dist_threshold: int, 
    blocked_coords: List[Coordinate] = []) -> List[Coordinate]:
        
        # make sure the points are close enough before interpolating
        if ((coord1.x - coord2.x)**2 + (coord1.y - coord2.y)**2)**0.5 > dist_threshold:
            return [coord1, coord2]
        else:
            dx = coord2.x - coord1.x
            dy = coord2.y - coord1.y
            nx = abs(dx)
            ny = abs(dy)
            sign_x = 1 if dx > 0 else -1
            sign_y = 1 if dy > 0 else -1
            p = Coordinate(coord1.x, coord1.y)
            prev_p = p
            points = [p]
            ix, iy = 0, 0
            while ix < nx or iy < ny:
                decision = (1 + 2 * ix) * ny - (1 + 2 * iy) * nx
                if decision == 0:
                    p = Coordinate(p.x + sign_x, p.y + sign_y)
                    ix += 1
                    iy += 1
                elif decision < 0:
                    p = Coordinate(p.x + sign_x, p.y)
                    ix += 1
                else:
                    p = Coordinate(p.x, p.y + sign_y)
                    iy += 1
                if p in blocked_coords:
                    break
                points.append(p)
                
            return points
    
    def avoid_object(self):
        object_coord = self.get_cartesian(self.current_angle, self.distance_to_obj)
        self.logger.info(f"Object {round(self.distance_to_obj,2)}cm away at an angle of {self.current_angle} degrees at point {object_coord}, within threshold of {self.threshold}cm. Stopping.")
        fc.stop()

    # scan is a boolean value that denotes whether to scan for objects while moving
    def move_forward(self, distance: float, seconds: float, scan: bool):
        self.logger.info(f"Moving FORWARD at {self.power} power for {round(seconds,2)}sec for a distance of {round(distance,2)}cm")
        # move the car forwards for a number of seconds
        start_time = curr_time = time.time()
        stop_time = start_time + seconds
        # while the car is moving forward for the given number of seconds, scan the surroundings for object detection
        # and if an object is found via self.scan_sweep_avoid(), a -999 return value results, so avoid object and break the loop..
        while curr_time < stop_time:
            fc.forward(self.power)
            if scan:
                self.scan_sweep_avoid()
                if self.distance_to_obj > 0 and self.distance_to_obj <= self.threshold:
                    self.avoid_object()
                    curr_time = time.time()
                    # need a new distance since the car didn't travel the whole original distance
                    move_time = curr_time - start_time
                    distance = (move_time/seconds)*distance
                    self.logger.info(f"Stopped early due to object detection, traveled {round(distance,2)}cm in {round(move_time,2)}sec.")
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
        elif new_direction_angle >= 180:
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
        elif new_direction_angle >= 180:
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
    
    # given a location and object coordiantes, find the "farthest" object coordindate
    # from the given location
    @staticmethod
    def find_farthest_point(location: Coordinate, object_coordinates):
        farthest_point = None
        max_distance = 0
        for coord in object_coordinates:
            curr_distance = np.linalg.norm(np.array([coord.x, coord.y]) - np.array([location.x,location.y]))
            if curr_distance > max_distance:
                max_distance = curr_distance
                farthest_point = coord

        return farthest_point
    
    # given a starting, ending, and farthest object position, figure out if the car has passed
    # the farthest object point subject to a given buffer distance
    @staticmethod
    def has_passed_object(start: Coordinate, end: Coordinate, object_pos: Coordinate, buffer_dist: int) -> bool:
        displacement = end - start
        displacement = np.array([displacement.x, displacement.y])
        object_to_start = object_pos - start
        object_to_start = np.array([object_to_start.x, object_to_start.y])
        dot_product = np.dot(displacement, object_to_start)
        has_passed = dot_product < -(buffer_dist**2)
        return has_passed


if __name__ == "__main__":
    
    pass
    
    
    
    
    
    

    
        
    
        





