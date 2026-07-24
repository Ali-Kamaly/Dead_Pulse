#Ali Kamaly | DEAD PULSE | Version 291
#Main

"""
DEAD PULSE's structure mainly follows the Single Responsibility Principle (SRP), 
making each file responsible for a specific aspect of the game

The game is structured using multiple files instead of a single large script.
This follows modular programming, improving code organisation, scalability, and maintainability
Folders (such as "Audio" and "Sprites") separate assets logically

Pythonic naming conventions have been used throughout the program, ranging from constants to class names
to file names
"""



"""
Modular design for maintainability & reusuability:
Imports are split across multiple custom files for clear separation of concerns; only necessary modules are imported
in any given file
This promotes readability, modular development and allows me to focus of high-level logic (focusing on what the program
does instead of how the computer executes it) in the main file

Program does not crash at all, it is robust- careful defensive coding has been carried out
"""
import pygame, sys, constants, random, pygame_menu, re, requests
from pygame.locals import*

from player import Player
from ui import FieldOfView, Timer, Text
from stats_manager import StatsManager
from map_management import Minimap, MapManager, WallManager
from spawners import BulletSpawner, MedkitSpawner, BatterySpawner, ZombieSpawner
from audio_manager import AudioManager
from camera_management import Background, Screen, Camera


"""
GameState class carries out too many responsiblities & duties
As my programming skill developed, I noticed how monolithic the main orchestrator class is
however I did not have enough time to restructure and change this class to follow the
single responsibility principle

I did make a plan of how to convert GameState into a more efficient structure that follows SRP:

MENU MANAGER: deals with only menu management- displaying and switching between different menus
--> displaying game over menu
--> performance menu 
--> toggle pause
--> display pause menu
--> display shop menu
--> display settings
--> returning to main menu
--> display main menu
--> display leaderboard menu
--> display sorted leaderboard (sorting data etc.)
     --> get sort value

SETTINGS MANAGER: deals with only settings management i.e. changing volume settings and keybindings
--> change keybinding (part of settings)
--> setting music and sound effects volume

UI: deals with displaying info to the player
--> HUD & updating info, drawing, displaying + handling on screen messages i.e. heart rate too high
--> displaying zombies on minimap

ENTITY MANAGER: deals with collision checking and zombie management i.e. increase in strength and decrementing counter
--> check collisions
--> adjust walls
--> dealing with dead zombies -> decreasing zombies remaining
--> increasing zombie health, attack

PLAYER MANAGER: deals with everything to do with the player i.e. rotten flesh and stats
--> username tracking, setting, validating
--> checking validing of username is username valid
--> updating player stats
--> checking saved game availability
--> increase player's rotten flesh 
--> increasing player stats

DATA MANAGER: deals with the data saved for the player as well as fetching data from coingecko api for BTC to GDP conversion
rates
--> deleting saved game before quitting
 --> bitcoin prices, update player info i.e. max health, buyting item (all inside display shop menu method)

WAVE MANAGER: deals with managing the smooth transition of waves, wave performance calculations and fetching data related
to a given map
--> loading new wave (includes spawning next batch of zombies)
--> next wave, change map, start wave
--> calculate wave performance
--> dealing with wave completion
--> is wave complete
(can use mapmanager in wavemanager class for the below:)
--> get map dimensions, map walls, map rooms, map boundaries
--> reset level for next wave

SPAWNER MANAGER: deals with all the spawning - will be used by wave manager


GAME MANAGER: oversees whole game thus all other manager classes go to game manager [CALLS OTHER MANAGERS, BUT DOESN'T DO THEIR JOBS]
--> creating game objects
--> playing again
--> play game
--> reset game
--> resume_game (getting off of pause menu)
"""
class GameState():
    """Manages the whole running of the game- the orchestrator
    The GameState class acts as the central orchestrator of DEAD PULSE, coordinating all major game systems — 
    player control, enemy spawning, AI logic, map management, heart rate integration, FOV torchlight, UI overlays etc

    It represents the game's core loop and lifecycle, switching between running, paused, and ended states, 
    while synchronising input, updates, and rendering

    -> bridges together classes spread over many files, showing clean architectural design
    -> demonstrates high-level abstraction by serving as the “director” of gameplay
    -> enables replayability feature

    """
    def __init__(self, map_manager, screen):
        self.state = "main menu"
        """Note on self.state:
        This project uses a simplified internal state system (via self.state) to control the game's flow
        Each string value (e.g. "playing", "paused", "shop", "main menu") represents a distinct high-level phase
        of the game and determines which code logic is executed.

        While not a formal finite state machine, this makeshift approach offers clarity and structure
        for managing complex interactions, enhancing readability and control during development.

        This technique was vital in helping me reason through the game's logic and keep each gameplay
        phase separate - particularly useful when developing dynamic features like wave transitions,
        and displaying menus."""

        self.paused = False
        #stores whether game is paused or not

        self.game_over = False
        self.cause_of_loss = None

        self.wave_number = 1
        self.zombies_left = 0
        self.wave_target_time = 180
        #time in seconds

        self.map_manager = map_manager
        self.current_map = "basement"

        #tracking player performance in a wave
        self.bullets_fired = 0 
        self.bullets_hit = 0
        self.player_health_start = constants.DEFAULT_CURRENT_HEALTH
        self.total_health_lost = 0
        self.rotten_flesh = 0
        self.zombies_killed = 0

        self.wave_performance = 1.0
        self.wave_score =1.0

        self.screen = screen

        self.field_of_view = FieldOfView()

        #self.display_main_menu(screen)
        #by default displays main menu when program is ran

        #error occurs if player does not press enter for username
        self.entered_username = ""
        self.username = ""
        self.stats_manager = None

        self.leaderboard_manager = StatsManager()

        self.overall_player_performance = {}
        self.saved_player_performance = {}


        """All game objects"""
        self.player = None
        self.player_list = None
        self.zombies = None
        self.bullets = None
        self.medkits = None
        self.batteries = None
        self.wall_manager = None
        self.camera = None
        self.background = None
        self.minimap = None
        self.timer = None

        self.audio_manager = AudioManager()
        self.base_time = constants.DEFAULT_BASE_TIME
        #base_time to compelte a wave is 30s

        #default zombie multipliers
        self.zombie_health_multiplier = 1
        self.zombie_attack_multiplier = 1
        self.previous_zombie_count = 1
        #default total zombies is 1

        #default pickable items spawn count
        self.battery_spawn_count = constants.DEFAULT_BATTERY_SPAWN_COUNT
        self.bullet_spawn_count = constants.DEFAULT_BULLET_SPAWN_COUNT
        self.medkit_spawn_count = constants.DEFAULT_MEDKIT_SPAWN_COUNT

        #surfaces
        self.wall_surface = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))

        self.item_surface = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), 
                                                    pygame.SRCALPHA)
        self.zombie_surface = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT),
                                                    pygame.SRCALPHA)
        self.projectile_surface = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT),
                                                    pygame.SRCALPHA)


        """settings"""
        self.current_music_volume = self.audio_manager.music_volume
        self.current_sound_effects_volume = self.audio_manager.sound_effect_volume
        self.keybinding_labels = {}

        #storing the keybinding labels so can later update them 
        #when player changes keybindings

        """Heartbeat maintenance"""
        self.last_heartbeat_check = pygame.time.get_ticks()
        self.zombies_hunting_heartbeat_threshold = constants.HUNTING_HEART_RATE_THRESHOLD
        #zombies hunting player heart rate threshold
        #if player's heartbeat exceeds this threshold, A* pathfinding will be enabled
        self.last_heartbeat_high_time = None

        #wave 1 zombie count
        self.walker_count = constants.DEFAULT_WALKER_COUNT
        self.runner_count = constants.DEFAULT_RUNNER_COUNT
        self.brute_count = constants.DEFAULT_BRUTE_COUNT


    def create_game_objects(self, loading_game = False):
        """Creates/loads from external file all the necessary game objects required for the running of the game"""
        if loading_game:

            #if user decides to load a previously saved game:
            self.wave_number = self.saved_game_data["Wave Number"]

            self.current_map = self.saved_game_data["Map"]
            map_name = self.current_map

            self.walker_count = self.saved_game_data["Walkers"]
            self.runner_count = self.saved_game_data["Runners"]
            self.brute_count = self.saved_game_data["Brutes"]

            self.battery_spawn_count = self.saved_game_data["Batteries Spawned"]
            self.bullet_spawn_count = self.saved_game_data["Bullets Spawned"]
            self.medkit_spawn_count = self.saved_game_data["Medkits Spawned"]

            self.zombie_health_multiplier = self.saved_game_data["Zombie Health Multiplier"]
            self.zombie_attack_multiplier = self.saved_game_data["Zombie Attack Multiplier"]
            self.saved_player_performance = self.saved_game_data["Game Performance"]

        else:
            map_name = self.current_map
            self.walker_count = constants.DEFAULT_WALKER_COUNT
            self.runner_count = constants.DEFAULT_RUNNER_COUNT
            self.brute_count = constants.DEFAULT_BRUTE_COUNT

        map_width, map_height = self.get_map_dimensions()
        map_walls = self.get_map_walls()

        self.map_manager.store_walls(map_walls)
        self.map_manager.create_walkable_nodes(self.current_map)


        self.player = Player(map_width/2 * constants.CAMERA_ZOOM,map_height/2 * constants.CAMERA_ZOOM)

        self.player.health_bar.set_max_health(self.stats_manager.player_stats["Max Health"])
        #setting player's personal max health from player stats.json
        #setting player's personal attack damage
        self.player.attack_damage = self.stats_manager.player_stats["Attack Damage"]

        if loading_game:
            self.player.health_bar.current_health= self.saved_game_data["Health"]
            self.player.ammo = self.saved_game_data["Ammo"]
            self.player.heart.current_heart_rate = self.saved_game_data["Heart Rate"]
            self.timer = Timer(self.saved_game_data["Time Allocated"])
        else:
            self.timer = Timer(self.base_time)

        self.player_list = pygame.sprite.Group()
        self.player_list.add(self.player)

        self.camera = Camera(map_width, map_height)
        self.background = Background(self.current_map)
        self.player_view = self.camera.transform_background(self.background.image)
        self.minimap = Minimap(map_width, map_height, map_name)
        self.wall_manager = WallManager(map_walls)
        self.wall_manager.load_walls()


        self.batteries = BatterySpawner(map_width, map_height)
        self.batteries.spawn(self.battery_spawn_count)

        self.bullets = BulletSpawner(map_width, map_height)
        self.bullets.spawn(self.bullet_spawn_count)

        self.medkits = MedkitSpawner(map_width, map_height)
        self.medkits.spawn(self.medkit_spawn_count)
        print(f"For wave {self.wave_number} spawned: {self.battery_spawn_count} Batteries,{self.bullet_spawn_count} Bullets,{self.medkit_spawn_count} Medkit")
        self.zombies = ZombieSpawner(map_width, map_height, self.map_manager)
        self.zombies.spawn_walkers(self.walker_count, map_name, self.map_manager,self)
        self.zombies.spawn_runners(self.runner_count, map_name, self.map_manager,self)
        self.zombies.spawn_brutes(self.brute_count, map_name, self.map_manager,self)


    def create_hud(self):
        """Creates the HUD: Heads Up Display, used by the user for important information about player, zombies and map etc."""

        self.bullets_left_display = Text("Impact",50, constants.SCREEN_WIDTH - 225, constants.SCREEN_HEIGHT-60, (255, 204, 0))
        self.zombies_left_display = Text("Slabo 27px",30, constants.SCREEN_WIDTH -335, self.minimap.new_height +100, (85, 107, 47))
        self.heart_rate_display = Text("Impact",50, 25, constants.SCREEN_HEIGHT-60, (168,63,57))
        self.rotten_flesh_display = Text("Impact",30,25,constants.SCREEN_HEIGHT-90, (133, 87, 35))
        self.wave_number_display = Text("Impact",50, 25, 100, (173,216,230))


    def update_hud_info(self):
        """Updates the HUD info"""

        self.bullets_left_display.update_content(f"Ammo: {self.player.ammo}")
        self.zombies_left_display.update_content(f"{self.zombies.walker_count} Walkers | {self.zombies.runner_count} Runners | {self.zombies.brute_count} Brutes")
        self.heart_rate_display.update_content(f"Heart Rate: {self.player.heart.current_heart_rate}")
        self.rotten_flesh_display.update_content(f"Rotten Flesh: {self.stats_manager.player_stats["Rotten Flesh"]}")        
        self.wave_number_display.update_content(f"Wave: {self.wave_number}")
        
        self.minimap.update_player_tracker(self.player.global_rect.x, self.player.global_rect.y)
        


    def draw_hud(self):
        """Draws the HUD information onto the screen"""

        self.bullets_left_display.draw(self.screen)
        self.zombies_left_display.draw(self.screen)
        self.heart_rate_display.draw(self.screen)
        self.rotten_flesh_display.draw(self.screen)
        self.wave_number_display.draw(self.screen)

        self.minimap.draw_player(self.screen)
        #draws zombies locations on minimap if there's at most 10 zombies still alive
        if self.minimap.display_zombies:
            self.minimap.update_zombie_tracker(self.zombies.zombie_list)
            self.minimap.draw_zombies(self.screen)
        

    def create_messages(self):
        """Creates all the messages to notify user of any in-game activity going on that the user
        may not understand or know when intially playing the game- allows for new users to play 
        the game efficiently without requiring external help"""

        #message for zombies hunting - heart rate is going to increase
        self.zombies_hunting_display_1 = Text("Times New Roman", 20, 20, constants.SCREEN_HEIGHT-700,(211, 211, 211))
        self.zombies_hunting_display_2 = Text("Times New Roman", 20, 20, constants.SCREEN_HEIGHT-675,(211, 211, 211))
        self.zombies_hunting_display_1.update_content("Heart Rate Too High - Max Is 250")
        self.zombies_hunting_display_2.update_content("Zombies Now Locating Your Heartbeat")

        #message for no vision - heart rate is going to increase
        self.vision_low_display_1 = Text("Times New Roman", 20, 20, constants.SCREEN_HEIGHT-645,(211, 211, 211))
        self.vision_low_display_2 = Text("Times New Roman", 20, 20, constants.SCREEN_HEIGHT-620,(211, 211, 211))
        self.vision_low_display_1.update_content("Vision Low")
        self.vision_low_display_2.update_content("Get Batteries Fast!")


    def display_messages(self):
        if self.player.heart.current_heart_rate>=self.player.heart.hunting_heart_rate_threshold:
            #need to save hunting heart rate threshold as a separate variable
            self.zombies_hunting_display_1.draw(self.screen)
            self.zombies_hunting_display_2.draw(self.screen)

        if self.field_of_view.radius< constants.GOOD_VISIBILITY_THRESHOLD:
            self.vision_low_display_1.draw(self.screen)
            self.vision_low_display_2.draw(self.screen)

    def handle_collisions(self, movement_x, movement_y):
        """Checks collisions between two game objects"""

        #player collision with walls
        walls_hit_list = pygame.sprite.spritecollide(self.player,self.wall_manager.walls_list,False)
        for _ in walls_hit_list:
            self.player.undo_movement(movement_x,movement_y)

        #player collision with bullets
        bullets_hit_list = pygame.sprite.spritecollide(self.player,self.bullets.items_list, True)
        for _ in bullets_hit_list:
            self.player.increase_ammo(constants.AMMO_PICKUP)

        #player collision with medkits
        medkits_hit_list = pygame.sprite.spritecollide(self.player,self.medkits.items_list, True)
        for _ in medkits_hit_list:
            self.player.health_bar.recover_health()

        #player collision with batteries
        batteries_hit_list = pygame.sprite.spritecollide(self.player,self.batteries.items_list,True)
        for _ in batteries_hit_list:
            self.field_of_view.increase_view()

        
        #checking player collision with zombies - using timer to prevent zombies from 
        #taking too much health from the player at once
        zombies_hit_list = pygame.sprite.spritecollide(self.player,self.zombies.zombie_list,False)
        for zombie in zombies_hit_list:
            current_time = pygame.time.get_ticks()
            if current_time - zombie.last_time_attacked >= zombie.attack_cooldown:
                self.player.health_bar.take_damage(game_state = self)
                self.total_health_lost += 5
                zombie.last_time_attacked = current_time
                self.player.getting_attacked = True

        #zombie collision with walls
        zombies_hitting_wall = pygame.sprite.groupcollide(self.zombies.zombie_list, self.wall_manager.walls_list, False, False)
        for zombie in zombies_hitting_wall:
            zombie.get_unstuck(self.wall_manager.walls_list)
            #doesn't work as intended

        #projectile collision with zombies
        pygame.sprite.groupcollide(self.wall_manager.walls_list, self.player.projectiles.items_list, False, True)
        zombies_hit_list = pygame.sprite.groupcollide(self.zombies.zombie_list, self.player.projectiles.items_list, False, True)
        for zombie in zombies_hit_list:
            zombie.health_bar.take_damage(damage = self.player.attack_damage)
            self.bullets_hit +=1

        #bullet pack collision with walls
        bullets_hit_walls_list = pygame.sprite.groupcollide(self.bullets.items_list, self.wall_manager.walls_list, True, False)
        for _ in bullets_hit_walls_list:
            self.bullets.spawn(1)
            #respawning bullet packs that have collided with walls
        
        #medkit collision with walls
        medkits_wall_hit_list = pygame.sprite.groupcollide(self.medkits.items_list,self.wall_manager.walls_list, True, False)
        for _ in medkits_wall_hit_list:
            self.medkits.spawn(1)

        batteries_wall_hit_list = pygame.sprite.groupcollide(self.batteries.items_list,self.wall_manager.walls_list,True,False)
        for _ in batteries_wall_hit_list:
            self.batteries.spawn(1)


    def handle_dead_zombies(self):
        """Deals with zombies that have been killed by the player and thus the immediate consequences 
        i.e. increment rotten flesh"""
        for zombie in self.zombies.zombie_list:
            #updating tracker of zombie on the minimap
            #minimap.update_tracker(zombie)
            if zombie.health_bar.current_health <= 0 :
                if zombie.type == "walker":
                    self.zombies.walker_count -=1
                elif zombie.type == "runner":
                    self.zombies.runner_count -=1
                else:
                    self.zombies.brute_count -=1
                zombie.on_death(self)
                self.stats_manager.increment_stat("Rotten Flesh", self.rotten_flesh)
                zombie.kill()
                self.zombies_killed +=1
                self.audio_manager.play_sound_effect("killed zombie", 15)
                #for 1 in every 15 zombies killed, sound effect will be played

                self.stats_manager.increment_stat("Total Zombies Killed")
                self.stats_manager.save_stats()
                #zombies killed is automatically saved after kill

    def update_player_stats(self):
        """Updating & saving player stats dynamically to an external file""" 
        self.stats_manager.increment_stat("Total Waves Survived")
        self.stats_manager.increment_stat("Total Bullets Fired", self.bullets_fired)
        self.stats_manager.increment_stat("Total Bullets Hit", self.bullets_hit)
        self.stats_manager.increment_stat("Total Score", int(self.wave_performance*1000)*self.wave_number)
        #score is calculated as the int of 1000* wave_performance * wave_number (to reward progressing to higher waves)
        self.stats_manager.update_wave_highscore(self.wave_number +1)
        #+1 as they've now moved to next wave

        #saving all the updated data
        self.stats_manager.save_stats()

    def load_next_wave(self):
        """Completes all necessary actions to prepare for and load next wave"""
        self.start_wave()
        self.next_wave()
        self.reset_level_for_next_wave()
        #saving at the beginning of every new wave
        self.stats_manager.save_game(self)
        self.minimap.display_zombies = False

    def should_display_zombies_on_minimap(self):
        """Zombies location is only shared on the minimap if there are less than or equal to 3 zombies still alive"""
        if len(self.zombies.zombie_list) <= constants.ZOMBIE_COUNT_THRESHOLD:
            self.minimap.display_zombies = True
    
    def update(self, zombies_list):
        self.zombies_left = len(zombies_list)
        current_time = pygame.time.get_ticks()
        
        #checking wave completion
        if self.zombies_left == 0:
            self.handle_wave_completion()

        #checking player heartbeat 
        if self.player.heart.current_heart_rate >= self.zombies_hunting_heartbeat_threshold:
            if self.last_heartbeat_high_time is None:
                self.last_heartbeat_high_time = current_time
                #starts tracking time of player's heartbeat

            #resets heartbeat high time (if player's heartbeat is less than threshold)

        #Assigning zombies dynamically to utilise A* pathfinding - ONLY IF player heartbeat >threshold
        #for 5+ seconds
        #if self.last_heartbeat_high_time and current_time - self.last_heartbeat_high_time>self.heartbeat_duration:
            if current_time - self.last_heartbeat_check >= 5000:
                #print("5 seconds of high heartrate has passed")
                #updates every 5 seconds
                self.last_heartbeat_check = current_time
                #print("gonna assign hunters now")
                self.zombies.assign_hunters((self.player.global_rect.x/constants.CAMERA_ZOOM,
                                            self.player.global_rect.y/constants.CAMERA_ZOOM))
                self.last_player_pos = self.player.global_rect.center
                self.last_hunter_assign_time = current_time
                #argument is a tuple of player's global coords

        else:
            # When the heartbeat drops below the threshold, clear the hunter status.
            self.last_heartbeat_high_time = None
            for zombie in self.zombies.active_hunters:
                zombie.path = []  
            self.zombies.active_hunters = [] 

        
        self.zombies.update_all(self, self.player, self.wall_manager.walls_list)
        #self.zombies.zombie_list.update(self, self.player, self.wall_manager.walls_list)

        #checking different causes of death for the player
        if self.timer.time_left ==0:
            self.game_over = True
            self.cause_of_loss = "Ran Out Of Time"

        elif self.player.health_bar.current_health == 0:
            self.game_over = True
            self.cause_of_loss = "Eaten Alive"

        elif self.player.heart.current_heart_rate >= self.player.heart.maximum_heart_rate:
            self.game_over = True
            self.cause_of_loss = "Heart Attack"

    def display_game_over(self, previous_menu = ""):
        """Displays game over menu after player has died"""

        if previous_menu:
            previous_menu.disable()

        self.audio_manager.stop_sound_effect()
        #stopping all current sound effects from overplaying onto game over
        self.audio_manager.play_music("main menu")

        game_over_menu =   pygame_menu.Menu(f" {self.username}", constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT,
                    theme = pygame_menu.themes.THEME_DARK)
        
        game_over_menu.add.label("GAME OVER", font_size = 100, font_color = (168,63,57), font_name = 'Fonts/grooved font.ttf')
        game_over_menu.add.label(f"{self.cause_of_loss}", font_name = 'Georgia', font_size = 30, font_color = (255, 204, 0))

        game_over_menu.add.button("Play Again", lambda:self.play_again(game_over_menu, player_died = True))
        game_over_menu.add.button("Game Performance", lambda:self.display_performance(game_over_menu))
        game_over_menu.add.button("Leaderboard", lambda:self.display_leaderboard(game_over_menu, return_to="game over menu"))
        game_over_menu.add.button("Help",lambda:self.display_help(game_over_menu, return_to="game over menu"))
        game_over_menu.add.button("Sign Out", lambda:self.return_to_main_menu(game_over_menu, player_died = True))
        game_over_menu.add.button("Quit", lambda:self.delete_saved_game_before_quitting())


        #locally storing game performance as the data will get deleted afterwards in json file
        #prevents user from bypassing deletion of saved game by exiting the program after dying
        #stopping the game from crashing
        try:
            self.game_performance = self.stats_manager.get_game_performance().items()
        except KeyError:
            #keyError will occur once performance data is delete in json file
            ...

        #performance data is deleted in external file
        self.stats_manager.delete_previous_game_save()
        #locally saved performance data is also reset
        self.saved_player_performance = {}

        game_over_menu.mainloop(self.screen)

    def delete_saved_game_before_quitting(self):
        """Deletes saved game data before exiting the program"""
        if 'Previous Game' in self.stats_manager.all_player_stats[self.username]:
            self.stats_manager.delete_previous_game_save()
        pygame_menu.events.EXIT
        sys.exit()


    def display_performance(self, game_over_menu):
        """game performance displays data of the player's game 
        (saves data of a game that was even previously left half way through)"""
        game_over_menu.disable()

        performance_menu = pygame_menu.Menu(f" {self.username}", constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT,
                    theme = pygame_menu.themes.THEME_DARK)
        
        performance_menu.add.label("Performance Breakdown", font_size = 100, font_color = (168,63,57), font_name = 'Fonts/grooved font.ttf')
        
        performance_table = performance_menu.add.table(font_size = 20)
        performance_table.add_row(["       ","    Time Taken    ","    Zombies Killed    ","   Accuracy    ","   Score   "],
            cell_font=pygame_menu.font.FONT_OPEN_SANS_BOLD,cell_align=pygame_menu.locals.ALIGN_CENTER)
        
        try:
            for wave, stats in self.game_performance:
                #game crashes if player dies in wave 1 and game performance is to be shown
                performance_table.add_row([
                    wave, 
                    stats["Time Taken"],
                    stats["Zombies Killed"],
                    stats["Accuracy"],
                    stats["Score"]], 
                    cell_align = pygame_menu.locals.ALIGN_CENTER)
        except AttributeError:
            #will occur if player dies in wave 1 and game performace is to be shown
            performance_table.add_row([
                "Wave 1",
                0,
                0,
                0,
                0],
                cell_align = pygame_menu.locals.ALIGN_CENTER)
        
        performance_menu.add.button("Back", lambda:self.display_game_over(performance_menu))

        performance_menu.mainloop(self.screen)

    def play_again(self, game_over_menu, player_died = False):
        #game_over_menu.disable()
        self.reset_game(player_died)
        self.play(menu=game_over_menu, play_again=True)


    def handle_wave_completion(self):
        self.state = "wave complete"
        print(f"Wave {self.wave_number} complete!")


    def toggle_pause(self):
        self.paused = not self.paused
        #changes True to False and vice verse
        if self.paused:
            self.display_pause_menu()

    def display_pause_menu(self, previous_menu = ""):
        if previous_menu:
            previous_menu.disable()
            #implemented manual menu switching - gives me full control over menu transitions etc. instead
            #of relying on built-in shortcuts like pygame_menu.events.BACK

            #scalable structure
        
        self.state = "paused"

        self.audio_manager.play_music("paused")
        self.audio_manager.set_music_volume(self.current_music_volume)
        self.audio_manager.set_sound_effect_volume(self.current_sound_effects_volume)

        #stopping timer countdown (when last 10 sects) from continuing to play
        self.audio_manager.stop_sound_effect("last 10 secs")
        self.timer.playing_audio_countdown = False

        #stopping 'we don't have enough time' audio
        self.audio_manager.stop_sound_effect("low time")
        self.timer.low_time_audio_played = False



        pause_menu = pygame_menu.Menu(f" {self.username}", constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT,
                    theme = pygame_menu.themes.THEME_DARK)
        
        pause_menu.add.label("PAUSED", font_size = 100, font_color = (168,63,57), font_name = 'Fonts/grooved font.ttf')

        pause_menu.add.button("Resume", lambda:self.resume_game(pause_menu))
        #if resume pressed, pause is changed back to False
        pause_menu.add.button("Settings", lambda: self.display_settings(pause_menu, "pause menu") )
        pause_menu.add.button("Shop", lambda: self.display_shop(pause_menu, "pause menu"))
        pause_menu.add.button("Leaderboard",lambda: self.display_leaderboard(pause_menu, "pause menu"))
        pause_menu.add.button("Help",lambda: self.display_help(pause_menu, "pause menu"))
        pause_menu.add.button("Sign Out", lambda: self.return_to_main_menu(pause_menu))
        pause_menu.add.button("Quit", pygame_menu.events.EXIT)

        
        pause_menu.mainloop(self.screen)

        #displays the pause menu to screen

    def resume_game(self, pause_menu):
        pause_menu.disable()
        self.paused = False
        self.state = "playing"
        self.audio_manager.play_music("wave")
        self.audio_manager.set_music_volume(self.current_music_volume)
        self.audio_manager.set_sound_effect_volume(self.current_sound_effects_volume)

        self.timer.last_time_updated = pygame.time.get_ticks()
        #prevents timer from reducing time left by time spend during pause

    def display_shop(self, previous_menu, return_to):
        """Handles the logic for the in-game shop screen
        This method contains nested helper subroutines (e.g. update_player_info, get_market_price)
        that are defined locally because they are tightly coupled with the shop logic and are 
        not required anywhere else in the program.

        This encapsulation improves modularity, keeps the program clean, and makes it easier to 
        reason about the shop's functionality in isolation from other sections of the code

        It also reflects my intention to design the game in a way where specific functionality is 
        self-contained and not unnecessarily exposed to the rest of the code."""
        previous_menu.disable()


        self.state = "shop"
        shop_menu = pygame_menu.Menu(f" {self.username}", constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT,
                        theme = pygame_menu.themes.THEME_DARK)
        
        shop = shop_menu.add.label("DEAD MANS DEALS", font_size = 100, font_color = (168,63,57), font_name = 'Fonts/grooved font.ttf')
        #grammatically incorrect -> giving shady, black-market feel
        tag_line = shop_menu.add.label("You bring the meat, I bring the heat", font_name = 'Georgia', font_size = 30, font_color = (255, 204, 0))

        #shop can only be accesed via the pause menu
        shop_menu.add.button("Back", lambda: self.display_pause_menu(shop_menu))

        #displays player's current details - making it easier to decide business transactions
        player_info_a = shop_menu.add.label(f"Rotten Flesh: {self.stats_manager.player_stats["Rotten Flesh"]} | Health: {self.player.health_bar.current_health}/{self.player.health_bar.max_health}", 
                            font_name = 'Georgia', font_size = 20, font_color = (255, 204, 0))
        player_info_b = shop_menu.add.label(f"Ammo: {self.player.ammo} | Attack Damage: {self.player.attack_damage} | Vision: {self.field_of_view.radius}/{self.field_of_view.max_radius}",
                            font_name = 'Georgia', font_size = 20, font_color = (255, 204, 0))

        def update_player_info():
            """Dynamically updates player info such as current health after a purchase"""
            player_info_a.set_title(f"Rotten Flesh: {self.stats_manager.player_stats["Rotten Flesh"]} | Health: {self.player.health_bar.current_health}/{self.player.health_bar.max_health}")
            player_info_b.set_title(f"Ammo: {self.player.ammo} | Attack Damage: {self.player.attack_damage} | Vision: {self.field_of_view.radius}/{self.field_of_view.max_radius}")



        def get_market_prices():
            """Gets Bitcoin API price and converts to rotten flesh currency - mimicing a voltaile market environment"""
            bitcoin_rate = get_bitcoin_price()
            #print(bitcoin_rate)

            if bitcoin_rate:
                print(f"Bitcoin rate: {bitcoin_rate}")
                print(f"""Instant Health Boost: Round {bitcoin_rate}/1000 + 5 = {round((bitcoin_rate/1000) + 5)}, Increase Max Health: Round {bitcoin_rate}/325 +53 = {round((round(bitcoin_rate/325)+53))}
                      Ammo: Round {bitcoin_rate}/750 = {round(bitcoin_rate/750)}, Increase Bullet Damage: Round {bitcoin_rate}/325 +68 = {round((bitcoin_rate/325)+68)}, Battery: Round {bitcoin_rate}/750 + 8 = {round((bitcoin_rate/750)+8)}""")
                return round((bitcoin_rate/1000) + 5), round((round(bitcoin_rate/325)+53)), round(bitcoin_rate/750), round((bitcoin_rate/325)+68), round((bitcoin_rate/750)+8)
                
                #returns prices of: instant health boost, increase max health, ammo, increase damage price, battery
                #minimum: 25, 50, 75

            #just in case fetching fails - coding defensively
            return 10,10,10

        def get_bitcoin_price():
            """Uses coingecko api to fetch conversion rate of bitcoin to GBP"""
            url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=gbp'
            try:
                response = requests.get(url)
                api_data = response.json()
                return api_data["bitcoin"]["gbp"]
            except:
                return constants.DEFAULT_BITCOIN_PRICE
                #fallback default exchange rate if api fails
                #robust - added try and except to prevent program from crashing if fetching of conversion rate fails


        def buy_item(item, price):
            """Deals with transaction of Rotten Flesh"""

            max_stat.hide()
            if self.stats_manager.player_stats["Rotten Flesh"]>= price:
                #self.stats_manager.player_stats["Rotten Flesh"] -= price

                #checking player doesn't already have max stat available
                if item == 'increase current health':
                    if self.player.health_bar.current_health==self.player.health_bar.max_health:
                        max_stat.show()
                        #print("didn't buy")
                        return
                elif item == 'increase fov':
                    if self.field_of_view.radius == self.field_of_view.max_radius:
                        max_stat.show()
                        #print("didn't buy")
                        return
                    
                if item == "increase current health":
                    self.player.health_bar.recover_health(constants.BOUGHT_IMMEDIATE_HEALTH_RECOVERY)
                    #print(self.player.health_bar.current_health)
                elif item == "increase max health":
                    self.player.health_bar.max_health += constants.MAX_HEALTH_INCREMENT
                    #updating max health in player stats
                    self.stats_manager.increment_stat("Max Health", 10)
                elif item == "increase ammo":
                    self.player.ammo += constants.PURCHASED_AMMO_INCREMENT
                elif item == "increase attack damage":
                    self.player.attack_damage= round(self.player.attack_damage*constants.ATTACK_DAMAGE_INCREMENT_RATIO)
                    #slow gradual growth of attack damage - more consistent vital especially since
                    #using a more random & voltaile pricing using bitcoin
                    self.stats_manager._set_stat("Attack Damage", self.player.attack_damage)
                elif item == 'increase fov':
                    self.field_of_view.increase_view()

                self.stats_manager.increment_stat("Rotten Flesh", -price)
                #print("Item bought")

                self.stats_manager.save_stats()
                #instantly updates changes
                update_player_info()

            else:
                not_enough_flesh.show()


        health_price, max_health_price, ammo_price, damage_price, battery_price = get_market_prices()
        #print(health_price, max_health_price, ammo_price)

        shop_menu.add.button(f"Emergency health boost (+25 current health): {health_price} Rotten Flesh", lambda: buy_item("increase current health", health_price))
        shop_menu.add.button(f"Increase Max Health (+10 max health): {max_health_price} Rotten Flesh", lambda: buy_item("increase max health", max_health_price))
        shop_menu.add.button(f"Ammo (+20): {ammo_price} Rotten Flesh", lambda: buy_item("increase ammo", ammo_price))
        shop_menu.add.button(f"Increase Attack Damage (x1.15): {damage_price}", lambda: buy_item("increase attack damage",damage_price))
        shop_menu.add.button(f"Torchlight battery (+200 radius): {battery_price}", lambda: buy_item("increase fov",battery_price))


        not_enough_flesh = shop_menu.add.label("Insufficient rotten flesh",
                            font_size = 25, font_color=(168,63,57), font_name = 'Georgia' )
        max_stat = shop_menu.add.label("Max Stat Brother",
                            font_size = 25, font_color=(168,63,57), font_name = 'Georgia')

        not_enough_flesh.hide()
        max_stat.hide()



        shop_menu.mainloop(self.screen)

    def display_settings(self, menu, return_to = "main menu"):
        menu.disable()
        #removes the previous menu that the player was on
        self.state = "settings"
        settings_menu = pygame_menu.Menu(f" {self.username}", constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT,
                        theme = pygame_menu.themes.THEME_DARK)

        settings = settings_menu.add.label("SETTINGS", font_size = 100, font_color = (168,63,57), font_name = 'Fonts/grooved font.ttf')

 
        if return_to == "pause menu":
            settings_menu.add.button("Back", lambda: self.display_pause_menu(settings_menu))


            """Keybinding is only allowed while in-game"""
            settings_menu.add.button("'Move Up' Key", lambda: self.change_keybinding("up"))
            settings_menu.add.button("'Move Left' Key", lambda: self.change_keybinding("left"))
            settings_menu.add.button("'Move Down' Key", lambda: self.change_keybinding("down"))
            settings_menu.add.button("'Move Right' Key", lambda: self.change_keybinding("right"))

            settings_menu.add.button("'Run' Key", lambda: self.change_keybinding("run"))
            settings_menu.add.button("'Shoot' Key", lambda: self.change_keybinding("shoot"))


            settings_menu.add.label("Keybindings:", font_name = 'Georgia', font_size = 40, font_color = (255, 204, 0))
           
            for action, key in self.player.keybindings.items():
                self.keybinding_labels[action] = settings_menu.add.label(
                    f"{action.capitalize()}: {pygame.key.name(key).capitalize()}")
                #storing default keybindings locally so can update later dynamically if necessary (i.e. player changed keybindings)
            
        else:
            settings_menu.add.button("Back", lambda: self.display_main_menu(settings_menu))

        self.music_volume = settings_menu.add.range_slider("Music Volume", default = self.audio_manager.music_volume, range_values=(0,100), increment = 1,
                        onchange= self.set_music_volume)

        self.sound_effects_volume = settings_menu.add.range_slider("Sound Effects Volume", default = self.audio_manager.sound_effect_volume, range_values=(0,100), increment = 1,
                        onchange= self.set_sound_effects_volume)
        
        """SOUND EFFECTS VOLUME SLIDER doesn't update in main menu since there are no sound effects being played
        in the main menu
        but the slider does work and automatically applies the set volume to sound when played i.e. in-game"""

        
        settings_menu.mainloop(self.screen)

    def change_keybinding(self, key):
        no_letter_pressed = True
        while no_letter_pressed:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    self.player.keybindings[key] = event.key
                    self.keybinding_labels[key].set_title(f"{key.capitalize()}: {pygame.key.name(event.key).capitalize()}")  
                    #set_title to instantly update label
                    #storing the letter pressed in keybindings dictionary
                    no_letter_pressed = False

    def set_music_volume(self, volume):
        #helps to store volume level after player has changed it
        self.current_music_volume = volume
        self.audio_manager.set_music_volume(self.current_music_volume)

    def set_sound_effects_volume(self, volume):
        self.current_sound_effects_volume = volume
        self.audio_manager.set_sound_effect_volume(self.current_sound_effects_volume)

    def return_to_main_menu(self, previous_menu = None, player_died = False):
        if previous_menu:
            previous_menu.disable()
            #if previous_menu parametere has been entered 

        self.username = ""
        #stops all sound effects that are being played
        self.audio_manager.stop_sound_effect()

        #removes pause menu and resets game state
        self.state = "main menu"
        if self.paused == True:
            self.paused = False
        self.reset_game(player_died)
        #resets all the data about current game i.e. zombie list etc.
        self.display_main_menu()

    #method from pygame menu website
    def display_main_menu(self, previous_menu = None, invalid_username_shown = False, previous_game_found = False):

        if previous_menu:
            #if coming from a previous menu
            previous_menu.disable()

        self.audio_manager.play_music("main menu")
        #self.audio_manager.set_music_volume(20)

        if previous_menu == "main menu":
            self.username=''
        top_right_name = ' '
        if previous_game_found:
            top_right_name = f" {self.username}"

        main_menu = pygame_menu.Menu(top_right_name, constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT,
                    theme=pygame_menu.themes.THEME_DARK)

        title = main_menu.add.label("DEAD PULSE", font_size = 275, font_color = (168,63,57), font_name = 'Fonts/grooved font.ttf')

        username_box = main_menu.add.text_input('Username: ', default=self.entered_username,onchange= self.track_username, maxchar= 18)
        #stops user from spamming letters into textbox - ruining the integrity/structure of the textbox and game
        #calls track_username which stores what is entered by user in 'username' box
        invalid_username_msg = main_menu.add.label("Invalid Username (3-17 characters: only letters, numbers and/or underscores- must start with a letter)",
                                                font_size = 25, font_color=(168,63,57), font_name = 'Georgia')
        if not invalid_username_shown: 
            invalid_username_msg.hide()
        #only hides invalid username message if username previously entered was invalid

        play_button = main_menu.add.button('Play', lambda:self.username_validation(invalid_username_msg, main_menu))

        new_game = main_menu.add.button('New Game', lambda:self.play(main_menu))
        load_game = main_menu.add.button('Load Saved Game', lambda:self.play(main_menu, load_game = True))


        #user shouldn't be able to change username after signining into someone in main menu

        settings_button = main_menu.add.button('Settings', lambda:self.display_settings(main_menu))
        leaderboard_button = main_menu.add.button('Leaderboard', lambda:self.display_leaderboard(main_menu))
        #not naming buttons if they're not going to be called later on in the program
        help_button = main_menu.add.button('Help', lambda:self.display_help(main_menu, return_to="main menu"))
        back_button = main_menu.add.button('Back', lambda:self.display_main_menu(main_menu))

        main_menu.add.button('Quit', pygame_menu.events.EXIT)
        main_menu.add.label("Ali Kamaly",font_size = 75,font_color=(255, 204, 0), font_name="Fonts/Bastliga One.ttf")

        if not previous_game_found:
            new_game.hide()
            load_game.hide()
            back_button.hide()
        else:
            username_box.hide()
            play_button.hide()
            settings_button.hide()
            leaderboard_button.hide()
            help_button.hide()

        main_menu.mainloop(self.screen)

    def track_username(self, username):
        #constantly updates username based on what the user is entering
        self.entered_username = username

    def _set_username(self, username):
        #only called within class
        self.username = username
        self.stats_manager = StatsManager(self.username)
        #leaves all the data handling to statsmanager

    def username_validation(self,invalid_username_msg, previous_menu):
        """Sets username if a valid username has been written"""

        if self.entered_username and self.is_valid_username(self.entered_username):
            #checks to make sure entered username is not empty
            self._set_username(self.entered_username)
            invalid_username_msg.hide()

            #directs to next stage: checking if a saved game is avaiable for the set user
            self.check_saved_game(previous_menu)

        else:
            #if a username has not been entered then player cannot continue
            self.display_main_menu(previous_menu,invalid_username_shown= True)
            #invalid_username.show()


    def check_saved_game(self, previous_menu):
        """Checks if the user has a saved game associated with their account"""

        if self.stats_manager.saved_game_avaiable():
            self.saved_game_data = self.stats_manager.get_saved_game_data()
            #print(self.saved_game_data)
            #print("loaded saved game")

            #let user choose if they want to play new game, or load saved game
            previous_menu.disable()
            #disables previous instance of main menu
            self.display_main_menu(previous_game_found = True)
        
        else:
            #if user doesn't have saved game associated with their account, they should
            #just automatically start playing the game

            #
            #print("no saved game found")
            self.play(previous_menu)



    def play(self, menu, play_again=False, load_game = False):

        if load_game:
            self.create_game_objects(loading_game=True)

        elif not play_again and not load_game:
            #username must be entered only if you are not playing again from last game
            self.create_game_objects() #only do if starting a complete new game

        else:
            #keeping the same username if playing again
            self._set_username(self.username)
            self.create_game_objects()


        self.timer.start()
        self.state = "playing"
        menu.disable()
        self.audio_manager.play_music("wave")
        self.audio_manager.set_music_volume(self.current_music_volume)
        self.audio_manager.set_sound_effect_volume(self.current_sound_effects_volume)


    def is_valid_username(self, username):
        """Checks validity of an entered username using regex to make sure an adequate username has been entered"""

        pattern = r"^[A-Za-z][A-Za-z0-9_]{2,16}$"


        #username requirement: must start with a letter, then have 2-17 instances of letters, numbers
        #and/or underscores combined
        return bool(re.fullmatch(pattern, username))

    def display_leaderboard(self, previous_menu = None, return_to = None):
        if previous_menu:
            previous_menu.disable()    

        leaderboard_menu = pygame_menu.Menu(f' {self.username}', constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT,
                           theme = pygame_menu.themes.THEME_DARK )

        self.display_sorted_leaderboard("Total Score", leaderboard_menu, return_to)
        #call sort leaderboard method to show top 10 players depending on a certain criteria i.e. 'Total Zombies Killed'
        #default criteria is total score

        leaderboard_menu.mainloop(self.screen)
    
    def display_sorted_leaderboard(self, sort_by, leaderboard_menu = None, return_to = None):
        """Sorts leaderboard, displaying only the top 10 of any criteria"""

        #loads every player's stats
        self.leaderboard_manager.load_all_stats()
        #first update all the data then display the data on leaderboard

        all_player_stats = self.leaderboard_manager.get_all_stats()
        #print(f"All player stats: {all_player_stats}")

        def get_sort_value(player):
            """Helper function - only needed in display_sorted_leaderboard method hence nested, keeps code neat & organised"""
            username, stats = player
            return stats.get("Stats",{}).get(sort_by, 0)
            #has to first look in the 'Stats' dictionary
            #if data is missing 0 is returned by default
            #returns name of a column i.e. 'Total Zombies Killed' from player stats.json

        sorted_leaderboard = sorted(all_player_stats.items(), key = get_sort_value, reverse = True)
        #descending order
        #.items() converts dictionary of all_player_stats to tuple so can be easier to sort values
        #key = what we're ordering by i.e. ordering by sort_by 

        top_10 = sorted_leaderboard[:10]

        if leaderboard_menu:
            leaderboard_menu.clear()
        #empty the leaderboard before adding to it

        leaderboard_menu.add.label("LEADERBOARD", font_size = 100, font_color = (168,63,57), font_name = 'Fonts/grooved font.ttf')

        #telling user how leaderboard is being sorted
        leaderboard_menu.add.label(f"Top 10 Sorted By: {sort_by}", font_color=(255, 204, 0), font_name = 'Georgia') 

        table = leaderboard_menu.add.table(font_size = 20)
        table.add_row(["    Username    ", "    Zombies Killed    ", "    Waves Survived    ", "    Wave Highscore    ",
                       "    Bullets Hit    ","    Bullets Fired    ","    Rotten Flesh    ","    Total Score    "],
            cell_font=pygame_menu.font.FONT_OPEN_SANS_BOLD,cell_align=pygame_menu.locals.ALIGN_CENTER)

        #gets data value for each user and column (i.e. total zombies killed)
        for username, user_data in top_10:
            stats = user_data.get("Stats",{})
            table.add_row([
                username,
                #included commas for numbers to help user read the numbers better

                "{:,}".format(stats.get('Total Zombies Killed', 0)),
                "{:,}".format(stats.get('Total Waves Survived', 0)),
                "{:,}".format(stats.get('Wave Highscore', 0)),
                "{:,}".format(stats.get('Total Bullets Hit', 0)),
                "{:,}".format(stats.get('Total Bullets Fired', 0)),
                "{:,}".format(stats.get('Rotten Flesh', 0)),
                "{:,}".format(stats.get('Total Score', 0))], cell_align=pygame_menu.locals.ALIGN_CENTER
                )
            #default value is 0

        if return_to == "pause menu":
            leaderboard_menu.add.button("Back", lambda: self.display_pause_menu(previous_menu=leaderboard_menu))
        elif return_to == "game over menu":
            leaderboard_menu.add.button("Back", lambda: self.display_game_over(previous_menu=leaderboard_menu))
        else:
            leaderboard_menu.add.button("Back", lambda: self.display_main_menu(leaderboard_menu))


        leaderboard_menu.add.label(f"Sort by:",font_color=(255,204,0), font_name = 'Georgia') 

        leaderboard_menu.add.button("==> Zombies Killed", lambda: self.display_sorted_leaderboard(
                                    "Total Zombies Killed", leaderboard_menu, return_to))
        leaderboard_menu.add.button("==> Waves Survived", lambda: self.display_sorted_leaderboard(
                                    "Total Waves Survived", leaderboard_menu, return_to))
        leaderboard_menu.add.button("==> Wave Highscore", lambda: self.display_sorted_leaderboard(
                                    "Wave Highscore", leaderboard_menu, return_to))
        leaderboard_menu.add.button("==> Bullets Hit", lambda: self.display_sorted_leaderboard(
                                    "Total Bullets Hit", leaderboard_menu, return_to))
        leaderboard_menu.add.button("==> Bullets Fired", lambda: self.display_sorted_leaderboard(
                                    "Total Bullets Fired", leaderboard_menu, return_to))
        leaderboard_menu.add.button("==> Rotten Flesh", lambda: self.display_sorted_leaderboard(
                                    "Rotten Flesh", leaderboard_menu, return_to))
        leaderboard_menu.add.button("==> Score", lambda: self.display_sorted_leaderboard(
                                    "Total Score", leaderboard_menu, return_to))

    def display_help(self, previous_menu = None, return_to = None):
        """Displays all the useful information for the game - allows the user to be able to play the game independently
        and gain knowledge about the game and some tips & tricks to help them improve in-game without any external help
        allowing the program to be used indepenedently"""
        if previous_menu:
            previous_menu.disable()

        help_menu = pygame_menu.Menu(f' {self.username}', constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT,
                        theme = pygame_menu.themes.THEME_DARK)
    
        help_menu.add.label("HELP", font_size = 100, font_color = (168,63,57), font_name = 'Fonts/grooved font.ttf')

        if return_to == "main menu":
            help_menu.add.button("Back",lambda: self.display_main_menu(help_menu))
        elif return_to == "main menu":
            help_menu.add.button("Back",lambda: self.display_pause_menu(help_menu))
        elif return_to == "game over menu":
            help_menu.add.button("Back",lambda: self.display_game_over(help_menu))
        
        else:
            help_menu.add.button("Back",lambda: self.display_pause_menu(help_menu))


        help_menu.add.label("ABOUT",font_name = 'Georgia', font_size = 25, font_color = (255, 204, 0))
        help_menu.add.label("Trapped in a relentless undead apocalypse, your only goal is to survive.\nNavigate eerie maps, manage your resources, and keep your heart rate in check\nas you fight off waves of evolving zombies.\nUse your torchlight to spot threats, but don't let it fade.\nEach wave gets tougher, with smarter enemies and a relentless ticking timer.\nAdapt, strategise, and endure - because in DEAD PULSE, survival isn't just about shooting.\nIt's about control.\n", 
                            font_size = 25,font_color = (255, 255, 255))

        help_menu.add.label("IN-GAME DISPLAY",font_name = 'Georgia', font_size = 25, font_color = (255, 204, 0))
        help_menu.add.image("Sprites/in-game description.png")

        help_menu.add.label("HEART RATE",font_name = 'Georgia', font_size = 25, font_color = (255, 204, 0))
        help_menu.add.label("Sprint, fight, or panic, and your pulse will skyrocket\nLet it exceed 250 BPM, and you'll suffer a fatal heart attack\n Heart rate falls when you aren't getting attacked,can't see and aren't running\nIf you also stand completely still, your heart rate falls faster\n ", 
                            font_size = 25,font_color = (255, 255, 255))

        help_menu.add.label("AI THAT LEARNS",font_name = 'Georgia', font_size = 25, font_color = (255, 204, 0))
        help_menu.add.label("The calmer you are, the dumber the zombies.\nLet your heart race, and they'll hunt you like predators using advanced AI pathfinding\n", 
                            font_size = 25,font_color = (255, 255, 255))
        
        help_menu.add.label("THE ZOMBIE HALL OF FAME",font_name = 'Georgia', font_size = 25, font_color = (255, 204, 0))

        help_menu.add.label("WALKERS",font_name = 'Times New Roman',font_size = 25,font_color = (255, 255, 255))
        help_menu.add.image("Sprites/walker.png")
        help_menu.add.label("The most basic of zombies.\nThey got normal health, speed and attack damage.\nDon't overlook these guys else they'll walk all over you\n", 
                            font_size = 25,font_color = (255, 255, 255))


        help_menu.add.label("RUNNERS",font_name = 'Times New Roman',font_size = 25,font_color = (255, 255, 255))
        help_menu.add.image("Sprites/runner.png")
        help_menu.add.label("These mad guys run like headless chickens.\nThey got low health and attack damage but high speed.\nKill 'em quick.\n", 
                            font_size = 25,font_color = (255, 255, 255))


        help_menu.add.label("BRUTES",font_name = 'Times New Roman',font_size = 25,font_color = (255, 255, 255))
        help_menu.add.image("Sprites/brute.png")
        help_menu.add.label("Don't mess with these big boys.\nThey got high health and attack damage but walk slower than my nan.\nTry not to be within close range of them.\n", 
                            font_size = 25,font_color = (255, 255, 255))


        help_menu.add.label("DYNAMIC TIMER",font_name = 'Georgia', font_size = 25, font_color = (255, 204, 0))
        help_menu.add.label("Each wave consists of a countdown. Complete the wave before the timer runs out to survive.\nMore time is allocated as the waves become more challenging\nBut be warned,the stronger you perform, the shorter it also gets\n", 
                            font_size = 25,font_color = (255, 255, 255))

        help_menu.add.label("TORCHLIGHT FIELD OF VIEW",font_name = 'Georgia', font_size = 25, font_color = (255, 204, 0))
        help_menu.add.label("Your torch is your lifeline in the darkness.\nIt illuminates your surroundings, letting you spot zombies and navigate safely\nMaintain your torchlight battery else your vision gets reduced.\nIf vision gets too low, your heart rate will escalate.\nScavenge for batteries to maintain your field of view, or risk being swallowed by the shadows.\n", 
                            font_size = 25,font_color = (255, 255, 255))

        help_menu.add.label("THE SHOP: DEAD MAN DEALS",font_name = 'Georgia', font_size = 25, font_color = (255, 204, 0))
        help_menu.add.label("In DEAD PULSE, survival comes at a price.\nTo access the shop, pause the game (press ESC)\nThe shop uses a real-time Bitcoin API, meaning item prices fluctuate dynamically just like in a real economy.\nOne moment, an item might be affordable, the next, it could cost a fortune\nKeep an eye on the market and buy strategically—waiting too long could leave you under-equipped when the undead close in.\n", 
                            font_size = 25,font_color = (255, 255, 255))
        
        help_menu.add.label("OBJECTIVES", font_name = 'Georgia', font_size = 25, font_color = (255, 204, 0))
        help_menu.add.label("1.Kill zombies to earn Rotten Flesh\n2.Manage Your Heart Rate to avoid zombies hunting you down\n3.Upgrade player stats to become stronger\n", 
                            font_size = 25,font_color = (255, 255, 255))

        help_menu.add.label("CONTROLS", font_name = 'Georgia', font_size = 25, font_color = (255, 204, 0))
        help_menu.add.label(f"Move Up: W\nMove Left : A\nMove Down : S\nMove Right: D\nShoot: Space\nSprint: Left Shift\nTurn: Use Mouse\nPause: ESC\n", 
                            font_size = 25,font_color = (255, 255, 255))

        help_menu.add.label("TIPS FOR SURVIVAL", font_name = 'Georgia', font_size = 25, font_color = (255, 204, 0))
        help_menu.add.label(f"Pace Yourself: Sprinting = panic = higher heart rate.\nBe Accurate: Conserve ammo—every bullet counts.\nVisit the shop often: Permanent upgrades are key to pushing your high score.\n WARNING: This game is designed to stress you out. Can you keep your cool when the horde closes in?\n", 
                            font_size = 25,font_color = (255, 255, 255))

        help_menu.add.label("Ali Kamaly",font_size = 75,font_color=(255, 204, 0), font_name="Fonts/Bastliga One.ttf")

        help_menu.mainloop(self.screen)


    def is_wave_complete(self):
        return self.state == "wave complete"
        #if self.state is "wave complete" then it returns True else False

    def next_wave(self):
        self.wave_number+=1
        #rotten flesh wave bonus
        self.stats_manager.increment_stat("Rotten Flesh", (self.wave_number-1) * constants.WAVE_COMPLETION_REWARD)
        #print(f"WAVE BONUS: +{(self.wave_number-1) * constants.WAVE_COMPLETION_REWARD} Rotten Flesh")
        self.stats_manager.save_stats()

        self.state = "playing"
        self.change_map()

        self.audio_manager.play_sound_effect("new wave", 2)
        #sound effect will only play 1 in every 2 new waves

        self.audio_manager.stop_sound_effect("low time")
        self.audio_manager.stop_sound_effect("last 10 secs")

    def change_map(self):
        maps = self.map_manager.maps
        #self.current_map = "basement"
        self.current_map = random.choice(maps)
        #print(self.current_map)

    def start_wave(self):
        #resetting time begin, bullets fired etc.
        #self.wave_start_time = pygame.time.get_ticks()
        self.state = "playing"
        self.bullets_fired = 0
        self.bullets_hit = 0
        self.total_health_lost = 0
        self.rotten_flesh = 0
        self.zombies_killed = 0
        self.player_health_start = self.player.health_bar.get_health()
 
    
    def calculate_wave_performance(self):
        """Calculates player's previous wave performance which is then used to dictate: the difficulty of the next wave,
        the strength increment of the zombies as well as the time allocated for the next wave - the game adapts its difficulty
        depending on how well the user performs making the game more challenging, interesting and appealing to the users"""

        wave_end_time = pygame.time.get_ticks()
        time_taken = (wave_end_time - self.timer.start_time)/1000
        #converting milliseconds to seconds

        #normalising time factor to be in the range [0.0, 1.0]
        try:
            time_factor = max(0, 1.0 - time_taken/self.wave_target_time)
        except ZeroDivisionError:
            time_factor = 0
        #0 = very slow, 1.0 = very fast


        #calculates bullet accuracy (value between 0.0 and 1.0)
        try:
            accuracy = self.bullets_hit / self.bullets_fired
            #0 = very inaccurate, 1 = very accurate
        except ZeroDivisionError:
            accuracy = 0
        #accuracy_factor = accuracy

        #converting total health lost to a scale from 0.0 to 1.0


        health_lost_factor = max(0, 1- (self.total_health_lost/100))
        #player didn't lose any health
        #if plaer lost more than 100 hp over the course of the wave, health_lost_factor = 0
        #i.e. player struggled, health_lost_factor = 1 -> player didn't struggle (didn't
        #lost a lot of health)

        #calculating overall wave performance, adding weights to make some factors
        #more crucial to the performance_score calculations

        self.wave_score = 1.0 + (time_factor*constants.TIME_WEIGHT) + (accuracy*constants.ACCURACY_WEIGHT) +(health_lost_factor * constants.HEALTH_LOST_WEIGHT)
        #base performance_score = 1.0 so difficulty will never decrease
        #added weights to make some factors (i.e. speed of wave completion) more important
        #than other factors
    
        #capping performance score to be under 2 (but >= 1.0)
        self.wave_performance = min(2.0, self.wave_score)


        #storing player's wave performance in dictionary
        #can then be displayed/accessed when game is over

        """
        every wave performance is stored in a dictionary associated with the player
        this data is then shared with the player after the player dies in the game over menu
        where they can see how well they've performed
        """
        self.overall_player_performance[f"Wave {self.wave_number}"]= {
            "Time Taken": time_taken, 
            "Zombies Killed": self.zombies_killed,
            "Accuracy": round(accuracy*100),
            "Score": int(self.wave_performance*1000)}





    """Delegating map-related functionality to the MapManager class.
    These forwarding methods allow GameState to maintain control of game flow
    while abstracting the complexity of map data handling. Instead of directly
    accessing or modifying map structures within GameState, these methods cleanly
    delegate responsibilities to MapManager, which specialises in map-related data
    """
    def get_map_dimensions(self):
        return self.map_manager.get_map_dimensions(self.current_map)

    def get_map_walls(self):
        return self.map_manager.get_map_walls(self.current_map)
    
    def get_map_rooms(self):
        return self.map_manager.get_map_rooms(self.current_map)
    
    def get_map_boundaries(self):
        return self.map_manager.get_map_boundaries(self.current_map)


    def reset_level_for_next_wave(self):
        """Prepares all game systems for a new wave, called when a wave has finished - changes whole map"""
        
        #removing objects stored in lists before reassigning

        self.zombies.zombie_list.empty()
        self.bullets.items_list.empty()
        self.medkits.items_list.empty()
        self.batteries.items_list.empty()
        self.wall_manager.walls_list.empty()


        
        #getting new map data
        map_width, map_height = self.get_map_dimensions()
        map_walls = self.get_map_walls()

        #creating new instances that have the same variable name
        self.wall_manager = WallManager(map_walls)
        self.wall_manager.load_walls()

        self.map_manager.create_walkable_nodes(self.current_map)

        #changing background
        self.background = Background(self.current_map)

        #resetting camera and minimap
        self.camera = Camera(map_width, map_height)
        self.player_view = self.camera.transform_background(self.background.image)
        self.minimap = Minimap(map_width, map_height, self.current_map)

        #redrawing zombies & calculating number of zombies to spawn for next wave
        #depending on player performance


        difficulty_multiplier = self.wave_performance
        total_zombies = round(self.wave_number * constants.ZOMBIE_COUNT_MULTIPLIER * difficulty_multiplier)
        print(f"Total Zombies Next Wave: wave num{self.wave_number} * base num{constants.ZOMBIE_COUNT_MULTIPLIER} * player performance: {difficulty_multiplier} = {total_zombies}")

        #total_zombies will always increase by at least 5 for every new wave
        #total_zombies will increase depending on player performance

        """ratio of walkers, runners and brutes will adjust as player progresses through more waves
        As player progresses, runners and brutes will become more common and walkers will be less common"""

        walker_ratio = max(constants.DEFAULT_WALKER_RATIO -(self.wave_number*0.01), constants.MIN_WALKER_RATIO)
        """walker_ratio will never be less than 10%
        walker ratio will decrease by 5% every wave
        """

        runner_ratio = min(constants.DEFAULT_RUNNER_RATIO+ (self.wave_number*0.01),constants.MAX_RUNNER_RATIO)
        """runner_ratio will never be more than 40%, increases ratio of runner by 5% every wave"""

        brute_ratio = min(constants.DEFAULT_BRUTE_RATIO + (self.wave_number*0.01),constants.MAX_BRUTE_RATIO)
        """brute_ratio will never be more than 50%"""
 
        total_ratio = walker_ratio + runner_ratio + brute_ratio
        walker_ratio /= total_ratio
        runner_ratio /= total_ratio
        brute_ratio /= total_ratio

        print(f"SO: walker ratio: {walker_ratio}, Runner ratio: {runner_ratio}, Brute ratio: {brute_ratio}")

        self.zombies = ZombieSpawner(map_width, map_height, self.map_manager)

        self.walker_count = int(walker_ratio * total_zombies)
        self.runner_count = int(runner_ratio * total_zombies)
        self.brute_count = int(brute_ratio * total_zombies)
        print(f"Walkers: {self.walker_count}, Runners: {self.runner_count}, Brutes: {self.brute_count}")

        #increasing zombies' health and attack damage - depending on player performance
        self.increase_zombie_health(difficulty_multiplier)
        self.increase_zombie_attack(difficulty_multiplier)

        self.zombies.spawn_walkers(self.walker_count, self.current_map, self.map_manager,self)
        self.zombies.spawn_runners(self.runner_count,self.current_map, self.map_manager,self)
        self.zombies.spawn_brutes(self.brute_count,self.current_map, self.map_manager,self)
        
        #calculating time allocation for next wave
        time_allocated = int((self.base_time + self.walker_count*10 + self.runner_count*15 + self.brute_count*20)/max(1.1,difficulty_multiplier/1.5))
        #the better a player performs the shorter time allocated (time is reduced if player_performance >1.5)

        #resetting timer duration:
        self.timer.reset(time_allocated)
        self.wave_target_time = time_allocated

        #calculating how many batteries, bullets and medkits to spawn next wave
        self.battery_spawn_count = time_allocated//3
        self.bullet_spawn_count = int(self.walker_count * 8 + self.runner_count *10 + self.brute_count*12)
        self.medkit_spawn_count = int(self.walker_count * 1 + self.runner_count * 2 + self.brute_count * 3)


        #redrawing pickable items
        self.bullets = BulletSpawner(map_width, map_height)
        self.bullets.spawn(self.bullet_spawn_count)

        self.medkits = MedkitSpawner(map_width, map_height)
        self.medkits.spawn(self.medkit_spawn_count)

        self.batteries = BatterySpawner(map_width, map_height)
        self.batteries.spawn(self.battery_spawn_count)

        #respawn player at the centre of the map
        self.player.global_rect.x, self.player.global_rect.y = map_width/2 * constants.CAMERA_ZOOM, map_height/2 * constants.CAMERA_ZOOM


    def increase_zombie_health(self, player_performance):
        """Increases zombie health - depending on player wave performance"""
        if player_performance>=1.5:
            increment = 0.1
        elif player_performance>=1.25:
            increment = 0.075
        else:
            increment = 0.05
        self.zombie_health_multiplier += increment
        print(f"ZOMBIE HEALTH MULTIPLIER: {self.zombie_health_multiplier}")
    
    def increase_zombie_attack(self, player_performance):
        """Increases zombie attack damage - depending on player wave performance"""
        if player_performance>=1.75:
            increment = 0.25
        elif player_performance>=1.3:
            increment = 0.2
        else:
            increment = 0.15
        self.zombie_attack_multiplier += increment
        print(f"ZOMBIE ATTACK MULTIPLIER: {self.zombie_attack_multiplier}")
    
    def reset_game(self, player_died = False):
        """Resets all game data i.e. zombie_list etc."""
        self.zombies.zombie_list.empty()
        self.bullets.items_list.empty()
        self.medkits.items_list.empty()
        self.batteries.items_list.empty()
        self.wall_manager.walls_list.empty()

        self.game_over = False

        #resetting player-related info
        self.player.ammo = 10
        self.player.heart.current_heart_rate = 80
        self.entered_username = ""

        self.overall_player_performance = {}

        #resetting settings
        self.current_music_volume= constants.DEFAULT_MUSIC_VOLUME
        self.current_sound_effects_volume = constants.DEFAULT_SOUND_EFFECTS_VOLUME

        #resetting saved game data only if player died (prevents them to outcheat death)
        if player_died:
            self.stats_manager.delete_previous_game_save()
        #resetting strength of zombies
        self.zombie_attack_multiplier = 1
        self.zombie_health_multiplier = 1
        self.zombies_killed = 0

        #getting new map data
        map_width, map_height = self.get_map_dimensions()
        map_walls = self.get_map_walls()

        #creating new instances that have the same variable name
        self.wall_manager = WallManager(map_walls)
        self.wall_manager.load_walls()

        #basement is default first map
        self.current_map = "basement"

        #changing background
        self.background = Background(self.current_map)

        #resetting camera and minimap
        self.camera = Camera(map_width, map_height)
        self.minimap = Minimap(map_width, map_height, self.current_map)

        #resetting field of view (battery starts at max)
        self.field_of_view = FieldOfView()

        self.zombies = ZombieSpawner(map_width, map_height, self.map_manager)

        #there will always only be 1 zombie on wave 1
        self.zombies.spawn_walkers(1, self.current_map, self.map_manager, self)

        #resetting bullet, medkit and batteries spawn count
        self.battery_spawn_count = constants.DEFAULT_BATTERY_SPAWN_COUNT
        self.bullet_spawn_count = constants.DEFAULT_BULLET_SPAWN_COUNT
        self.medkit_spawn_count = constants.DEFAULT_MEDKIT_SPAWN_COUNT

        self.batteries = BatterySpawner(map_width, map_height)
        self.batteries.spawn(self.battery_spawn_count)

        self.bullets = BulletSpawner(map_width, map_height)
        self.bullets.spawn(self.bullet_spawn_count)

        self.medkits = MedkitSpawner(map_width, map_height)
        self.medkits.spawn(self.medkit_spawn_count)


        #respawn player at the centre of the map
        self.player.global_rect.x, self.player.global_rect.y = map_width/2 * constants.CAMERA_ZOOM, map_height/2 * constants.CAMERA_ZOOM

        self.wave_number = 1
        #return wall_manager, background, camera, player_view, minimap, zombies, bullets, medkits, batteries



def adjust_game_objects_coords(game_state,offset_x, offset_y):
    """Initially used OOP but it lead to significant drop in performance, which, I believe, was due to high usage of .self in loops
    To improve efficiency, I strategically reverted to a procedural design for this subroutine. By centralising the coordinate
    adjustments and rendering logic in one place, I reduced overhead and improved cache locality, resulting in significantly
    smoother gameplay.

    I only sacrificed OOP locally - the overall architecture remains clean and object-oriented, and I kept the modularity
    of the code
    """
    
    for wall in game_state.wall_manager.walls_list:            
        wall.adjust_coords(offset_x, offset_y)
        game_state.wall_surface.blit(wall.enlarged_image,(wall.rect.x,wall.rect.y))
    game_state.screen.blit(game_state.player_view,(-offset_x, -offset_y)) 
    #lets walls be seen

    for bullet in game_state.bullets.items_list:
        bullet.adjust_coords(offset_x, offset_y)
        game_state.item_surface.blit(bullet.image,(bullet.rect.x,bullet.rect.y))

    for medkit in game_state.medkits.items_list:
        medkit.adjust_coords(offset_x, offset_y)
        game_state.item_surface.blit(medkit.image,(medkit.rect.x,medkit.rect.y))

    for battery in game_state.batteries.items_list:
        battery.adjust_coords(offset_x, offset_y)
        game_state.item_surface.blit(battery.image,(battery.rect.x,battery.rect.y))

    for zombie in game_state.zombies.zombie_list:
        zombie.adjust_coords(offset_x, offset_y)
        zombie.health_bar.draw(game_state.screen,(zombie.rect.x,zombie.rect.y-20))

        #draws health_bar of each zombie above zombie
        game_state.zombie_surface.blit(zombie.image,(zombie.rect.x,zombie.rect.y))

    for projectile in game_state.player.projectiles.items_list:
        #print("displaying projectile")
        projectile.travel()

        projectile.adjust_coords(offset_x, offset_y)
        #print(projectile.rect.x, projectile.rect.y)
        game_state.projectile_surface.blit(projectile.image,(projectile.rect.x,projectile.rect.y))

def main():

    pygame.init()
    screen = Screen()
    map_manager = MapManager()
    game_state = GameState(map_manager,screen.display)

    game_state.display_main_menu()

    screen_centre_x, screen_centre_y = screen.get_centre()
    """this is the player's local coordinate AT ALL TIMES in the game
    since the player will always be in the centre of the camera, the local coordinate will always be the same"""

    clock = pygame.time.Clock()

    game_state.create_hud()
    game_state.create_messages()

    BATTERY_DRAIN_EFFECT = pygame.USEREVENT + 1
    pygame.time.set_timer(BATTERY_DRAIN_EFFECT, 100)


    current_map = game_state.current_map  
    previous_shake_intensity = 0

    while True:

        if game_state.state == "main menu":
            game_state.reset_game()


        game_state.update(game_state.zombies.zombie_list)

        #changes wave if wave is complete:
        if game_state.is_wave_complete():

            game_state.calculate_wave_performance()
            game_state.update_player_stats()
            game_state.load_next_wave()

            game_state.minimap.display_zombies = False
        
        game_state.update(game_state.zombies.zombie_list)
        game_state.should_display_zombies_on_minimap()

        if game_state.current_map != current_map:  
            # Only update if the map changes
            current_map = game_state.current_map

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == MOUSEMOTION:
                mouse_pos_x, mouse_pos_y = pygame.mouse.get_pos()
                direction_vector = game_state.player.calculate_direction_vector(mouse_pos_x, mouse_pos_y)

                angle = game_state.player.calculate_rotation(direction_vector[0], direction_vector[1])
                game_state.player.rotate(angle)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state.toggle_pause()
        
            if event.type == BATTERY_DRAIN_EFFECT:
                game_state.field_of_view.decrease_view()
                
        if game_state.game_over:
            game_state.display_game_over()

        if game_state.paused:
            continue
            #skips whole iteration of loop if the game is paused
            #this stops game from updating and puts everythinPlayeg on hold
            

        movement_x , movement_y = game_state.player.calculate_movement(game_state)
        #gives general relative movement of player & camera
        game_state.player.update_global_coords(movement_x, movement_y)
        #updating player global coords taking into consideration the zoom

        offset_x, offset_y = game_state.camera.calculate_offset(game_state.player)
        offset_x, offset_y, previous_shake_intensity = game_state.camera.apply_screen_shake(game_state.player,offset_x, offset_y, previous_shake_intensity)

        screen.display.fill((0,0,0))

        adjust_game_objects_coords(game_state, offset_x, offset_y)
        
        clock.tick(60)

        game_state.handle_collisions(movement_x, movement_y)

        game_state.player.update_heart_rate(movement_x, movement_y, game_state.field_of_view.get_radius(), game_state)

        """removing zombies that have no health left reducing the zombie count, relative to its zombie type"""
        game_state.handle_dead_zombies()
              
        game_state.player_list.update()
        screen.display.blit(game_state.player.image, (screen_centre_x - game_state.player.rect.width/2, screen_centre_y-game_state.player.rect.height/2))

        """not using the sprite class to draw so can specify where to draw the player
        player will always be drawn at the centre of screen despite its global variable changing
        depending on player input"""
        
        game_state.field_of_view.draw_mask(screen)

        game_state.player.health_bar.draw(screen.display, (constants.SCREEN_WIDTH/2 - 50, constants.SCREEN_HEIGHT/2 - 70))

        game_state.timer.draw(screen.display, game_state=game_state)
        game_state.timer.update(game_state)

        game_state.update_hud_info()
        game_state.draw_hud()

        game_state.display_messages()

        """DRAWS RECTS OF PLAYER, WALLS, BULLETS, MEDKITS, BATTERIES, ZOMBIES & PROJECTILES
            FOR TESTING & DEBUGGING"""
        
        """pygame.draw.rect(screen.display, (0, 255, 0), game_state.player.rect, 2)
        for wall in game_state.wall_manager.walls_list:
            pygame.draw.rect(screen.display, (0, 0, 255), wall.rect, 2)
        for bullet in game_state.bullets.items_list:
            pygame.draw.rect(screen.display, (255, 0, 0), bullet.rect, 2)
        for medkit in game_state.medkits.items_list:
            pygame.draw.rect(screen.display, (255, 255, 0), medkit.rect, 2)
        for battery in game_state.batteries.items_list:
            pygame.draw.rect(screen.display, (255, 255, 255), battery.rect, 2)
        for zombie in game_state.zombies.zombie_list:
            pygame.draw.rect(screen.display, (255, 0, 255), zombie.rect, 2)
        for projectile in game_state.player.projectiles.items_list:
            pygame.draw.rect(screen.display, (255,255,255), projectile.rect, 2)"""
        #map_manager.draw_grid(screen.display, offset_x, offset_y)

        pygame.display.flip()

if __name__ == "__main__":
    main()