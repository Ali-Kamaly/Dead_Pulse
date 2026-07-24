#Ali Kamaly | DEAD PULSE
#ui-related classes

import pygame, constants, random

class HealthBar(pygame.sprite.Sprite):

    """
    Polymorphic design allows healthbar to be used for both the player and every instance
    of a zombie

    Audio is outputted if health remaining reaches certain percentages, using randomised selection
    of audio messages to prevent repetition of the same messages  
    """

    #used for both player and zombies
    def __init__(self,max_health=100, width=100,height = 20):
        super(HealthBar,self).__init__()
        self.max_health = max_health
        self.current_health = self.max_health
        self.width = width
        self.height = height
        self.box = pygame.Surface((self.width,self.height))
        self.rect = self.box.get_rect()

    def draw(self, surface, coords=(10,10)):
        self.ratio = self.current_health/self.max_health
        #calculates portion of the box that should be green (will always be <1)
        self.box.fill((255,0,0))
        self.box.fill((0,255,0),(0,0,self.ratio*self.width,self.height))
        surface.blit(self.box,coords)

    def get_health(self):
        return self.current_health

    def take_damage(self, damage = 5, game_state = None):
        self.current_health = max(self.current_health - damage, 0)

        if game_state:
            if self.current_health<=self.max_health/4 and not game_state.player.low_health_sound_played:
                chosen_sound = random.choice(["scared low health", "cheeky low health 1", "cheeky low health 2"])
                game_state.audio_manager.play_sound_effect(chosen_sound)
                #randomly plays 3 variants of the same message to prevent over-use
                game_state.player.low_health_sound_played = True
            
            elif self.current_health>self.max_health/4:
                game_state.player.low_health_sound_played = False

    def recover_health(self, increment = constants.DEFAULT_HEALTH_RECOVERY):
        self.current_health = min(self.current_health + increment, self.max_health)

    def set_max_health(self, max_health):
        self.max_health = max_health
        self.current_health = self.max_health
        #player will always start at max_health

class FieldOfView():
    def __init__(self):
        self.radius = constants.DEFAULT_RADIUS
        self.max_radius = constants.MAXIMUM_RADIUS
        self.battery_level = constants.DEFAULT_BATTERY_LEVEL
        #the greater the level of battery the greater the radius of fov

    def draw_mask(self, screen):
        mask = pygame.Surface((constants.SCREEN_WIDTH,constants.SCREEN_HEIGHT),pygame.SRCALPHA)
        #SRCALPHA allows transparency
        mask.fill((0,0,0,constants.TRANSPARENCY))
        #255 = no transparancy - everything outside the circle is completely black

        pygame.draw.circle(mask,(0,0,0,0),(constants.SCREEN_WIDTH//2,constants.SCREEN_HEIGHT//2),self.radius)
        screen.display.blit(mask, (0,0))

    def decrease_view(self):
        self.radius = max(self.radius -0.75, 100)

    def increase_view(self):
        self.radius = min(self.radius + constants.INCREASE_VIEW_VALUE,self.max_radius)

    def get_radius(self):
        return self.radius

class Timer():
    def __init__(self, duration):
        self.duration = duration
        #in seconds
        self.time_left = duration

        self.counting = False
        self.start_time = 0

        self.width = constants.SCREEN_WIDTH/2
        self.height = 25
        self.box = pygame.Surface((self.width, self.height))
        self.rect = self.box.get_rect()

        self.last_time_updated = 0
        self.low_time_audio_played = False
        self.playing_audio_countdown = False

    def start(self):
        self.start_time = pygame.time.get_ticks()
        self.last_time_updated = self.start_time
        self.counting = True

    def reset(self, duration = None):
        """Reset the timer - can optionally change the duration"""
        if duration:
            self.duration = duration
        self.time_left = self.duration
        self.start()


    def is_finished(self):
        return self.time_left == 0
    
    def draw(self, surface, game_state):
        #if self.counting:
        self.ratio = max(0, (self.time_left/self.duration))
        back_colour = (50,50,50)

        #front colour adjusts depending on % of time left
        if self.ratio <= 0.33:
            front_colour = (211,47,47)
            if not self.low_time_audio_played:
                game_state.audio_manager.play_sound_effect("low time")
                self.low_time_audio_played = True
        elif self.ratio <=0.66:
            front_colour = (255,179,0)
            self.low_time_audio_played = False
        else:
            front_colour = (76,175,80)
            self.low_time_audio_played = False


        self.box.fill(back_colour)
        self.box.fill(front_colour,(0,0,self.ratio*self.width, self.height))
        surface.blit(self.box, (constants.SCREEN_WIDTH/4, 20))
        #print("drawing")

    def update(self, game_state):
        if self.counting:
            current_time = pygame.time.get_ticks()
            time_passed = (current_time-self.last_time_updated)/1000
            #converting to seconds
            self.time_left = max(0,self.time_left - time_passed)
            self.last_time_updated = current_time

            if self.time_left <=10 and not self.playing_audio_countdown:
                game_state.audio_manager.play_sound_effect("last 10 secs")
                self.playing_audio_countdown = True

            if self.time_left == 0:
                #timer has finished
                self.counting = False
                game_state.audio_manager.stop_sound_effect("last 10 secs")
                self.playing_audio_countdown = False

class Text():
    def __init__(self, font, font_size, x,y, colour):
        self.font_size = font_size
        self.colour = colour
        self.x = x
        self.y = y

        self.font_info =pygame.font.SysFont(font, font_size)

    def update_content(self, content):
        self.content = content

    def draw(self,screen):
        font_surf = self.font_info.render(self.content, True, self.colour)
        screen.blit(font_surf, (self.x,self.y))
