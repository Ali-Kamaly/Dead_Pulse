#Ali Kamaly | DEAD PULSE
#Map-related Classes

import pygame, constants, math as maths, random
from ui import HealthBar

class Zombie(pygame.sprite.Sprite):

    """
    The base zombie class handles core AI behaviors for all zombie types. It implements a 
    state system (idle, chasing, hunting) that changes based on player proximity and player heartbeat 
    The zombie 'chasing' behavior uses vector math to calculate smooth pursuit paths, while 'hunting' 
    mode utilises A* pathfinding for navigation around walls in a map
    Each zombie has its own health bar and deals damage with attack cooldowns, depending on zombie type
    
    The code efficiently handles coordinate conversions (global and local) between screen 
    and map space for proper camera-relative positioning

    Utilises states for zombies which cleanly transitions between each other, with proper cleanup
    (like path clearing) when exiting states. This creates organic-feeling zombies that are simple 
    when distant (allows for program performance enhancements) but clever when threatened/in proximity
    """


    def __init__(self,x,y,map_manager, image, zombie_type):
        super(Zombie,self).__init__()

        #states = ["idle", "chasing", "fleeing"]
        self.state = "idle"
        self.type = zombie_type
        self.map_manager = map_manager
        self.zombie_type = zombie_type

        self.original_x, self.original_y = map_manager.find_nearest_walkable_node(x,y)
        #zombie snaps to nearest walkable node when spawned in

        self.original_image = pygame.image.load(image)
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(self.original_x, self.original_y))
        self.chasing_distance = 600

        self.health_bar = HealthBar()

        #default values (walkers and brutes will have different values):
        self.attack_damage = 5
        self.attack_cooldown = 200
        self.last_time_attacked = 0

        self.target_position = None
        #last known coord of player - zombie will travel there
        self.path = []
        #the path the zombie must take to quickly reach the player (when A* pathfinding is being used)
        self.following_path_speed = 1

        self.active_hunters = []
        self.snapped_to_node = False
        #stores list of zombies that can use a* pathfinding (max 5 zombies - performance reasons)


        self.last_path_update = None
        self.last_path_goal = None
        self.last_path_start = None

    #Entering and exiting states:
    #using _ as they're private methods which shouldn't be used outside of the class
    def _enter_idle_state(self):
        if self.state!= "idle":
            self.state = "idle"
            self.path = []
            self.original_x, self.original_y = self.map_manager.find_nearest_walkable_node(self.original_x, self.original_y)
            #zombie snaps to nearest walkable node when entering idle state
            self.snapped_to_node = True


    def _enter_chasing_state(self):
        self.state = "chasing"
        self.path = []
        #stops following a* path
        self.snapped_to_node = False
        #zombie won't be snapping to nodes when chasing - it'll move freely and gridless
        #target doesn't need to be snapped to node (zombie will chase grid-less)

    def _exit_chasing_state(self):
        self.state = "idle"
        self.original_x, self.original_y = self.map_manager.find_nearest_walkable_node(self.original_x,self.original_y)
        self.snapped_to_node = True
        #zombie snaps to node closest to it when sight of player is lost and is idle

    def _enter_hunting_state(self):
        if self.state != "hunting":
            self.state = "hunting"

            self.snapped_to_node = False

    def follow_path(self, target):
        """Move smoothly towards the next node in the A* path"""
        
        #first checks if first node in the a* pathway is the node zombie is already on
        next_x, next_y = self.path[0]
        if (self.original_x,self.original_y) == (next_x, next_y):
            try:
                self.path.pop(0)
            except IndexError:
                return

        try:
            next_x, next_y = self.path[0]
        except IndexError:
            return

        direction_x = next_x - self.original_x
        direction_y = next_y - self.original_y
        distance = maths.sqrt(direction_x**2 + direction_y**2)


        if distance>0:
            if self.type == "runner":
                self.following_path_speed = 1.1
            elif self.type == "brute":
                self.following_path_speed = 0.8

            dx = (direction_x/distance)*self.following_path_speed
            dy = (direction_y/distance)*self.following_path_speed

            self.original_x+=dx
            self.original_y+=dy
            angle = self.calculate_rotation(dx, dy)
            self.rotate(angle)


            #if zombie has reached next node, snap to next node
            if distance<= self.following_path_speed:
                self.original_x, self.original_y = next_x, next_y
                #snaps to next node if close enough
                try:
                    self.path.pop(0)
                except IndexError:
                    return
                #removes the now reached node



    def adjust_coords(self, offset_x, offset_y):
        self.rect.x = self.original_x * constants.CAMERA_ZOOM - offset_x
        self.rect.y = self.original_y * constants.CAMERA_ZOOM - offset_y

    """Currently not being used"""
    def will_collide(self, dx, dy, walls_list,offset_x, offset_y):
        adjusted_dx = constants.CAMERA_ZOOM *self.original_x 
        adjusted_dy = constants.CAMERA_ZOOM * self.original_y 
        temp_rect = self.rect.move(adjusted_dx -offset_x,adjusted_dy-offset_y)
        for wall in walls_list:
            if temp_rect.colliderect(wall):
                return True
        return False

    def move(self, dx, dy):
        self.original_x +=dx
        self.original_y +=dy


    def can_see_player(self, player, walls_list):
        """Checks zombie proximity to player"""
        player_map_x = player.global_rect.x/constants.CAMERA_ZOOM
        player_map_y = player.global_rect.y/constants.CAMERA_ZOOM

        dx, dy = player_map_x - self.rect.centerx, player_map_y - self.rect.centery
        proximity = maths.sqrt(dx**2 + dy**2)
        if proximity <self.chasing_distance:
            for wall in walls_list:

                #checks if line there's a collision inbetween corresponding points of player and zombie rect
                #i.e. checks if there's an obstacle inbetween player and zombie preventing the zombie from chasing player
                if wall.rect.clipline(
                    (self.rect.bottomleft[0],self.rect.bottomleft[1]),player.rect.bottomleft) or wall.rect.clipline(
                        (self.rect.bottomright[0],self.rect.bottomright[1]),player.rect.bottomright) or wall.rect.clipline(
                        (self.rect.topright[0],self.rect.topright[1]),player.rect.topright) or wall.rect.clipline(
                            (self.rect.topleft[0],self.rect.topleft[1]),player.rect.topleft):
                    return False
            return True
        return False

        
    def chase_player(self, player):
        """Zombie chases player - speed dependant on zombie type"""
        player_map_x = player.global_rect.centerx/constants.CAMERA_ZOOM
        player_map_y = player.global_rect.centery/constants.CAMERA_ZOOM

        dx, dy = player_map_x - self.original_x, player_map_y - self.original_y
        proximity = maths.sqrt(dx**2 + dy**2)

        if 0<proximity:
            if self.type == "walker":
                speed = 0.8
            elif self.type == "runner":
                speed = 1
            else:
                speed = 0.6
            self.original_x += (dx/proximity)*speed
            self.original_y += (dy/proximity)*speed
            self.rotate(self.calculate_rotation(dx,dy))

    def calculate_rotation(self, dx,dy):
        angle= -(maths.atan2(dy,dx)*180/maths.pi)
        return angle

    def rotate(self, angle):
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=(self.rect.center))

    def get_unstuck(self, walls_list):
        #Doesn't work as intended

        for wall in walls_list:
            if self.rect.right>wall.rect.left:
                direction = [(-1,0)]
            if self.rect.left<wall.rect.right:
                direction = [(1,0)]
            if self.rect.bottom > wall.rect.top:
                direction = [(0,-1)]
            if self.rect.top < wall.rect.bottom:
                direction = [(-1,0)]
            
        for dx, dy in direction:
            temp_rect = self.rect.move(dx*5, dy*5)
            if not any(wall.rect.colliderect(temp_rect) for wall in walls_list):
                self.move(dx*5, dy*5)
                break       

    
    def update(self, game_state, player, walls_list):

        if self.can_see_player(player, walls_list):
            if self.state != "chasing":
                self._enter_chasing_state()
            self.chase_player(player)
        else:
            if self.state == "chasing":
                self._exit_chasing_state()

            #only for hunter zombies
            if self in game_state.zombies.active_hunters:

                #zombie will only go into hunting state and hunt only if player's heartbeat
                #has reached/surpassed the heartbeat threshold
                if game_state.player.heart.current_heart_rate >= game_state.zombies_hunting_heartbeat_threshold:
                    self._enter_hunting_state()
                    self.handle_hunting(game_state)
                    #should only run if player's heartbeat is high
                else:
                    if self.state != "idle":
                        self._enter_idle_state()
            
            else:
                if self.state != "idle":
                    self._enter_idle_state()


    def on_death(self, game_state):
        """Drops random amount of rotten flesh - dependant on zombie type"""

        if self.type == "walker":
            game_state.rotten_flesh += random.randint(1,5)
        elif self.type == "runner":
            game_state.rotten_flesh += random.randint(3,8)
        else:
            game_state.rotten_flesh += random.randint(8,13)


    def handle_hunting(self, game_state):
        current_time = pygame.time.get_ticks()


        #only calculate new path if path doesn't exist or 5 seconds of high heartbeat has passed
        if not self.path or current_time - self.last_path_update > 5000:
            snapped_start = self.map_manager.find_nearest_walkable_node(self.original_x, self.original_y)
            snapped_goal = game_state.zombies.hunter_target
            #zombie should already be snapped before hunting so no need to snap here
            #snapping should've happened when entering hunting state

            #only recalculate new path if player and/or zombie has moved from their previous location
            if snapped_start != self.last_path_start or snapped_goal != self.last_path_goal:
                self.path = game_state.map_manager.a_star(snapped_start, snapped_goal)

                self.last_path_update = current_time
                self.last_path_start = snapped_start
                self.last_path_goal = snapped_goal
        

        if self.path:
            self.follow_path(game_state.zombies.hunter_target)

    
class Walker(Zombie):
    """
    Inheriting from base zombie class
    The standard zombie type that inherits all base behaviors. Walkers have balanced stats 
    and serve as the common enemy type. Their movement speed and damage values provide a baseline 
    that other zombie types modify
    """
    def __init__(self,x,y, map_manager):
        super().__init__(x,y,map_manager,"Sprites/walker.png", "walker")

class Runner(Zombie):
    """
    Inheriting from base zombie class
    A faster but weaker zombie variant. Runners move quicker than walkers but have less health 
    and deal reduced damage. This creates distinct gameplay where players must prioritise them 
    due to their speed while managing other threats
    """
    def __init__(self,x,y, map_manager):
        super().__init__(x,y,map_manager,"Sprites/runner.png","runner")
        self.attack_damage = 2
        self.attack_cooldown = 100
        self.health_bar = HealthBar(max_health = 80)

class Brute(Zombie):
    """
    Inheriting from base zombie class
    The tank-type zombie with high health and heavy damage but slow movement. Brutes force players 
    to use different tactics. Their extended attack cooldown gives players brief recovery windows 
    between attacks
    """
    def __init__(self,x,y, map_manager):
        super().__init__(x,y,map_manager,"Sprites/brute.png","brute")
        self.attack_damage = 12
        self.attack_cooldown = 300
        self.health_bar = HealthBar(max_health = 130)

