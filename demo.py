from skytree import config
from skytree.game import *

# Set configurations, instantiate game and set event controllers.

config.set_all_paths("./demo_resources/")
config.CANVAS_DIM = (208, 160)
config.WINDOW_DIM = (832, 640)
config.MIXER_BUFFER = (1024)
config.SOUND_ENTER_STAGE = "orb.ogg"
config.SOUND_ACTIVATE_CHECKPOINT = "checkpoint.ogg"

keyboard_reader = KeyboardReader({
    **{key: "left" for key in (K_a, K_LEFT)},
    **{key: "up" for key in (K_w, K_UP, K_SPACE)},
    **{key: "right" for key in (K_d, K_RIGHT)},
    **{key: "down" for key in (K_s, K_DOWN)},
    K_SPACE: "action1", #Shoot
    **{key: "action2" for key in (K_RCTRL, K_LCTRL)}, #Run
    K_f: "fullscreen",
    K_ESCAPE: "esc",
    K_RETURN: "enter"
    })

game = Game()
for event in (KEYUP, KEYDOWN):
    game.set_event_controller(event, keyboard_reader)

from skytree.key_commands import KeyboardReader
from skytree.collidable import Collidable, CircleHB
from skytree.tileset import TileSet
from skytree.animated import Particle
from skytree.boards import Board, TiledBoard, OnePlayerTiledBoard
from skytree.layers import Layer, TiledLayer, MovingTiledLayer
from skytree.tile_objects import *
from skytree.sprites import *
from skytree.user_interface import PauseState
from skytree.resource_manager import ResourceManager

# Constants

PLAYER_IMG_DIM = (16, 24)
MAP_TILE_DIM = (16, 16)
TILE_DIM = (8, 8)
GOON_DIM = (16, 16)

GOON_SPEED = 15
GOON_SPEED_HEAVY = 25
GOON_JUMP = 5
GOON_JUMP_HEAVY = 7
GOON_JUMP_HEAVY_COOLDOWN = 1000
GHOST_SPEED = 7
GHOST_SPEED_FAST = 12
GHOST_PATROL = 2400
GHOST_OSC = 300

HOOK_SPEED = 3
HOOK_DELAY = 150

DBOOST = 1000

FONT = "ArcadeClassic.ttf"

# Tilesets

level_tset = TileSet("terrain.png", TILE_DIM)
map_tset = TileSet("paths.png", MAP_TILE_DIM)
hook_ts = TileSet("hook.png", TILE_DIM)

# Sprite animations and hitbox adjustments

ss_player_anims = {
    "idle_right": ((0,20), (1,1)),
    "walk_right": ((2,1), (0,1), (3,1), (0,1)),
    "crouch_right": ((4,20), (5,1)),
    "jump_right": ((2,float("inf")),),
    "idle_left": ((7,20), (8,1)),
    "walk_left": ((9,1), (7,1), (10,1), (7,1)),
    "crouch_left": ((11,20), (12,1)),
    "jump_left": ((9,float("inf")),),
    "death": ((14,1),(15,1),(16,1),(17,1))
    }   
ss_player_first_anim = "idle_right"
ss_player_hb_adjust = (-8, -1, 4, 1)

td_player_anims = {
    "idle_right": ((0,20), (1,1)),
    "walk_right": ((2,1), (0,1), (3,1), (0,1)),
    "idle_left": ((7,20), (8,1)),
    "walk_left": ((9,1), (7,1), (10,1), (7,1)),
    "idle_up": ((25,float("inf")),),
    "walk_up": ((26,1), (25,1), (27,1), (25,1)),
    "idle_down": ((21,20), (22,1)),
    "walk_down": ((23,1), (21,1), (24,1), (21,1)),
    "idle_right_up": ((32,float("inf")),),
    "walk_right_up": ((33,1), (32,1), (34,1), (32,1)),
    "idle_right_down": ((28,20), (29,1)),
    "walk_right_down": ((30,1), (28,1), (31,1), (28,1)),
    "idle_left_up": ((39,float("inf")),),
    "walk_left_up": ((40,1), (39,1), (41,1), (39,1)),
    "idle_left_down": ((35,20), (36,1)),
    "walk_left_down": ((37,1), (35,1), (38,1), (35,1))
    }
td_player_first_anim = "idle_right"
td_player_hb_adjust = (-8, -1, 4, 1)

map_player_anims={
    "default": ((0,1),(1,1)),
    "enter": ((2,float("inf")),)
    }

ss_enemy_anims = {
    "default": ((0,1), (1,1), (2,1), (3,1)),
    "stomped": ((4,float("inf")),)
    }

ss_enemy_hb_adjust = (-4, -2, 2, 2)
hov_enemy_hb_adjust = (-4, -2, 2, 1)

# Custom classes

class Text(Drawable):
    """A quick and dirty text object."""
    def __init__(self, text, fsize=None, color=(255,255,255), **kwargs):
        super().__init__(ResourceManager().get_font(FONT, fsize).render(text, 0, color), **kwargs)

class Orb(Sprite):
    def __init__(self, start_label="start1", exit_label="default", **kwargs):
        super().__init__(tileset=TileSet("orb.png", TILE_DIM), tags=("exit","beat"), hb_adjust=(-2,-2,1,1), **kwargs)
        self.dest_board = "map"
        self.start_label = start_label
        self.exit_label = exit_label
        self.sound = ResourceManager().get_sound("orb.ogg")

    def _move_and_collide_level(self, dt):
        # Skip
        pass

class GravityOrb(Orb, GravityBound):
    def __init__(self, start_label="start1", exit_label="default", **kwargs):
        super().__init__(start_label, exit_label, vel=(0,-3), gravity=15, **kwargs)
        
    def _move_and_collide_level(self, dt):
        # Vertical movement / horizontal collision only
        self._move_collide_vertical(dt)

class ExitArea(Collidable):
    def __init__(self, dest_board, start_label="start1", **kwargs):
        super().__init__(tags=("exit",), **kwargs)
        self.dest_board = dest_board
        self.start_label = start_label

class PungBall(FixedBounce, GravityBound):
    def __init__(self, size_factor=2, pos=[50,50], direction=1, tags=()):
        """Calculate image filename, tile size, horizontal velocity and vertical bounce from size factor."""
        super().__init__(pos=pos, tileset=TileSet("ball{s}.png".format(s=size_factor), 2**(size_factor+3)), 
                         Shape=CircleHB, tags=tags+("ball",), vel = ((1 + size_factor * 0.5) * direction, -2),
                         gravity=8, bounce=((1 + size_factor * 0.5), size_factor + 3.5), sounds={"pop":"pung_pop{s}.ogg".format(s=size_factor)})
        # Size factor must be between 0 and 2
        self.size_factor = size_factor

    def pop(self):
        """It the ball's big enough, spawn two balls of the immediatly smaller size class going in opposite directions."""
        if self.size_factor > 0:
            self.play_sound("pop")
            self.owner.add_component(PungBall(self.size_factor-1, self.pos, -1))
            self.owner.add_component(PungBall(self.size_factor-1, (self.x+(self.width/2), self.y)))
        else:
            if len(tuple(filter(lambda x: isinstance(x, PungBall), self.board._components))) > 1:
                self.play_sound("pop")
                self.owner.add_component(Particle(TileSet("ball_pop.png",8), pos=self.pos, frame_duration=50))
            else:
                self.game.active_stage.beat(exit_state="map", start_label="stage3", exit_label="up")
        Game().mark_for_destruction(self)

class Hook(VelocityMovement):
    def __init__(self, pos, **kwargs):
        anims = {"default":((0,1), (1,1)), "tail":((2,1),(3,1))}
        super().__init__(pos=pos, tileset=hook_ts, vel=(0,-HOOK_SPEED), anims=anims, tags=("hook",), sounds={"shoot":"pung_shoot.ogg"}, **kwargs)
        self.init_y = self.y
        self.play_sound("shoot")
        
    def _move_and_collide_board(self, dt):
        # Base class works fine, but it does some extraneous work.
        self.y += self.vel_y
        
    def _border_check(self, dt):
        if self.y < 0:
            Game().mark_for_destruction(self)

    def _collided_ball(self, obj):
        obj.pop()
        Game().mark_for_destruction(self)
        return True

    def draw(self, canvas):
        # Draw chain as well as hook.
        super().draw(canvas)
        pos_y = self.draw_rect.bottom
        while pos_y < self.init_y:
            self._tileset.hot_draw(canvas, (self.x, pos_y), self.anims[self.anim][self.anim_idx][0]+2)
            pos_y += self.draw_rect.height
    
    def destroy(self):
        self.owner.allow_commands()
        super().destroy()
        self.stop_sound("shoot")

class PungPlayer(SidescrollerPlayer):
    def __init__(self, pos=(20,104), hp=3):
        super().__init__(pos=pos, tileset=TileSet("player.png", PLAYER_IMG_DIM), anims=ss_player_anims, first_anim=ss_player_first_anim, hb_adjust=ss_player_hb_adjust, sounds={"jump":"jump.ogg", "death":"player_death.ogg", "hurt":"player_hurt.ogg"})
        self.anims["shoot"] = ((6,1), (13,float("inf"))) # Extend animations painlessly :)
        self.hp = hp
        self._reset_data["attributes"]["hp"] = hp
        self._font = ResourceManager().get_font("Pixel-Miners.otf", 8)
        self.hud = Drawable(self._font.render("HP: 3", 0, (255,255,255)))
        Game().add_component(self.hud)
        self.hud.align_right()

    @property
    def shooting(self):
        return "hook" in self.tagged

    def _determine_anim(self, dt):
        if self.shooting:
            self.anim = "shoot"
            return
        super()._determine_anim(dt)

    def shoot(self):
        hook = Hook((self.x + 4, self.y - 1))
        self.add_component(hook)
        self.move_to_back(hook)

    def _collided_ball(self, obj):
        if not "dboost" in self.named:
            self.damage()

    def damage(self):
        self.hp -= 1
        self.hud.canvas = self._font.render("HP: "+str(self.hp), 0, (255,255,255))
        self.add_component(Delay(DBOOST, name="dboost"))
        if self.hp < 1:
            self.kill("a dodgeball accident")
        else:
            self.play_sound("hurt")

    def draw(self, canvas):
        # Blink if damage boosting.
        if not "dboost" in self.named or int(self.named["dboost"].time / 100)%2 == 0:
            super().draw(canvas)
            
    def _command_action1(self, press, **kwargs):
        if press and not self.vel_y:
            if self.crouching:
                self._com_down_release()
                if self.crouching: return
            self.block_commands()
            self.vel_x = 0
            self._accel_x = 0
            self.add_component(Delay(HOOK_DELAY, self.shoot, tags=("hook",)))

    def reset(self):
        super().reset()
        self.hud.canvas = self._font.render("HP: "+str(self.hp), 0, (255,255,255))
        
# Tilemaps

MAP_TILES = {
                "2": (PathTile, {"idx": 2, "tags": ("left", "right")}),
                "3": (PathTile, {"idx": 3, "tags": ("up", "down")}),
                "4": (PathTile, {"idx": 4, "tags": ("left", "up")}),
                "5": (PathTile, {"idx": 5, "tags": ("up", "right")}),
                "6": (PathTile, {"idx": 6, "tags": ("right", "down")}),
                "7": (PathTile, {"idx": 7, "tags": ("down", "left")}),
                "8": (PathTile, {"idx": 8, "tags": ("left", "up", "right")}),
                "9": (PathTile, {"idx": 9, "tags": ("up", "right", "down")}),
                "10": (PathTile, {"idx": 10, "tags": ("right", "down", "left")}),
                "11": (PathTile, {"idx": 11, "tags": ("down", "left", "up")}),
                "12": (PathTile, {"idx": 12, "tags": ("left", "up", "right", "down")}),
                "A": (StageTile, {"idx": (0, 1), "name": "stage1", "entry_state": "simple", "traversable": True, "tags": ("right",)}),
                "B": (StageTile, {"idx": (0, 1), "name": "stage2", "entry_state": "sidescroller1", "tags": ("left", "down")}),
                "C": (StageTile, {"idx": (0, 1), "name": "stage3", "entry_state": "pung", "tags": ("left", "up")}),
            }

STG_TILES = {
                "0": (DraColTile, {"idx": 0, "tags":("solid",)}),
                "Hz": (DraColTile, {"idx": 48, "tags":("lethal",)}),
                "S1": (StartTile, {"name":"start1"}),
                "S2": (StartTile, {"name":"start2"})
            }

BCK_SOLID = {
                "0": (AniColTile, {"idx": (9,3,6,12), "tags":("solid",)}),
            }

BCK_NOTSOLID = {
                   "0": (AnimatedTile, {"idx": (9,3,6,12)}),
               }

# Players

sidescroller_player = (SidescrollerPlayer, {"tileset": (TileSet, {"canvas": "player.png", "tile_dim": PLAYER_IMG_DIM}), "anims": ss_player_anims, "first_anim": ss_player_first_anim, "hb_adjust": ss_player_hb_adjust, "sounds": {"jump": "jump.ogg", "death": "player_death.ogg"}})
topdown_player = TopDownPlayer(tileset=TileSet(canvas = "player.png", tile_dim=PLAYER_IMG_DIM), pos=(16, 120), anims=td_player_anims, first_anim=td_player_first_anim, hb_adjust=td_player_hb_adjust)
map_player = MapPlayer(tileset=TileSet("player_map.png", MAP_TILE_DIM), pos=(48,32), frame_duration=300, anims=map_player_anims, sounds={"enter":"enter_stage.ogg"})

# Music

level_music = "skytree_stage.ogg"

# Boards

#######
# MAP #
#######

OnePlayerTiledBoard(TiledLayer(map_tset, "demo_map.txt", MAP_TILES, tags=("persistent_tiles",)), music="fade", name="map", first_state=True,
                    backgrounds=(Drawable("demo_map.png"),), entities=(map_player,))

###########
# STAGE 1 #
###########

Board(name="simple", border_policies="solid", music=level_music,
      entities=(Text("KEYS OR WASD TO MOVE", pos=(10,10)), Text("ESC TO PAUSE", pos=(10,26)),
                Orb(start_label="stage1", exit_label="right", pos=(184, 16)), topdown_player),)

###########
# STAGE 2 #
###########

# Exits
OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr1.txt",
                               {**STG_TILES,
                                "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(8,0), "dest_board":"sidescroller2", "start_label":"start1"})
                                }),
                    name="sidescroller1", entities=(Text("TILES", pos=(18,18)), Text("STARTS AND EXITS", pos=(18,34)), sidescroller_player,), music=level_music)
# Checkpoints and falls
OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr2.txt",
                               {**STG_TILES,
                                "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller1", "start_label":"start2"}),
                                "E2": (ExitTile, {"hb_dim":(1,8), "hb_offset":(8,0), "dest_board":"sidescroller3", "start_label":"start1"}),
                                "C1": (VisibleCheckpointTile, {"board": "sidescroller2", "idx":(51,52), "offset":(0,-16)})
                                }),
                    name="sidescroller2", entities=(Text("A CHECKPOINT AND A FALL", pos=(18,18)), sidescroller_player),
                    music=level_music)
# Sprite kill margins
OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr2.txt",
                               {**STG_TILES,
                                "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller2", "start_label":"start2"}),
                                "E2": (ExitTile, {"hb_dim":(1,8), "hb_offset":(8,0), "dest_board":"sidescroller4", "start_label":"start1"}),
                                "C1": (VisibleCheckpointTile, {"board": "sidescroller3", "idx":(51,52), "offset":(0,-16)})
                                }),
                    name="sidescroller3", entities=(Text("SOME FALLS ARE LONGER", pos=(18,18)), sidescroller_player),
                    music=level_music, kill_margins=500)
# Tile hazards
OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr3.txt",
                               {**STG_TILES,
                                "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller3", "start_label":"start2"}),
                                "E2": (ExitTile, {"hb_dim":(1,8), "hb_offset":(8,0), "dest_board":"sidescroller5", "start_label":"start1"}),
                                "C1": (VisibleCheckpointTile, {"board": "sidescroller4", "idx":(51,52), "offset":(0,-16)})
                                }),
                    name="sidescroller4", entities=(Text("SOME TILES WANT TO", pos=(18,18)), Text("HURT YOU", pos=(18,34)), sidescroller_player),
                    music=level_music)
# Screen wrap
OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr4.txt",
                               {**STG_TILES,
                                "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(8,0), "dest_board":"sidescroller6", "start_label":"start1"}),
                                "C1": (VisibleCheckpointTile, {"board": "sidescroller5", "idx":(51,52), "offset":(0,-16)})
                                }),
                    name="sidescroller5", entities=(Text("REMEMBER", pos=(94,18)), Text("PACMAN", pos=(94, 34)), sidescroller_player),
                    music=level_music, border_policies="wrap")
# Big screen
OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr5.txt",
                               {**STG_TILES,
                                "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller5", "start_label":"start2"}),
                                "E2": (ExitTile, {"hb_dim":(1,8), "hb_offset":(8,0), "dest_board":"sidescroller7", "start_label":"start1"}),
                                "C1": (VisibleCheckpointTile, {"board": "sidescroller6", "idx":(51,52), "offset":(0,-16)})
                                }),
                    name="sidescroller6", entities=(Text("SOME ROOMS ARE BIGGER", pos=(18,102)), sidescroller_player,), music=level_music)
# Layers and parallax
OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr6.txt",
                               {**STG_TILES,
                                "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller6", "start_label":"start2"}),
                                "E2": (ExitTile, {"hb_dim":(1,8), "hb_offset":(8,0), "dest_board":"sidescroller8", "start_label":"start1"}),
                                "C1": (VisibleCheckpointTile, {"board": "sidescroller7", "idx":(51,52), "offset":(0,-16)})
                                }),
                    backgrounds=(Layer("demo_bg.png"), Layer("demo_bg2.png")),
                    foregrounds=(Layer(config.CANVAS_DIM, subsurface=True, components=(Text("PARALLAX LAYERS", pos=(72,18)),)),),
                    name="sidescroller7", entities=(sidescroller_player,), music=level_music)
# Moving, solid and animated layers
OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr7.txt",
                               {**STG_TILES,
                                "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller7", "start_label":"start2"}),
                                "E2": (ExitTile, {"hb_dim":(1,8), "hb_offset":(8,0), "dest_board":"sidescroller9", "start_label":"start1"}),
                                "C1": (VisibleCheckpointTile, {"board": "sidescroller8", "idx":(51,52), "offset":(0,-16)})
                                }),
                    backgrounds=(Layer("demo_bg.png"), MovingTiledLayer(level_tset, "demo_scr7_bg.txt", BCK_SOLID,
                                                                                parallax_adjust=(0,-64,0,0),
                                                                                destinations=(((0,-64),1000),((0,0),1000)))),
                    name="sidescroller8", music=level_music,
                    entities=(Text("LAYERS CAN BE", pos=(90,18)), Text("TILED", pos=(90,34)), Text("MOVING", pos=(90,50)), Text("INTERACTIBLE", pos=(90,64)),
                              Text("ANIMATED", pos=(90,80)), Text("LOOK OUT", pos=(232,96), color=(255,0,0)), sidescroller_player))
# Moving layers and parallax
OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr8.txt",
                               {**STG_TILES,
                                "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller8", "start_label":"start2"}),
                                "E2": (ExitTile, {"hb_dim":(1,8), "hb_offset":(8,0), "dest_board":"sidescroller10", "start_label":"start1"}),
                                "C1": (VisibleCheckpointTile, {"board": "sidescroller9", "idx":(51,52), "offset":(0,-16)})
                                }),
                    backgrounds=(Layer("demo_bg_smol.png"), MovingTiledLayer(level_tset, "demo_scr8_bg.txt", BCK_NOTSOLID,
                                                                                parallax_adjust=(-32,-32,16,16), speed=100,
                                                                                destinations=(((16,16),200),((16,-16),200),((-16,-16),200),((-16,16),200)))),
                    name="sidescroller9", entities=(Text("PARALLAX WITH MOVING LAYERS", pos=(24,90)), sidescroller_player,), music=level_music)
# Getting weird with layers
OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr9.txt",
                               {**STG_TILES,
                                "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller9", "start_label":"start2"}),
                                "C1": (VisibleCheckpointTile, {"board": "sidescroller10", "idx":(51,52), "offset":(0,-16)})
                                }),
                    backgrounds=(Layer("demo_bg_smol.png"), TiledLayer(level_tset, "demo_scr9_bg.txt", {**STG_TILES,"C1":(DrawableTile, {"idx":(51)})})),
                    name="sidescroller10", entities=(Text("SORRY", pos=(84,18)), sidescroller_player, ExitArea("sidescroller11", pos=(0,176), hb_dim=(208,1))), music=level_music)
# Spawners and enemies
OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr10.txt",
                               {**STG_TILES,
                                "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller12", "start_label":"start1"}),
                                "s1": (SpawnerTile, {"obj":(SsWalkingEnemy, {"tileset":(TileSet,{"canvas":"lethal_serious.png", "tile_dim":GOON_DIM}),
                                                                             "speed":GOON_SPEED, "direction":"right", "tags":("lethal",), "solids":("solid","lethal"),
                                                                             "anims":ss_enemy_anims, "hb_adjust":ss_enemy_hb_adjust})})
                                }),
                    backgrounds=(MovingTiledLayer(level_tset, "demo_scr10_bg.txt", BCK_SOLID, destinations=(((0,40),0),((0,0),0))),),
                    name="sidescroller11", entities=(Text("SPAWNERS", pos=(118,18)), sidescroller_player,), music=level_music)
# Different enemy behaviours
OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr11.txt",
                               {**STG_TILES,
                                "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller11", "start_label":"start2"}),
                                "E2": (ExitTile, {"hb_dim":(1,8), "hb_offset":(8,0), "dest_board":"sidescroller13", "start_label":"start1"}),
                                "C1": (VisibleCheckpointTile, {"board": "sidescroller12", "idx":(51,52), "offset":(0,-16)}),
                                "s1": (SpawnerTile, {"obj":(SsCautiousEnemy, {"tileset":(TileSet,{"canvas":"lethal_serious.png", "tile_dim":GOON_DIM}),
                                                                              "speed":GOON_SPEED, "direction":"right", "tags":("lethal",),
                                                                              "anims":ss_enemy_anims, "hb_adjust":ss_enemy_hb_adjust})}),
                                "s2": (SpawnerTile, {"obj":(SsWalkingEnemy, {"tileset":(TileSet,{"canvas":"lethal_grinny.png", "tile_dim":GOON_DIM}),
                                                                             "speed":GOON_SPEED, "direction":"left", "tags":("lethal",),
                                                                             "anims":ss_enemy_anims, "hb_adjust":ss_enemy_hb_adjust})})
                                }),
                    name="sidescroller12", entities=(Text("ENEMY BEHAVIOURS", pos=(18,18)), sidescroller_player,), music=level_music)
# Stompable enemies
OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr11.txt",
                               {**STG_TILES,
                                "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller12", "start_label":"start2"}),
                                "E2": (ExitTile, {"hb_dim":(1,8), "hb_offset":(8,0), "dest_board":"sidescroller14", "start_label":"start1"}),
                                "C1": (VisibleCheckpointTile, {"board": "sidescroller13", "idx":(51,52), "offset":(0,-16)}),
                                "s1": (SpawnerTile, {"obj":(SsCautiousEnemy, {"tileset":(TileSet,{"canvas":"squishy_serious.png", "tile_dim":GOON_DIM}),
                                                                              "speed":GOON_SPEED, "direction":"right", "tags":("stompable",),
                                                                              "anims":ss_enemy_anims, "hb_adjust":ss_enemy_hb_adjust,
                                                                              "sounds":{"stomp":"stomp.ogg"}})}),
                                "s2": (SpawnerTile, {"obj":(SsWalkingEnemy, {"tileset":(TileSet,{"canvas":"squishy_grinny.png", "tile_dim":GOON_DIM}),
                                                                             "speed":GOON_SPEED, "direction":"left", "tags":("stompable",),
                                                                             "anims":ss_enemy_anims, "hb_adjust":ss_enemy_hb_adjust,
                                                                             "sounds":{"stomp":"stomp.ogg"}})})
                                }),
                    name="sidescroller13", entities=(Text("YOU CAN STOMP THESE", pos=(18,18)), sidescroller_player,), music=level_music)
# Jumping enemies
OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr12.txt",
                               {**STG_TILES,
                                "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller13", "start_label":"start2"}),
                                "E2": (ExitTile, {"hb_dim":(1,8), "hb_offset":(8,0), "dest_board":"sidescroller15", "start_label":"start1"}),
                                "C1": (VisibleCheckpointTile, {"board": "sidescroller14", "idx":(51,52), "offset":(0,-16)}),
                                "s1": (SpawnerTile, {"obj":(SsJumpyEnemy, {"tileset":(TileSet,{"canvas":"squishy_serious.png", "tile_dim":GOON_DIM}),
                                                                           "speed":GOON_SPEED_HEAVY, "jump_speed":GOON_JUMP_HEAVY, "jump_cooldown":GOON_JUMP_HEAVY_COOLDOWN,
                                                                           "direction":"right", "tags":("stompable",), "anims":ss_enemy_anims, "hb_adjust":ss_enemy_hb_adjust,
                                                                           "sounds":{"stomp":"stomp.ogg"}})}),
                                "s2": (SpawnerTile, {"obj":(SsJumpyEnemy, {"tileset":(TileSet,{"canvas":"squishy_grinny.png", "tile_dim":GOON_DIM}),
                                                                           "speed":GOON_SPEED, "jump_speed":GOON_JUMP, "direction":"left", "tags":("stompable",),
                                                                           "anims":ss_enemy_anims, "hb_adjust":ss_enemy_hb_adjust,
                                                                           "sounds":{"stomp":"stomp.ogg"}})})
                                }),
                    name="sidescroller14", entities=(Text("THEY CAN JUMP NOW", pos=(50,18)), sidescroller_player,), music=level_music)
# Hovering enemies and spawner options
OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr13.txt",
                               {**STG_TILES,
                                "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller14", "start_label":"start2"}),
                                "C1": (VisibleCheckpointTile, {"board": "sidescroller15", "idx":(51,52), "offset":(0,-16)}),
                                "s1": (SpawnerTile, {"obj":(HoveringEnemy, {"tileset":(TileSet,{"canvas":"spooky_serious.png", "tile_dim":GOON_DIM}),
                                                                            "speed":GHOST_SPEED, "direction":"left", "patrol_time": GHOST_PATROL,
                                                                            "osc_period": GHOST_OSC, "tags":("lethal",), "solids":(), "hb_adjust":hov_enemy_hb_adjust})}),
                                "s2": (DraSpaTile, {"idx":0, "obj":(HoveringEnemy, {"tileset":(TileSet,{"canvas":"spooky_grinny.png", "tile_dim":GOON_DIM}),
                                                                                    "speed":GHOST_SPEED, "direction":"left", "tags":("lethal",),
                                                                                    "solids":(), "hb_adjust":hov_enemy_hb_adjust}),
                                                    "cooldown":0}),
                                "s3": (DraSpaTile, {"idx":0, "obj":(HoveringEnemy, {"tileset":(TileSet,{"canvas":"spooky_grinny.png", "tile_dim":GOON_DIM}),
                                                                                    "speed":GHOST_SPEED_FAST, "direction":"left", "tags":("lethal",),
                                                                                    "solids":(), "hb_adjust":hov_enemy_hb_adjust}),
                                                    "obj_limit":2, "cooldown":2000}),
                                "s4": (SpawnerTile, {"obj":(GravityOrb, {"start_label":"stage2", "exit_label":"down"})}),
                                }),
                    name="sidescroller15", entities=(Text("SPAWNER", pos=(50,18)), Text("SETTINGS", pos=(50,34)), sidescroller_player,), music=level_music)


###########
# STAGE 3 #
###########

TiledBoard(TiledLayer(TileSet("terrain.png", TILE_DIM), "demo_pung.txt", STG_TILES), name="pung",
           pos=(0,10), entities=(Text("SPACE TO SHOOT", pos=(10,2)), PungPlayer(), PungBall),
           border_policies=("solid", None), kill_margins=100, music=level_music)

game.run()
