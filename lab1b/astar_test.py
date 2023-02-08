import numpy as np

class Node():
    """
    A node class for A* search algorithm
    """
    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position
        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        return self.position == other.position

def astar(maze, start, end):
    """
    Returns a list as a path from the starting point to the ending point in the maze all provided as inputs
    Based on the Node class, create start and end nodes and initialize scores
    """
    start_node = Node(None, start)
    #print(start_node.parent)
    start_node.g = start_node.h = start_node.f = 0
    end_node = Node(None, end)
    end_node.g = end_node.h = end_node.f = 0
    
    #Initialize both open and closed list for sorting neighbour nodes
    
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
            return path[::-1] # Return reversed path

        # Generate children
        children = []
        # Searching in adjacent nodes
        for adj_nodes in [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]:

            # Get the adjacent node position
            node_position = (current_node.position[0] + adj_nodes[0], current_node.position[1] + adj_nodes[1])

            # Make sure within range of the maze
            if node_position[0] > (len(maze) - 1) or node_position[0] < 0 or node_position[1] > (len(maze[len(maze)-1]) -1) or node_position[1] < 0:
                continue

            # Adjacent node is not an obstacle            
            if maze[node_position[0]][node_position[1]] != 0:
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
            child.h = ((child.position[0] - end_node.position[0]) ** 2) + ((child.position[1] - end_node.position[1]) ** 2)
            child.f = child.g + child.h

            # Child is already in the open list
            for open_node in open_list:
                if child == open_node and child.g > open_node.g:
                    continue

            # Add the child to the open list
            open_list.append(child)

if __name__ == '__main__':
    
    maze = np.zeros([3000,3000])

    y = 1
    for x in range(0,2998):
        maze[x, y] = 1

    print(maze)

    start = (0,0)
    end = (100,100)

    path = astar(maze, start, end)
    print(maze)
    print(path)
