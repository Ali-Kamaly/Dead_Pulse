#Ali Kamaly | DEAD PULSE
#Spawner-related Classes

import pygame, json, math as maths, random
from zombies import Walker, Runner, Brute
from pickable_items import Bullets, Medkit, Battery


class Spawner():
    """
    Centralised spawner for all different types of items

    Base class encapsulates core spawning logic including coordinate randomisation with collision avoidance, 
    while specialised spawners such as: BulletSpawner and MedkitSpawner extend this functionality through clean inheritance
    """
    def __init__(self, map_width, map_height):
        self.items_list = pygame.sprite.Group()
        self.map_width = map_width
        self.map_height = map_height

    def spawn(self, item_class, num_items):
        coords = [(-1,-1)]
        for i in range(num_items):
            x = -1
            y = -1            
            while (x,y) in coords:
                x = random.randrange(0,self.map_width)
                y = random.randrange(0,self.map_height)
            coords.append((x,y))
            self.items_list.add(item_class(x,y))        
            
class BulletSpawner(Spawner):
    def __init__(self, map_width, map_height):
        super().__init__(map_width, map_height)

    def spawn(self, num_bullets):
        super().spawn(Bullets,num_bullets)

class MedkitSpawner(Spawner):
    def __init__(self, map_width, map_height):
        super().__init__(map_width, map_height)

    def spawn(self, num_medkits):
        super().spawn(Medkit,num_medkits)

class BatterySpawner(Spawner):
    def __init__(self, map_width, map_height):
        super().__init__(map_width, map_height)

    def spawn(self, num_batteries):
        super().spawn(Battery,num_batteries)

class ZombieSpawner(Spawner):
    """
    Utilises dynamic zombie distribution system that intelligently distributes enemies across map rooms 
    using weighted randomisation

    Implements zombie 'hunter' assignment algorithm that calculates Euclidean distances to identify the closest zombies
    to the player to be allowed to use A* pathfinding to 'hunt' the player i.e. track the player down

    Dynamically loads room boundaries and metadata from external JSON file, separating game logic from level design
    """
    def __init__(self, map_width, map_height, map_manager):
        self.walker_count = 0
        self.runner_count = 0
        self.brute_count = 0
        self.map_manager = map_manager

        self.zombie_list = pygame.sprite.Group()
        self.active_hunters = []

        super().__init__(map_width, map_height)

    def spawn_walkers(self,num_walkers,map_name, map_manager,game_state):
        self.spawn_zombie(Walker,num_walkers,map_name, map_manager,game_state)
        self.walker_count += num_walkers
    
    def spawn_runners(self,num_runners,map_name, map_manager,game_state):
        self.spawn_zombie(Runner,num_runners,map_name, map_manager,game_state)
        self.runner_count += num_runners

    def spawn_brutes(self,num_brutes,map_name,map_manager,game_state):
        self.spawn_zombie(Brute,num_brutes,map_name,map_manager, game_state)
        self.brute_count += num_brutes

    def spawn_zombie(self, zombie_type, num_of_zombies, map_name, map_manager, game_state):
        num_of_rooms = map_manager.get_map_rooms(map_name)
        boundaries = map_manager.get_map_boundaries(map_name)
        #refers back to mapmanager class to get data about map

        zombie_distribution = self._distribute_zombies(num_of_zombies,num_of_rooms)
        self._spawn_random_location(zombie_distribution,boundaries,zombie_type, map_manager, game_state)


    def get_distance(self, zombie):
        dx = zombie.original_x - self.player_pos[0]
        dy = zombie.original_y - self.player_pos[1]
        return maths.sqrt(dx**2 + dy**2)
        #returns shortest distance from zombie and player
    

    def assign_hunters(self, player_pos):
        """
        Dynamically assigns the nth closest zombies to the player as hunters, granting them the 
        ability to utilise the A* pathfinding algorithm to 'hunt' the player
        """

        self.player_pos = player_pos
        self.active_hunters = self._get_closest_zombies(5)
        self.hunter_target = self.map_manager.find_nearest_walkable_node(player_pos[0], player_pos[1])
        
    def update_all (self, game_state, player, walls):
        for zombie in self.zombie_list:
            zombie.update(game_state, player, walls)


    def _get_closest_zombies(self, number):
        """Returns the nth closest zombies to the player using Euclidian distance"""
        all_zombies = list(self.zombie_list)
        all_zombies.sort(key=self.get_distance)
        return all_zombies[:number]
        #returns the [number] closest zombies to the player


    def get_map_rooms_info(self,map_name):
        """Returns information about all the rooms in a map"""
        boundaries = {}
        with open ("Data/maps.json","r") as file:
            data = json.load(file)
            for room in data[map_name]["rooms"]:
                room_number = room["room_number"]
                boundaries[room_number] = room["boundary"]

        return boundaries, len(boundaries)   

    def _distribute_zombies(self, num_zombies, num_rooms):
        """Randomly distributes zombies into pre-defined rooms on a given map"""

        distribution = [0] * num_rooms
        """
        creates a list of 0s, number of elements = number of rooms, where each index represents
        a room_number
        i.e. [0, 0, 0, 0] = 4 rooms
        distribution[0] = room_number 0 etc.
        """
        for i in range(num_zombies):
            room_index = random.randint(0,num_rooms-1)
            distribution[room_index] += 1
            """
            every zombie to be spawned will be assigned a random room_number
            distribution could look like [2, 4, 5]
            this means: 
            --> 2 zombies will be spawned at room_number 0, 4 at room_number 1 etc.
            """
        return distribution

    def _spawn_random_location(self, distribution, boundaries, zombie_type,map_manager, game_state):
        """Spawns zombies in random locations within a given room"""

        for room_number in boundaries:
            num_zombies = distribution[room_number]
            for _ in range(num_zombies):
                #iterates n times depending on how many zombies are in that one specific room_number
                boundary = boundaries[room_number]
                x_min, x_max = boundary.get("x_min"), boundary.get("x_max")
                y_min, y_max = boundary.get("y_min"), boundary.get("y_max")

                x = random.randint(x_min,x_max)
                y = random.randint(y_min,y_max)
                #randomly generates coords for a zombie within the boundary 

                zombie = zombie_type(x,y,map_manager)

                #applying updated health and attack from previous wave completion 
                zombie.health_bar.max_health = round(zombie.health_bar.max_health*game_state.zombie_health_multiplier)
                zombie.health_bar.current_health = zombie.health_bar.max_health
                zombie.attack_damage = round(zombie.attack_damage * game_state.zombie_attack_multiplier) 
                #print(f"{zombie.type} Health: {zombie.health_bar.max_health}")
                #print(f"{zombie.type} Attack: {zombie.attack_damage}")


                self.zombie_list.add(zombie)
        #randomly generates coords that fit within the boundary of any given wall, indicated by room_number

