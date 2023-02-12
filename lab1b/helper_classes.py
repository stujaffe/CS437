from enum import Enum
import numpy as np
import logging

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
    
    def __str__(self):
        return f"(x:{self.x},y:{self.y})"
    
    def __repr__(self):
        return f"(x:{self.x},y:{self.y})"
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def __lt__(self, other):
        return self.x < other.x

# class to hold the obstacle course
class Maze(object):
    def __init__(self, x_length: int, y_length: int) -> None:
        self.x_length = x_length
        self.y_length = y_length
        self.maze = np.zeros(shape=(x_length, y_length))
        self.shape = (x_length, y_length)
        self.logger = logging.getLogger()
        logging.basicConfig(format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                datefmt='%Y-%m-%d:%H:%M:%S',
                level=logging.DEBUG)

    def __str__(self):
        return str(self.maze)
    
    def __getitem__(self, idx):
        try:
            if type(idx) == int:
                return self.maze[idx]
            else:
                return self.maze[idx[0],idx[1]]
        except IndexError:
            return None
    
    def __len__(self):
        return self.maze.shape[0]
    
    # mark object only if within boundaries of the map
    def mark_object(self, coord1: Coordinate, x_lower: int, x_upper: int, y_lower: int, y_upper: int) -> None:
        if coord1.x >= x_lower and coord1.x < x_upper and coord1.y >= y_lower and coord1.y < y_upper:
            self.maze[coord1.x, coord1.y] = 1
            
            

# hold the directions and their corresponding angles from the perspective of going north
# using polar coordinates with 0 degrees as north and negative angles since the ultrasonic sensor
# produces from -90 degrees (facing east of the car) to 90 degrees (facing west of the car)
class Direction(Enum):
    north = 0
    northeast = -45 #315
    east = -90 #270
    southeast = -135 #225
    south = -180 #180
    southwest = 135
    west = 90
    northwest = 45

if __name__ == "__main__":
    pass
