#Ali Kamaly | DEAD PULSE
#Constants

"""
Centralises all game-wide constants, making the game more scalable, 
and easily configurable. By storing key values such as default base time and camera zoom
in a single file, changes can be made easily without modifying multiple files
(thanks to the encapsulation of key values). This improves code organisation and reduces 
the risk of hardcoded values being scattered across the project. Also, using 
constants enhances readability, prevents accidental modifications, and ensures 
consistency throughout the program (ensures all parts of the game reference the same values)
"""



#SCREEN SETTINGS
"""
The game's UI is designed to be robust and scalable, ensuring that increasing
or decreasing SCREEN_WIDTH and SCREEN_HEIGHT does not break the visual layout
or core functionality of the program. UI elements dynamically adjust their positions relative
to the screen size, maintaining a consistent and visually appealing experience
across different screen sizes
i.e. the game adapts to different screen sizes without requiring manual UI adjustments
"""
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 1000
SCREEN_CENTER_X = SCREEN_WIDTH / 2
SCREEN_CENTER_Y = SCREEN_HEIGHT / 2


#PLAYER SETTINGS
PLAYER_WIDTH = 120
PLAYER_HEIGHT = 71
DEFAULT_CURRENT_HEALTH = 100
SPEED = 15
RUN_SPEED = SPEED * 2
PLAYER_STARTING_AMMO = 30
AMMO_PICKUP = 10


#HEART RATE MECHANICS
RESTING_HEART_RATE = 80
CURRENT_DEFAULT_HEART_RATE = 80
MAXIMUM_HEART_RATE = 250
HUNTING_HEART_RATE_THRESHOLD = 180

IDLE_HEART_RATE_DECREASE = 5
WALK_HEART_RATE_DECREASE = 1
GETTING_ATTACKED_HEART_RATE_INCREASE_RANGE = (1, 3)


#ZOMBIE SETTINGS
ZOMBIE_WIDTH = 190
ZOMBIE_HEIGHT = 171

DEFAULT_WALKER_COUNT = 1
DEFAULT_RUNNER_COUNT = 0
DEFAULT_BRUTE_COUNT = 0
ZOMBIE_COUNT_THRESHOLD = 100000 # change back to 3

DEFAULT_WALKER_RATIO = 0.7
DEFAULT_RUNNER_RATIO = 0.2
DEFAULT_BRUTE_RATIO = 0.1

MIN_WALKER_RATIO = 0.1
MAX_RUNNER_RATIO = 0.4
MAX_BRUTE_RATIO = 0.5


#FIELD OF VIEW
TRANSPARENCY = 255
DEFAULT_RADIUS = 500
MAXIMUM_RADIUS = 500
DEFAULT_BATTERY_LEVEL = 100
INCREASE_VIEW_VALUE = 200
GOOD_VISIBILITY_THRESHOLD = 150  


#AUDIO SETTINGS
DEFAULT_MUSIC_VOLUME = 100
DEFAULT_SOUND_EFFECTS_VOLUME = 100


#TIMER SETTINGS
DEFAULT_BASE_TIME = 50


#CAMERA SETTINGS
CAMERA_ZOOM = 10
MINIMAP_ZOOM = 0.2


#PLAYER TRACKER
PLAYER_TRACKER_WIDTH = 20
PLAYER_TRACKER_HEIGHT = 20


#ITEM SPAWN SETTINGS
DEFAULT_BATTERY_SPAWN_COUNT = 25
DEFAULT_BULLET_SPAWN_COUNT = 25
DEFAULT_MEDKIT_SPAWN_COUNT = 15


#HEALTH BAR SETTINGS
DEFAULT_HEALTH_RECOVERY = 50
BOUGHT_IMMEDIATE_HEALTH_RECOVERY = 25


#SHOP SETTINGS
DEFAULT_BITCOIN_PRICE = 70000
MAX_HEALTH_INCREMENT = 10
PURCHASED_AMMO_INCREMENT = 20
ATTACK_DAMAGE_INCREMENT_RATIO = 1.15
WAVE_COMPLETION_REWARD = 10


#WAVE SCORE WEIGHTS
TIME_WEIGHT = 0.5
ACCURACY_WEIGHT = 0.2
HEALTH_LOST_WEIGHT = 0.4
ZOMBIE_COUNT_MULTIPLIER = 2