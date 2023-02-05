from enum import Enum

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
