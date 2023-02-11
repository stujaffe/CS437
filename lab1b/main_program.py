
from astar import astar
from navigate import PiCar
from helper_classes import Coordinate, Maze, Direction
import picar_4wd as fc
import math
import numpy as np

def main():
    
    # initialize map and start/end points
    global_map = Maze(3000,3000)
    
    # set the upper and lower bounds of the map. for example, in a 3000x3000
    # array you could have the lower bound be 0 for x and y and the upper bound
    # be 3000 for x and y. Or the lower bound could be -1000 for x and y and
    # the upper bound be 2000 for x and y. This will influence whether the scans
    # from the ultrasonic sensor for mapping purposes will mark objects.
    x_lower = 0
    x_upper = 3000
    y_lower = 0
    y_upper = 3000
    
    global_start = Coordinate(0,0)
    global_end = Coordinate(100,100)
    
    # initialize the car
    picar = PiCar(start_loc=global_start, goal_loc=global_end)

    # keep track of the cycle so we can periodically clear the map
    cycle = 0
    
    # navigate the car along the path
    while True:

        path = None
        # starting point (local start) is the car's current location
        local_start = picar.current_loc
        # get angle associated with current direction N/W/E/S
        angle_direction = Direction[picar.direction].value
        
        # first check to see if we can end the navigation
        if local_start == global_end:
            picar.logger.info(f"Congrats! The car has reached the destination point of {global_end}. Distance traveled: {round(picar.distance_traveled,2)}")
            picar.stop_car()
            break
        if ((local_start.x - global_end.x)**2 + (local_start.y - global_end.y)**2)**0.5 < 4:
            picar.logger.info(f"Congrats! The car has reached {local_start}, pretty close to its destination point of {global_end}. Distance traveled: {round(picar.distance_traveled,2)}")
            break
        if path is not None and len(path) == 1:
            picar.logger.info(f"Congrats! The car reached the end of the path, it's current location is {local_start} versus the goal of {global_end}. Distance traveled: {round(picar.distance_traveled,2)}")
            picar.stop_car()
            break
        
        # clear the map so the car doesn't get confused by previous object readings
        global_map.maze.fill(0)
        picar.logger.info(f"Cleared the global map. Number of marked objects now: {global_map.maze.sum()}")
        
        
        # while the car is stopped, scan the surroundings for obstacles
        scan = picar.scan_sweep_map()
        
        # get the cartesian coordinates from the ultrasonic sensor readings
        # the get_cartesian() function will adjust for the car's location by default, but
        # you can adjust that parameter
        scan_points = []
        for item in scan:
            curr_point = picar.get_cartesian(angle=item[1], distance=item[0])
            is_in_map = picar.is_point_in_map(curr_point, x_lower=x_lower, x_upper=x_upper, y_lower=y_lower, y_upper=y_upper)
            if is_in_map:
                scan_points.append(curr_point)
        
        # if the car detects any objects, then navigate to a "clearance point"
        # the "clearance point" is defined as follows:
        ## 1. Take the farthest 1 (i.e. marked obstacle) from the car's current location
        ## 2. Make sure there is a buffer between that 1 and the clearance point
        ## while keeping the clearance point as close as possible to the global end point
        if len(scan_points) > 0:
        
            # sort the points so the interpolation is easier
            scan_points = sorted(scan_points)
        
            picar.logger.info(f"Current location: {picar.current_loc}. Objects detected at: {scan_points}")
            
            # interpolation of the scanned points
            scan_points_lerp = []
            prev_point = None
            for curr_point in scan_points:
                scan_points_lerp.append(curr_point)
                if prev_point is not None:
                    # interpolate points subject to distance threshold. that way if two object
                    # readings are too far, they will be considered separate
                    # 25cm is roughly the with of the car
                    points_lerp = picar.supercover_line(prev_point, curr_point, picar.car_width_cm)
                    for point in points_lerp:
                        scan_points_lerp.append(point)
                prev_point = curr_point
    
            # dedup points and sort
            scan_points_lerp = sorted(list(set(scan_points_lerp)))

            picar.logger.info(f"Current location: {picar.current_loc}. Object points interpolated: {scan_points_lerp}")

            # mark the objects on the map
            for point in scan_points_lerp:
                global_map.mark_object(coord1=point, x_lower=x_lower, x_upper=x_upper, y_lower=y_lower, y_upper=y_upper)
        
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
                            global_map.mark_object(coord1=buff_point, x_lower=x_lower, x_upper=x_upper, y_lower=y_lower, y_upper=y_upper)
                            # for logging purposes, make sure the point was actually marked
                            if global_map[buff_point.x,buff_point.y] == 1:
                                all_buff_points.append(buff_point)

            all_buff_points = sorted(list(set(all_buff_points)))
        
            # mark car's location (to be removed soon)
            global_map.maze[picar.current_loc.x,picar.current_loc.y] = 4

            picar.logger.info(f"The following buffer points were marked: {all_buff_points}")

            picar.logger.info(f"Total obstacles now marked on the map: {np.sum(global_map.maze[global_map.maze==1])}")
            picar.logger.info(f"Current map around car: \n \
                    {global_map.maze[picar.current_loc.x-5:picar.current_loc.x+6, picar.current_loc.y-5:picar.current_loc.y+6]}")    

            # mark the car's location back to 0
            global_map.maze[picar.current_loc.x,picar.current_loc.y] = 0
        
            # first get the map subset where the cluster of ones should be (i.e. in front of the car
            # all the way to the global end)
            cluster_coordinates = np.where(global_map.maze == 1)
            # now get that clearance point. if there are no obstacles marked, this will be the same
            # as the global end point
            clearance_point = picar.find_farthest_point(global_map.maze, cluster_coordinates, local_start, global_end, 5)
            picar.logger.info(f"The clearance point past the object markers is: {clearance_point}")
        
        
            # recompute the path with A* now that obstacles are marked
            picar.logger.info("Attempting to recompute new A* path.")
            path = astar(array = global_map, start=local_start, end=clearance_point)
            picar.logger.info(f"Recomputed path with A*: {path}")
            
            # navigate the car around the object to the clearance point with the A* path
        
            prev_step = None
            for curr_step in path:
                
                # skip current location
                if curr_step == local_start:
                    prev_step = curr_step
                    continue
                
                # calculate turn angle adjusting for the car's current direction
                angle_btwn_points = picar.calc_angle_btwn(prev_step, curr_step)
                picar.logger.info(f"The angle between the points at 0 degree direction: {round(angle_btwn_points,2)}. Car's current angle direction: {round(Direction[picar.direction].value,2)}.")
                # the get_turn_data() function will adjust for the car's direction and get the angle to turn
                # in the nearest 45 degree increment
                turn_data = picar.get_turn_data(angle_btwn_points)
                
                picar.logger.info(f"The car is turning {turn_data.get('angle')} degrees.")
                # turn the car if needed to face the global destination
                if turn_data.get("turn_direction") == "left":
                    picar.turn_left(turn_data.get("seconds"),turn_data.get("angle"))
                if turn_data.get("turn_direction") == "right":
                    picar.turn_right(turn_data.get("seconds"),turn_data.get("angle"))
                    
                # get distance between coordinates and seconds to move based on current power
                movement_data = picar.get_movement_data(prev_step, curr_step)

                # move the car forward after turning
                picar.move_forward(movement_data.get("distance"), movement_data.get("seconds"))
            
        # if there are no objects to be mapped, then continue onward to the global end
        # while continuing to scan for objects in order to avoid (not mapping)
        else:
            
            # mark car's location (to be removed soon)
            global_map.maze[picar.current_loc.x,picar.current_loc.y] = 4

            picar.logger.info(f"Total obstacles now marked on the map: {np.sum(global_map.maze[global_map.maze==1])}")
            picar.logger.info(f"Current map around car: \n \
                    {global_map.maze[picar.current_loc.x-5:picar.current_loc.x+6, picar.current_loc.y-5:picar.current_loc.y+6]}")    

            # mark the car's location back to 0
            global_map.maze[picar.current_loc.x,picar.current_loc.y] = 0
            
            # recompute the path with A* with no obstacles marked
            picar.logger.info("Attempting to recompute new A* path.")
            path = astar(array = global_map, start=local_start, end=global_end)
            picar.logger.info(f"Recomputed path with A*: {path}")
            
            # figure out the farthest next point (local_end) after the local_start the car does not have to make a turn
            local_end = global_end
            for step in path:
                if step == local_start:
                    continue
                angle_btwn_points = picar.calc_angle_btwn(local_start, step)
                angle_adj = angle_btwn_points - Direction[picar.direction].value 
                angle_adj_45 = round(angle_adj/45)*45
                # take the closest point that requires at least a 45 degree turn taking into account the car's direction
                if abs(angle_adj_45) >= 45:
                    local_end = step
                    break
        
            picar.logger.info(f"The farthest point without turning more than 45 dgrees is: {local_end}")
            
            picar.logger.info(f"The angle between the points at 0 degree direction: {round(angle_btwn_points,2)}. Car's current angle direction: {round(Direction[picar.direction].value,2)}.")
            # the get_turn_data() function will adjust for the car's direction and get the angle to turn
            # in the nearest 45 degree increment
            turn_data = picar.get_turn_data(angle_btwn_points)
            
            picar.logger.info(f"The car is turning {turn_data.get('angle')} degrees.")
            # turn the car if needed to face the global destination
            if turn_data.get("turn_direction") == "left":
                picar.turn_left(turn_data.get("seconds"),turn_data.get("angle"))
            if turn_data.get("turn_direction") == "right":
                picar.turn_right(turn_data.get("seconds"),turn_data.get("angle"))
                
            # get distance between coordinates and seconds to move based on current power
            movement_data = picar.get_movement_data(local_start, local_end)

            # move the car forward after turning
            picar.move_forward(movement_data.get("distance"), movement_data.get("seconds"))
    
            
if __name__ == "__main__":

    try:
        main()
    except Exception as e:
        print(f"Encountered the following exception in the main program: {e}")
        fc.stop()
    
    
    
    
    
    
