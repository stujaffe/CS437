
from astar import astar
from navigate import PiCar
from helper_classes import Coordinate, Maze, Direction
import picar_4wd as fc


def main():
    
    # initialize map and start/end points
    global_map = Maze(300,300)
    
    global_start = Coordinate(0,0)
    global_end = Coordinate(50,10)
    
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
        if i >= len(path):
            picar.logger.info(f"Congrats! The car reached the end of the path, it's current location is {local_start} versus the goal of {global_end}. Distance traveled: {round(picar.distance_traveled,2)}")
            picar.stop_car()
            break
        # ending point is the current coordinate in the path
        local_end = path[i]
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
        picar.logger.info(f"The angle between the points adjusted for car's direction: {angle_btwn-car_direction}")
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
        
        # increment the path counter
        i += 1
        
            
if __name__ == "__main__":

    try:
        main()
    except Exception as e:
        print(e)
        fc.stop()
    
    
    
    
    
    
