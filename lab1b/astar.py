import warnings
from helper_classes import Coordinate

class Node:
    """
    A node class for A* search algorithm
    """

    def __init__(self, parent: Coordinate=None, position: Coordinate=None):
        self.parent = parent
        self.position = position
        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        return self.position == other.position
    
    def __str__(self):
        return f"(Position: {self.position})"
    
    def get_parents(self):
        return f"[Parents: {self.parent}]"


def astar(maze, start: Coordinate, end: Coordinate):
    """
    Returns a list as a path from the starting point to the ending point in the maze all provided as inputs
    Based on the Node class, create start and end nodes and initialize scores
    """
    maze_x_len = maze.shape[0]
    maze_y_len = maze.shape[1]

    if start.y > maze_y_len-1 or start.x > maze_x_len-1:
        raise Exception("The starting point is invalid. The point is outside the maze.")
    if end.y > maze_y_len-1 or end.x > maze_x_len-1:
        raise Exception("The ending point is invalid. The point is outside the maze.")
    
    if maze[end.x, end.y] == 1:
        temp_end = None
        # Check adjacent points for any open points:
        for adj_nodes in [
            (0, -1),
            (0, 1),
            (-1, 0),
            (1, 0),
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
        ]:
            if maze[end.x + adj_nodes[0],end.y + adj_nodes[1]] == 0:
                temp_end = Coordinate(end.x + adj_nodes[0],end.y + adj_nodes[1])
                break
        if temp_end is not None:
            warnings.warn(message = f"The ending point of {end} has an obstacle, cannot navigate there. Navigating to {temp_end} instead.")
        else:
            raise Exception(f"The ending point of {end} and all adjacent points have an obstacle. Ending navigation.")
        
        end = temp_end

    start_node = Node(None, start)
    # print(start_node.parent)
    start_node.g = start_node.h = start_node.f = 0
    end_node = Node(None, end)
    end_node.g = end_node.h = end_node.f = 0

    
    # Initialize both open and closed list for sorting neighbour nodes
    open_list = []
    closed_list = []

    
    # Add the start node to the open list
    open_list.append(start_node)

    
    # Loop until you find the end point
    while len(open_list) > 0:
        # Get the current node
        current_node = open_list[0]
        current_index = 0
        for index, item in enumerate(open_list):
            if item.f < current_node.f:
                current_node = item
                current_index = index

        # Pop current off open list, add to closed list
        open_list.pop(current_index)
        closed_list.append(current_node)

        # Found the goal
        if current_node == end_node:
            path = []
            current = current_node
            while current is not None:
                path.append(current.position)
                current = current.parent
            return path[::-1]  # Return reversed path

        # Generate children
        children = []
        # Searching in adjacent nodes
        for adj_nodes in [
            (0, -1),
            (0, 1),
            (-1, 0),
            (1, 0),
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
        ]:
            # Get the adjacent node position
            node_position = Coordinate(
                current_node.position.x + adj_nodes[0],
                current_node.position.y + adj_nodes[1],
            )

            # Make sure within range of the maze
            if (
                node_position.x > (len(maze) - 1)
                or node_position.x < 0
                or node_position.y > (len(maze[len(maze) - 1]) - 1)
                or node_position.y < 0
            ):
                continue

            # Adjacent node is not an obstacle
            if maze[node_position.x][node_position.y] != 0:
                continue

            # Create new node
            new_node = Node(current_node, node_position)

            # Append
            children.append(new_node)

        # Loop through children
        for child in children:
            # Child is on the closed list
            for closed_child in closed_list:
                if child == closed_child:
                    continue

            # Create the f, g, and h values
            child.g = current_node.g + 1
            child.h = ((child.position.x - end_node.position.x) ** 2) + (
                (child.position.y - end_node.position.y) ** 2
            )
            child.f = child.g + child.h

            # Child is already in the open list
            for open_node in open_list:
                if child == open_node and child.g > open_node.g:
                    continue

            # Add the child to the open list
            open_list.append(child)

if __name__ == "__main__":

    import numpy as np
    from helper_classes import Maze, Coordinate

    # Note for numpy arrays the "origin" is in the upper-left corner
    # and the axes are "flipped" so the x-axis would be the "vertical" one and vice-versa for the y-axis
    
    maze = Maze(3000,3000)

    y = 1
    for x in range(0,2998):
        coord = Coordinate(x,y)
        maze.mark_object(coord)

    print(maze)

    start = Coordinate(0,0)
    end = Coordinate(100,100)

    path = astar(maze, start, end)
    print(maze)
    print(path)
