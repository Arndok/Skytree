"""
Definition of classes that represent visible layers in a game space.

Classes:
Layer(Drawable, Updateable): a draw level within a board; supports parallax.
MovingLayer(Layer): a Layer that can be programmed to move automatically.
TiledLayer(Layer, Collidable): a Layer that manages a matrix of Tile objects.
MovingTiledLayer(TiledLayer, MovingLayer): combines MovingLayer and TiledLayer.

Variables used from config: LAYER_SPEED, TILE_FRAME_DURATION
"""

import warnings
from skytree.helpers import repack4, bake_obj
from skytree import config
from skytree.drawable import Drawable
from skytree.updateable import Updateable
from skytree.collidable import Collidable
from skytree.resource_manager import ResourceManager
from skytree.tile_objects import UpdateableTile, DrawableTile, CollidableTile, AnimatedTile
from skytree.timers import Timer, Delay, Cycle

class Layer(Drawable, Updateable, Collidable):
    """
    Extend Drawable and Updateable to represent layer within a Board.
    
    Inherits all behaviours from Component, Updateable, Positional and Drawable.
    Extends Updateable.update(dt).
    
    Supports parallax.
    
    Public methods:
    get_position_of(label): return the position of the component with name matching given label.
    """
    
    def __init__(self, canvas, parallax_adjust=(0,0,0,0), **kwargs):
        """
        Extend Drawable to store some parallax adjustments.
        
        Parallax adjustments are (trim_width, trim_height, offset_x, offset_y).
        Keep in mind that trims are ADDED (so for intended functionality, express them as negative).
        """
        super().__init__(canvas, **kwargs)
        self._parallax_adjust = parallax_adjust
        """Adjustments over canvas dimensions and position for the sake of parallax calculations (trim_width, trim_height, offset_x, offset_y)."""

    def update(self, dt):
        """
        Extend Updateable to calculate layer parallax.
        
        Adjust layer position = - layer_range * main_layer_pos / main_layer_range
        Will work propperly as long as layer's dimensions are at least as big as the frame.
        """
        self.x = (self.board.width - (self.width + self._parallax_adjust[0])) * self.board.frame.x / max(self.board.width - self.board.frame.width, 1) - self._parallax_adjust[2]
        self.y = (self.board.height - (self.height + self._parallax_adjust[1])) * self.board.frame.y / max(self.board.height - self.board.frame.height, 1) - self._parallax_adjust[3]
        super().update(dt)
    
    @property
    def board(self):
        """Current game board."""
        return self.game.state.board if self.game else None
        
    def get_position_of(self, label):
        """Return the position of the component with name matching given label; return None if absent."""
        return self.named[label].pos if label in self.named else None
        
class MovingLayer(Layer):
    """
    Extend Layer to apply automatic movement.
    
    Inherits all behaviours from Component, Updateable, Positional, Drawable and Layer.
    Extends Layer.update(dt) and Component.reset().
    
    Movement is done by linear interpolation. The only supported lerp function is linear movement.

    Notes on setters:
    Setting either _offset_x or _offset_y will trigger movement; setting _offset, however, will not.
    Setting _destination will update _origin and start a timer to be used to manage the movement on update time.
    """
    
    def __init__(self, canvas, destinations, speed=config.LAYER_SPEED, **kwargs):
        """
        Extend Layer to store a list of tuples in the form (destination point, waiting time at arrival).
        
        The sequence loops. Set waiting time to 0 to move immediately to next destination; set it to infinite on the last destination to stop the loop.
        Set destination to starting position to establish an initial delay (keep in mind that this will spill into the next iteration of the loop).
        """
        super().__init__(canvas, **kwargs)
        self._destinations = destinations
        """A list of tuples (destination point, waiting time at arrival)."""
        self._speed = speed
        """The speed of the layer (in pixels per millisecond)."""
        self._dest_idx = 0
        """The index that points to the current destination pair (point, waiting time)."""
        self._offset = self.pos
        """Object 2D movement offset."""
        self._origin = self.pos
        """The point from which the current lerp movement starts."""
        self._destination = destinations[0][0]
        """The point to which the current lerp movement goes."""
        
    @property
    def _offset(self):
        """Object 2D movement offset."""
        return tuple((self._offset_x, self._offset_y))
        
    @_offset.setter
    def _offset(self, value):
        """Teleport Layer to pos without triggering movement."""
        self._offset_x, self._offset_y = value
        self._destination_x, self._destination_y = value
    
    @property
    def _origin(self):
        """Object 2D origin point"""
        return tuple((self._origin_x, self._origin_y))
        
    @_origin.setter
    def _origin(self, value):
        self._origin_x, self._origin_y = value
        
    @property
    def _destination(self):
        """Object 2D destination point"""
        return tuple((self._destination_x, self._destination_y))

    @_destination.setter
    def _destination(self, value):
        """After setting destination, update origin as current position and start timer."""
        self._destination_x, self._destination_y = value
        self._origin = self._offset
        self.add_component(Timer(name="move_timer"))
        
    def _next_destination(self):
        """
        Set movement to next destination.
        
        Called when the layer arrives to its current destination,
        immediately or as a trigger to the waiting timer (if a wait time is set).
        """
        self._dest_idx = (self._dest_idx + 1) % len(self._destinations)
        self._destination = self._destinations[self._dest_idx][0]
        
    def update(self, dt):
        """
        Extend Layer to apply lerp movement.
        
        On arrival, call _next_destination if there's no waiting time or set a delay for calling this method if there is.
        """
        super().update(dt)
        # Apply movement
        if not "wait_timer" in self.named:
            # Linear lerp: origin + (destination - origin) * proportion
            # Proportion = be time elapsed * speed / distance, capped at 1.
            if self._offset_x != self._destination_x:
                old_offset_x = self._offset_x
                self._offset_x = self._origin_x + (self._destination_x-self._origin_x) * min(self.named["move_timer"].time * self._speed / (abs(self._destination_x-self._origin_x) * 1000), 1)
                self.vel_x = self._offset_x - old_offset_x # Register horizontal velocity
            if self._offset_y != self._destination_y:
                old_offset_y = self._offset_y
                self._offset_y = self._origin_y + (self._destination_y-self._origin_y) * min(self.named["move_timer"].time * self._speed / (abs(self._destination_y-self._origin_y) * 1000), 1)
                self.vel_y = self._offset_y - old_offset_y # Register vertical velocity

            if self._offset == self._destination and "move_timer" in self.named:
                # Destroy timer and update destination or set wait timer to do so.
                self.named["move_timer"].destroy()
                if self._destinations[self._dest_idx][1] == 0:
                    self._next_destination() # If waiting time is 0, go to next point
                elif self._destinations[self._dest_idx][1] == float("inf"):
                    self.add_component(Component(name="wait_timer")) # If waiting time is infinite, stop moving
                else:
                    self.add_component(Delay(self._destinations[self._dest_idx][1], self._next_destination, name="wait_timer"))
        # Apply offset (parallax already applied).
        self.x += self._offset_x
        self.y += self._offset_y
        
    def reset(self):
        """Extend Component to recover initial position and movement on reset."""
        if "move_timer" in self.named:
            self.named["move_timer"].destroy()
        super().reset()
        self._dest_idx = 0
        # The following two lines need to be executed in this order (see setters)
        self._offset = self.pos
        self._destination = self._destinations[0][0]
        
class TiledLayer(Layer):
    """
    Extend Layer and Collidable to represent a tiled space.
    
    Inherits all behaviours from Component, Updateable, Positional, Drawable, Collidable and Layer.
    Extends Layer.update(dt) and Drawable._render_components(canvas).
    Overrides get_position_of(label) to include tiles
    
    Has an object matrix; each entry may hold a drawable, updateable and/or collidable tile object.
    Matrix coordinates map (tile_dim:1) to 2d positions in space.
    Only visible tiles get rendered each frame.
    Only tiles within a margin of the screen borders and marked as always active get updated each frame.
    Only tiles matching a hitbox position are checked for collisions.
    The draw, update and collision systems are overriden to include the appropriate tile objects
      (see _render_components(canvas), update(dt), get_collisions(self, obj, obj_tags) and get_collisions_hitbox(self, obj, obj_tags))
    The point of doing this instead of just having the tile objects be Components is filtering the objects that actually do need to be
    taken in account each frame so we can save computational cost, especially on large layers.
    
    Public methods:
    get_tile_at(coord): return the tile object at the specified tile coordinates.
    delete_tile_at(coord): delete the tile object at the specified tile coordinates.
    put_tile_at(coord, obj): put the given tile object in the specified tile coordinates.
    """
    
    def __init__(self, tileset, tilemap, key2object, active_margins=(0,0,0,0), frame_duration=config.TILE_FRAME_DURATION, **kwargs):
        """
        Extend Subsurface, Updateable and WithResources to construct an object matrix.
        
        The tileset is going to be used by the tile objects. It's fetched by reference every time (so it can be changed on the fly
          with a noticeable effect and no extra computational cost).
        tilemap is the name of the file that defines the matrix; every row and every column must have the same length.
        key2object is the dictionary that defines how to convert symbols into objects, in the form {symbol: (Class, kwargs)}.
          Tile objects are baked on this init and they're also given a position, and a reference to this layer.
        active_margins will define how far an updateable tile can be from the screen border and still be updated.
          The value can be a single value, (horizontal, vertical) or (left, top, right, bottom). Value expresses tiles, not pixels.
        """
        self._rows = ResourceManager().get_file(tilemap)
        """The list of rows from the tilemap tile."""
        # Calculate canvas dimensions and finish super() initialization
        canvas_dim = ((len(self._rows[0].strip().split(",")) * tileset.width, 
                       len(self._rows) * tileset.height))
        super().__init__(canvas=canvas_dim, subsurface=True, **kwargs)
        
        self.tileset = bake_obj(tileset)
        """
        The tileset to be used by this layer's tile objects.
        
        It's not stored as a component; therefore, it may be shared with other layers.
        """
        self._objects = []
        """The tile object matrix."""
        self.named_tiles = {}
        """A dictionary of sets of tiles referenced by name."""
        self.tagged_tiles = {}
        """A dictionary of sets of tiles referenced by tag."""
        self._always_active = set({})
        """The set of updateable tiles that update every frame."""
        self._global_animations = set({})
        """The set of animated tiles whose animations are ticked by the layer's clock."""
        self._visible_tiles = set({})
        """The set of drawable tiles that are going to be drawn this frame."""
        self._active_tiles = set({})
        """The set of updateable tiles that are going to be updated this frame."""
        self._key2obj = key2object # dict str: (class, {kwargs})
        """The dictionary that defines how to convert symbols into objects ({symbol: (Class, kwargs)})."""
        self._active_margins = repack4(active_margins)
        """How far an updateable tile can be from the screen border and still be updated."""
        # Build the animation clock and bake the tile objects.
        self.add_persistent_component(Cycle(frame_duration, self._tick_anims))
        self._bake()
    
    @property
    def tile_width(self):
        """Tile width (from TileSet; read-only)."""
        return self.tileset.width
        
    @property
    def tile_height(self):
        """Tile height (from TileSet; read-only)."""
        return self.tileset.height
        
    @property
    def tile_dim(self):
        """Tile 2D dimensions (from TileSet; read-only)."""
        return tuple((self.tileset.width, self.tileset.height))
    
    def _bake(self):
        """
        Build tile objects and populate object matrix.
        
        Clear the matrix, dictionaries and sets; traverse the tilemap lines and build the tile objects according
          to each symbol and the key2obj dictionary. Include a reference to the appropriate position and this
          layer in each tile object and add it to the matrix. Add the object to the named / tagged tiles dictionaries,
          global animation and always active sets if needed.
        Raise AttributeError if an object's name is already in use.
        """
        # Clear collections.
        self._objects = []
        self.named_tiles = {}
        self.tagged_tiles = {}
        self._always_active = set({})
        self._global_animations = set({})
        # Traverse tilemap (self._rows)
        for i_row in range(len(self._rows)):
            self._objects.append([])
            vals = self._rows[i_row].strip().split(",")
            for i_val in range(len(vals)):
                tile_key = vals[i_val].strip()
                if tile_key in self._key2obj:
                    # Build tile object using key2obj
                    Tile = self._key2obj[tile_key][0]
                    kwa = self._key2obj[tile_key][1] if len(self._key2obj[tile_key]) == 2 else {}
                    pos = [i_val * self.tile_width, i_row * self.tile_height]
                    # Include reference to the appropriate position and this layer
                    obj = Tile(owner=self, pos=pos, **kwa)
                    self._objects[-1].append(obj)
                    # Named and tiled objects.
                    if obj.name:
                        if obj.name in self.named_tiles:
                            raise AttributeError("Tile tried to use a name that's already in use.")
                        else:
                            self.named_tiles[obj.name] = obj
                    for tag in obj.tags:
                        if tag in self.tagged_tiles:
                            self.tagged_tiles[tag].append(obj)
                        else:
                            self.tagged_tiles[tag] = [obj]
                    # Tile objects animated with layer clock.
                    if isinstance(obj, AnimatedTile) and not obj.anim_timer:
                        self._global_animations.add(obj)
                    # Tile objects that update every frame.
                    if isinstance(self._objects[-1][-1], UpdateableTile) and self._objects[-1][-1].always_active:
                        self._always_active.add(self._objects[-1][-1])
                else:
                    # If the key doesn't point to any kind of object, leave an empty space in the matrix.
                    self._objects[-1].append(None)
    
    def _prepare_tiles(self, frame):
        """
        Use the given frame (intended for board frame) to calculate visible and active tiles.
        
        Visible tiles are drawables inside the frame
        Active tiles are, in this step, updateables inside the active margins over the frame.
          Always-active tiles are included on update time.
        """
        # Clear lists
        self._active_tiles = set({})
        self._visible_tiles = set({})
        # Calculate ranges (and name them so that the next section can be read without wanting to headbutt a wall)
        first_visible_x = max(int((frame.left - self.x)/self.tile_width), 0)
        first_active_x = max(first_visible_x - self._active_margins[0], 0)
        first_visible_y = max(int((frame.top - self.y)/self.tile_height), 0)
        first_active_y = max(first_visible_y - self._active_margins[1], 0)
        last_visible_x = min(int((frame.right - self.x)/self.tile_width), len(self._objects[0])-1)
        last_active_x = min(last_visible_x + self._active_margins[2], len(self._objects[0])-1)
        last_visible_y = min(int((frame.bottom - self.y)/self.tile_height), len(self._objects)-1)
        last_active_y = min(last_visible_y + self._active_margins[3], len(self._objects)-1)
        # Iterate over active range
        for i in range(first_active_x, last_active_x+1):
            for j in range(first_active_y, last_active_y+1):
                obj = self._objects[j][i]
                # Set object as active if updateable
                if isinstance(obj, UpdateableTile):
                    self._active_tiles.add(obj)
                # Set object as visible if drawable and in visible range
                if isinstance(obj, DrawableTile) and i >= first_visible_x and i <= last_visible_x \
                                                 and j >= first_visible_y and j <= last_visible_y:
                    self._visible_tiles.add(obj)
    
    def _get_tile_collisions(self, hitbox, obj_tags):
        """
        Test collisions with tile objects on tiles overlapping with the hitbox.
        
        Tile coordinates are local to the layer and that's somewhat tricky.
          TiledLayers are subsurfaces, so tiles are drawn on it and then it's drawn on the board.
          This means that we don't have to worry about the tiles' drawing process.
          Conversely, layer position must be taken into account before using collision coordinates.
          We can get the appropriate final positions using the tile's position (as opposed to its hitbox);
          their positions remain unaffected and we won't accumulate the offset.
        Return a set of colliding tile objects.
        """
        # Calculate tiles
        leftmost = max(int((hitbox.left-self.x) / self.tile_width),0)
        rightmost = min(int((hitbox.right-self.x) / self.tile_width)+1, len(self._objects[0]))
        topmost = max(int((hitbox.top-self.y) / self.tile_height),0)
        bottommost = min(int((hitbox.bottom-self.y) / self.tile_height)+1, len(self._objects))
        possible = []
        # Iterate and fetch objects with a hitbox.
        for i in range(topmost, bottommost):
            for j in range(leftmost, rightmost):
                if isinstance(self._objects[i][j], CollidableTile):
                    # Relocate object hitbox using layer position, object position and hitbox offset.
                    self._objects[i][j].hitbox.x = self._objects[i][j].x + self.x + self._objects[i][j].hitbox.offset_x
                    self._objects[i][j].hitbox.y = self._objects[i][j].y + self.y + self._objects[i][j].hitbox.offset_y
                    possible.append(self._objects[i][j])
        return set(filter(lambda x: any(x.tags.intersection(obj_tags)) and x.hitbox.collides(hitbox), possible))  
    
    def _tick_anims(self):
        """Tick the animation of all subscribed tiles; triggered by layer's animation timer."""
        for tile in self._global_animations:
            tile.tick_anim()
    
    def _render_components(self, canvas):
        """Override Drawable to include visible tiles"""
        for obj in self._visible_tiles: 
            obj.draw(canvas)
        super()._render_components(canvas)
    
    def get_tile_at(self, coord):
        """Return the tile object at the specified tile coordinates or None if there's no object there or the coordinates are outside the matrix."""
        if coord[0] < 0 or coord[0] >= len(self._objects[0]) or coord[1] < 0 or coord[1] >= len(self._objects):
            # Coordinates outside the object matrix. You gaze into the abysm --you get None.
            return None
        else:
            return self._objects[coord[1]][coord[0]]
        
    def delete_tile_at(self, coord):
        """Delete the tile object at the specified tile coordinates."""
        obj = self.get_tile_at(coord)
        if obj:
            if obj.name in self.named_tiles:
                del self.named_tiles[obj.name]
            for tag in obj.tags:
                if len(self.tagged_tiles[tag]) > 1:
                    self.tagged_tiles[tag].remove(obj)
                else:
                    del self.tagged_tiles[tag]
        
    def put_tile_at(self, coord, obj):
        """
        Put the tile object in the specified tile coordinates, replacing existing object if any.
        
        Raise AttributeError if the object's name is already in use.
        """
        self.delete_tile_at(coord)
        self._objects[coord[1]][coord[0]] = obj
        if obj.name in self.named_tiles:
            raise AttributeError("Tile tried to use a name that's already in use.")
        else:
            self.named_tiles[obj.name] = obj
        for tag in obj.tags:
            if tag in self.tagged_tiles:
                self.tagged_tiles[tag].append(obj)
            else:
                self.tagged_tiles[tag] = [obj]
        
    def get_position_of(self, label):
        """
        Return the position of the component or tile with name matching given label; return None if absent.
        
        Prioritizes components.
        """
        return self.named[label].pos if label in self.named else \
               self.named_tiles[label].target_pos if label in self.named_tiles else None
        
    def update(self, dt):
        """Override Updateable to include active tiles, both currently and always active."""
        self._prepare_tiles(self.board.frame)
        for obj in self._active_tiles.union(self._always_active): obj.update(dt)
        super().update(dt)
        
    def get_collisions(self, obj, obj_tags=None):
        """Extend Collidable to include tile collisions."""
        return super().get_collisions(obj, obj_tags).union(self._get_tile_collisions(obj.hitbox, obj_tags))
        
    def get_collisions_hitbox(self, hitbox, obj_tags):
        """Extend Collidable to include tile collisions."""
        return super().get_collisions_hitbox(hitbox, obj_tags).union(self._get_tile_collisions(hitbox, obj_tags))
                    
    def reset(self):
        """Extend Component to re-bake all tile objects unless prevented by the use of tag 'persistent_tiles'."""
        if not "persistent_tiles" in self.tags:
            self._bake()
        super().reset()
        
class MovingTiledLayer(TiledLayer, MovingLayer):
    """Combine MovingLayer with TiledLayer"""
    pass
        