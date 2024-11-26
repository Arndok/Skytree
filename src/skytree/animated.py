"""
Definition of classes that use TileSets to support frame-by-frame animation.

Classes:
Animated(Drawable, Updateable): holds a tileset, methods to select its drawable frame and an animation timer.
Particle(Animated): plays a single animation and then self-destructs.

Variables used from config: SPRITE_FRAME_DURATION
"""

from skytree.helpers import bake_obj
from skytree import config
from skytree.drawable import Drawable
from skytree.updateable import Updateable
from skytree.timers import Cycle, Delay

class Animated(Drawable, Updateable):
    """
    Extend Drawable and Updateable to support frame-by-frame animation.
    
    Inherits all behaviour from Component, Positional, Updateable and Drawable.
    Extends Drawable.draw(canvas).
    
    Animation frames are fetched from a TileSet.
    
    Public methods:
    tick_anim(): advance the animation frame (triggered by an animation timer).
    lock_anim(): disable animation changes.
    unlock_anim(): enable animation changes.
    draw(canvas): set the appropriate frame in the tileset and draw.
    
    Notes on setters:
    Setting tileset will update components and reset_data.
    Setting anim will reset the animation.
    """
    
    def __init__(self, tileset, anims=None, first_anim=None, frame_duration=config.SPRITE_FRAME_DURATION, local_timer=True, **kwargs):
        """
        Extend Drawable to construct tileset if needed, set animation timer, store animations and set first active animation.
        
        tileset may be a Tileset object or a (Type, {kwargs}) tuple.
        anims is a dictionary of animations data, structured like this: {name: ((tileset idx, duration in frames), ...), ...}
          Duration in frames can be float("inf") (use at the end to prevent looping).
          If left empty, defaults to a continuous looped animation using all tiles in the tileset, labeled as "default".
        first_anim is the identifying label of the first animation that should be set.
        frame_duration is expressed in milliseconds.
          Can be set to float("inf") to have a static image with a selectable tile, but that would be best achieved by setting local_timer = False.
        local_timer indicates whether the object should build a clock to tick its animation. Defaults to True.
        """
        self._tileset = bake_obj(tileset)
        """A set of selectable tiles."""
        super().__init__(canvas=self._tileset.dim, **kwargs)
        self.add_persistent_component(self._tileset)
        
        self.anim_lock = False
        """Whether animation changes are locked or not."""
        
        # Set animation timer.
        if local_timer:
            self.add_persistent_component(Cycle(frame_duration, self.tick_anim, name="anim_timer"))
        # If local_timer is set to False, the animation won't be ticked unless an external object assumes that responsibility.

        # Store animations.
        self.anims = anims if anims else {"default":tuple(((i, 1) for i in range(len(self._tileset.frames))))}
        """A dictionary of named animations, expressed as tuples of (rect_idx, duration_in_frames) pairs."""
        
        # Set current animation.
        self._anim = None
        """The name of the current animation."""
        self._anim_frame_counter = 0
        """The current frame of the animation."""
        self.anim_idx = 0
        """The index of the tuple that holds the current tileset index."""
        self.anim = first_anim if first_anim else "default" if "default" in self.anims else list(anims)[0]
        # First animation = stated anim if present, otherwise "default" if present, otherwise random ¯\_(ツ)_/¯
        self._reset_data["attributes"]["anim"] = self.anim
        
    @property
    def tileset(self):
        """Object's tileset."""
        return self._tileset
        
    @tileset.setter
    def tileset(self, value):
        """Remove previous tileset and add this one."""
        if value == self._tileset:
            return
        if self._tileset:
            self.remove_persistent_component(self._tileset)
        self._tileset = value
        if value:
            self.add_persistent_component(self._tileset)
    
    @property
    def tile_width(self):
        """Tile width (from tileset)."""
        return self._tileset.width
        
    @property
    def tile_height(self):
        """Tile height (from tileset)."""
        return self._tileset.height
        
    @property
    def tile_dim(self):
        """Tile dimensions (from tileset)."""
        return tuple((self._tileset.width, self._tileset.height))
        
    @property
    def anim(self):
        """Public reference to current animation."""
        return self._anim
        
    @anim.setter
    def anim(self, value):
        """
        Set stated animation as active.
        
        Raise KeyError if the animation is not in self.anims.
        Reset animation index, timer and rame counter.
        """
        # Raise error if value is not present.
        if not value in self.anims: 
            raise KeyError("Animated sprite tried to load absent animation {a}. Valid animations: {aa}".format(a=value, aa=self.anims.keys()))
        # Short out if value is already current animation or if animation lock is active.
        if self._anim == value or self.anim_lock: 
            return
        # Set current animation and reset the process.
        self._anim = value
        self.anim_idx = 0
        if self._anim_timer:
            self._anim_timer.reset()
        self._anim_frame_counter = 0
        
    @property
    def _anim_timer(self):
        """Animation timer (read-only)."""
        return self._named.get("anim_timer", None)
        
    def tick_anim(self):
        """Advance animation (called by the animation timer)."""
        self._anim_frame_counter += 1
        if self._anim_frame_counter >= self.anims[self.anim][self.anim_idx][1]:
            self.anim_idx = (self.anim_idx + 1) % len(self.anims[self.anim])
            self._anim_frame_counter = 0
            
    def lock_anim(self):
        """Prevent animation from being changed."""
        self.anim_lock = True
        
    def unlock_anim(self):
        """Stop preventing animation from being changed."""
        self.anim_lock = False
            
    def draw(self, canvas):
        """Extend Drawable to set the appropriate frame in the tileset before drawing."""
        self._tileset.set_render(self.pos, self.anims[self.anim][self.anim_idx][0])
        super().draw(canvas)
        
class Particle(Animated):
    """An object with an animation that plays once, then it self-destroys."""
    
    def __init__(self, tileset, frame_duration=config.SPRITE_FRAME_DURATION, **kwargs):
        """Extend superclass to add a countdown that destroys itself when the animation finishes."""
        super().__init__(tileset, frame_duration=frame_duration, **kwargs)
        self.add_component(Delay(sum(x for _,x in self.anims[self.anim])*frame_duration, self.destroy))