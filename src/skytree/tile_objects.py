"""
Definition of objects that can be used as tiles in a TiledLayer.

Tiles are not Components, but their inheritance structure mirror some core Component behaviours.

Classes:
Tile: the base class for tile objects.
UpdateableTile(Tile): a Tile that can do some work on each frame.
DrawableTile(Tile): a Tile with a visible appearance.
CollidableTile(Tile): a Tile with a Hitbox.
AnimatedTile(DrawableTile, UpdateableTile): a Tile with an animation.
DraColTile(DrawableTile, CollidableTile): combines DrawableTile with CollidableTile.
AniColTile(AnimatedTile, CollidableTile): combines AnimatedTile with CollidableTile.
StartTile(Tile): a Tile with a target position for a sprite to place in.
ExitTile(CollidableTile): a collidable Tile that holds information for state transitions.
PathTile(DrawableTile): a Tile that holds information for a sprite to traverse a space.
StageTile(PathTile, StartTile, Stage): a Tile that both links to a Stage in a map and acts as one.
CheckpointTile(StartTile, CollidableTile): a Tile that has checkpoint functionality for a Stage.
VisibleCheckpointTile(CheckpointTile, DrawableTile): a CheckpointTile with a visible appearance.
SpawnerTile(UpdateableTile): a tile that can spawn sprites.
DraSpaTile(DrawableTile, SpawnerTile): combines DrawableTile with SpawnerTile.

Variables used from config: TILE_FRAME_DURATION
"""

from skytree.helpers import repack2, bake_obj
from skytree import config
from skytree.collidable import RectHB
from skytree.timers import Cycle, Countdown
from skytree.stage import Stage
from skytree.resource_manager import ResourceManager

class Tile:
    """
    An object representing a tile on a tiled layer.
    
    It is not a Component, so it can't leverage the Component system.
    """
    
    def __init__(self, owner, pos, name=None, tags=(), **kwargs):
        """
        Store owner (a tile layer), position and possibly name and/or tags.
        
        Tile constructor will always receive an owner and position.
        Once set by the layer, position shouldn't be changed anymore.
        """
        self._owner = owner
        """Tile object's owner object."""
        self._name = name
        """Tile object's name."""
        self._tags = set(tags)
        """Tile object's tags."""
        self.pos = pos
        """Tile object's 2D position."""
        
    @property
    def owner(self):
        """Public reference to the tile object's owner (read-only)."""
        return self._owner
    
    @property
    def name(self):
        """Public reference to the object's name (read-only)."""
        return self._name
    
    @property
    def tags(self):
        """Public reference to the object's tags (read-only)."""
        return self._tags
        
    @property
    def pos(self):
        """Tile object's 2D position."""
        return tuple((self.x, self.y))
        
    @pos.setter
    def pos(self, value):
        self.x, self.y = value
        
    @property
    def width(self):
        """Tile object's width (from owner's tileset)."""
        return self._owner.tileset.width
    
    @property
    def height(self):
        """Tile object's height (from owner's tileset)."""
        return self._owner.tileset.height
        
    @property
    def dim(self):
        """Tile object's 2D dimensions (from owner's tileset)."""
        return tuple((self._owner.tileset.width, self._owner.tileset.height))
    
    @property
    def tile_x(self):
        """Tile object's x-coordinate."""
        return int(self.x / self.width)
        
    @property
    def tile_y(self):
        """Tile object's y-coordinate."""
        return int(self.y / self.height)
        
    @property
    def coords(self):
        """Tile object's 2D coordinates."""
        return tuple((int(self.x / self.width), int(self.y / self.height)))

class UpdateableTile(Tile):
    """
    Extend Tile to be able to update.
    
    Inherits all Tile behaviour.
    
    Public methods:
    update(dt): receive delta time and do some work every frame the tile's active.
      On each frame, this method is called by owner if either its position is close
      enough to the board frame or it is marked as always active.
    """
    
    def __init__(self, always_active=False, **kwargs):
        """Excend Tile to include always_active flag (False by default)."""
        super().__init__(**kwargs)
        self.always_active = always_active
        """Whether or not this object updates every frame, disregarding its position."""
        
    def update(self, dt):
        """Implement on subclasses to do some work on every frame this object's active.
        
        dt is delta time (time elapsed since previous frame), passed by Game at the root level.
        """
        pass

class DrawableTile(Tile):
    """
    Extend Tile to be able to be drawn.
    
    Inherits all Tile behaviour.
    
    Public methods:
    draw(canvas): renders on canvas frame of the tileset pointed to by idx.
    """
    
    def __init__(self, idx, **kwargs):
        """Extend Tile to store a tileset frame index."""
        super().__init__(**kwargs)
        self._idx = idx
        """An index for the frame in the tileset to be drawn for this object."""
        
    def draw(self, canvas):
        """Render on given canvas the frame of the tileset pointed to by self._idx."""
        self._owner.tileset.hot_draw(canvas, self.pos, self._idx)
        
class CollidableTile(Tile):
    """
    Extend Tile to have a hitbox.

    Inherits all Tile behaviour.
    
    Collidable TileObjects don't look for other collidables.
    It's the colliding entity's responsibility to check the tile's tags and react accordingly.
    Also, keep in mind that when receiving a tile object in the context of a collision check,
      you might be more interested on its owner (such as when updating a sprite's inertial frame of reference).
    """
    
    def __init__(self, hb_dim=None, hb_offset=(0,0), **kwargs):
        """
        Extend tile to construct a rectangular hitbox.
        
        Hitbox dimensions default to tile dimensions and hitbox offset defaults to (0, 0).
        A CollidableTile's hitbox' dimensions and offset cannot be changed.
        """
        super().__init__(**kwargs)
        if not hb_dim:
            hb_dim = self._owner.tile_dim
        else:
            hb_dim = repack2(hb_dim)   
        self.hitbox = RectHB(self.pos, hb_dim, offset=hb_offset)
        """This tile's hitbox."""
            
class AnimatedTile(DrawableTile, UpdateableTile):
    """
    Extend DrawableTile and UpdateableTile to have the tile be animated.
    
    Inherits all behaviour from Tile, DrawableTile and UpdateableTile.
    Overrides DrawableTile.draw(canvas).
    
    Allows only a single animation as a loop of frames with equal time.
    
    Public methods:
    tick_anim(): advances one animation frame. Can be called by an external timer.
    """

    def __init__(self, frame_duration=config.TILE_FRAME_DURATION, local_timer=False, **kwargs):
        """
        Extend superclasses to define an animation clock and index.
        
        idx is a list of indices for the frames in the tileset that form the animation.
        local_timer defines whether the tile makes its own timer or subscribes to its layer's
        """
        super().__init__(**kwargs)
        self._anim_timer = Cycle(frame_duration, self.tick_anim) if local_timer else None
        """This tile's animation timer."""
        self._anim_index = 0
        """The index for the current frame in the tileset."""
        
    @property
    def anim_timer(self):
        """Public reference to the tile object's animation timer if present (read-only)."""
        return self._anim_timer

    def update(self, dt):
        """Update the animation clock."""
        if self._anim_timer:
            self._anim_timer.update(dt)
        
    def draw(self, canvas):
        """Override DrawableTile to render on canvas frame of the tileset pointed to by idx[_anim_index]."""
        self._owner.tileset.hot_draw(canvas, self.pos, self._idx[self._anim_index])
    
    def tick_anim(self):
        """
        Advance the animation index.
        
        Can be called by this object's animation timer or its owner's.
        """
        self._anim_index = (self._anim_index + 1) % len(self._idx)
            
class DraColTile(DrawableTile, CollidableTile):
    """Combines DrawableTile with CollidableTile."""
    pass
                         
class AniColTile(AnimatedTile, CollidableTile):
    """Combines AnimatedTile with CollidableTile."""
    pass

class StartTile(Tile):
    """
    Extend Tile to hold a target position and ensure a unique name.
    
    Inherits all Tile behaviour.
    
    Signals towards a point where a sprite (i.e the player) should be placed on board entry.
    Target position can be set as absolute (with target_pos) or relative to the tile's position (target_offset).
    If none of those are passed as arguments, target position defaults to tile position.
    """
    
    def __init__(self, owner, target_pos=None, offset=(0,0), name=None, **kwargs):
        """
        Extend Tile; store an offset and set a tag for later identification.
        
        If a unique (at the moment) name is not provided, use 'start{n}' 
        with n being the first int resulting in a unique name.
        Caution is advised when using this behaviour:
        - The resulting name could be set manually in a tile object instantiated later
          (an exception would be raised).
        - More importantly, the resulting name depends on closeness to origin and will
          change if tiles are moved around.
        Points of entry into a board are referenced by object position. Keeping in mind that
        origin in Pygame is (left, top), this means that these points are coupled with sprite
        height. If you want to account for player sprites with different heights, you need to
        do that on Board.enter.
        """
        if not name:
            i = 1
            while "start"+str(i) in owner.named_tiles:
                i += 1
            name = "start"+str(i)
        super().__init__(owner=owner, name=name, **kwargs)
        self.target_pos = target_pos if target_pos else (self.x+offset[0], self.y+offset[1])
    
class ExitTile(CollidableTile):
    """
    Extend CollidableTile to hold a board and start position labels to transition to on player collision.
    
    Inherits all Tile and CollidableTile behaviour.
    """
    
    def __init__(self, dest_board=None, start_label=None, tags=(), **kwargs):
        """
        Extend CollidableTile; store destination board and start label.
        
        Exit references are going to be used on Game.set_state, so destination board can either be
        an actual game state or a string label pointing to it on the Game.states dictionary.
        The tag "exit" is hardcoded into this object.
        """
        super().__init__(tags=tags+("exit",), **kwargs)
        self.dest_board = dest_board
        self.start_label = start_label

class PathTile(DrawableTile):
    """
    Extend DrawableTile to hold valid direction information and a traversable status.
    
    Inherits all Tile and DrawableTile behaviour.
    Extends DrawableTile.draw(canvas).
    
    Valid directions are expressed as present or absent directional tags ("left", "up", "right", "down").
    Traversable status is a boolean attribute, and it defines both whether a sprite can move into this tile
      and whether the tile's image is drawn or not.
    
    Public methods:
    open(): make this tile traversable and propagate the command to all reachable path tiles.
    """
    
    def __init__(self, traversable=False, **kwargs):
        """Extend DrawableTile to store a traversable flag (defaults to False)."""
        super().__init__(**kwargs)
        self.traversable = traversable
        """Whether or not this tile's traversable and its image is drawn."""
        
    def open(self):
        """Make this tile traversable and propagate the command to all reachable path tiles."""
        if self.traversable:
            return # Short out if already traversable
        self.traversable = True
        if "left" in self.tags:
            self._owner.get_tile_at((self.tile_x-1, self.tile_y)).open()
        if "up" in self.tags:
            self._owner.get_tile_at((self.tile_x, self.tile_y-1)).open()
        if "right" in self.tags:
            self._owner.get_tile_at((self.tile_x+1, self.tile_y)).open()
        if "down" in self.tags:
            self._owner.get_tile_at((self.tile_x, self.tile_y+1)).open()
        
    def draw(self, canvas):
        """Extend DrawableTile to only draw this tile if it's currently traversable."""
        if self.traversable:
            super().draw(canvas)

class StageTile(PathTile, StartTile, Stage):
    """
    Extend PathTile, StartTile and Stage to represents a stage in an overworld map.
    
    Inherits all behaviour from Tile, DrawableTile, PathTile, StartTile and Stage.
    Overrides PathTile.open().
    
    As this object inherits not only from Tile objects but also from Stage, it can hold
      checkpoint information and work as an active stage.
    
    Public methods:
    beat(exit_label, **kwargs): set image for a complete stage and open the appropriate path. 
    """

    def __init__(self, idx, entry_state, start_label="start1", **kwargs):
        """Extend PathTile, StartTile and Stage to store indices for both pending and complete stage."""
        super().__init__(idx=idx[0], **kwargs)
        Stage.__init__(self, entry_state, start_label, exit_label=self.name)
        self._idcs = idx
        """The indices for pending and complete stage on this tile's owner's tileset."""

    def open(self):
        """Override PathTile to avoid propagating the command to neighbouring paths."""
        self.traversable = True

    def beat(self, exit_label, **kwargs):
        """Extend Stage to set 'complete' image and open path indicated by exit_label."""
        super().beat(exit_label=exit_label, **kwargs)
        self._idx = self._idcs[1]
        self._owner.get_tile_at({"left":(self.tile_x-1, self.tile_y),
                                "up":(self.tile_x, self.tile_y-1),
                                "right":(self.tile_x+1, self.tile_y),
                                "down":(self.tile_x, self.tile_y+1)}[exit_label]).open()

class CheckpointTile(StartTile, CollidableTile):
    """
    Extend StartTile and CollidableTile to hold a starting position and an active status.
    
    Inherits all behaviour from Tile, CollidableTile and StartTile.
    
    Notes on setters:
    Setting this object's active status will bind it to or unbind it from the active stage.
    """
    def __init__(self, owner, board, name="checkpoint", tags=(), **kwargs):
        """
        Extend superclasses to hold a reference to the active game and another to a specific board.
        
        The tag "checkpoint" is hardcoded into this object.
        """
        self.board = board
        """The Board this checkpoint points to."""
        self._sound = ResourceManager().get_sound(config.SOUND_ACTIVATE_CHECKPOINT) if config.SOUND_ACTIVATE_CHECKPOINT else None
        """A sound to play on activation."""
        super().__init__(owner=owner, name=name, tags=tags+("checkpoint",), **kwargs)
        
    @property
    def game(self):
        """The active Game instance (from owner)."""
        return self._owner.game
        
    @property
    def active(self):
        """Return True if this object's data matches the checkpoint in the active stage; False otherwise."""
        return self.game is not None and \
               self.game.active_stage is not None and \
               self.game.active_stage.checkpoint is not None and \
               self.game.active_stage.checkpoint.name == self.name and \
               self.game.active_stage.checkpoint.board == self.board
    
    @active.setter
    def active(self, value):
        """Bind this object to the active stage if the value is True; unbind it otherwise."""
        if value:
            if not self.active:
                self.game.active_stage.checkpoint = self
                if self._sound:
                    self._sound.play()
        elif self.active:
            self.game.active_stage.checkpoint = None

class VisibleCheckpointTile(CheckpointTile, DrawableTile):
    """
    Extend CheckpointTile to have an image, with two variants according to active status.
    
    Inherits all behaviour from Tile, DrawableTile, CollidableTile, StartTile and CheckpointTile.
    Overrides DrawableTile.draw(canvas).
    """
    def __init__(self, idx, **kwargs):
        self._idcs = idx
        """The indices for active and inactive checkpoint on this tile's owner's tileset."""
        super().__init__(idx=None, **kwargs)
    
    def draw(self, canvas):
        """Extend Drawable to select the approppriate image before drawing."""
        self._idx = self._idcs[self.active]
        super().draw(canvas)
            

class SpawnerTile(UpdateableTile):
    """
    Extend UpdateableTile to be able to spawns objects.
    
    Inherits all Tile and UpdateableTile behaviours.
    Implements UpdateableTile.update().
    
    Holds one object type. Allows for an object limit, cooldown between spawns,
    an initial delay and a direction for the movement of the spawned objects.
    The direction can be absolute or towards the center of the frame either horizontally or vertically.
    
    Public methods:
    spawn(): build the object, add it to the board and spawned set and reset cooldown.
    notify_death(obj): remove the object from the spawned set.
    """
    
    def __init__(self, obj, offset=(0,0), obj_limit=1, cooldown=float("inf"), first_delay=0, direction=None, tags=(), **kwargs):
        """
        Extend UpdateableTile to store the necessary information to spawn the given object in the intended way.
        
        obj is the object to be spawned --unbaked; in the form (Type, {kwargs})
        """
        super().__init__(tags=tags+("spawner",), **kwargs)
        self._obj = obj
        """The type of object to be spawned."""
        self._spawned = set({})
        """A set of spawned objects that are currently alive."""
        self._offset = offset
        """An offset for the spawn point in relation to the tile's position."""
        self._obj_limit = obj_limit
        """How many spawned objects can exist at the same time for this tile."""
        self._cooldown = Countdown(cooldown)
        """A timer that ensures a minimum amount of time between spawns."""
        self._cooldown.time = first_delay
        self._direction = direction
        """
        The direction in which the spawned objects should start moving.
        
        Allows: 'left', 'up', 'right', 'down', 'variable_horizontal' and 'variable_vertical' (the latter two towards the center of the frame).
        """
    
    def update(self, dt):
        """
        Perform a spawn whenever the conditions are right.
        
        Conditions: the number of spawned objects are below this tile's object limit and the cooldown time is at or below zero.
        """
        self._cooldown.update(dt)
        if len(self._spawned) < self._obj_limit and self._cooldown.time <=0:
            self.spawn()
    
    def spawn(self):
        """
        Build object, add it to the board and to the spawned set and reset cooldown.
        
        Position is taken from tile position and offset. This tile object is passed to the spawned object as "spawner".
        Direction, as stated on class and init docstrings, can be set as absolute or relative to the frame
          (going towards its center either horizontally or vertically).
        """
        kwargs = {"pos":(self.x + self._offset[0], self.y + self._offset[1]), "spawner":self, **self._obj[1]}
        if self._direction:
            if self._direction == "variable_horizontal":
                kwargs["direction"] = "left" if self.x + self.width/2 > self._owner.board.frame.centerx else "right"
            elif self._direction == "variable_vertical":
                kwargs["direction"] = "up" if self.y + self.height/2 > self._owner.board.frame.centery else "down"
            else:
                kwargs["direction"] = self._direction
        obj = self._obj[0](**kwargs)
        self._owner.board.add_component(obj)
        self._spawned.add(obj)
        self._cooldown.reset()
        
    
            
    def notify_death(self, obj):
        """
        Remove the given object from the spawned set.
        
        This method is called from the spawned object's destroy method.
        """
        self._spawned.discard(obj)
        
class DraSpaTile(DrawableTile, SpawnerTile):
    """Combines DrawableTile with SpawnerTile."""
    pass
