"""
Definition of game entity classes.

Sprites are constructed mostly through multiple inheritance.
The Sprite base class defines an update script with methods that can be extended or overriden by subclasses.
Other standard methods that can be coded on Sprite subclasses are collision methods and commands
  (see documentation on collidable.Collidable and key_commands.KeyCommandReader respectively).
A sprite can inherit from classes that define:
- Movement methods.
- Collision methods (solid or otherwise).
- Actions.
- Command reading methods (map these to actions).
- Behaviours.

Classes:
Sprite(Animated, Collidable, Updateable): base class for game entities.
    ### Movement controlled through velocity
VelocityMovement(Sprite): base class for Sprites that move by applying velocity to movement.
GravityBound(VelocityMovement): a Sprite that is affected by gravity.
AccelerationMovement(VelocityMovement): a Sprite with an acceleration that affects their velocity.
AcceleratedHorizontal(AccelerationMovement): a Sprite with horizontal acceleration control.
AcceleratedVertical(AccelerationMovement): a Sprite with vertical acceleration control.
FixedBounce(VelocityMovement): a Sprite that bounces with a fixed force on a solid collision.
    ### Actions for a VelocityMovement Sprite
AccelerationSpeedUp(AccelerationMovement): a Sprite that can toggle an acceleration speedup.
SidescrollerWalk(AcceleratedHorizontal, GravityBound): a Sprite with horizontal walk actions.
SidescrollerJump(SidescrollerWalk): s Sprite with a jump action on a side view.
SidescrollerCrouch(SidescrollerWalk): a Sprite with a crouch action.
TopDownWalk(AcceleratedHorizontal, AcceleratedVertical): a Sprite with four-directional walk actions.
Hover(AcceleratedHorizontal, AcceleratedVertical): a Sprite with orthogonal hover and perpendicular oscillation.
    ### Movement controlled through linear interpolation
LerpMovement(Sprite): base class for Sprites that move by linear interpolation.
GridMovement(LerpMovement): a LerpMovement sprite that moves on a grid.
    ### Sample player sprites
SidescrollerPlayer(SidescrollerJump, SidescrollerCrouch, AccelerationSpeedUp, KeyCommandReader):
  a Sprite that maps commands to sidescroller actions.
TopDownPlayer(TopDownWalk, AccelerationSpeedUp, KeyCommandReader): a Sprite that maps commands to
  four-directional movement actions.
GridPlayer(GridMovement, KeyCommandReader): a Sprite that maps commands to grid movement actions.
MapPlayer(GridPlayer): a GridPlayer that includes an action for entering a stage from a StageTile.
    ### Sample enemy sprites
SsWalkingEnemy(SidescrollerWalk): base class for a sidescroller enemy sprite; moves automatically and
  turns around when colliding with a solid.
SsCautiousEnemy(SsWalkingEnemy): a sidescroller walking enemy that also turns around when it's about to fall off a ledge.
HoveringEnemy(Hover): a hovering enemy that can patrol.

Variables used from config: SPRITE_GRAVITY, SPRITE_ACCEL_SPEED, SPRITE_FRICTION, SPRITE_RUN_FACTOR, SPRITE_JUMP_SPEED,
                            SPRITE_BONK_SLOWDOWN, SPRITE_LERP_SPEED, STOMP_HIGH_BOUNCE, STOMP_LOW_BOUNCE, PLAYER_REVIVIFY_DELAY
"""

import warnings
from functools import reduce
from pygame import Rect
from .helpers import repack2, repack4, bake_obj
from . import config
from .updateable import Updateable
from .key_commands import KeyCommandReader
from .positional import Positional
from .collidable import Collidable, RectHB
from .animated import Animated
from .timers import Timer, Delay, Cycle
from .tile_objects import Tile, PathTile, StageTile
from .resource_manager import ResourceManager
from .user_interface import PauseState

class Sprite(Animated, Collidable, Updateable):
    """
    Extend Animated, Collidable and Updateable to represent a game entity.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable and Animated.
    Extends update(dt) to decompose in the following steps:
    _apply_forces: actions that affect object velocity; implement in subclasses as needed.
    _move: actions that affect object movement; implement in subclasses as needed (include solid collisions).
    _collide_entities(): check non-solid collisions; implemented in base class.
    _border_check(): check interaction with borders; implemented in base class.
      This method looks for methods called _border_[direction in ("left", "top", "right", "bottom")]_[policy], to be implemented in subclasses as needed.
    super().update(): update components.
    _determine_anim(): select appropriate animation; implement in subclasses as needed.
    Extends draw(canvas) to deal with screen wrap.
    
    Public methods:
    kill(): trigger entity death.
    unpause(): do some work on unpausing if needed.
    lock_movement(), unlock_movement(): disable or enable sprite movement.
    """
    
    def __init__(self, tileset, hb_adjust=(0,0,0,0), kill_margins="board", border_policies="board", solids=("solid",), spawner=None, **kwargs):
        """
        Extend superclasses to store some values used to interact with the active board, possibly a spawner entity, and to keep track of sprite orientation.
        
        The tileset can be passed as a (canvas, tile_dim) pair; the Animated constructor will build it.
          This is useful when several sprites need to use the "same" tileset. An Animated object's tileset is a componet, so it can't be shared.
        Hitbox adjustments go (trim_width, trim_height, offset_x, offset_y). Trims are ADDED (express them as negative).
        """
        tileset = bake_obj(tileset)
        super().__init__(tileset=tileset, hb_dim=(tileset.width + hb_adjust[0], tileset.height + hb_adjust[1]), \
                         hb_offset=[hb_adjust[2], hb_adjust[3]], **kwargs)
        self._solids = set(solids)
        """A set of tags that this sprite treats as solid objects; defaults to {"solid"}."""
        self._kill_margins = repack4(kill_margins)
        """
        How far, in pixels, this sprite can stray from the board frame before being killed.
        
        Can be passed as single value, (horizontal, vertical) or (left, top, right, bottom). These values CANNOT be infinite.
        Any one of these can be set as "board" to look up and use active board's defined value.
        """
        self._border_policies = repack4(border_policies)
        """
        How sprites should interact with borders (by default; can be overriden by each sprite).
        
        Can be passed as single value, (horizontal, vertical) or (left, top, right, bottom). Options:
            "board": Look up and apply active board's policy.
            "solid": Treat border as a solid barrier.
            "wrap": Teleport sprite to opposite border.
            None: Do nothing.
        """
        self._spawner = spawner
        """The builder of this object, if any."""
        self._orientation = ("right", None)
        """The horizontal and vertical orientation of this object."""
        self._movement_lock = False
        """Whether movement is locked or not."""

    @property
    def _orientation(self):
        """Sprite's 2D orientation."""
        return tuple((self._orientation_x, self._orientation_y))
        
    @_orientation.setter
    def _orientation(self, value):
        self._orientation_x, self._orientation_y = value

    @property
    def board(self):
        """Current game board."""
        return self.game.state.board if self.game else None

    @property
    def border_left(self):
        """Left border policy."""
        return self._border_policies[0] if self._border_policies[0] != "board" else self.board.border_policies[0]

    @property
    def border_top(self):
        """Top border policy."""
        return self._border_policies[1] if self._border_policies[1] != "board" else self.board.border_policies[1]
        
    @property
    def border_right(self):
        """Right border policy."""
        return self._border_policies[2] if self._border_policies[2] != "board" else self.board.border_policies[2]
        
    @property
    def border_bottom(self):
        """Bottom border policy."""
        return self._border_policies[3] if self._border_policies[3] != "board" else self.board.border_policies[3]

    def update(self, dt):
        """Perform whatever work is needed for movement, collision and animation control."""
        if not self._movement_lock:
            self._apply_forces(dt)
            self._move(dt)
            self._collide_entities(dt)
            self._border_check(dt)
        super().update(dt) # Update components.
        self._determine_anim(dt)

    def _apply_forces(self, dt):
        """Apply forces (implement in subclasses as needed)."""
        pass
        
    def _move(self, dt):
        """Move (implement in subclasses as needed)."""
        pass

    def _collide_entities(self, dt):
        """Check collisions with board entities."""
        if not self._hb_lock:
            for obj in self.board.get_collisions(self):
                if self._collided(obj):
                    break
        
    def _border_check(self, dt):
        """
        Check interaction with board borders and applies appropriate method for border policy.
        
        Border policy methods must be implemented with name _border_[direction in ("left", "top", "right", "bottom")]_[policy name]
        """
        # Rects
        killrect = self.board.get_frame_borders(tuple(self.board.kill_margins[i] if self._kill_margins[i]=="board" else self._kill_margins[i] for i in range(4)))
        borders = self.board.get_frame_borders()
        
        # Kill Sprite if outside of killrect
        if self.hitbox.right < killrect.left or self.hitbox.left > killrect.right or \
           self.hitbox.bottom < killrect.top or self.hitbox.top > killrect.bottom:
            self.kill("entropy")
        
        # Check border collisions
        policy = ""
        if self.hitbox.left < borders.left-1:
            policy = "_border_left_" + str(self.border_left)
        elif self.hitbox.right > borders.right:
            policy = "_border_right_" + str(self.border_right)
        if policy in dir(self):
            exec("self."+policy+"()")
        elif policy != "" and policy[-4:] != "None":
            warnings.warn("Sprite {s} tried to apply border policy {p}, which is not implemented.".format(s=self, p=policy), RuntimeWarning)
        policy = ""
        if self.hitbox.top < borders.top-1:
            policy = "_border_top_" + str(self.border_top)
        elif self.hitbox.bottom > borders.bottom:
            policy = "_border_bottom_" + str(self.border_bottom)
        if policy in dir(self):
            exec("self."+policy+"()")
        elif policy != "" and policy[-4:] != "None":
            warnings.warn("Sprite {s} tried to apply border policy {p}, which is not implemented.".format(s=self, p=policy), RuntimeWarning)
        
    def _determine_anim(self, dt):
        """Select appropriate animation (implement in subclasses as needed)."""
        pass
    
    def draw(self, canvas):
        """Extend Drawable to draw Sprite on opposite sides / corner of the board in case of screen wrap."""
        lateral_wrap = None
        if self.x < 0 and self.border_left == "wrap":
            lateral_wrap = "left"
            self.x += self.board.width+1
            super().draw(canvas)
            self.x -= self.board.width+1
        elif self.x + self.width > self.board.width and self.border_right == "wrap":
            lateral_wrap = "right"
            self.x -= self.board.width+1
            super().draw(canvas)
            self.x += self.board.width+1
        if self.y < 0 and self.border_top == "wrap":
            self.y += self.board.height+1
            super().draw(canvas)
            if lateral_wrap == "left":
                self.x += self.board.width+1
                super().draw(canvas)
                self.x -= self.board.width+1
            elif lateral_wrap == "right":
                self.x -= self.board.width+1
                super().draw(canvas)
                self.x += self.board.width+1
            self.y -= self.board.height+1
        elif self.y + self.height > self.board.height and self.border_bottom == "wrap":
            self.y -= self.board.height+1
            super().draw(canvas)
            if lateral_wrap == "left":
                self.x += self.board.width+1
                super().draw(canvas)
                self.x -= self.board.width+1
            elif lateral_wrap == "right":
                self.x -= self.board.width+1
                super().draw(canvas)
                self.x += self.board.width+1
            self.y += self.board.height+1
        super().draw(canvas)
    
    def kill(self, note="natural causes"):
        """
        Trigger entity death.
        
        Mark object for destruction, lock hitbox and notify spawner.
        Calls to this method can include a note; currently used only for debug purposes.
        """
        self.game.mark_for_destruction(self)
        self.lock_hitbox()
        if self._spawner:
            self._spawner.notify_death(self)

    def unpause(self):
        """
        Do work on unpause.
        
        Mostly intended for player controlled sprites.
        """
        pass
        
    def lock_movement(self):
        """Disable movement."""
        self._movement_lock = True
        
    def unlock_movement(self):
        """Enable movement."""
        self._movement_lock = False

############
# MOVEMENT #
############

class VelocityMovement(Sprite):
    """
    Extend Sprite to apply velocity.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable, Animated and Sprite.
    Implements Sprite._move(dt).
    Implements border policies "wrap" and "solid".
    
    Movement includes solid collisions. The method is divided on vertical and horizontal movement, in this order.
    A solid collision will trigger a method in the form _collided_solid_[direction in ("left", "top", "right", "bottom")].
      By default, stop the sprite at the colliding object's border. Extend or override in subclasses as needed.
    A VelocityMovement Sprite can hold another object as an inertial frame of reference.
      ...I mean, I hope I'm using the term right. In this context, an "inertial frame of reference" is an
      object that applies its velocity to the sprite's position. Use when the sprite is standing on, or in any
      other way attached to, another moving object.
    """
    
    def __init__(self, tileset, **kwargs):
        """Extend Sprite to initialize an attribute for storing an inertial frame of reference."""
        super().__init__(tileset=tileset, **kwargs)
        self._inertial_for = None
        """An object that translates its movement to the sprite."""
        
    @property
    def ifor_vel_x(self):
        """Horizontal velocity of the inertial frame of reference."""
        return self._inertial_for.vel_x if self._inertial_for else 0
        
    @property
    def ifor_vel_y(self):
        """Vertical velocity of the inertial frame of reference."""
        return self._inertial_for.vel_y if self._inertial_for else 0
        
    @property
    def ifor_vel(self):
        """2D velocity of the inertial frame of reference."""
        return self._inertial_for.vel if self._inertial_for else tuple((0,0))
    
    def _move(self, dt):
        """Perform vertical movement/collision and then horizontal."""
        self._move_collide_vertical()
        self._move_collide_horizontal()
        
    def _move_collide_vertical(self):
        """
        Perform vertical movement and board collision.
        
        Apply velocity from self and inertial frame of reference.
        Deal with solid collisions.
          Solid collisions get their own built-in methods (see _collide_solid_[direction].).
          Collision direction is decided from own movement, or object movement if the sprite is still.
        Detect crushing by doing a second solid collision check.
        """
        self.y += self.vel_y + self.ifor_vel_y
        solids = self.board.get_collisions(self, self._solids)
        if any(solids):
            topmost = reduce(lambda a,b: a if a.hitbox.y < b.hitbox.y else b, solids)
            bottommost = reduce(lambda a,b: a if a.hitbox.y > b.hitbox.y else b, solids)
            if self.vel_y + self.ifor_vel_y > 0:
                self._collide_solid_bottom(topmost.hitbox.top, topmost)
            elif self.vel_y + self.ifor_vel_y < 0:
                self._collide_solid_top(bottommost.hitbox.bottom+1, bottommost)
            elif topmost.owner.vel_y < 0:
                self._collide_solid_bottom(topmost.hitbox.top, topmost)
            elif bottommost.owner.vel_y > 0:
                self._collide_solid_top(bottommost.hitbox.bottom+1, bottommost)
        if any(self.board.get_collisions(self, self._solids)):
            self.kill("crushing")
        
    def _move_collide_horizontal(self):
        """
        Perform horizontal movement and board collision.
        
        Apply velocity from self and inertial frame of reference.
        Deal with solid collisions.
          Solid collisions get their own built-in methods (see _collide_solid_[direction].).
          Collision direction is decided from own movement, or object movement if the sprite is still.
        Detect crushing by doing a second solid collision check.
        """
        self.x += self.vel_x + self.ifor_vel_x
        solids = self.board.get_collisions(self, self._solids)
        if any(solids):
            leftmost = reduce(lambda a,b: a if a.hitbox.x < b.hitbox.x else b, solids)
            rightmost = reduce(lambda a,b: a if a.hitbox.x > b.hitbox.x else b, solids)
            if self.vel_x + self.ifor_vel_x > 0:
                self._collide_solid_right(leftmost.hitbox.left, leftmost)
            elif self.vel_x + self.ifor_vel_x < 0:
                self._collide_solid_left(rightmost.hitbox.right+1, rightmost)
            elif leftmost.owner.vel_x < 0:
                self._collide_solid_right(leftmost.hitbox.left, leftmost)
            elif rightmost.owner.vel_x > 0:
                self._collide_solid_left(rightmost.hitbox.right+1, rightmost)
        if any(self.board.get_collisions(self, self._solids)):
            self.kill("crushing")
    
    def _collide_solid_left(self, x, obj=None):
        """Solid left collision."""
        self.hitbox.left = x + .01 # Rounding subpixels.
        
    def _collide_solid_top(self, y, obj=None):
        """Solid top collision."""
        self.hitbox.top = y + .01 # Rounding subpixels.
        
    def _collide_solid_right(self, x, obj=None):
        """Solid right collision."""
        self.hitbox.right = x - .01 # Rounding subpixels.
        
    def _collide_solid_bottom(self, y, obj=None):
        """Solid bottom collision."""
        self.hitbox.bottom = y - .01 # Rounding subpixels.
    
    def _border_left_solid(self):
        """Border left collision."""
        self._collide_solid_left(self.board.frame.x - 1)
        
    def _border_top_solid(self):
        """Border top collision."""
        self._collide_solid_top(self.board.frame.y - 1)
        
    def _border_right_solid(self):
        """Border right collision."""
        self._collide_solid_right(self.board.frame.right)
        
    def _border_bottom_solid(self):
        """Border bottom collision."""
        self._collide_solid_bottom(self.board.frame.bottom)
    
    def _border_left_wrap(self):
        """Screen wrap left."""
        if self.hitbox.centerx < self.board.frame.x - 1:
            self.x += self.board.width
        
    def _border_top_wrap(self):
        """Screen wrap top."""
        if self.hitbox.centery < self.board.frame.y - 1:
            self.y += self.board.height
        
    def _border_right_wrap(self):
        """Screen wrap right."""
        if self.hitbox.centerx > self.board.frame.right:
            self.x -= self.board.width
        
    def _border_bottom_wrap(self):
        """Screen wrap bottom."""
        if self.hitbox.centery > self.board.frame.bottom:
            self.y -= self.board.height

class GravityBound(VelocityMovement):
    """
    Extend VelocityMovement to include a gravity effect on _apply_forces.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable, Animated, Sprite and VelocityMovement.
    Extends Sprite.apply_forces(dt), VelocityMovement._collide_solid_top(y, obj) and VelocityMovement._collide_solid_bottom(y, obj).
    
    Also, this subclass deals with binding to inertial frames of reference (when landing) and unbinding from them (when airborne).
    """
    
    def __init__(self, tileset, gravity=config.SPRITE_GRAVITY, **kwargs):
        """Extend VelocityMovement to store a gravity speed (in pixels per second)."""
        super().__init__(tileset=tileset, **kwargs)
        self._gravity = gravity
    
    def _apply_forces(self, dt):
        """
        Extend Sprite to apply gravity to each frame.
        
        Works by checking collisions below sprite to see if it has to fall (hence "coyote_feet"),
          and by adding an established amount of vertical velocity each frame when the sprite's falling.
        Unbind from inertial frame of reference if airborne.
        """
        if abs(self.vel_y) > 0.5: # Hardcoded constant
            # Falling
            self.vel_y += self._gravity * dt/1000
        elif self.vel_y <= 0:
            coyote_feet = RectHB((self.hitbox.x, self.hitbox.bottom-1), (self.hitbox.width-1, 1))
            collisions = tuple(filter(lambda x: x not in (self, None), self.board.get_collisions(coyote_feet, self._solids)))
            if len(collisions) == 0:
                # Starting to fall
                self.vel_y = 1 # Hardcoded constant
            else:
                # Sliding into a new frame of reference.
                obj = reduce(lambda a,b: a if a.hitbox.y < b.hitbox.y else b, collisions)
                self._inertial_for = obj.owner if isinstance(obj, Tile) else obj
        if self.vel_y != 0:
            self._inertial_for = None
        super()._apply_forces(dt)
        
    def _collide_solid_top(self, y, obj=None):
        """Extend VelocityMovement to stop vertical velocity on bonking the ceiling."""
        super()._collide_solid_top(y, obj)
        self.vel_y = 1

    def _collide_solid_bottom(self, y, obj=None):
        """Extend VelocityMovement to stop vertical velocity on landing and bind to an inertial frame of reference."""
        super()._collide_solid_bottom(y, obj)
        self.vel_y = 0
        self._inertial_for = obj.owner if isinstance(obj, Tile) else obj

class AccelerationMovement(VelocityMovement):
    """
    Extend VelocityMovement to include acceleration information.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable, Animated, Sprite and VelocityMovement.
    """
    
    def __init__(self, tileset, speed=config.SPRITE_ACCEL_SPEED, friction=config.SPRITE_FRICTION, **kwargs):
        """
        Extend Sprite to store an acceleration, speed and factors.
        
        friction works as a slowing factor every frame, effectively curbing acceleration.
          At 1, effect is disabled. Keep below 1 for it to work as intended.
          This value can be manipulated to affect general surface slipperyness (think Super Mario World ice physics).
        """
        super().__init__(tileset=tileset, **kwargs)
        self._speed = speed
        """The speed of the sprite (in pixels per millisecond)."""
        self._friction = friction
        """
        Slowing factor for the sprite's velocity.
        
        Keep above 0 and below 1 for intended functionality.
        """
        self._accel_factor = 1
        """An acceleration factor. Use to apply temporary speed modifyers (such as running)."""
        self._accel = (0,0)
        """Sprite's 2D acceleration."""
        self._reset_data["attributes"]["_accel"] = (0,0)
        
    @property
    def _accel(self):
        """Sprite's 2D acceleration."""
        return tuple((self._accel_x, self._accel_y))
        
    @_accel.setter
    def _accel(self, value):
        self._accel_x, self._accel_y = value
        
class AcceleratedHorizontal(AccelerationMovement):
    """
    Extend AccelerationMovement to apply horizontal acceleration on _apply_forces.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable, Animated,
                                Sprite, VelocityMovement and AccelerationMovement.
    Extends Sprite._apply_forces(dt).
    """
    
    def _apply_forces(self, dt):
        """
        Extend AccelerationMovement to apply x acceleration.
        
        Sums acceleration * accel_factor to velocity (adjusted for delta time),
        then applies friction, then stops the Sprite if it's slow enough.
        """
        self.vel_x += self._accel_x * self._accel_factor * dt/1000
        self.vel_x *= self._friction
        if abs(self.vel_x) < 0.1: # Hardcoded constant. Affects minimum speed.
            self.vel_x = 0 # (round down to 0 when velocity is slow enough)
        super()._apply_forces(dt)
        
class AcceleratedVertical(AccelerationMovement):
    """
    Extend AccelerationMovement to apply vertical acceleration on _apply_forces.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable, Animated,
                                Sprite, VelocityMovement and AccelerationMovement.
    Extends Sprite._apply_forces(dt).
    """
    
    def _apply_forces(self, dt):
        """
        Extend AccelerationMovement to apply y acceleration.
        
        Sums acceleration * accel_factor to velocity (adjusted for delta time),
        then applies friction, then stops the Sprite if it's slow enough.
        """
        self.vel_y += self._accel_y * self._accel_factor * dt/1000
        self.vel_y *= self._friction
        if abs(self.vel_y) < 0.1: # Hardcoded constant. Affects minimum speed.
            self.vel_y = 0 # (round down to 0 when velocity is slow enough)
        super()._apply_forces(dt)
        
class FixedBounce(VelocityMovement):
    """
    Extend VelocityMovement to apply a bounce on solid collisions.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable, Animated, Sprite and VelocityMovement.
    Overrides VelocityMovement's solid collision methods.
    """
    
    def __init__(self, tileset, bounce=0, **kwargs):
        """Extend VelocityMovement to store a 2D bounce velocity value."""
        super().__init__(tileset=tileset, **kwargs)
        self._bounce = bounce
        """Sprite's 2D bounce velocity."""
        
    @property
    def _bounce(self):
        """Sprite's 2D bounce velocity."""
        return tuple((self._bounce_x, self._bounce_y))
        
    @_bounce.setter
    def _bounce(self, value):
        self._bounce_x, self._bounce_y = repack2(value)
    
    def _collide_solid_left(self, x, obj=None):
        """Override VelocityMovement to apply x bounce velocity, correcting position for hitbox overlap."""
        self.hitbox.left += (x - self.hitbox.left)*2
        self.vel_x = self._bounce_x
        
    def _collide_solid_top(self, y, obj=None):
        """Override VelocityMovement to apply y bounce velocity, correcting position for hitbox overlap."""
        self.hitbox.top += (y - self.hitbox.top)*2
        self.vel_y = self._bounce_y
        
    def _collide_solid_right(self, x, obj=None):
        """Override VelocityMovement to apply x bounce velocity, correcting position for hitbox overlap."""
        self.hitbox.right -= (self.hitbox.right - x)*2
        self.vel_x = -self._bounce_x
        
    def _collide_solid_bottom(self, y, obj=None):
        """Override VelocityMovement to apply y bounce velocity, correcting position for hitbox overlap."""
        self.hitbox.bottom -= (self.hitbox.bottom - y)*2
        self.vel_y = -self._bounce_y
        
#############################
# VELOCITY MOVEMENT ACTIONS #
#############################

class AccelerationSpeedUp(AccelerationMovement):
    """
    Extend AccelerationMovement to implement throttling acceleration actions.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable, Animated,
                                Sprite, VelocityMovement and AccelerationMovement.
    
    Public methods:
    run(): apply run factor.
    stop_running(): stop applying run factor.
    """
    
    def __init__(self, tileset, run_factor=config.SPRITE_RUN_FACTOR, **kwargs):
        """Extend SidescrollerWalk to store a run factor."""
        super().__init__(tileset=tileset, **kwargs)
        self._run_factor = run_factor
        """How much acceleration's multiplied when running."""
        
    def run(self):
        """Apply run factor."""
        self._accel_factor = self._run_factor
        
    def stop_running(self):
        """Stop applying run factor."""
        self._accel_factor = 1
    
class SidescrollerWalk(AcceleratedHorizontal, GravityBound):
    """
    Base subclass for Sidescroller movement; extend AcceleratedHorizontal and GravityBound to implement walking actions.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable, Animated, Sprite,
                                VelocityMovement, AccelerationMovement, AcceleratedHorizontal and GravityBound.
    
    Public methods:
    walk_left(), walk_right(): update horizontal orientation and acceleration.
    stop_walking(): stop accelerating.
    """
        
    def walk_left(self):
        """Update horizontal orientation and acceleration."""
        if not self._hb_lock:
            self._orientation_x = "left"
            self._accel_x = -self._speed

    def walk_right(self):
        """Update horizontal orientation and acceleration."""
        if not self._hb_lock:
            self._orientation_x = "right"
            self._accel_x = self._speed
    
    def stop_walking(self):
        """Stop accelerating."""
        self._accel_x = 0

class SidescrollerJump(SidescrollerWalk):
    """
    Extend SidescrollerWalk to implement jumping actions.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable, Animated, Sprite,
                                VelocityMovement, AccelerationMovement, AcceleratedHorizontal, GravityBound
                                and SidescrollerWalk.
    Extends VelocityMovement._collide_solid_top(y, obj).
    
    NOT commited (horizontal movement control while in the air is allowed).
    
    Public methods:
    jump(): perform jump and return True if not in the air; return False otherwise.
    stop_jumping(): stop applying vertical negative velocity.
    """
    
    def __init__(self, tileset, jump_speed=config.SPRITE_JUMP_SPEED, bonk_slowdown=config.SPRITE_BONK_SLOWDOWN, **kwargs):
        """Extend SidescrollerWalk to store a jump speed and a bonk horizontal slowdown factor."""
        super().__init__(tileset=tileset, **kwargs)
        self.jump_speed = jump_speed
        """The force of the sprite's jump."""
        self.bonk_slowdown = bonk_slowdown
        """
        How much bonking the ceiling slows the sprite's horizontal movement.
        
        Keep above 0 and at or below 1 for intended functionality; set to 1 to disable.
        """
        
    def _collide_solid_top(self, y, obj=None):
        """Extend VelocityMovement to slow down horizontal velocity on bonking."""
        super()._collide_solid_top(y)
        self.vel_x *= self.bonk_slowdown
        
    def jump(self):
        """Perform jump and return True if not in the air; return False otherwise."""
        if self._inertial_for and not self._hb_lock:
            self.vel_y = -self.jump_speed
            return True
        return False

    def stop_jumping(self):
        """Stop applying vertical negative velocity."""
        if self.vel_y < 0:
            self.vel_y = 0
        
class SidescrollerCrouch(SidescrollerWalk):
    """
    Extend SidescrollerWalk to implement crouching actions.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable, Animated, Sprite,
                                VelocityMovement, AccelerationMovement, AcceleratedHorizontal, GravityBound
                                and SidescrollerWalk.
    Extends VelocityMovement._collide_solid_bottom(y, obj). Overrides SidescrollerWalk.walk_left() and SidescrollerWalk.walk_right().
    
    Doesn't allow walking while crouching, but it does allow jumping (with horizontal movement control).
    
    Public methods:
    crouch(): enter crouch if not in the air.
    stop_crouching(): exit crouch if there's enough room above.
    """
    
    def __init__(self, tileset, crouch_shrink=None, **kwargs):
        """
        Extend SidescrollerWalk to build a crouching hitbox.
        
        Asumes a rectangular hitbox.
        If no crouch_shrink is provided, defaults to half hitbox height.
        """
        super().__init__(tileset=tileset, **kwargs)
        self._standing_hitbox = self.hitbox
        """Sprite's hitbox while not crouching."""
        crouch_shrink = crouch_shrink if crouch_shrink != None else int(self.hitbox.height/2)
        self._crouching_hitbox = RectHB((0,0), (self.hitbox.width, self.hitbox.height-crouch_shrink), (self.hitbox.offset_x, self.hitbox.offset_y+crouch_shrink))
        """Sprite's hitbox while crouching."""
        
    @property
    def crouching(self):
        """Return True if this actor's using its crouching hitbox; False otherwise."""
        return self.hitbox == self._crouching_hitbox
        
    def _collide_solid_bottom(self, y, obj=None):
        """Extend VelocityMovement to stop horizontal velocity on landing if crouching."""
        super()._collide_solid_bottom(y, obj)
        if self.crouching:
            self._accel_x = 0
        
    def walk_left(self):
        """Override SidescrollerWalk to block movement while crouching and on the ground."""
        self._orientation_x = "left" # Always allow orientation changes.
        if not self.crouching or self.vel_y != 0:
            self._accel_x = -self._speed

    def walk_right(self):
        """Override SidescrollerWalk to block movement while crouching and on the ground."""
        self._orientation_x = "right" # Always allow orientation changes.
        if not self.crouching or self.vel_y != 0:
            self._accel_x = self._speed

    def crouch(self):
        """Enter crouch if not in the air."""
        if not self.crouching and not self.vel_y:
            self.hitbox = self._crouching_hitbox
            self._accel_x = 0
            return True
        return False
        
    def stop_crouching(self):
        """Exit crouch if there's enough room above."""
        if self.crouching:
            bonk_canary = RectHB((self.hitbox.x, self.hitbox.bottom - (self._standing_hitbox.height-1)), 
                                       (self.hitbox.width-1, self.hitbox.height-1))
            # Check board collisions against bonk_canary; stand up only if there aren't any.
            if not any(self.board.get_collisions(bonk_canary, self._solids)):
                self.hitbox = self._standing_hitbox
                return True
        return False

class TopDownWalk(AcceleratedHorizontal, AcceleratedVertical):
    """
    Base class for top-down movement; extend AcceleratedHorizontal and AcceleratedVertical.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable, Animated, Sprite,
                                VelocityMovement, AccelerationMovement, AcceleratedHorizontal and AcceleratedVertical.
    
    When both horizontal and vertical movement are being applied, speed is multiplied by sin(45º).
    
    Public methods:
    walk_left(), walk_right(): update horizontal orientation and acceleration and apply diagonal correction if needed.
    walk_up(), walk_down(): update horizontal orientation and acceleration and apply diagonal correction if needed.
    stop_walking_horizontal(): stop accelerating horizontally and apply vertical correction if needed.
    stop_walking_vertical(): stop accelerating vertically and apply horizontal correction if needed.
    """
    
    def _diagonal_movement_correction(self):
        """Check if there's both horizontal and vertical movement; if so, multiply speed by sin(45º)."""
        if self._accel_x and self._accel_y:
            self._accel_x = self._speed * (0.70711 if self._accel_x > 0 else -0.70711)
            self._accel_y = self._speed * (0.70711 if self._accel_y > 0 else -0.70711)
        
    def _horizontal_movement_correction(self):
        """Check if there's horizontal movement; if so, reset to default speed."""
        if self._accel_x:
            self._accel_x = self._speed if self._accel_x > 0 else -self._speed
            
    def _vertical_movement_correction(self):
        """Check if there's vertical movement; if so, reset to default speed."""
        if self._accel_y:
            self._accel_y = self._speed if self._accel_y > 0 else -self._speed
        
    def _horizontal_orientation_check(self):
        """Reset horizontal orientation if the sprite has a vertical orientation and is stopped horizontally."""
        if self._orientation_y and self.game.pressing.intersection(set({"up", "down"})):
            self._orientation_x = None
        
    def _vertical_orientation_check(self):
        """Reset vertical orientation if the sprite has a horizontal orientation and is stopped vertically."""
        if self._orientation_x and self.game.pressing.intersection(set({"left", "right"})):
            self._orientation_y = None
        
    def walk_left(self):
        """Update horizontal orientation and acceleration and apply diagonal correction if needed."""
        self._orientation_x = "left"
        if not self._accel_y:
            self._orientation_y = None
        self._accel_x = -self._speed
        self._diagonal_movement_correction()
        
    def walk_up(self):
        """Update vertical orientation and acceleration and apply diagonal correction if needed."""
        self._orientation_y = "up"
        if not self._accel_x:
            self._orientation_x = None
        self._accel_y = -self._speed
        self._diagonal_movement_correction()

    def walk_right(self):
        """Update horizontal orientation and acceleration and apply diagonal correction if needed."""
        self._orientation_x = "right"
        if not self._accel_y:
            self._orientation_y = None
        self._accel_x = self._speed
        self._diagonal_movement_correction()
        
    def walk_down(self):
        """Update vertical orientation and acceleration and apply diagonal correction if needed."""
        self._orientation_y = "down"
        if not self._accel_x:
            self._orientation_x = None
        self._accel_y = self._speed
        self._diagonal_movement_correction()
    
    def stop_walking_horizontal(self):
        """
        Stop accelerating horizontally and apply vertical correction if needed.
        
        Orientation checks are delayed in order to recognize close key releases as simultaneous.
        """
        self.add_component(Delay(config.ORIENTATION_CHECK_DELAY, self._horizontal_orientation_check))
        self._accel_x = 0
        self._vertical_movement_correction()
            
    def stop_walking_vertical(self):
        """
        Stop accelerating vertically and apply horizontal correction if needed.
        
        Orientation checks are delayed in order to recognize close key releases as simultaneous.
        """
        self.add_component(Delay(config.ORIENTATION_CHECK_DELAY, self._vertical_orientation_check))
        self._accel_y = 0
        self._horizontal_movement_correction()

class Hover(AcceleratedHorizontal, AcceleratedVertical):
    """
    Extend AcceleratedHorizontal and AcceleratedVertical to implement an orthogonal hover with a perpendicular oscillation.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable, Animated, Sprite,
                                VelocityMovement, AccelerationMovement, AcceleratedHorizontal and AcceleratedVertical.
    
    Public methods:
    hover_left(), hover_right(): update horizontal orientation and acceleration.
    hover_up(), hover_down(): update vertical orientation and acceleration.
    stop_hovering_horizontal(): stop accelerating horizontally.
    stop_hovering_vertical(): stop accelerating vertically.
    """
    
    def __init__(self, tileset, movement="horizontal", osc_period=None, reverse_phase=False, **kwargs):
        """
        Extend superclasses to store a movement direction and start an oscillation.
        
        Oscillations start by default up or leftwards (perpendicular to movement).
          Set reverse_phase to True to start down or rightwards instead.
          Leave osc_period as None to disable oscillation.
        """
        super().__init__(tileset=tileset, **kwargs)
        self._movement = movement
        """The direction of the sprite's movement."""
        if osc_period:
            if self._movement=="horizontal":
                if reverse_phase:
                    self.hover_down()
                else:
                    self.hover_up()
            else:
                if reverse_phase:
                    self.hover_right()
                else:
                    self.hover_left()
            self.add_persistent_component(Cycle(osc_period, self._reverse_oscillation))
        
    def _reverse_oscillation(self):
        """Reverse movement in the oscillation axis (called by timer)."""
        if self._movement == "horizontal":
            if self.vel_y > 0:
                self.hover_up()
            else:
                self.hover_down()
        else:
            if self.vel_x > 0:
                self.hover_left()
            else:
                self.hover_right()
        
    def hover_left(self):
        """Update horizontal orientation and acceleration."""
        self._orientation_x = "left"
        self._accel_x = -self._speed
        
    def hover_up(self):
        """Update vertical orientation and acceleration."""
        self._orientation_y = "up"
        self._accel_y = -self._speed

    def hover_right(self):
        """Update horizontal orientation and acceleration."""
        self._orientation_x = "right"
        self._accel_x = self._speed
        
    def hover_down(self):
        """Update vertical orientation and acceleration."""
        self._orientation_y = "down"
        self._accel_y = self._speed
    
    def stop_hovering_horizontal(self):
        """Stop accelerating horizontally."""
        self._accel_x = 0
            
    def stop_hovering_vertical(self):
        """Stop accelerating vertically."""
        self._accel_y = 0

#################
# LERP MOVEMENT #
#################

class LerpMovement(Sprite):
    """
    Extend Sprite to support lerp movement.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable, Animated and Sprite.
    Implements Sprite._move(dt).
    Implements border policy "wrap".
    
    Movement is done by linear interpolation. The only supported lerp function is linear movement.
    
    Public methods:
    on_arrival(): implement on subclasses to do something when the sprite reaches a destination.
    
    Notes on setters:
    Setting either x or y will trigger movement; setting pos, however, will not.
    Setting _destination will update _origin and start a timer to be used to manage the movement on update time.
    """
    
    def __init__(self, tileset, speed=config.SPRITE_LERP_SPEED, **kwargs):
        """Extend Sprite to store a speed and declare origin and destination points."""
        super().__init__(tileset=tileset, **kwargs)
        self._speed = speed
        """The speed of the sprite (in pixels per millisecond)."""
        self._origin = self.pos
        """The point from which the current lerp movement starts."""
        self._destination_x, self._destination_y = self.pos
        """The point to which the current lerp movement goes."""
    
    @property
    def pos(self):
        """Object 2D position."""
        return tuple((self.x, self.y))
        
    @pos.setter
    def pos(self, value):
        """Teleport Sprite to pos without triggering movement."""
        self.x, self.y = value
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
        self._origin = self.pos
        self.add_component(Timer(name="move_timer"))
        
    def _move(self, dt):
        """Linear lerp towards destination if it's not the sprite's current position; call on_arrival when destination is reached."""
        # Linear lerp: origin + (destination - origin) * proportion
        # Proportion = time elapsed * speed / distance, capped at 1.
        if self.x != self._destination_x:
            old_x = self.x
            self.x = self._origin_x + (self._destination_x-self._origin_x) * min(self.named["move_timer"].time * self._speed / (self._tileset.width * 1000), 1)
            self.vel_x = self.x - old_x # Register horizontal velocity
        if self.y != self._destination_y:
            old_y = self.y
            self.y = self._origin_y + (self._destination_y-self._origin_y) * min(self.named["move_timer"].time * self._speed / (self._tileset.height * 1000), 1)
            self.vel_y = self.y - old_y # Register vertical velocity
        if self.pos == self._destination and "move_timer" in self.named:
            # Destroy timer and call on_arrival
            self.named["move_timer"].destroy()
            self.on_arrival()
            
    def on_arrival(self):
        """Implement on subclasses to do something when the Sprite reaches a destination."""
        pass
        
    def _border_left_wrap(self):
        """Screen wrap left."""
        if self.hitbox.centerx < self.board.frame.x - 1:
            self.x += self.board.width
            self._origin_x += self.board.width
            self._destination_x += self.board.width
        
    def _border_top_wrap(self):
        """Screen wrap top."""
        if self.hitbox.centery < self.board.frame.y - 1:
            self.y += self.board.height
            self._origin_y += self.board.height
            self._destination_y += self.board.height
        
    def _border_right_wrap(self):
        """Screen wrap right."""
        if self.hitbox.centerx > self.board.frame.right:
            self.x -= self.board.width
            self._origin_x -= self.board.width
            self._destination_x -= self.board.width
        
    def _border_bottom_wrap(self):
        """Screen wrap bottom."""
        if self.hitbox.centery > self.board.frame.bottom:
            self.y -= self.board.height
            self._origin_y -= self.board.height
            self._destination_y -= self.board.height
        
class GridMovement(LerpMovement):
    """
    Extend LerpMovement to support tile by tile movement.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable, Animated, Sprite and LerpMovement.
    
    Public methods:
    move_left(), move_up(), move_right(), move_down(): go one tile towards the specified direction if not moving and that direction is traversable.
    """
        
    @property
    def tile_x(self):
        """X-coordinate of Sprite in terms of tiles within the Board."""
        return int(self.x / self._tileset.width)
        
    @property
    def tile_y(self):
        """Y-coordinate of Sprite in terms of tiles within the Board."""
        return int(self.y / self._tileset.height)
        
    @property
    def tile(self):
        """Coordinates of Sprite in terms of tiles within the Board."""
        return tuple((self.tile_x, self.tile_y))
        
    def move_left(self):
        """Go one tile left if not moving and path is traversable."""
        if self.x == 0 and self.border_left == "solid":
            return # Solid left border
        if self._destination == self.pos:
            tile = self.board.get_tile_at(self.tile)
            if not tile or "left" in tile.tags:
                dest_x = int(self.board.width/self.tile_width)-1 if self.x == 0 and self.border_left == "wrap" else self.tile_x-1
                dest_tile = self.board.get_tile_at((dest_x, self.tile_y))
                if not dest_tile or dest_tile.traversable:
                    self._destination = (self.x - self.tile_width, self.y)
                    # self._border_left_wrap() will update position and destination if needed.
        
    def move_up(self):
        """Go one tile up if not moving and path is traversable."""
        if self.y == 0 and self.border_top == "solid":
            return # Solid top border
        if self._destination == self.pos:
            tile = self.board.get_tile_at(self.tile)
            if not tile or "up" in tile.tags:
                dest_y = int(self.board.height/self.tile_height)-1 if self.y == 0 and self.border_top == "wrap" else self.tile_y-1
                dest_tile = self.board.get_tile_at((self.tile_x, dest_y))
                if not dest_tile or dest_tile.traversable:
                    self._destination = (self.x, self.y - self.tile_height)
                    # self._border_up_wrap() will update position and destination if needed.
        
    def move_right(self):
        """Go one tile right if not moving and path is traversable."""
        if self.x == self.board.width - self.tile_width and self.border_right == "solid":
            return # Solid right border
        if self._destination == self.pos:
            tile = self.board.get_tile_at(self.tile)
            if not tile or "right" in tile.tags:
                dest_x = 0 if self.x == int(self.board.width/self.tile_width)-1 and self.border_right == "wrap" else self.tile_x+1
                dest_tile = self.board.get_tile_at((dest_x, self.tile_y))
                if not dest_tile or dest_tile.traversable:
                    self._destination = (self.x + self.tile_width, self.y)
                    # self._border_right_wrap() will update position and destination if needed.
        
    def move_down(self):
        """Go one tile down if not moving and path is traversable."""
        if self.y == self.board.height - self.tile_height and self.border_bottom == "solid":
            return # Solid bottom border
        if self._destination == self.pos:
            tile = self.board.get_tile_at(self.tile)
            if not tile or "down" in tile.tags:
                dest_y = 0 if self.y == int(self.board.height/self.tile_height)-1 and self.border_bottom == "wrap" else self.tile_y+1
                dest_tile = self.board.get_tile_at((self.tile_x, dest_y))
                if not dest_tile or dest_tile.traversable:
                    self._destination = (self.x, self.y + self.tile_height)
                    # self._border_down_wrap() will update position and destination if needed.


###########################################################################################
###########################################################################################
###########################################################################################

##################
# SAMPLE PLAYERS #
##################


class SidescrollerPlayer(SidescrollerJump, SidescrollerCrouch, AccelerationSpeedUp, KeyCommandReader):
    """
    Extend SidescrollerJump, SidescrollerCrouch, AccelerationSpeedUp and KeyCommandReader to represent
      a player sprite with keyboard/velocity control that moves in a side view.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable, Animated, Sprite,
                                VelocityMovement, AccelerationMovement, AcceleratedHorizontal, GravityBound
                                SidescrollerWalk, SidescrollerJump, SidescrollerCrouch, AccelerationSpeedUp
                                and KeyCommandReader.
    Implements Sprite._determine_anim(dt).
    Extends Sprite.update(dt).
    Extends Sprite.unpause().
    
    Maps key commands to actions and performs command checks as needed.
    Can jump, crouch, stomp some sprites and activate checkpoints and board exits.
    Has sounds associated with jumping and dying.
    
    Key commands:
    left, right: walk towards the specified direction.
    up: perform jump.
    down: perform crouch.
    run: throttle speed.
    
    Collisions:
    exit: perform a state transition.
    checkpoint: set stage checkpoint.
    lethal: kill the player sprite.
    stompable: stomp the colliding object if conditions are fulfilled; otherwise, treat as lethal.
    
    Required animations: idle_right, walk_right, crouch_right, jump_right, idle_left, walk_left, crouch_left, jump_left, death.
    """
    
    def __init__(self, tileset, **kwargs):
        """
        Extend superclasses to load jump and death sounds and hardcode name="player".
        """
        super().__init__(tileset=tileset, name="player", **kwargs)
        self._alive = True
        """Whether the player is alive or not."""
        self._jump_sound = ResourceManager().get_sound("jump.ogg")
        """Sound to be played on jumping."""
        self._death_sound = ResourceManager().get_sound("player_death.ogg")
        """Sound to be played on death."""
            
    def _determine_anim(self, dt):
        """Determine and set animation."""
        if self.crouching:
            action = "crouch"
        elif self.vel_y != 0:
            action = "jump"
        elif self.vel_x != 0:
            action = "walk"
        else:
            action = "idle"
        self.anim = action + "_" + self._orientation_x

    def _command_left(self, press, **kwargs):
        """Walk left or stop walking."""
        if press:
            if not self.crouching or self.vel_y != 0:
                self.walk_left()
            else:
                self._orientation_x = "left"
        else:
            self.stop_walking()
            # Check whether "right" is pressed
            self.activate_if_pressing("right") 
    
    def _command_right(self, press, **kwargs):
        """Walk right or stop walking."""
        if press:
            if not self.crouching or self.vel_y != 0:
                self.walk_right()
            else:
                self._orientation_x = "right"
        else:
            self.stop_walking()
            # Check whether "left" is pressed
            self.activate_if_pressing("left") 
        
    def _command_up(self, press, **kwargs):
        """Jump or stop jumping."""
        if press:
            self.jump()
            if self.crouching and self.vel_y:
                # If crouching, check whether "left" or "right" are pressed
                self.activate_if_pressing("left", "right")
        else:
            self.stop_jumping()

    def _command_down(self, press, **kwargs):
        """Crouch or stop crouching."""
        if press:
            self.crouch()
        else:
            self.stop_crouching()
            if not self.crouching:
                # If successful, check whether "left" or "right" are pressed
                self.activate_if_pressing("left", "right")
    
    def _command_run(self, press, **kwargs):
        """Run or stop running."""
        if press:
            self.run()
        else:
            self.stop_running()

    def _collide_solid_bottom(self, y, obj=None):
        """Extend VerticalMovement to check if we need to crouch on landing."""
        super()._collide_solid_bottom(y, obj)
        self.activate_if_pressing("down")
        
    def _collided_exit(self, obj):
        """Activate the appropriate transition."""
        if "beat" in obj.tags:
            self.game.active_stage.beat(exit_state=obj.dest_board, start_label=obj.start_label, exit_label=obj.exit_label)
        else:
            self.game.set_state(obj.dest_board, start_label=obj.start_label)

    def _collided_checkpoint(self, obj):
        """Set the checkpoint."""
        obj.active = True
        
    def _collided_lethal(self, obj):
        """Kill the player sprite."""
        self.kill("a lethal hazard")
        
    def _collided_stompable(self, obj):
        """
        Stomp the object if the collision fulfills stomping conditions; otherwise, kill the player sprite.
        
        Possible conditions for stomping:
         - Player is falling or about to fall.
         - Player is reasonably higher than stompable object.
        On current implementation, which is rather generous, the object is stomped on collision if the player's bottom
          is at least 1/3 of the stompable object's height above its bottom.
        Stomping triggers a high bounce for the player sprite if command "up" is being pressed, or a low bounce if it is not.
        """
        if self.hitbox.bottom < obj.hitbox.bottom - (obj.hitbox.height/3):
            obj.stomp()
            if "up" in self.game.pressing:
                self.vel_y = -config.STOMP_HIGH_BOUNCE
            else:
                self.vel_y = -config.STOMP_LOW_BOUNCE
        else:
            self.kill("a lethal hazard")

    def revivify(self):
        """
        Revive the player sprite.
        
        3rd level necromancy; consumes diamonds worth 300gp; V. S. M.
        No srsly: reset the stage and unlock the sprite.
        """
        self.game.reset_stage()
        self._alive = True
        self.unlock_anim()
        self.unlock_controller()
        self.check_commands()
        self.unlock_hitbox()
        self.unlock_movement()

    def kill(self, note="natural causes"):
        """Extend Sprite to lock the sprite, play the stored death sound, set the death animation and trigger quick retry on a delay."""
        if self._alive:
            self._death_sound.play()
            self._alive = False
            self.anim = "death"
            self._accel, self.vel=(0,0),(0,0)
            self.lock_anim()
            self.lock_controller()
            self.lock_movement()
            self.add_component(Delay(config.PLAYER_REVIVIFY_DELAY, self.revivify))

    def unpause(self):
        """Extend Sprite to check all commands on unpause."""
        self.check_commands()

    def update(self, dt):
        """
        Extend Sprite to check if it needs to uncrouch.
        
        This covers the case of releasing the crouch key while in a tight space.
        """
        self.deactivate_unless_pressing("down")
        super().update(dt)
        
    def jump(self):
        """Extend SidescrollerJump to play the stored jump sound."""
        if super().jump():
            self._jump_sound.play()

class TopDownPlayer(TopDownWalk, AccelerationSpeedUp, KeyCommandReader):
    """
    Extend TopDownWalk, AccelerationSpeedUp and KeyCommandReader to represent a player sprite with
      keyboard/velocity control that moves in a top-down view.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable, Animated, Sprite,
                                VelocityMovement, AccelerationMovement, AcceleratedHorizontal, GravityBound
                                TopDownWalk, AccelerationSpeedUp and KeyCommandReader.
    Extends Sprite.unpause().
    
    Maps key commands to actions and performs command checks as needed.
    
    Key commands:
    left, up, right, down: walk towards the specified direction.
    run: throttle speed.
    
    Required animations: idle_right, walk_right, idle_left, walk_left, idle_up, walk_up, idle_down, walk_down,
      idle_right_up, walk_right_up, idle_right_down, walk_right_down, idle_left_up, walk_left_up, idle_left_down, walk_left_down.
    """
    
    def __init__(self, tileset, **kwargs):
        """
        Extend superclasses to hardcode name="player".
        """
        super().__init__(tileset=tileset, name="player", **kwargs)
    
    def _determine_anim(self, dt):
        """Determine and set animation."""
        if self.vel_x != 0 or self.vel_y != 0:
            anim = "walk"
        else:
            anim = "idle"
        if self._orientation_x:
            anim = anim = anim + "_" + self._orientation_x
        if self._orientation_y:
            anim = anim = anim + "_" + self._orientation_y
        self.anim = anim
    
    def _command_left(self, press, **kwargs):
        """Walk left or stop walking."""
        if press:
            self.walk_left()
        else:
            if not ("right" in self.game.pressing):
                self.stop_walking_horizontal()
            # Check whether "right" is pressed
            self.activate_if_pressing("right")
    
    def _command_up(self, press, **kwargs):
        """Walk up or stop walking."""
        if press:
            self.walk_up()
        else:
            if not ("down" in self.game.pressing):
                self.stop_walking_vertical()
            # Check whether "down" is pressed
            self.activate_if_pressing("down")
    
    def _command_right(self, press, **kwargs):
        """Walk right or stop walking."""
        if press:
            self.walk_right()
        else:
            if not ("left" in self.game.pressing):
                self.stop_walking_horizontal()
            # Check whether "left" is pressed
            self.activate_if_pressing("left")
    
    def _command_down(self, press, **kwargs):
        """Walk down or stop walking."""
        if press:
            self.walk_down()
        else:
            if not ("up" in self.game.pressing):
                self.stop_walking_vertical()
            # Check whether "up" is pressed
            self.activate_if_pressing("up")
    
    def _collided_exit(self, obj):
        """Activate the appropriate transition."""
        if "beat" in obj.tags:
            self.game.active_stage.beat(exit_state=obj.dest_board, start_label=obj.start_label, exit_label=obj.exit_label)
        else:
            self.game.set_state(obj.dest_board, start_label=obj.start_label)
    
    def unpause(self):
        """Extend Sprite to check all commands on unpause."""
        self.check_commands()

class GridPlayer(GridMovement, KeyCommandReader):
    """
    Extend GridMovement and KeyCommandReader to represent a player sprite with keyboard/lerp control that moves in a grid.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable, Animated, Sprite, LerpMovement and GridMovement.
    Implements GridMovement.on_arrival()
    
    Maps key commands to actions and performs command checks as needed.

    Key commands:
    left, up, right, down: move towards the specified direction.
    
    Required animations: [default].
    """
    
    def __init__(self, tileset, commands=(), **kwargs):
        """
        Extend superclasses to hardcode name="player".
        """
        super().__init__(tileset=tileset, name="player", **kwargs)

    def on_arrival(self):
        """Extend LerpMovement to check for pending commands."""
        self.activate_if_pressing()
    
    def _command_left(self, press, **kwargs):
        """Move left."""
        if press:
            self.move_left()
    
    def _command_up(self, press, **kwargs):
        """Move up."""
        if press:
            self.move_up()
        
    def _command_right(self, press, **kwargs):
        """Move right."""
        if press:
            self.move_right()
        
    def _command_down(self, press, **kwargs):
        """Move down."""
        if press:
            self.move_down()

class MapPlayer(GridPlayer):
    """
    Extend GridPlayer to be able to enter a stage associated with the TileObject in the sprite's current tile.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable, Animated, Sprite, LerpMovement, GridMovement and GridPlayer.
    
    Maps key commands to actions and performs command checks as needed.
    
    Public methods:
    enter_stage(): enter the active stage; reset and unlock the player sprite (called from a delay).
    
    Key commands:
    left, up, right, down: move towards the specified direction.
    enter: if the sprite's in a valid tile: sets active stage, sets "enter" animation and activates a delay to enter the stage.
    
    Required animations: [default], enter.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._enter_sound = ResourceManager().get_sound("enter_stage.ogg")

    def enter_stage(self):
        """Enter the active stage; reset and unlock the player sprite (called from a delay)."""
        self.game.enter_active_stage(self.game.state)
        self.reset()
        self.unlock_controller()
        self.anim = self._reset_data["attributes"]["anim"]

    def _command_enter(self, press, **kwargs):
        """
        If possible, set an active stage and a delay to enter it.
        
        Conditions are: the player is still and in a valid tile (StageTile).
        Set player "enter" animation and lock it until entering the stage.
        """
        if press and self._destination == self.pos:
            tile = self.board.get_tile_at(self.tile)
            if tile and isinstance(tile, StageTile):
                self._enter_sound.play()
                self.game.active_stage = tile
                self.anim = "enter"
                self.lock_controller()
                self.add_component(Delay(900, self.enter_stage))

########################
# SAMPLE ENEMY SPRITES #
########################

class SsWalkingEnemy(SidescrollerWalk):
    """
    Base class for sidescroller enemy sprites. Extend SidescrollerWalk.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable, Animated, Sprite,
                                VelocityMovement, AccelerationMovement, AcceleratedHorizontal, GravityBound
                                and SidescrollerWalk.
    Extends horizontal collisions to change direction.
    Extends reset to unlock the sprite's hitbox and start moving.
    
    Public methods:
    stomp: kill the sprite by stomping: lock its hitbox, stop its movement and set a delay for its destruction.
    
    Required animations: [default], also "stomped" if the enemy can be stomped.
    """
    
    def __init__(self, tileset, direction="left", **kwargs):
        """
        Extend superclasses to store a movement direction and start movement.
        """
        super().__init__(tileset=tileset, **kwargs)
        self._direction = direction
        """The sprite's movement direction."""
        self._reset_data["attributes"]["_direction"] = direction
        exec("self.walk_{d}()".format(d=direction))
        self._stomp_sound = ResourceManager().get_sound("stomp.ogg")
        
    def _collide_solid_left(self, x, obj=None):
        """Solid left collision; extend VelocityMovement to change direction."""
        super()._collide_solid_left(x)
        self.walk_right()
        
    def _collide_solid_right(self, x, obj=None):
        """Solid right collision; extend VelocityMovement to change direction."""
        super()._collide_solid_right(x)
        self.walk_left()
            
    def stomp(self):
        """
        Kill the sprite by stomping.
        
        Lock the sprite's hitbox, stop its movement and set a delay for its destruction.
        """
        self._stomp_sound.play()
        self.anim = "stomped"
        self.lock_hitbox()
        self.vel, self._accel = (0,0), (0,0)
        self.add_component(Delay(600, (self.kill, {"note": "stomping"})))
        
    def reset(self):
        """Extend Component to unlock the sprite's hitbox and start its movement."""
        super().reset()
        self.unlock_hitbox()
        exec("self.walk_{d}()".format(d=self._direction))

class SsCautiousEnemy(SsWalkingEnemy):
    """
    Extend SsWalkingEnemy to turn around when about to fall off a ledge.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable, Animated, Sprite,
                                VelocityMovement, AccelerationMovement, AcceleratedHorizontal, GravityBound
                                SidescrollerWalk and SsWalkingEnemy.
    Extends VelocityMovement._move(dt).
    
    Required animations: [default], also "stomped" if the enemy can be stomped.
    """
    
    def _move(self, dt):
        """Extend VelocityMovement to turn around when about to fall off a ledge."""
        super()._move(dt)
        if self.vel_y == 0:
            # Test if they're about to fall off a ledge while walking right.
            if self.vel_x > 0:
                fall_canary = RectHB((self.hitbox.right+self.vel_x, self.hitbox.bottom+1), (self.hitbox.width, 1))
                if not any(self.board.get_collisions(fall_canary, self._solids)):
                    self.walk_left()
            # Test if they're about to fall off a ledge while walking left.
            elif self.vel_x < 0:
                fall_canary = RectHB((self.hitbox.left-self.hitbox.width+self.vel_x, self.hitbox.bottom+1), (self.hitbox.width, 1))
                if not any(self.board.get_collisions(fall_canary, self._solids)):
                    self.walk_right()
        
class SsJumpyEnemy(SsWalkingEnemy, SidescrollerJump):
    """
    Extend SsWalkingEnemy and SidescrollerJump to move by hopping.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable, Animated, Sprite,
                                VelocityMovement, AccelerationMovement, AcceleratedHorizontal, GravityBound
                                SidescrollerWalk, SidescrollerJump and SsWalkingEnemy.
    Extends SidescrollerJump and sollid bottom collisions to execute jumps when appropriate.
    
    Required animations: [default], also "stomped" if the enemy can be stomped.
    """
    
    def __init__(self, tileset, jump_cooldown=0, **kwargs):
        """Extend superclasses to store a jump cooldown."""
        super().__init__(tileset, **kwargs)
        self._jump_cooldown = jump_cooldown
        """Milliseconds for the sprite to wait between landing and jumping again."""
        
    def _collide_solid_bottom(self, y, obj=None):
        """Extend GravityBound to stop horizontal movement and then jump, either immediately or after a delay."""
        super()._collide_solid_bottom(y, obj)
        self.stop_walking()
        if self._jump_cooldown:
            if not "cooldown" in self.named:
                self.add_component(Delay(self._jump_cooldown, self.jump, name="cooldown"))
        elif not self._hb_lock: # If alive
            self.jump()
    
    def jump(self):
        """Extend SidescrollerJump to activate horizontal movement."""
        super().jump()
        if self._orientation_x == "left":
            self.walk_left()
        else:
            self.walk_right()
        
class HoveringEnemy(Hover):
    """
    Extend Hover to represent a hovering enemy that can patrol back and forth.
    
    Inherits all behaviour from Component, Updateable, Positional, Collidable, Drawable, Animated, Sprite,
                                VelocityMovement, AccelerationMovement, AcceleratedHorizontal, AcceleratedVertical and Hover.
    Extends reset to unlock the sprite's hitbox and start moving.
    Patrolling is controlled by time, not position, so:
      - Be aware that solid collisions can disturb the patrolling route.
      - Remember you can set solids=() to ignore solid collisions.
    
    Public methods:
    reverse_patrol(): reverse movement in the patrolling axis (called by timer).
    
    Required animations: [default], also "stomped" if the enemy can be stomped.
    """
    def __init__(self, tileset, direction="left", patrol_time=None, **kwargs):
        """
        Extend superclasses to start moving in an initial direction and set oscillation and patrol (both optional).
        
        direction must be in ("left", "up", "right", "down"); movement will be set automatically according to this.
        Either leave patrol_time as none or set it to infinite (if that's how you roll) to opt out of patrolling.
        """
        movement = "horizontal" if direction in ("left", "right") else "vertical"
        super().__init__(tileset=tileset, movement=movement, **kwargs)
        
        {"left":self.hover_left, "up":self.hover_up, "right":self.hover_right, "down":self.hover_down}[direction]() # Cool dictionary trick :)
        if patrol_time and patrol_time < float("inf"):
            self.add_persistent_component(Cycle(patrol_time, self.reverse_patrol))

    def reverse_patrol(self):
        """Reverse movement in the patrolling axis (called by timer)."""
        if self._movement == "horizontal":
            if self.vel_x > 0:
                self.hover_left()
            else:
                self.hover_right()
        else:
            if self.vel_y > 0:
                self.hover_up()
            else:
                self.hover_down()

    def reset(self):
        """Extend Component to unlock the sprite's hitbox and start its movement."""
        super().reset()
        self.unlock_hitbox()
        exec("self.hover_{d}()".format(d=self._direction))