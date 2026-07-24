#Ali Kamaly | DEAD PULSE
#Map-related Classes

import pygame, json, heapq, constants, math as maths, random

"""
Handles loading, parsing, and managing the game map using JSON data

By using JSON for map storage, DEAD PULSE is:
--> More flexible: Maps can be modified without editing the code
--> Easier to debug: JSON is readable and structured, unlike hardcoded lists
--> More scalable: New maps can be added easily
--> More robust: The error handling prevents crashes due to missing/corrupt map data
"""


class Minimap():
    """Encapsulates all the minimap's logic - relating to minimap image, updating and drawing player & zombie trackers
    onto the minimap"""
    def __init__(self, map_width, map_height, map_name):
        self.original_image = pygame.image.load(f"Maps/{map_name}.png")
        self.rect = self.original_image.get_rect()
        self.map_width = map_width
        self.map_height = map_height

        self.new_width = self.original_image.get_width()*constants.MINIMAP_ZOOM
        self.new_height = self.original_image.get_height()*constants.MINIMAP_ZOOM
        
        self.image = pygame.transform.scale(self.original_image,(self.new_width,self.new_height))

        self.player_tracker = pygame.image.load("Sprites/player_tracker.png")
        self.zombie_tracker_image = pygame.image.load("Sprites/zombie_tracker.png")
        self.rect = self.player_tracker.get_rect()

        self.player_tracker_x = constants.SCREEN_WIDTH-self.new_width
        self.player_tracker_y = self.new_height/2

        self.zombie_trackers = []
        self.display_zombies = False

    def update_player_tracker(self, player_global_x, player_global_y):
        self.player_tracker_x = (player_global_x/self.map_width/constants.CAMERA_ZOOM * self.new_width) + (constants.SCREEN_WIDTH-self.new_width)
        self.player_tracker_y = (player_global_y/self.map_height/constants.CAMERA_ZOOM * self.new_height)

    def update_zombie_tracker(self,zombies):
        self.zombie_trackers = []
        if self.display_zombies:
            for zombie in zombies:
                x = (zombie.original_x/self.map_width*self.new_width) + (constants.SCREEN_WIDTH - self.new_width)
                y = (zombie.original_y/self.map_height*self.new_height) 
                self.zombie_trackers.append((x,y))

    def draw_player(self,screen):
        screen.blit(self.image, (constants.SCREEN_WIDTH-self.new_width,0))
        screen.blit(self.player_tracker, (self.player_tracker_x, self.player_tracker_y))

    def draw_zombies(self,screen):
        if self.display_zombies:
            for x,y in self.zombie_trackers:
                screen.blit(self.zombie_tracker_image,(x,y))

class MapManager():
    """
    High-Level Features:
    - Implements A* (A-Star) pathfinding algorithm for efficient zombie AI navigation around any given map
    - Creates nodes in any given map by splitting the map into small grid sizes
    - Uses a 'Snap-to-Nearest-Walkable-Node' logic to align zombies with valid map positions i.e. nodes on a map
    - Loads map data from JSON, supporting dynamic level changes without modifying code
    - Uses modular design, making the map system reusable and extendable, helping to expand the game in the future
    """
    def __init__(self):
        self.json_file = "Data/maps.json"
        self.data = self._load_data()
        #stores all data from json file - data doesn't have to be parsed everytime now saving time
        self.maps = list(self.data.keys())
        #gets a list of all names of maps

        self.grid_size = 25
        #need a grid size that gives good distance between each node but one that is also not too small else
        #performance will drop

        self.wall_positions = set()
        #uses hashtables making searches way faster than lists to search through --> O(1)
        #makes it easier to check if a node collides with a wall
        #performance optimising
        self.walkable_nodes = set()
        #set that stores all nodes that zombies can walk on i.e. nodes that don't collide with a wall

    def store_walls(self,walls):
        #resetting wall_positions
        self.wall_positions = set()
        for wall in walls:
            for x in range(wall["x"], wall["x"]+wall["width"],self.grid_size):
                for y in range(wall["y"],wall["y"]+wall["height"],self.grid_size):
                    self.wall_positions.add((x,y))
                    #every 25 pixel step inside the wall is stored for better collision detection
                    #stores all 4 points of a wall instead of just 1 point which is stored in the maps.json file

    def create_walkable_nodes(self, map_name):
        """Creates nodes for the map- specifying where zombies can walk on"""

        #resetting walkable_nodes
        self.walkable_nodes = set()
        map_width, map_height = self.get_map_dimensions(map_name)
        walls = self.get_map_walls(map_name)

        self.walkable_nodes.clear()

        for x in range(0,map_width, self.grid_size):
            for y in range(0,map_height, self.grid_size):
                node = (x,y)
                if not self.is_inside_wall(node,walls):
                    #if node doesn't collide with a wall, the node is walkable for the zombie
                    self.walkable_nodes.add(node)

    def is_inside_wall(self, node, walls):
        """Checks node collision with walls in a given map"""
        
        node_rect = pygame.Rect(node[0], node[1], self.grid_size, self.grid_size)
        for wall in walls:
            wall_rect = pygame.Rect(wall["x"], wall["y"], wall["width"], wall["height"])
            if node_rect.colliderect(wall_rect):
                return True
        return False

    def find_nearest_walkable_node(self, x,y):
        """Zombie will snap to the nearest walkable node - will not snap to a node that's colliding with a wall"""
        
        grid_size = self.grid_size
        grid_x = (x // grid_size) * grid_size
        grid_y = (y // grid_size) * grid_size
        
        grid_x, grid_y = (x//self.grid_size)*self.grid_size, (y//self.grid_size)*self.grid_size
        #moves x and y to the top left of a node


        if (grid_x, grid_y) in self.walkable_nodes:
            return grid_x,grid_y
        for dx in [-self.grid_size, 0, self.grid_size]:
            #checking left, centre, right
            for dy in [-self.grid_size, 0, self.grid_size]:
                #checking up, centre, down
                new_x, new_y = grid_x +dx, grid_y + dy
                if (new_x, new_y) in self.walkable_nodes:
                    return new_x, new_y
                
        #if no adjacent walkable node is found the original coord is returned
        #which shouldn't happen but just in case it does - example of coding defensively

        return grid_x, grid_y

    def a_star(self, start, goal):
        """Calculates the shortest path using A* algorithm from start to goal nodes

        g = distance between current node and the start node
        h = heuristic- estimated distance from current node to end node
        f = total cost of the node (g+h)"""


        start = (int(start[0]), int(start[1]))
        goal = (int(goal[0]), int(goal[1]))

        open_set = []
        #list of nodes algorithm should check
        closed_set = set()
        #stores nodes that have already been checked - stops algorithm from re-looking at same node

        heapq.heappush(open_set,(0,Node(start[0], start[1])))
        #pushes start node to open_set with an f cost of 0
        #heapq utilises priority tree

        #using heapq makes it O(logn) to insert and pop


        nodes = {start: Node(start[0],start[1])}
        #create dictionary to store Node objects using (x,y) as the key


        while open_set:
            #keep searching until path found or run out of nodes to search through
            current = heapq.heappop(open_set)[1]
            #takes the node with the lowest f cost from open_set 

            if (current.x, current.y) == goal:
                return self.reconstruct_path(current)
                #shortest path found - now need to trace back the path
            closed_set.add((current.x,current.y)) 
            #adds current node to closed_set so algorithm won't re-check same node

            for neighbour in self.get_neighbours(current):
                if (neighbour.x, neighbour.y) in closed_set:
                    #O(1) time complexity as set is used not a list
                    continue
                    #if a neighbour's in closed_set it means algorithm has already checked that node so go to next neighbour
                
                tentative_g = current.g + self.grid_size 
                #the calculated cost of reaching a neighboring node from the current node

                #adding to open set if new or better path is found
                if (neighbour.x, neighbour.y) not in nodes:

                    #checking if neighbour node is diagonal to current node
                    if abs(neighbour.x - current.x) == self.grid_size and abs(neighbour.y - current.y) == self.grid_size:
                        neighbour.g = tentative_g * maths.sqrt(2)
                        #neighbour is diagonal therefore multiply distance weight by root 2
                    else:
                        #neighbour has either the same x or y coordinate
                        neighbour.g = tentative_g
                    neighbour.h = self.calculate_heuristic(neighbour, goal)

                    neighbour.f = neighbour.g+ neighbour.h

                    neighbour.parent = current
                    #stores the node that led to this neighbour
                    heapq.heappush(open_set,(neighbour.f,neighbour))
                    nodes[(neighbour.x,neighbour.y)] = neighbour
                    #ensures no duplicate keys
            
            #if no path found i.e. path doesn't exist, return empty list
        #print("no path found")
        return []

    def get_neighbours(self, node):
        """Returns all valid adjacent nodes to current node - includes diagonal ones"""
        x = node.x
        y = node.y
        step_size = self.grid_size

        #8 possible adjacent nodes (neighbours): left, right, up, down, top left, top right, bottom left, bottom right
        neighbours = [(x+step_size,y),(x-step_size, y), (x,y+step_size),(x,y-step_size),
                      (x+step_size,y+step_size),(x+step_size,y-step_size),
                      (x-step_size,y+step_size),(x-step_size,y-step_size)]

        #check to see if node is walkable
        valid_neighbours = []
        for x,y in neighbours:
            if (x,y) in self.walkable_nodes:
                valid_neighbours.append(Node(x,y))

        return valid_neighbours


    def calculate_heuristic(self, node, goal):
        """Calculates the euclidian shortest distance from node to goal (hypotenuse) - takes into account diagonal movement"""
        return maths.sqrt((node.x - goal[0])**2 + (node.y - goal[1])**2)
        #simple pythagoras 

    def reconstruct_path(self,node):
        """Traces back the shortest path from the goal node to the start"""
        path = []
        while node:
            #loop will continue until node.parent is None which ONLY happens when start node is reached
            path.append((node.x, node.y))
            #adds the current nodes coordinates to the path 
            node = node.parent 
            #moves to previous node in the path
            
        path.reverse()
        #reverses the list so path is start--> goal

        return path



    def _load_data(self):
        #programming defensively: _ at the beginning of method to indicate this method should not be used outside of this class
        #i.e. this is a private method not public
        with open (self.json_file, "r") as file:
            return json.load(file)
    
    def select_random_map(self):
        return(random.choice(self.maps))
        #randomly returns a map from list of maps

    def get_map_dimensions(self, map_name):
        map_data = self.data.get(map_name,{})
        #uses attribute self.data which has stored already all the data from json file 
        #return an empty list if no data found - error prevention
        return map_data.get("width"), map_data.get("height")
    
    def get_map_walls(self,map_name):
        map_data = self.data.get(map_name,{})
        return map_data.get("walls",[])
        #returns empty list if no walls data is available
    
    def get_map_rooms(self,map_name):
        map_data = self.data.get(map_name,{})
        rooms = map_data.get("rooms",[])
        return len(rooms)
        #returns empty list if no walls data is available

    def get_map_boundaries(self,map_name):
        map_data = self.data.get(map_name, {})
        rooms = map_data.get("rooms",[])
        #room_numbers = rooms.get("room_number","")
        boundaries = {}

        for room in rooms:
            room_number = room.get("room_number")
            boundary = room.get("boundary",{})

            x_min = boundary.get("x_min")
            x_max = boundary.get("x_max")
            y_min = boundary.get("y_min")
            y_max = boundary.get("y_max")

            if None not in (x_min, x_max, y_min, y_max):
                #avoid code breakage
                #only adds to dictionary if value exists
                boundaries[room_number] = {"x_min": x_min, "x_max": x_max, "y_min": y_min, "y_max": y_max}
        return boundaries
        
class Node():
    def __init__(self,x,y):
        self.x = x
        self.y = y
        """
        g = cost from start to this specific node
        h = heuristic (estimated) cost to the goal
        f = total cost (g+h)
        """

        self.g = 0
        self.h = 0
        self.f = 0
        self.parent = None
        #pointer to previous node on the path (the node that was before this node during traverasl)
        #allows for the reconstruction of shortest path once the goal is reached 

    def __lt__(self,other):
        """Defines how Python should compare two Node instances using the < (less than) operator.

        In the context of A* pathfinding, this allows nodes to be automatically sorted based on their f-value
        (total estimated cost), which is essential for using a priority queue to efficiently find the shortest path"""

        return self.f < other.f
                
class Wall(pygame.sprite.Sprite):
    """Defines the structure and behavior of a single wall	 """
    def __init__(self, x, y, width, height):
        super(Wall, self).__init__()
            
        self.width = width
        self.height = height
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill((0,0,0))
        self.original_rect = self.image.get_rect()
        self.original_x = x
        self.original_y = y

        self.enlarged_width = width*constants.CAMERA_ZOOM
        self.enlarged_height = height*constants.CAMERA_ZOOM
        self.enlarged_image = pygame.Surface((self.enlarged_width,self.enlarged_height))
        self.enlarged_image.fill((0,0,0))

        self.rect = self.enlarged_image.get_rect()

    def adjust_coords(self, offset_x, offset_y):
        self.rect.x = self.original_x * constants.CAMERA_ZOOM - offset_x
        self.rect.y = self.original_y * constants.CAMERA_ZOOM - offset_y

class WallManager():
    """Manages all walls, deals with loading and retrieval of walls 
    separates the logic of managing multiple Wall instances
    from the logic of what an individual wall does; this is an example of Separation of Concerns (SoC)"""
    def __init__(self, walls_data):
        self.walls_list = pygame.sprite.Group()
        self.walls_data = walls_data
        

    def load_walls(self):
        for wall_data in self.walls_data:
            self.walls_list.add(Wall(wall_data["x"],wall_data["y"],wall_data["width"],wall_data["height"]))

    def get_walls_list(self):
        return self.walls_list

