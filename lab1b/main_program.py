
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
    
    # navigate the car along the path
    while True:
        
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
    
        # dedup points and sort
        points = sorted(list(set(points)))

        picar.logger.info(f"Current location: {picar.current_loc}. Potential objects just mapped: {points}")

        # mark the objects on the map
        for point in points:
            global_map.mark_object(point)
        
        # mark points in either direction direction along the a-xis so the car
        # has room to move around the object, otherwise the A* algo will just
        # alter the path slightly. e.g. from (1,2) to (2,2), but (2,2) is also blocked.
        all_buff_points = []
        if len(points) > 0:
            radius = 2
            # mark buffers around the points
            for point in points:
                buff_points = picar.within_radius(point, radius)
                for buff_point in buff_points:
                    if buff_point != picar.current_loc:
                        global_map.mark_object(buff_point)
                        # for logging purposes, make sure the point was actually marked
                        if global_map[buff_point.x,buff_point.y] == 1:
                            all_buff_points.append(buff_point)

        all_buff_points = sorted(list(set(all_buff_points)))

        picar.logger.info(f"The following buffer points were marked: {all_buff_points}")

        picar.logger.info(f"Total obstacles now marked on the map: {global_map.maze.sum()}")
        np.savetxt(f"saved_maps/global_map_{int(global_map.maze.sum())}.txt",global_map.maze,fmt="%d")

        # recompute the path with A* now that obstacles are marked
        picar.logger.info("Attempting to recompute new A* path.")
        path = astar(array = global_map, start=local_start, end=global_end)
        picar.logger.info(f"Recomputed path with A*: {path}")
    
        # next point in the path should be the point reachable by not turning
        local_end = path[-1] # default value is last point in the path
        for point in path:
            if local_start == point:
                continue
            turn_angle = picar.calc_angle_btwn(local_start, point) - Direction[picar.direction].value
            if turn_angle != 0:
                local_end = Coordinate(point.x,point.y)
                break

        picar.logger.info(f"Local start : {local_start}")
        picar.logger.info(f"Local end : {local_end}")
        # don't try to navigate to car's current location
        if local_start == local_end:
            picar.logger.info("Current car position is the same as next destination. Continuing along path.")
            continue
        
        # navigate to the current coordindate
        angle_btwn = picar.calc_angle_btwn(local_start, local_end)
        car_direction = Direction[picar.direction].value
        picar.logger.info(f"The angle between the points assuming 0 degree direction: {angle_btwn}. Car's current angle direction: {car_direction}.")
        turn_data = picar.get_turn_data(angle_btwn)
        
        # turn the car if needed
        if turn_data.get("turn_direction") == "left":
            picar.turn_left(turn_data.get("seconds"),turn_data.get("angle"))
        if turn_data.get("turn_direction") == "right":
            picar.turn_right(turn_data.get("seconds"),turn_data.get("angle"))

        # get distance between coordinates and seconds to move based on ucrrent power
        movement_data = picar.get_movement_data(local_start, local_end)

        # move the car forward after turning
        picar.move_forward(movement_data.get("distance"), movement_data.get("seconds"))
       
        
            
if __name__ == "__main__":

    try:
        main()
    except Exception as e:
        print(e)
        fc.stop()
    
    
    
    
    
    
