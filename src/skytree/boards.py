"""
Definition of classes that represent continuous game spaces.

Classes:
LayerContainer(Updateable, Drawable, Collidable): an ad-hoc class to help boards organize draw layers.
Board(Updateable, Drawable, Collidable, KeyCommandReader, GameState): base game space class.
TiledBoard(Board): a board that supports interaction with tiled layers.
PlayerCam(Board): a board with a frame that follows the player around.
OnePlayerTiledBoard(TiledBoard, PlayerCam): combines TiledBoard and PlayerCam

Variables used from config: BOARD_BGCOLOR, CANVAS_DIM
"""

from itertools import chain
from pygame import Rect
from skytree.helpers import repack2, repack4, bake_obj
from skytree import config
from skytree.game import GameState
from skytree.updateable import Updateable
from skytree.collidable import Collidable
from skytree.drawable import Drawable
from skytree.key_commands import KeyCommandReader
from skytree.layers import Layer, TiledLayer
from skytree.stage import Stage
from skytree.user_interface import PauseState
from skytree.sprites import SidescrollerPlayer

class LayerContainer(Updateable, Drawable, Collidable):
    """Combine Updateable, Drawable and Collidable."""
    pass
    
class Board(Updateable, Drawable, Collidable, KeyCommandReader, GameState):
    """
    Extend Updateable, Drawable, Collidable and KeyCommandReader to represent a game space.
    
    Inherits all behaviour from Component, Updateable, Positional, Drawable, Collidable and KeyCommandReader.
    Implements game.GameState interface.
    Extends Component.add_component(component).
    
    Organizes draw levels; can hold border policies and music.
    
    Public methods:
    add_component(component): extend Component to make sure foregrounds always remain on top.
    add_background(layer); add_midground(layer); add_foreground(layer); remove_layer(layer):
        access the appropriate LayerContainer component to add/remove their own components.
    get_frame_borders(margins): return a pygame Rect constructed from the board's frame and the given margins.
    
    Key commands:
    esc: transitions to a pause state.
    """

    def __init__(self, main_layer=None, frame=None, bgcolor=config.BOARD_BGCOLOR, kill_margins=config.KILL_MARGINS, border_policies=None,
                 backgrounds=(), midgrounds=(), foregrounds=(), entities=(), music=None, **kwargs):
        """
        Set canvas / frame dimensions and declare layer containers.
        
        If main layer is not provided, use an empty Drawable with game canvas dimensions.
        If frame dimensions aren't explicitly set, try to default to the smallest between game canvas and main layer dimensions.
        Use main layer to calculate canvas dimensions.
        Add main layer as the first midground.
        Store music and default kill margins and border policies for this board.
        """
        self._music = music
        """The music for this board, applied on entry; can be None (no effect), file name or 'stop'|'fade' """
        main_layer = bake_obj(main_layer) if main_layer else Drawable(config.CANVAS_DIM)
        # Frame dimensions
        if not frame:
            # Defaults to minimum between game canvas and main layer dimensions (Asumes game is already initialized)
            frame = (min(config.CANVAS_DIM[0], main_layer.width), min(config.CANVAS_DIM[1], main_layer.height))
        
        # Layer containers.
        self._backgrounds = LayerContainer(components=backgrounds)
        """The container holding background layers (behind main layer)"""
        self._midgrounds = LayerContainer(components=(main_layer,)+midgrounds)
        """The container holding main and midground layers (in front of main layer; behind entities)"""
        self._foregrounds = LayerContainer(components=foregrounds)
        """The container holding foreground layers (in front of entities)"""
        # Note that LayerContainers are not KeyCommandReaders, so as it is currently objects inside layers can't receive commands.
        
        # Initialization and canvas dimensions.
        # Component order is important, as it'll determine update order (we want layers to update before entities).
        super().__init__(canvas=main_layer.dim, frame=frame, subsurface=True, bgcolor=bgcolor,
                         components=(self.backgrounds, self.midgrounds, self.foregrounds, *entities), **kwargs)
        
        # Borders
        self.kill_margins = repack4(kill_margins)
        """
        How far, in pixels, a sprite can stray from the frame before being killed (by default; can be overriden by each sprite).
        
        Can be passed as single value, (horizontal, vertical) or (left, top, right, bottom). These values CANNOT be infinite.
        """
        self.border_policies = repack4(border_policies)
        """
        How sprites should interact with borders (by default; can be overriden by each sprite).
        
        Can be passed as single value, (horizontal, vertical) or (left, top, right, bottom). Options:
            "solid": Treat border as a solid barrier.
            "wrap": Teleport sprite to opposite border.
            None: Do nothing.
        """
    
    @property
    def backgrounds(self):
        """Public reference to backgrounds container (read-only)."""
        return self._backgrounds
    
    @property
    def midgrounds(self):
        """Public reference to midgrounds container (read-only)."""
        return self._midgrounds
        
    @property
    def foregrounds(self):
        """Public reference to frontgrounds container (read-only)."""
        return self._foregrounds
    
    @property
    def main_layer(self):
        """Alias for first layer on midgrounds."""
        return self.midgrounds._drawable[0]
    
    @property
    def board(self):
        """Alias for self, for the sake of generalizing board access from game state."""
        return self
    
    def add_component(self, component):
        """Extend Component; make sure foregrounds stay on top."""
        super().add_component(component)
        if "foregrounds" in dir(self) and self.foregrounds in self:
            self.move_to_front(self.foregrounds)

    def add_background(self, layer):
        """Add a component to the backgrounds container."""
        self.backgrounds.add_component(layer)
        
    def add_midground(self, layer):
        """Add a component to the midgrounds container."""
        self.midgrounds.add_component(layer)
        
    def add_foreground(self, layer):
        """Add a component to the foregrounds container."""
        self.foregrounds.add_component(layer)
            
    def remove_layer(self, layer):
        """Remove a layer from its container, unless it's the first one on midgrounds."""
        if layer == main_layer:
            raise AttributeError("Board tried to delete its main layer.")
        for container in (self.backgrounds, self.midgrounds, self.foregrounds):
            container.remove_component(layer)
     
    def get_frame_borders(self, margins=(0,0,0,0)):
        """
        Return a pygame Rect constructed from the board's frame and the specified margins.
        
        Margins can be single value, (horizontal, vertical) or (left, top, right, bottom).
        """
        margins = repack4(margins)
        return Rect((self.frame.x - margins[0], self.frame.y - margins[1]), 
                    (self.frame.width + margins[0] + margins[2], 
                     self.frame.height + margins[1] + margins[3]))
    
    def _command_esc(self, press, **kwargs):
        """Enter a pause state on ESC press."""
        if press:
            self.game.set_state("pause", exit_state=self)
        # Referencing pause state by tag uncouples pause state class from board.
        # Do make sure there's a "pause" entry on the game's state dict though.
    
    def enter(self, start_label=None, **kwargs):
        """
        Set music and player starting position if needed.
        
        This method is called from Game().set_state()
        """
        if self._music:
            self.game.music = self._music
        if start_label and "player" in self.named:
            player = self.named["player"]
            # Try and set player position in reference to hitbox and without triggering lerp movement.
            if isinstance(self.main_layer, Layer):
                target_pos = self.main_layer.get_position_of(start_label)
                if target_pos:
                    player.pos = (target_pos[0] - player.hitbox.offset_x, target_pos[1] - player.hitbox.offset_y)
                    player._reset_data["attributes"]["pos"] = player.pos
            # Refactor this ASAP
            if isinstance(player, SidescrollerPlayer):
                player.check_commands("left", "right", "run")

    def leave(self, new_state=None, **kwargs):
        """Reset the board unless entering a pause state."""
        # This is meant to reference the base pause state class. Revise this if that changes.
        if not isinstance(new_state, PauseState):
            self.reset()

class TiledBoard(Board):
    """
    Extend Board to support interaction with tiled layers.
    
    Public methods:
    get_tile_at(coord): return tile object at specified coordinates on main layer.
    """
    
    def get_tile_at(self, coord):
        """Ask main layer for the tile object at the specified coordinates."""
        return self.main_layer.get_tile_at(coord)
        
class PlayerCam(Board):
    """
    Extend Board to move its frame following the player.
    
    Extends Updateable.update(dt).
    """

    def _adjust_frame(self):
        """Have the board frame follow the player around by trying to move the frame whenever the player tries to surpass the middle."""
        if "player" in self.named:
            player_x, player_y = self.named["player"].pos
            self.frame.x = min(max(player_x - int(self.frame.width/2), 0), self.draw_rect.width-self.frame.width)
            self.frame.y = min(max(player_y - int(self.frame.height/2), 0), self.draw_rect.height-self.frame.height)
    
    def update(self, dt):
        """Extend Board to perform _adjust_frame() on update time."""
        self._adjust_frame()
        super().update(dt)
        
class OnePlayerTiledBoard(TiledBoard, PlayerCam):
    """Combine TiledBoard with PlayerCam."""
    pass