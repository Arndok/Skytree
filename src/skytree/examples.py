"""
An example of how to set up a game, as well as a showcase of Skytree's features.

Commentaries along the code show a suggested workflow for setting a game
and point at some features of the framework. 

Functions:
run_demo(): Run the demo. Called by default when executing as a script.
"""

# Import pygame constants
from pygame.locals import K_a, K_w, K_d, K_s, K_LEFT, K_UP, K_RIGHT, K_DOWN, K_ESCAPE, K_RETURN, K_SPACE, K_RCTRL, K_LCTRL, K_f, KEYUP, KEYDOWN

def run_demo():
    """Run the demo."""
    
    #############
    # FIRST STEP: SETTING UP THE GAME MANAGER
    
    # Import configuration file and game manager
    
    from skytree import config
    from skytree.game import Game
    from skytree.key_commands import KeyboardReader

    # Set configurations

    import os
    #config.set_all_paths("[desired_path]/") # Use this to set up your resources folders. You can also set them separately (check out config functions).
    config.CANVAS_DIM = (208, 160)
    config.WINDOW_MAGNIFY = 4
    config.MIXER_BUFFER = (1024)
    config.SOUND_ENTER_STAGE = "orb.ogg"
    config.SOUND_ACTIVATE_CHECKPOINT = "checkpoint.ogg"

    # Define event controllers

    keyboard_reader = KeyboardReader({
        **{key: "left" for key in (K_a, K_LEFT)},
        **{key: "up" for key in (K_w, K_UP)},
        **{key: "right" for key in (K_d, K_RIGHT)},
        **{key: "down" for key in (K_s, K_DOWN)},
        K_SPACE: "action1", #Shoot
        **{key: "action2" for key in (K_RCTRL, K_LCTRL)}, #Run
        K_f: "fullscreen",
        K_ESCAPE: "esc",
        K_RETURN: "enter"
        })

    # Instantiate game

    game = Game()
    
    # Bind event controllers to game
    
    for event in (KEYUP, KEYDOWN):
        game.set_event_controller(event, keyboard_reader)

    ##############
    # SECOND STEP: MAKING SOME GAME OBJECTS

    # Import whatever other classes you need from the framework

    from skytree.drawable import Drawable
    from skytree.collidable import Collidable, CircleHB
    from skytree.timers import Delay
    from skytree.tileset import TileSet
    from skytree.animated import Particle
    from skytree.boards import Board, TiledBoard, OnePlayerTiledBoard
    from skytree.layers import Layer, TiledLayer, MovingTiledLayer
    from skytree.tile_objects import DrawableTile, AnimatedTile, DraColTile, AniColTile, SpawnerTile, DraSpaTile, \
                                     StartTile, ExitTile, VisibleCheckpointTile, PathTile, StageTile
    from skytree.sprites import Sprite, FixedBounce, GravityBound, VelocityMovement, SidescrollerPlayer, TopDownPlayer, MapPlayer, \
                                SsWalkingEnemy, SsCautiousEnemy, SsJumpyEnemy, HoveringEnemy
    from skytree.user_interface import PauseState
    from skytree.resource_manager import ResourceManager

    # From here on, there's some leeway in the order you can do things.
    # This'd be ONE suggested workflow.

    #####
    # Define your game constants

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

    MAIN_MUSIC = "skytree_groove.ogg"
    PUNG_MUSIC = "skytree_bounce.ogg"
    INTRO_MUSIC = "skytree_bask.ogg"

    #####
    # Tilesets that can be defined outside their owners:
    # - Tilesets for ANY TILED LAYER
    # - Tilesets for UNIQUE SPRITES
    # A quirk of Skytree in its current version is that
    # sprites' tilesets are Components (so they can't be shared),
    # whereas tiled layers' tilesets are not (so they can be shared).

    level_tset = TileSet("terrain.png", TILE_DIM)
    map_tset = TileSet("demo_map_tiles.png", MAP_TILE_DIM)
    hook_ts = TileSet("hook.png", TILE_DIM)

    #####
    # Definitions for sprites:
    # animations and hitbox adjustments

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

    #####
    # You can leverage Skytree classes to define your own!

    class Text(Drawable):
        """A quick and dirty text object."""
        
        def __init__(self, text, font=config.DEFAULT_FONT, fsize=None, color=(255,255,255), **kwargs):
            """Extend to initialize canvas as a text object."""
            super().__init__(ResourceManager().get_font(font, fsize).render(text, 0, color), **kwargs)

    class Orb(Sprite):
        """A collectable that beats the stage when you pick it."""
        
        def __init__(self, start_label="start1", exit_label="default", **kwargs):
            """Extend to define appropriate labels and load pickup sound."""
            super().__init__(tileset=TileSet("orb.png", TILE_DIM), tags=("exit","beat"), hb_adjust=(-2,-2,1,1), **kwargs)
            self.dest_board = "map"
            self.start_label = start_label
            self.exit_label = exit_label
            self.sound = ResourceManager().get_sound("orb.ogg")

        def _move_and_collide_level(self, dt):
            """Override to skip movement stage during update time."""
            pass

    class GravityOrb(Orb, GravityBound):
        """An orb that's affected by gravity."""
        
        def __init__(self, start_label="start1", exit_label="default", **kwargs):
            """Extend to make object bounce upwards on instantiation."""
            super().__init__(start_label, exit_label, vel=(0,-3), gravity=15, **kwargs)
            
        def _move_and_collide_level(self, dt):
            """Override to perform only vertical movement during movement stage on update time."""
            self._move_collide_vertical(dt)

    class ExitArea(Collidable):
        """An area that triggers a board transition on player collision."""
        
        def __init__(self, dest_board, start_label="start1", **kwargs):
            """Extend to define appropriate labels."""
            super().__init__(tags=("exit",), **kwargs)
            self.dest_board = dest_board
            self.start_label = start_label

    class PungBall(FixedBounce, GravityBound):
        """A bouncy ball that hurts the player and can be popped, generating two smaller balls if it's big enough."""
    
        def __init__(self, size_factor=2, pos=[50,50], direction=1, tags=()):
            """Extend to calculate image and sound filenames, tile size, horizontal velocity and vertical bounce from size factor."""
            super().__init__(pos=pos, tileset=TileSet("ball{s}.png".format(s=size_factor), 2**(size_factor+3)), 
                             Shape=CircleHB, tags=tags+("ball",), vel = ((1 + size_factor * 0.5) * direction, -2),
                             gravity=8, bounce=((1 + size_factor * 0.5), size_factor + 3.5), sounds={"pop":"pung_pop{s}.ogg".format(s=size_factor)})
            # Size factor must be between 0 and 2
            self.size_factor = size_factor

        def pop(self):
            """
            Destroy the ball.
            
            It the ball's big enough, spawn two balls of the immediatly smaller size class going in opposite directions.
            If it's the last ball, beat the stage.
            """
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
        """
        A player shootable projectile.
        
        Self destroys in contact with an object or the level top border.
        Chain graphics included!
        """
    
        def __init__(self, pos, **kwargs):
            """Extend to set up appropriate sprite definitions, store initial y-position and play shoot sound."""
            anims = {"default":((0,1), (1,1)), "tail":((2,1),(3,1))}
            super().__init__(pos=pos, tileset=hook_ts, vel=(0,-HOOK_SPEED), anims=anims, tags=("hook",), sounds={"shoot":"pung_shoot.ogg"}, **kwargs)
            self.init_y = self.y
            self.play_sound("shoot")
            
        def _move_and_collide_board(self, dt):
            """Override to simplify movement."""
            self.y += self.vel_y
            
        def _border_check(self, dt):
            """Override to self destroy on top border collision."""
            if self.y < 0:
                Game().mark_for_destruction(self)

        def _collided_ball(self, obj):
            """Pop ball and self destroy on ball collision."""
            obj.pop()
            Game().mark_for_destruction(self)
            return True

        def draw(self, canvas):
            """Extend to draw a chain connecting the hook all the way down to the player sprite."""
            super().draw(canvas)
            pos_y = self.draw_rect.bottom
            while pos_y < self.init_y:
                self._tileset.hot_draw(canvas, (self.x, pos_y), self.anims[self.anim][self.anim_idx][0]+2)
                pos_y += self.draw_rect.height
        
        def destroy(self):
            """Extend to stop sound if needed and unlock player sprite commands (shooting the hook is a commited action)."""
            self.owner.allow_commands()
            self.stop_sound("shoot")
            super().destroy()

    class PungPlayer(SidescrollerPlayer):
        """A player that has hp and can be hurt; and can also shoot a hook upwards."""
        
        def __init__(self, pos=(20,104), hp=3):
            """Set up appropriate sprite definitions; add the HP HUD component to the game manager"""
            super().__init__(pos=pos, tileset=TileSet("player.png", PLAYER_IMG_DIM), anims=ss_player_anims, first_anim=ss_player_first_anim, hb_adjust=ss_player_hb_adjust, sounds={"jump":"jump.ogg", "death":"player_death.ogg", "hurt":"player_hurt.ogg"})
            self.anims["shoot"] = ((6,1), (13,float("inf"))) # Extend animations painlessly :)
            self.hp = hp
            self._reset_data["attributes"]["hp"] = hp
            self._font = ResourceManager().get_font(config.DEFAULT_FONT, 8)
            self.hud = Drawable(self._font.render("HP: 3", 0, (255,255,255)))
            Game().add_component(self.hud)
            self.hud.align_right()

        @property
        def shooting(self):
            """Whether the player sprite's currently shooting."""
            return "hook" in self.tagged

        def _determine_anim(self, dt):
            """Extend to consider shooting animation."""
            if self.shooting:
                self.anim = "shoot"
                return
            super()._determine_anim(dt)

        def shoot(self):
            """Create a hook sprite, add it as a component and set it to draw below the player sprite."""
            hook = Hook((self.x + 4, self.y - 1))
            self.add_component(hook)
            self.move_to_back(hook)

        def _collided_ball(self, obj):
            """Damage self on ball collision."""
            if not "dboost" in self.named:
                self.damage()

        def damage(self):
            """
            Hurt the player sprite.
            
            Decrement HP; kill the player sprite if HP reaches zero; play hurt sound otherwise.
            Set a "damage boosting" clock (player can't be hurt again immediately).
            """
            self.hp -= 1
            self.hud.canvas = self._font.render("HP: "+str(self.hp), 0, (255,255,255))
            self.add_component(Delay(DBOOST, name="dboost"))
            if self.hp < 1:
                self.kill("a dodgeball accident")
            else:
                self.play_sound("hurt")

        def draw(self, canvas):
            """Extend to blink if the player's damage boosting."""
            if not "dboost" in self.named or int(self.named["dboost"].time / 100)%2 == 0:
                super().draw(canvas)
                
        def _command_action1(self, press, **kwargs):
            """
            Bind 'action1' command to shooting the hook.
            
            Shooting the hook is a commited action, so it blocks player commands.
            It's also on a slight delay so it feels heavier.
            """
            if press and not self.shooting and not self.vel_y:
                if self.crouching:
                    self._com_down_release()
                    if self.crouching: return
                self.block_commands()
                self.vel_x = 0
                self._accel_x = 0
                self.add_component(Delay(HOOK_DELAY, self.shoot, tags=("hook",)))

        def reset(self):
            """Reset HP HUD."""
            super().reset()
            self.allow_commands()
            self.hud.canvas = self._font.render("HP: "+str(self.hp), 0, (255,255,255))
            
        def destroy(self):
            """Remove HP HUD component from game manager."""
            super().destroy()
            self.hud.destroy()
            
    #####
    # Dictionaries for mapping symbols in tilemaps to tile objects for the tiled layer to build.

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
                    "w": (AnimatedTile, {"idx": (16,17,18,19)}),
                }

    STG_TILES = {
                    **{str(i): (DraColTile, {"idx": i, "tags":("solid",)}) for i in range(47)},
                    "0": (DraColTile, {"idx": 0, "tags":("solid",)}),
                    "Hz": (DraColTile, {"idx": 48, "tags":("lethal",)}),
                    "S1": (StartTile, {"name":"start1"}),
                    "S2": (StartTile, {"name":"start2"})
                }

    BCK_SOLID = {
                    "0": (AniColTile, {"idx": (56,57,58,59), "tags":("solid",)}),
                }

    BCK_NOTSOLID = {
                       "0": (AnimatedTile, {"idx": (60,61,62,63)}),
                   }

    #####
    # Player sprites.
    #
    # Notice the sidescroller player is defined as a tuple (Class, {kwargs}). This is to avoid conflicts between different boards setting it as a component.

    sidescroller_player = (SidescrollerPlayer, {"tileset": (TileSet, {"canvas": "player.png", "tile_dim": PLAYER_IMG_DIM}), "anims": ss_player_anims, "first_anim": ss_player_first_anim, "hb_adjust": ss_player_hb_adjust, "sounds": {"jump": "jump.ogg", "death": "player_death.ogg"}})
    topdown_player = TopDownPlayer(tileset=TileSet(canvas = "player.png", tile_dim=PLAYER_IMG_DIM), pos=(16, 120), anims=td_player_anims, first_anim=td_player_first_anim, hb_adjust=td_player_hb_adjust)
    map_player = MapPlayer(tileset=TileSet("player_map.png", MAP_TILE_DIM), pos=(48,32), frame_duration=300, anims=map_player_anims, sounds={"enter":"enter_stage.ogg"})

    #############
    # THIRD STEP: SETTING UP THE BOARDS

    #######
    # MAP #
    #######
    
    # Map board.
    # - Using grid movement player.
    # - Switching stages while keeping a persistent state.
    # Instantiating a board with a name makes it automatically available as a game state.

    OnePlayerTiledBoard(TiledLayer(map_tset, "demo_map.txt", MAP_TILES, tags=("persistent_tiles",)), music="fade", name="map", first_state=True,
                        backgrounds=(TiledLayer(map_tset, "demo_map_bg.txt", MAP_TILES, frame_duration=600), Drawable("demo_map.png"),),
                        entities=(map_player,))

    ###########
    # STAGE 1 #
    ###########
    
    # A simple stage.
    # - Using top-down player.
    # - Setting solid border policies.
    Board(name="simple", border_policies="solid", music=INTRO_MUSIC,
          entities=(Text("KEYS OR WASD TO MOVE", pos=(10,10)), Text("ESC TO PAUSE", pos=(10,26)),
                    Text("^", pos=(186, 28)), Text("|", pos=(188, 28)), Text("Touch", pos=(170, 36)),
                    Orb(start_label="stage1", exit_label="right", pos=(184, 16)), topdown_player),)

    ###########
    # STAGE 2 #
    ###########

    # A stage to showcase framework features, focusing on sidescrollers.
    # - Using sidescroller player.
    # - Board transitions.

    # Exits
    # - Tiled layer.
    # - Tiles representing solid ground and starts / exits for the player sprite.
    OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr1.txt",
                                   {**STG_TILES,
                                    "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(8,0), "dest_board":"sidescroller2", "start_label":"start1"})
                                    }),
                        name="sidescroller1", entities=(Text("TILES", pos=(18,18)), Text("STARTS AND EXITS", pos=(18,34)), sidescroller_player,), music=MAIN_MUSIC)
    # Checkpoints and falls
    # - A tile that sets the active checkpoint with visual / audio feedback.
    # - Killing the sprite when it leaves the frame.
    OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr2.txt",
                                   {**STG_TILES,
                                    "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller1", "start_label":"start2"}),
                                    "E2": (ExitTile, {"hb_dim":(1,8), "hb_offset":(8,0), "dest_board":"sidescroller3", "start_label":"start1"}),
                                    "C1": (VisibleCheckpointTile, {"board": "sidescroller2", "idx":(51,52), "offset":(0,-16)})
                                    }),
                        name="sidescroller2", entities=(Text("A CHECKPOINT AND A FALL", pos=(18,18)), sidescroller_player),
                        music=MAIN_MUSIC)
    # Sprite kill margins
    # - Setting the margin for killing the sprite outside the frame.
    OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr2.txt",
                                   {**STG_TILES,
                                    "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller2", "start_label":"start2"}),
                                    "E2": (ExitTile, {"hb_dim":(1,8), "hb_offset":(8,0), "dest_board":"sidescroller4", "start_label":"start1"}),
                                    "C1": (VisibleCheckpointTile, {"board": "sidescroller3", "idx":(51,52), "offset":(0,-16)})
                                    }),
                        name="sidescroller3", entities=(Text("SOME FALLS ARE LONGER", pos=(18,18)), sidescroller_player),
                        music=MAIN_MUSIC, kill_margins=500)
    # Tile hazards
    # - Tiles that hurt the player.
    OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr3.txt",
                                   {**STG_TILES,
                                    "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller3", "start_label":"start2"}),
                                    "E2": (ExitTile, {"hb_dim":(1,8), "hb_offset":(8,0), "dest_board":"sidescroller5", "start_label":"start1"}),
                                    "C1": (VisibleCheckpointTile, {"board": "sidescroller4", "idx":(51,52), "offset":(0,-16)})
                                    }),
                        name="sidescroller4", entities=(Text("SOME TILES WANT TO", pos=(18,18)), Text("HURT YOU", pos=(18,34)), sidescroller_player),
                        music=MAIN_MUSIC)
    # Screen wrap
    # - Screen wrap border policies.
    OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr4.txt",
                                   {**STG_TILES,
                                    "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(8,0), "dest_board":"sidescroller6", "start_label":"start1"}),
                                    "C1": (VisibleCheckpointTile, {"board": "sidescroller5", "idx":(51,52), "offset":(0,-16)})
                                    }),
                        name="sidescroller5", entities=(Text("REMEMBER", pos=(90,18)), Text("PACMAN?", pos=(90, 34)), sidescroller_player),
                        music=MAIN_MUSIC, border_policies="wrap")
    # Big screen
    # - Boards bigger than the frame.
    # - Board subclass that has the frame follow the player.
    OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr5.txt",
                                   {**STG_TILES,
                                    "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller5", "start_label":"start2"}),
                                    "E2": (ExitTile, {"hb_dim":(1,8), "hb_offset":(8,0), "dest_board":"sidescroller7", "start_label":"start1"}),
                                    "C1": (VisibleCheckpointTile, {"board": "sidescroller6", "idx":(51,52), "offset":(0,-16)})
                                    }),
                        name="sidescroller6", entities=(Text("SOME ROOMS ARE BIGGER", pos=(18,98)), sidescroller_player,), music=MAIN_MUSIC)
    # Layers and parallax
    # - Parallax layers.
    # - Backgrounds and foregrounds.
    # - The foreground layer is set as a subsurface for the entity it contains to be positioned in reference to it.
    OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr6.txt",
                                   {**STG_TILES,
                                    "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller6", "start_label":"start2"}),
                                    "E2": (ExitTile, {"hb_dim":(1,8), "hb_offset":(8,0), "dest_board":"sidescroller8", "start_label":"start1"}),
                                    "C1": (VisibleCheckpointTile, {"board": "sidescroller7", "idx":(51,52), "offset":(0,-16)})
                                    }),
                        backgrounds=(Layer("demo_bg.png"), Layer("demo_bg2.png")),
                        foregrounds=(Layer(config.CANVAS_DIM, subsurface=True, components=(Text("PARALLAX LAYERS", pos=(96,18)),)),),
                        name="sidescroller7", entities=(sidescroller_player,), music=MAIN_MUSIC)
    # Moving, solid and animated layers
    # - Layer with automatic movement.
    # - Layer with solid ground.
    # - Animated tiles --all tiles in a layer are synchronized to the same clock by default.
    # - Player can be crushed.
    OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr7.txt",
                                   {**STG_TILES,
                                    "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller7", "start_label":"start2"}),
                                    "E2": (ExitTile, {"hb_dim":(1,8), "hb_offset":(8,0), "dest_board":"sidescroller9", "start_label":"start1"}),
                                    "C1": (VisibleCheckpointTile, {"board": "sidescroller8", "idx":(51,52), "offset":(0,-16)})
                                    }),
                        backgrounds=(Layer("demo_bg.png", components=(Text("LOOK OUT!!", pos=(224,98), color=(255,0,0)),)),
                                     MovingTiledLayer(level_tset, "demo_scr7_bg.txt", BCK_SOLID, parallax_adjust=(0,-64,0,0), destinations=(((0,-64),1000),((0,0),1000)))),
                        name="sidescroller8", music=MAIN_MUSIC,
                        entities=(Text("LAYERS CAN BE", pos=(90,18)), Text("TILED", pos=(90,34)), Text("MOVING", pos=(90,50)), Text("INTERACTIBLE", pos=(90,64)),
                                  Text("ANIMATED", pos=(90,80)), sidescroller_player))
    # Moving layers and parallax
    # - Parallax layer with automatic movement.
    OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr8.txt",
                                   {**STG_TILES,
                                    "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller8", "start_label":"start2"}),
                                    "E2": (ExitTile, {"hb_dim":(1,8), "hb_offset":(8,0), "dest_board":"sidescroller10", "start_label":"start1"}),
                                    "C1": (VisibleCheckpointTile, {"board": "sidescroller9", "idx":(51,52), "offset":(0,-16)})
                                    }),
                        backgrounds=(Layer("demo_bg_smol.png"), MovingTiledLayer(level_tset, "demo_scr8_bg.txt", BCK_NOTSOLID,
                                                                                    parallax_adjust=(-32,-32,16,16), speed=100,
                                                                                    destinations=(((16,16),200),((16,-16),200),((-16,-16),200),((-16,16),200)))),
                        name="sidescroller9", entities=(Text("PARALLAX WITH MOVING LAYERS", pos=(36,90)), sidescroller_player,), music=MAIN_MUSIC)
    # Getting weird with layers
    # - This is a light-hearted troll I've seen in a couple Super Mario World Kaizo levels.
    # - Uses parallax to have the ground move with the frame.
    OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr9.txt",
                                   {**STG_TILES,
                                    "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller9", "start_label":"start2"}),
                                    "C1": (VisibleCheckpointTile, {"board": "sidescroller10", "idx":(51,52), "offset":(0,-16)})
                                    }),
                        backgrounds=(Layer("demo_bg_smol.png"), TiledLayer(level_tset, "demo_scr9_bg.txt", {**STG_TILES,"C1":(DrawableTile, {"idx":(51)})},
                                                                           components=(Text("SORRY", pos=(84,18)),))),
                        name="sidescroller10", entities=(sidescroller_player, ExitArea("sidescroller11", pos=(-100,500), hb_dim=(408,1))), music=MAIN_MUSIC, kill_margins=500)
    # Spawners and enemies
    # - Tiles that make entities appear.
    # - Entities other than the player sprite can interact with layers too.
    OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr10.txt",
                                   {**STG_TILES,
                                    "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller12", "start_label":"start1"}),
                                    "s1": (SpawnerTile, {"obj":(SsWalkingEnemy, {"tileset":(TileSet,{"canvas":"lethal_serious.png", "tile_dim":GOON_DIM}),
                                                                                 "speed":GOON_SPEED, "direction":"right", "tags":("lethal",), "solids":("solid","lethal"),
                                                                                 "anims":ss_enemy_anims, "hb_adjust":ss_enemy_hb_adjust})})
                                    }),
                        backgrounds=(MovingTiledLayer(level_tset, "demo_scr10_bg.txt", BCK_SOLID, destinations=(((0,40),0),((0,0),0))),
                                     Layer(config.CANVAS_DIM, components=(Drawable("demo_bg_scr10.png", pos=(72,0)),))),
                        name="sidescroller11", entities=(Text("SPAWNERS", pos=(136,18)), sidescroller_player,), music=MAIN_MUSIC)
    # Different enemy behaviours
    # - One example enemy turns around when encountering a platform border; the other drops.
    # - Most basic enemy behaviour distinction in Super Mario Bros.
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
                        name="sidescroller12", entities=(Text("ENEMY BEHAVIOURS", pos=(18,18)), sidescroller_player,), music=MAIN_MUSIC)
    # Stompable enemies
    # - Same kind of behaviours as enemies in the previous board.
    # - These ones can be killed by jumping on them.
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
                        name="sidescroller13", entities=(Text("YOU CAN STOMP THESE", pos=(18,18)), sidescroller_player,), music=MAIN_MUSIC)
    # Jumping enemies
    # - More enemy behaviours.
    # - One enemy does smaller jumps continuously, the other one does bigger jumps on a timer.
    # - Using same visual indicators as enemies in the previous board to help the player distinguish between behaviours.
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
                        name="sidescroller14", entities=(Text("THEY CAN JUMP NOW", pos=(50,18)), sidescroller_player,), music=MAIN_MUSIC)
    # Hovering enemies and spawner options
    # - These enemies hover in a direction, can oscillate perpendicularly, and can have a patrolling behaviour or not (velocity controlled).
    # - Spawners can be set for different maximum numbers of spawned enemies allowed at the same time, and can have different cooldowns between spawns.
    OnePlayerTiledBoard(TiledLayer(level_tset, "demo_scr13.txt",
                                   {**STG_TILES,
                                    "E1": (ExitTile, {"hb_dim":(1,8), "hb_offset":(-1,0), "dest_board":"sidescroller14", "start_label":"start2"}),
                                    "C1": (VisibleCheckpointTile, {"board": "sidescroller15", "idx":(51,52), "offset":(0,-16)}),
                                    "s1": (SpawnerTile, {"obj":(HoveringEnemy, {"tileset":(TileSet,{"canvas":"spooky_serious.png", "tile_dim":GOON_DIM}),
                                                                                "speed":GHOST_SPEED, "direction":"left", "patrol_time": GHOST_PATROL,
                                                                                "osc_period": GHOST_OSC, "tags":("lethal",), "solids":(), "hb_adjust":hov_enemy_hb_adjust})}),
                                    "s2": (DraSpaTile, {"idx":46, "obj":(HoveringEnemy, {"tileset":(TileSet,{"canvas":"spooky_grinny.png", "tile_dim":GOON_DIM}),
                                                                                         "speed":GHOST_SPEED, "direction":"left", "tags":("lethal",),
                                                                                         "solids":(), "hb_adjust":hov_enemy_hb_adjust}),
                                                        "cooldown":0}),
                                    "s3": (DraSpaTile, {"idx":46, "obj":(HoveringEnemy, {"tileset":(TileSet,{"canvas":"spooky_grinny.png", "tile_dim":GOON_DIM}),
                                                                                         "speed":GHOST_SPEED_FAST, "direction":"left", "tags":("lethal",),
                                                                                         "solids":(), "hb_adjust":hov_enemy_hb_adjust}),
                                                        "obj_limit":2, "cooldown":2000}),
                                    "s4": (SpawnerTile, {"obj":(GravityOrb, {"start_label":"stage2", "exit_label":"down"})}),
                                    }),
                        name="sidescroller15", entities=(Text("SPAWNER", pos=(50,18)), Text("SETTINGS", pos=(50,34)), sidescroller_player,), music=MAIN_MUSIC)


    ###########
    # STAGE 3 #
    ###########
    
    # A Pang clone
    # - Using custom entities while leveraging superclasses provided by the framework.
    # - Interaction between differently shaped hitboxes.
    TiledBoard(TiledLayer(TileSet("terrain.png", TILE_DIM), "demo_pung.txt", STG_TILES), name="pung",
               pos=(0,10), entities=(Text("SPACE TO SHOOT", pos=(10,2)), PungPlayer(), PungBall),
               border_policies=("solid", None), kill_margins=100, music=PUNG_MUSIC)

    game.run()

if __name__ == "__main__":
    run_demo()
