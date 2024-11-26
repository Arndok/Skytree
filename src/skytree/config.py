"""
A repository of variables to be used as definitions for other classes.

Import this and change whatever is needed before importing anything else in the package.
Most of these variables are used as defaults (see each module documentation to check which ones).

Functions:
set_all_paths(path): set every resource path to the given string.
"""

import sys

# Paths
if sys.version_info >= (3, 7):
    from importlib.resources import files
    EXAMPLE_RESOURCES_PATH = str(files("skytree") / "example_resources") + "/"
else:
    import pkg_resources
    EXAMPLE_RESOURCES_PATH = pkg_resources.resource_filename("skytree", "example_resources") + "/"

FILE_PATH = EXAMPLE_RESOURCES_PATH
"""Default path for files."""
IMG_PATH = EXAMPLE_RESOURCES_PATH
"""Default path for image files."""
FONT_PATH = EXAMPLE_RESOURCES_PATH
"""Default path for font files."""
MUSIC_PATH = EXAMPLE_RESOURCES_PATH
"""Default path for music files."""
SOUND_PATH = EXAMPLE_RESOURCES_PATH
"""Default path for sound files."""

def set_all_paths(path):
    """Set every resource path to the given string."""
    global MUSIC_PATH, IMG_PATH, FILE_PATH, FONT_PATH, SOUND_PATH
    MUSIC_PATH = path
    IMG_PATH = path
    FILE_PATH = path
    FONT_PATH = path
    SOUND_PATH = path

# Game
START_FULLSCREEN = False
"""Whether the game starts in fullscreen mode or not by default."""
FPS_CAP = 60
"""Default maximum frames per second. FPS must always be capped."""
CAPTION = "SkyTree"
"""Default window caption."""
CANVAS_DIM = (256, 240)
"""Default game canvas dimensions."""
WINDOW_MAGNIFY = 1
"""Default window scaling."""
MAIN_COLOR = (0,0,0) # Black
"""Default color for drawing shapes and text."""
GAME_BGCOLOR = (0,0,0) # Black
"""Default color for game background."""
DEFAULT_FONT = "SkyFont.ttf"
"""Default font."""
FONT_SIZE = 8
"""Default font size."""

# Audio
MIXER_FREQUENCY = 44100
"""Default mixer frequency. Should match audio resources for best sound quality."""
MIXER_SIZE = -16
"""Default mixer sample size. Should match audio resources for best sound quality."""
MIXER_CHANNELS = 2
"""Default mixer number of channels."""
MIXER_BUFFER = 512
"""Default mixer buffer size."""
DEF_FADEOUT = 1000
"""Default music fadeout (when keyword 'fade' is used)."""
MUSIC_VOLUME = 0.8
"""Music volume."""

# Boards
BOARD_BGCOLOR = (100, 100, 255) # Light blue. Well-- kinda light; not super light.
"""Default color for board background."""
KILL_MARGINS = 16
"""Default threshold to kill a Sprite when it exits a board."""
LAYER_SPEED = 50
"""Default lerp speed for layers (in pizels per second)."""

# Animations
SPRITE_FRAME_DURATION = 150
"""Default frame duration for sprite animations (in milliseconds)."""
TILE_FRAME_DURATION = 300
"""Default frame duration for tile animations (in milliseconds)."""

# Sprites
SPRITE_ACCEL_SPEED = 35
"""Default acceleration speed for sprites (in pizels per second)."""
SPRITE_JUMP_SPEED = 5
"""Default jump speed for sprites (immediate; affects sprite velocity)."""
SPRITE_FRICTION = .85
"""Default acceleration reduction factor for sprites (applied every frame)."""
SPRITE_GRAVITY = 20
"""Default jump speed for sprites (in pizels per second; affects sprite velocity)."""
SPRITE_RUN_FACTOR = 1.5
"""Default acceleration increase factor for running sprites."""
SPRITE_BONK_SLOWDOWN = .5
"""Default horizontal slowdown factor for sprites bonking the ceiling."""
SPRITE_LERP_SPEED = 100
"""Default lerp speed for sprites (in pizels per second)."""
STOMP_LOW_BOUNCE = 3
"""Default low bounce for sprites (immediate; affects sprite velocity)."""
STOMP_HIGH_BOUNCE = 6
"""Default high bounce for sprites (immediate; affects sprite velocity)."""
PLAYER_REVIVIFY_DELAY = 600
"""Default millisecond delay for revivifying player sprites after death."""
ORIENTATION_CHECK_DELAY = 50
"""Default millisecond delay for checking orientation on omnidirectional walking \
player controlled sprites after releasing a key (see sprites.TopDownWalk)."""

# Sounds
SOUND_ENTER_STAGE = None
SOUND_ACTIVATE_CHECKPOINT = None
