#Ali Kamaly | DEAD PULSE
#Pickable-items-related Classes

import pygame, constants

"""
Utilising inheritance to avoid redundancy by centralising shared functionality 
(e.g., image loading, positioning, and coordinate adjustment) in the base class

By using inheritance, each item class focuses only on its unique properties (e.g. image paths)
while inheriting common behavior from 'PickableItem'. This modular approach helps the code to remain
concise and easy to maintain, which is a key aspect of a well-structured, scalable software
"""

class PickableItem(pygame.sprite.Sprite):
    def __init__(self,x,y,image):
        super(PickableItem,self).__init__()
        self.original_x = x
        self.original_y = y
        self.image = pygame.image.load(image)
        self.rect = self.image.get_rect(center=(x,y))

    def adjust_coords(self, offset_x, offset_y):
        self.rect.x = self.original_x * constants.CAMERA_ZOOM - offset_x
        self.rect.y = self.original_y * constants.CAMERA_ZOOM - offset_y


class Bullets(PickableItem):
    def __init__(self,x,y):
        super().__init__(x,y,"Sprites/bullet.png")
    
    def get_coords(self):
        return (self.rect.x, self.rect.y)

class Medkit(PickableItem):
    def __init__(self,x,y):
        super().__init__(x,y,"Sprites/medkit.png")
    
    def get_coords(self):
        return (self.rect.x, self.rect.y)

class Battery(PickableItem):
    def __init__(self,x,y):
        super().__init__(x,y,"Sprites/battery.png")
    
    def get_coords(self):
        return (self.rect.x, self.rect.y)

