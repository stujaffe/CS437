
from astar import astar
from navigate import PiCar
from helper_classes import Coordinate, Maze, Direction
import picar_4wd as fc


def main():
    
    # initialize map and start/end points
    global_map = Maze(300,300)
    
    global_start = Coordinate(0,0)
    global_end = Coordinate(100,100)
    
    # initialize the car
    picar = PiCar(start_loc=global_start, goal_loc=global_end)
    
    # get the initial A* path
    path = astar(maze = global_map, start=global_start, end=global_end)
    picar.logger.info(f"Starting Path: {path}")
    # navigate the car along the path
    i = 0
    while True:
        # starting point is the car's current location
        local_start = picar.current_loc
        # end navigation if car has reached it's destination
        if local_start == global_end:
            picar.logger.info(f"Congrats! The car has reached the destination point of {global_end}. Distance traveled: {round(picar.distance_traveled,2)}")
            picar.stop_car()
            break
        if len(path) == 1:
            picar.logger.info(f"Congrats! The car reached the end of the path, it's current location is {local_start} versus the goal of {global_end}. Distance traveled: {round(picar.distance_traveled,2)}")
            picar.stop_car()
            break
        
        # scan for obstacles and build a map
        scan = picar.scan_sweep_map()
        last_point = None
        last_angle = None
        # fill in the map with obstacles
        for i in range(len(scan)):
            curr_item = scan[i]
            # only mark item if it's close enough
            if curr_item[0] > -2:
                curr_point = picar.get_cartesian(angle=curr_item[1], distance=curr_item[0])
                # mark point if the first reading in the scan
                if i == 0:
                    global_map.mark_object(curr_point)
                # if past the first reading in the scan and consecutive angle readings had objects, mark points in between
                elif i > 0 and abs(scan[i][1] - scan[i-1][1]) <= abs(picar.step):
                    last_item = scan[i-1]
                    last_point = picar.get_cartesian(angle=last_item[1], distance=last_item[0])
                    points_inbtwn = picar.get_points_inbtwn(last_point, curr_point)
                    for point in points_inbtwn:
                        global_map.mark_object(point)
                # if past the first reading but consecutive points did not have readings, just mark the solo point
                    global_map.mark_object(curr_point)
		

        # recompute the path with A* now that obstacles are marked
        path = astar(maze = global_map, start=local_start, end=global_end)
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
            i += 1
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

        # VERY IMPORTANT! get the movement data AFTER turning since it depends on which direction the car is facing
        movement_data = picar.get_movement_data(local_start, local_end)

        # move the car forward after turning
        picar.move_forward(movement_data.get("distance"), movement_data.get("seconds"))
       
        
            
if __name__ == "__main__":

    try:
        main()
    except Exception as e:
        print(e)
        fc.stop()
    
    
    
    
    
    
