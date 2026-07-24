#Ali Kamaly | DEAD PULSE
#Player-related Classes

import pygame, constants, random, math as maths
from ui import HealthBar

class Player(pygame.sprite.Sprite):

    """
    Class serves as the central hub for managing player behavior, integrating a wide range of systems 
    including movement, shooting, health, audio, and visual feedback - it favours composition over inheritance
    i.e. self.heart = Heart(), self.healt_bar= HealthBar() etc.

    Manages gameplay feedback tightly: visual effects like shooting spread and rotation, 
    as well as responsive audio messages are triggered under specific conditions (e.g., low visibility or health)
    all contribute to an immersive player experience

    Time-based mechanics such as total_time_running and total_time_idle are used to gradually increase 
    or decrease heart rate based on activity, simulating physiological stress in a way that directly impacts 
    the gameplay

    The use of logarithmic functions to gradually increase heart rate ensures smooth gameplay balancing, 
    avoiding any sharp increases in the heart rate

    The class also tracks both local screen coordinates and global world coordinates, allowing for camera-relative 
    rendering while maintaining accurate player positioning in the game world
    This separation of concerns is a necessary design choice for implementing scrolling maps (i.e. zoomed in camera)

    Having bullet spread use trigonometric logic that scales with the player's heart rate, 
    adds depth to the combat system and links player performance to in-game stress

    """


    def __init__ (self,x,y):
        super(Player,self).__init__()
        self.original_image = pygame.image.load("Sprites/player.png")
        self.image = self.original_image.convert_alpha()
        self.rect = self.image.get_rect(center = (constants.SCREEN_WIDTH/2,constants.SCREEN_HEIGHT/2))
        self.global_rect = self.image.get_rect(center = (x,y))
        

        self.state = 'idle'
        #default player state is idle i.e. player is not moving
        #Player state : idle, attacking etc.

        self.heart = Heart()
        self.health_bar = HealthBar(max_health = constants.DEFAULT_CURRENT_HEALTH)
        self.projectiles = SpawnProjectile()

        self.rotten_flesh = 0
        #currency 

        self.rect.center = (constants.SCREEN_WIDTH/2,constants.SCREEN_HEIGHT/2)

        self.local_coord_x = constants.SCREEN_WIDTH/2
        self.local_coord_y = constants.SCREEN_HEIGHT/2
        #local coord will always stay the same 

        self.dist_x = 0
        self.dist_y = 0
        #default distance between player and mouse is 0

        #stores the value of their movement and how far player is moving
        self.dx = 0
        self.dy = 0

        #stores total displacement of player from original position
        #this value can then be used to help the camera 'follow' the player
        self.dx_total = 0
        self.dy_total = 0

        #total number of bullets player has - new player = 10
        self.ammo = 10
        #default attack deamage
        self.attack_damage = 5


        """Time duration running"""
        self.total_time_running = 0
        self.time_running_interval = 0
        #resets after every running_interval passed - used to prevent player's heart rate to rapidly increase
        self.is_running = False
        self.getting_attacked = False

        self.num_of_running_intervals = 0
        #as player runs longer and longer, num of intervals increases

        self.last_update_time = pygame.time.get_ticks()
        self.running_interval = 1000 
        #if player runs for longer than the running_interval, player's heartrate would increase

        self.last_heart_rate_increase = 0
        #time since heart_rate was increased (used so player heart rate does not increase constantly but instead in regular intervals)

        """Time duration idle"""

        self.total_time_idle = 0
        self.time_idle_interval = 0

        self.idle_interval = 500
        self.last_heart_rate_decrease = 0


        """Visibility"""
        self.total_time_blind = 0
        self.time_blind_interval = 500
        self.last_blind_heart_rate_increase = 0

        self.num_of_blind_intervals = 0

        """default keybindings for movement: WASD"""
        self.keybindings = {
            "up": pygame.K_w,
            "left": pygame.K_a,
            "down": pygame.K_s,
            "right": pygame.K_d,
            "run": pygame.K_LSHIFT,
            "shoot": pygame.K_SPACE
        }

        """Tracking shooting time - for audio tracking"""
        self.last_time_shot = 0
        self.shoot_cooldown = 100

        """Tracking player dialogue"""
        self.low_health_sound_played = False
        self.low_visibility_sound_played = False


        
    def update_heart_rate(self, movement_x, movement_y, visibility, game_state):
        current_time = pygame.time.get_ticks()
        time = current_time - self.last_update_time
        self.last_update_time = current_time

        if self.is_running and (movement_x!= 0 or movement_y!= 0):
            self.total_time_running += time
            self.time_running_interval += time
            if self.time_running_interval > self.running_interval:
                self.num_of_running_intervals+=1
                self.heart.increase_heart_rate(int(maths.log2(self.num_of_running_intervals+1)*10-2))
                #increases player's heart rate using logarithmic growth

                #Smooth difficulty scaling, player gets an initial challenge but not punished too harshly for longer runs
                #more predictible and manageble than 2^t - 
                #it’s easier to balance  game since the heart rate increase slows over time
                #as num_of_running_intervals increases, the increment decreases 
                #https://www.desmos.com/calculator/4ra9e8fwgd


                #player's heart rate increases at a higher rate, the longer he runs around 2^k
                #i.e. 1 second = +2, 2 seconds = +4, 3 seconds = +8 etc.
                self.time_running_interval = 0
            
        else:
            self.total_time_running = 0
            self.time_running_interval = 0
            self.num_of_running_intervals = 0

        if not self.is_running and not self.getting_attacked and visibility>150:
            self.total_time_idle +=time
            self.time_idle_interval +=time
            if self.time_idle_interval > self.idle_interval:
                self.time_idle_interval = 0
                if movement_x ==0 and movement_y == 0 :
                    self.heart.decrease_heart_rate(5)
                    #i.e. if player is completely idle heart rate decreases faster
                else:
                    self.heart.decrease_heart_rate(1)
        else:
            self.total_time_idle = 0
            self.time_idle_interval = 0

        if self.getting_attacked:
            self.heart.increase_heart_rate(random.randint(1,3))

        if visibility<=150:
            self.total_time_blind += time
            if self.total_time_blind - self.last_blind_heart_rate_increase > self.time_blind_interval:
                self.heart.increase_heart_rate()
                self.total_time_blind = 0
                self.last_blind_heart_rate_increase = time

            if not self.low_visibility_sound_played:
                game_state.audio_manager.play_sound_effect("low vision")
                self.low_visibility_sound_played = True
                #sound effect only played once when vision is low

        else:
            self.low_visibility_sound_played = False

        self.getting_attacked = False

    def get_global_coords(self):
        return (self.rect.x, self.rect.y)
    
    def undo_movement(self,dx,dy):
        #if collision occurs, undo movement that lead to that said collision
        self.global_rect.x -= dx
        self.global_rect.y -= dy

    def increase_ammo(self, increment):
        self.ammo += increment

    #update player's global coords depending on player input
    def update_global_coords(self,dx,dy):
        self.global_rect.x += dx
        self.global_rect.y += dy

    #movement logic
    def calculate_movement(self, game_state):
        self.dx = 0
        self.dy = 0
        self.is_running = False
        speed = constants.SPEED

        keys_pressed = pygame.key.get_pressed()

        if keys_pressed[self.keybindings["run"]]:
            self.is_running = True
            speed = constants.RUN_SPEED

        if keys_pressed[self.keybindings["shoot"]]:
            self.shoot(game_state)
        
        else:
            game_state.audio_manager.stop_sound_effect("shooting")
            #instantly stops shooting sound effect if space isn't being pressed

        if keys_pressed[self.keybindings["left"]]:
            self.dx -= speed
        if keys_pressed[self.keybindings["right"]]:
            self.dx += speed
            
        if keys_pressed[self.keybindings["up"]]:
            self.dy -= speed
        if keys_pressed[self.keybindings["down"]]:
            self.dy += speed

        self.dx_total += self.dx
        self.dy_total += self.dy

        return (self.dx, self.dy)
    

    def shoot(self, game_state):
        current_time = pygame.time.get_ticks()
        if self.ammo>0 and current_time - self.last_time_shot >=self.shoot_cooldown:
            game_state.audio_manager.play_sound_effect("shooting")

            mouse_pos_x, mouse_pos_y = pygame.mouse.get_pos()
            direction_vector = self.calculate_direction_vector(mouse_pos_x, mouse_pos_y)
            direction_vector = self.apply_shooting_spread(direction_vector)
            self.projectiles.spawn(self.global_rect.x,self.global_rect.y, direction_vector)
            self.ammo -=1
            game_state.bullets_fired +=1
            self.last_time_shot = current_time
        elif self.ammo ==0:
            game_state.audio_manager.stop_sound_effect("shooting")
 

    def apply_shooting_spread(self, direction_vector):
        """Applies random spread to shooting - varies increasingly as heart rate increases"""

        base_angle = maths.atan2(direction_vector[1],direction_vector[0])

        if self.heart.current_heart_rate <= 150:
            max_spread = 0.1
            # default spread is 0.1 rads (5.7 degrees)

        else:
            max_spread = min(0.1 + (self.heart.current_heart_rate - 150)/100 * 0.35 , 0.45)
            #normalising heart rate and scaling value to interval [0.1 - 0.45]
            #max spread is 0.45 rads (25.8 degrees)


        spread_angle = random.uniform(-max_spread, max_spread)

        new_angle = base_angle + spread_angle

        #converting back to x,y unit vectors
        spread_x = maths.cos(new_angle)
        spread_y = maths.sin(new_angle)

        return [spread_x, spread_y]
    
    def check_collision(self, walls_list):
        temp_rect = self.image.get_rect()
        temp_rect.x+=self.dx
        temp_rect.y+=self.dy
        if pygame.sprite.spritecollide(self,walls_list,False):
            return True
        return False        

    def get_total_displacement(self):
        return (self.dx_total, self.dy_total)
    
    def calculate_rotation(self, dx, dy):
        angle =  -(maths.atan2((dy),(dx)))*180/maths.pi
        #converting to degrees (-ve to convert to anti-clockwise)
        return angle

    def calculate_direction_vector(self, mouse_pos_x, mouse_pos_y):
        dx = self.rect.centerx - mouse_pos_x
        dy = self.rect.centery - mouse_pos_y
        magnitude = maths.sqrt(dx**2 + dy**2)
        dx_unit = dx
        dy_unit = dy
        if magnitude!=0:
            dx_unit = -dx/magnitude
            dy_unit = -dy/magnitude

        return [dx_unit,dy_unit]
    
    def rotate(self, angle):
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=(self.rect.center))

class Heart():
    """Manages the Heart logic which is only used by the Player - controls increasing/decreasing heart rate"""
    def __init__(self):
        super(Heart,self).__init__()
        self.resting_heart_rate = 80
        self.current_heart_rate = 80

        self.maximum_heart_rate = 250
        self.hunting_heart_rate_threshold = constants.HUNTING_HEART_RATE_THRESHOLD
        #the heart rate threshold for zombies to use A* pathfinding

    def increase_heart_rate(self, increment=1):
        self.current_heart_rate +=increment


    def decrease_heart_rate(self, decrement=1):
        self.current_heart_rate = max(self.current_heart_rate - decrement, self.resting_heart_rate)

class Projectile(pygame.sprite.Sprite):

    """
    Focuses solely on projectile physics and rendering. It handles the essential behaviors of 
    a projectile including maintaining both the global (map) and local (screen) coordinates for 
    camera-relative positioning, implementing vector-based movement using normalised direction vectors
    """

    def __init__(self,x ,y, direction_vector):
        self.local_x = constants.SCREEN_WIDTH/2
        self.local_y = constants.SCREEN_HEIGHT/2

        self.speed = 50

        self.global_x = x
        self.global_y = y 

        self.items_list = pygame.sprite.Group()

        self.direction_vector = direction_vector

        super(Projectile,self).__init__()
        self.image = pygame.Surface((20,20),pygame.SRCALPHA)
        self.image.fill((0,0,0,0))
        pygame.draw.circle(self.image, (255,204,0),(10,10), 10)
        self.rect = self.image.get_rect(center = (self.global_x, self.global_y))

    def adjust_coords(self,offset_x, offset_y):
        self.rect.center = (self.global_x - offset_x, self.global_y - offset_y)

    def travel(self):
        x = self.direction_vector[0]
        y = self.direction_vector[1]
        x = round(x,2)
        y = round(y,2)

        self.global_x += x*self.speed
        self.global_y += y*self.speed

class SpawnProjectile():
    """
    Maintains a sprite group for all active projectiles and provides a clean interface 
    for spawning new ones, completely decoupled from the projectile's internal physics or rendering logic
    """
    def __init__(self):
        self.items_list = pygame.sprite.Group()

    def spawn(self, global_x,global_y,direction_vector):
        self.items_list.add(Projectile(global_x,global_y,direction_vector))
            
