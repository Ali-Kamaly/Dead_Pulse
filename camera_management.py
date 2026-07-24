#Ali Kamaly | DEAD PULSE
#Camera-related Classes

import pygame, constants, random

class Background(pygame.sprite.Sprite):
    def __init__ (self, background):
        super(Background,self).__init__()
        self.image = pygame.image.load(f"Maps/{background}.png")
        self.rect = self.image.get_rect()

class Screen(pygame.sprite.Sprite):
    def __init__(self):
        super(Screen,self).__init__()
        self.size = (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)
        self.display = pygame.display.set_mode(self.size)        
        pygame.display.set_caption('DEAD PULSE')

    def get_centre(self):
        return(constants.SCREEN_WIDTH//2, constants.SCREEN_HEIGHT//2)

class Camera():
    def __init__ (self, map_width, map_height):
        self.dx = 0
        self.dy = 0
        self.dx_total = 0
        self.dy_total = 0
        self.map_width = map_width
        self.map_height = map_height
        self.default_image_size = (self.map_width*constants.CAMERA_ZOOM, self.map_height*constants.CAMERA_ZOOM)

    def transform_background(self, original_background):
        return pygame.transform.scale(original_background, self.default_image_size)
    
    def calculate_offset(self, player):
        #encapsulates data about camera in camera class rather than having to use directly player class
        offset_x, offset_y = player.global_rect.x - constants.SCREEN_WIDTH/2, player.global_rect.y - constants.SCREEN_HEIGHT/2
        #offset is completely independant of map size - so movement should be consistent no matter map size
        #player is always at center of screen

        return offset_x, offset_y

    def apply_screen_shake(self, player, camera_offset_x, camera_offset_y, previous_shake_intensity):
        """Uses the player's heart rate to dynamically calculate screen shake intensity, adding 
        a psychological gameplay effect that reflects the player's stress level. The intensity fades over time, 
        which demonstrates my awareness of UX principles"""
        if player.heart.current_heart_rate> player.heart.hunting_heart_rate_threshold:
            shake_intensity = (player.heart.current_heart_rate - player.heart.hunting_heart_rate_threshold)/10
        else:
            shake_intensity = abs(previous_shake_intensity*0.9)
            #gradually fading shake intensity out for smoother experience
            #need to reset shake_intensity for when playing again or signing out 

        shake_x = random.uniform(-shake_intensity, shake_intensity)
        shake_y = random.uniform(-shake_intensity, shake_intensity)

        return int(shake_x + camera_offset_x), int(shake_y + camera_offset_y), shake_intensity

