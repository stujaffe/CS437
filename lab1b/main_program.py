
from astar import astar
from navigate import PiCar
from helper_classes import Coordinate, Maze, Direction
import picar_4wd as fc
import math
import numpy as np

def main():
    
    # initialize map and start/end points
    global_map = Maze(3000,3000)
    
    global_start = Coordinate(0,0)
    global_end = Coordinate(100,100)
    
    # initialize the car
    picar = PiCar(start_loc=global_start, goal_loc=global_end)

    # keep track of the cycle so we can periodically clear the map
    cycle = 0
    
    # navigate the car along the path
    while True:

        # clear the map if every 2nd cycle
        if cycle > 0 and cycle % 2 == 0:
            global_map.maze.fill(0)
            picar.logger.info(f"Cleared the global map. Number of marked objects now: {global_map.maze.sum()}")
        
        path = None
        # starting point is the car's current location
        local_start = picar.current_loc
        # end navigation if car has reached it's destination
        if local_start == global_end:
            picar.logger.info(f"Congrats! The car has reached the destination point of {global_end}. Distance traveled: {round(picar.distance_traveled,2)}")
            picar.stop_car()
            break
        if ((local_start.x - global_end.x)**2 + (local_start.y - global_end.y)**2)**0.5 < 5:
            picar.logger.info(f"Congrats! The car has reached pretty close to its destination point of {global_end}. Distance traveled: {round(picar.distance_traveled,2)}")
            break
        if path is not None and len(path) == 1:
            picar.logger.info(f"Congrats! The car reached the end of the path, it's current location is {local_start} versus the goal of {global_end}. Distance traveled: {round(picar.distance_traveled,2)}")
            picar.stop_car()
            break
        
        # scan for obstacles and build a map
        scan = picar.scan_sweep_map()
        
        # get the cartesian coordinates from the ultrasonic sensor readings
        scan_points = []
        for item in scan:
            curr_point = picar.get_cartesian(angle=item[1], distance=item[0])
            scan_points.append(curr_point)
        
        scan_points = sorted(scan_points)
        
        picar.logger.info(f"Current location: {picar.current_loc}. Objects detected at: {scan_points}")
            
        # interpolation of the scanned points
        scan_points_lerp = []
        last_point = None
        for point in scan_points:
            scan_points_lerp.append(point)
            if last_point is not None:
                # interpolate points subject to distance threshold. that way if two object
                # readings are too far, they will be considered separate
                # 25cm is roughly the with of the car
                points_lerp = picar.supercover_line(last_point, point, picar.car_width_cm)
                for point in points_lerp:
                    scan_points_lerp.append(point)
            last_point = point
    
        # dedup points and sort
        scan_points_lerp = sorted(list(set(scan_points_lerp)))

        picar.logger.info(f"Current location: {picar.current_loc}. Object points interpolated: {scan_points_lerp}")

        # mark the objects on the map
        for point in scan_points_lerp:
            global_map.mark_object(point)
        
        # mark points in either direction direction along the a-xis so the car
        # has room to move around the object, otherwise the A* algo will just
        # alter the path slightly. e.g. from (1,2) to (2,2), but (2,2) is also blocked.
        all_buff_points = []
        if len(scan_points_lerp) > 0:
            radius = 1
            # mark buffers around the points
            for point in scan_points_lerp:
                buff_points = picar.within_radius(point, radius)
                for buff_point in buff_points:
                    if buff_point != picar.current_loc:
                        global_map.mark_object(buff_point)
                        # for logging purposes, make sure the point was actually marked
                        if global_map[buff_point.x,buff_point.y] == 1:
                            all_buff_points.append(buff_point)

        all_buff_points = sorted(list(set(all_buff_points)))
        
        # mark car's location (to be removed soon)
        global_map.maze[picar.current_loc.x,picar.current_loc.y] = 4

        picar.logger.info(f"The following buffer points were marked: {all_buff_points}")

        picar.logger.info(f"Total obstacles now marked on the map: {global_map.maze.sum()}")
        picar.logger.info(f"Current map around car: \n \
                {global_map.maze[picar.current_loc.x-5:picar.current_loc.x+6, picar.current_loc.y-5:picar.current_loc.y+6]}")    

        # mark the car's location back to 0
        global_map.maze[picar.current_loc.x,picar.current_loc.y] = 0

        # recompute the path with A* now that obstacles are marked
        picar.logger.info("Attempting to recompute new A* path.")
        path = astar(array = global_map, start=local_start, end=global_end)
        picar.logger.info(f"Recomputed path with A*: {path}")
        
        # figure out the farthest next point after the local_start the car does not
        # have to make a turn, the local_end
        local_end = global_end
        for point in path:
            if point == local_start:
                continue
            angle = picar.calc_angle_btwn(local_start, point)
            angle_45 = round(angle/45)*45
            # only bother if the angle is close enough to 45 degrees
            if abs(angle_45) >= 45:
                local_end = point
                break
        
        picar.logger.info(f"The farthest point without turning more than 45 dgrees is: {local_end}")
    
        # calculate turn angle adjusting for the car's current direction
        car_direction = Direction[picar.direction].value
        picar.logger.info(f"The angle between the points at 0 degree direction: {round(angle,2)}. Rounded to nearest 45: {round(angle_45,2)}. Car's current angle direction: {car_direction}.")
        turn_data = picar.get_turn_data(angle_45)
        
    
        # turn the car if needed to face the global destination
        if turn_data.get("turn_direction") == "left":
            picar.turn_left(turn_data.get("seconds"),turn_data.get("angle"))
        if turn_data.get("turn_direction") == "right":
            picar.turn_right(turn_data.get("seconds"),turn_data.get("angle"))
        

        # get distance between coordinates and seconds to move based on ucrrent power
        movement_data = picar.get_movement_data(local_start, local_end)

        # move the car forward after turning
        picar.move_forward(movement_data.get("distance"), movement_data.get("seconds"))

        cycle += 1
       
        
            
if __name__ == "__main__":

    try:
        main()
    except Exception as e:
        print(e)
        fc.stop()
    
    
    
    
    
    
