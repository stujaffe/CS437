import numpy as np
import heapq

def heuristic(a, b):
    # calculate the Euclidean distance as the heuristic
    return np.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)

def astar(array, start, end):

    start = (start[0],start[1])
    end = (end[0],end[1])

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
            neighbor = (current[0] + direction[0], current[1] + direction[1])

            if (neighbor[0] < 0 or neighbor[0] >= array.shape[0] or
                neighbor[1] < 0 or neighbor[1] >= array.shape[1] or
                array[neighbor[0]][neighbor[1]] == 1 or
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


if __name__ == '__main__':
    
    maze_save = np.loadtxt("saved_maps/global_map_254.txt",dtype=int)
    

    start = (80,79)
    end = (100,100)

    path = astar(maze_save, start, end)
    
    maze_save_area = maze_save[start[0]-5:start[0]+5,start[1]-5:start[1]+5]

    print(maze_save_area)
    print(path)
