import warnings
from helper_classes import Coordinate
import heapq
import numpy as np
import math

def heuristic(coord1, coord2):
    # calculate the Euclidean distance as the heuristic
    return math.ceil(np.sqrt((coord1.x - coord2.x) ** 2 + (coord1.y - coord2.y) ** 2))

def astar(array, start, end):

    # initialize the heap for the open list and the closed list
    heap = []
    heapq.heappush(heap, (0, start))
    closed_list = set()

    # initialize the distances and parent nodes
    g_values = {start: 0}
    f_values = {start: heuristic(start, end)}
    parents = {start: None}

    while heap:
        (f, current) = heapq.heappop(heap)

        if current == end:
            # reconstruct the path from the parent nodes
            path = []
            while current is not None:
                path.append(current)
                current = parents[current]
            path.reverse()
            return path

        closed_list.add(current)

        for direction in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            neighbor = Coordinate(current.x + direction[0], current.y + direction[1])

            if (neighbor.x < 0 or neighbor.x >= array.shape[0] or
                neighbor.y < 0 or neighbor.y >= array.shape[1] or
                array[neighbor.x][neighbor.y] == 1 or
                neighbor in closed_list):
                continue

            g = g_values[current] + 1
            f = g + heuristic(neighbor, end)

            if neighbor in g_values and g >= g_values[neighbor]:
                continue

            heapq.heappush(heap, (f, neighbor))
            g_values[neighbor] = g
            f_values[neighbor] = f
            parents[neighbor] = current

    return None


if __name__ == "__main__":

    import numpy as np
    from helper_classes import Maze, Coordinate

    # Note for numpy arrays the "origin" is in the upper-left corner
    # and the axes are "flipped" so the x-axis would be the "vertical" one and vice-versa for the y-axis
    
    maze = Maze(3000,3000)

    y = 1
    for x in range(0,3000):
        coord = Coordinate(x,y)
        maze.mark_object(coord)

    print(maze)

    start = Coordinate(0,0)
    end = Coordinate(100,100)

    path = astar(maze, start, end)
    print(maze)
    print(path)
