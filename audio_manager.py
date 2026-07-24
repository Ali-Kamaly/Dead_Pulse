#Ali Kamaly | DEAD PULSE
#Audio Manager Class

import pygame, constants, random
#importing only necessary modules/files

class AudioManager():
    """Manages all sounds: music tracks & sound effects - encapsulates all sound responsibilities
    Promotes modular design and improves code maintainability"""
    def __init__(self):
        pygame.mixer.init()
        self.music_tracks = {
            "main menu": "Audio/main menu track.ogg",
            "wave": "Audio/wave track.ogg",
            "shop": "Audio/shop track.ogg",
            "paused": "Audio/paused track.ogg"
        }
        #Use of .ogg format ensures seamless looping (efficient for game music)


        self.sound_effects = {
            "shooting": pygame.mixer.Sound("Audio/gunshot.mp3"),
            "zombie near": pygame.mixer.Sound("Audio/errrm did u guys hear that.wav"), 
            "new wave": pygame.mixer.Sound("Audio/how many more do I have to kill.wav"),
            "low vision": pygame.mixer.Sound("Audio/I can't see.wav"),
            "low time": pygame.mixer.Sound("Audio/hurry we don't have enough time.wav"),
            "last 10 secs": pygame.mixer.Sound("Audio/last 10 secs clock.wav"),
            "scared low health": pygame.mixer.Sound("Audio/is this it (low health).wav"),
            "cheeky low health 1": pygame.mixer.Sound("Audio/ooh that's gonna hurt in the morning 1.wav"),
            "cheeky low health 2": pygame.mixer.Sound("Audio/ooh that's gonna hurt in the morning 2.wav"),
            "killed zombie": pygame.mixer.Sound("Audio/haha didn't like him anyways.wav")
        }
        """Sound effects stored in a dictionary allow for intuitive access and easy scalability
        this reflects a high-level programming approach called data-driven design, which improves 
        maintainability and supports future features such as player-drive audio customisation"""

        self.current_music = None

        #default sound settings
        self.music_volume = constants.DEFAULT_MUSIC_VOLUME
        self.sound_effect_volume = constants.DEFAULT_SOUND_EFFECTS_VOLUME


    def play_music(self, track_name):
        if self.current_music == track_name:
            return
        
        if track_name in self.music_tracks:
            pygame.mixer.music.load(self.music_tracks[track_name])
            pygame.mixer.music.play(-1)
            #loops indefinitely
            self.current_music = track_name
    
    def play_sound_effect(self, sound, chance = 1):
        """Adds randomness to prevent repetition of certain SFX (e.g. dialogue).
        Makes audio feel dynamic and more realistic"""
        random_num = random.randint(1,chance)
        if random_num == 1:
            #some sound effects won't play even if an external condition
            #i.e. new wave has been met (to prevent over repeated sounds)
            if sound in self.sound_effects:
                self.sound_effects[sound].play()

    def stop_sound_effect(self, sound=None):
        """
        Stops individual sound or all currently playing SFX.
        Increases control and avoids overlapping chaotic audio
        """
        if sound:
            if sound in self.sound_effects:
                self.sound_effects[sound].stop()
        else:
            #if no argument is given, stop all sound effects that are being played
            for sound in self.sound_effects.values():
                sound.stop()

    def set_music_volume(self, volume):
        """
        Allows dynamic control of volume via settings menu
        Conversion from 0-100 to 0.0-1.0 required by pygame
        """
        if self.music_volume != volume:
            pygame.mixer.music.set_volume(volume/100)
            self.music_volume = volume
            #pygame volume is between 0.0 and 1.0

    def set_sound_effect_volume(self, volume):
        """Updates volume for all SFX at once"""

        if self.sound_effect_volume != volume:
            for sound_effect in self.sound_effects.values():
                sound_effect.set_volume(volume/100)
                #pygame volume is between 0.0 and 1.0
            self.sound_effect_volume = volume
    

    def get_music_volume(self):
        """Returns music volume in user-friendly 0-100 scale."""
        return pygame.mixer.music.get_volume()*100
