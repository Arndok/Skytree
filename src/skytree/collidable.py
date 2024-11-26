"""
Definition of Hitbox classes and a Positional Component (Collidable) that uses them.

Classes:
Hitbox(ABC): base abstract class for a hitbox; subclasses can test overlapping with other hitboxes.
PointHB(Hitbox): a point hitbox.
RectHB(Hitbox): a rect hitbox.
CircleHB(Hitbox): a circle hitbox.
Collidable(Positional): a Component that can have a hitbox and functionalities to test collisions with it, or hold other components that do so.

To add more collision shapes:
  - Define new Hitbox subclass with its new collision methods.
  - Update all other Hitbox subclasses to include a collision method for the new shape.
  - Update Hitbox.collide method (on superclass).

Beyond sprite collisions with solids (which is its own thing; check sprites.VelocityMovement):
  to code collision behaviours to a Collidable object, use tags on objects to check collisions with
  and implement on subclasses methods with name '_collided_[tag]' that accept an object as an argument.
  Tags used in these names can't have underscores in them.
"""

import warnings
from abc import ABC, abstractmethod
from pygame import Rect
from skytree.helpers import distance, repack2
from skytree.positional import Positional

##########
# SHAPES #
##########

class Hitbox(ABC):
    """
    A 2D shape that will be owned by a Component and used to check collisions with other Components.
    
    Can hold a 2D offset (in relation to its owner's position).
    Changes to a Hitbox position will relocate its owner and viceversa.
    Subclasses must implement virtual attributes left, top, right, bottom, center,
      centerx, centery, width, height and dim.
    
    Public methods:
    collides(hitbox): routes the command to the appropriate shape-specific method;
      returns True if the shapes overlap and False otherwise.
    Shape-specific abstract collision testing methods:
      collidepoint(hitbox)
      colliderect(hitbox)
      collidecircle(hitbox)
    
    Notes on setters:
    Setting x, y or pos will update this object's owner's position.
    """
    
    def __init__(self, pos, dim=None, offset=(0,0)):
        """
        Initialize the hitbox's position and owner
        (we have to do it manually since this isn't a Component subclass).
        
        Owner will be set automatically when hitbox is assigned to a Collidable.
        pos is a 2D position.
        dim is a shape-dependent variable representing dimension.
        offset is a 2D offset in relation to this object's owner's position.
        """
        self.owner = None
        """This object's owner."""
        self.offset = offset
        """The offset of this object's position in relation to its owner's."""
        self._x, self._y = (pos[0] + offset[0], pos[1] + offset[1])
        """
        This object's position.
        
        Modify private x and y to avoid trying to update owner's position.
        """
        
    @property
    def offset(self):
        """Hitbox's offset (x, y)."""
        return tuple((self.offset_x, self.offset_y))
        
    @offset.setter
    def offset(self, value):
        self.offset_x, self.offset_y = repack2(value)
        
    @property
    def pos(self):
        """Hitbox's 2D position (x, y)."""
        return tuple((self._x, self._y))
        
    @pos.setter
    def pos(self, value):
        self.x, self.y = value

    @property
    def x(self):
        """Hitbox' x position."""
        return self._x
        
    @x.setter
    def x(self, value):
        """Update owner's x position each time the hitbox's moved horizontally."""
        self._x = value
        if self.owner and self.owner.x != self.x - self.offset_x:
            self.owner.x = self.x - self.offset_x

    @property
    def y(self):
        """Hitbox' y position."""
        return self._y
        
    @y.setter
    def y(self, value):
        """Update owner's y position each time the hitbox's moved vertically."""
        self._y = value
        if self.owner and self.owner.y != self.y - self.offset_y:
            self.owner.y = self.y - self.offset_y

    @property
    def left(self):
        """Hitbox' leftmost x position."""
        return self._x
        
    @left.setter
    def left(self, value):
        self.x = value
        
    @property
    def top(self):
        """Hitbox' topmost y position."""
        return self._y

    @top.setter
    def top(self, value):
        self.y = value

    def collides(self, hitbox):
        """Read hitbox shape and route the command to the appropriate method."""
        if not isinstance(hitbox, Hitbox):
            warnings.warn("Tried to collide hitbox {s} with {h} (not a Hitbox).".format(s=self, h=hitbox), RuntimeWarning)
            return False
        elif isinstance(hitbox, PointHB):
            return self.collidepoint(hitbox)
        elif isinstance(hitbox, RectHB):
            return self.colliderect(hitbox)
        elif isinstance(hitbox, CircleHB):
            return self.collidecircle(hitbox)
        else:
            warnings.warn("Shape {s} of {h} not recognized; check Collidable module.".format(s=type(hitbox).__name__, h=hitbox), RuntimeWarning)
            return False

    @abstractmethod
    def collidepoint(self, hitbox): 
        """Test point collision."""
        pass
        
    @abstractmethod
    def colliderect(self, hitbox): 
        """Test rect collision."""
        pass
        
    @abstractmethod
    def collidecircle(self, hitbox): 
        """Test circle collision."""
        pass

class PointHB(Hitbox):
    """
    Extend Hitbox to represent a 2D point.
    
    Inherits position behaviour from Hitbox.
    (changes to a Hitbox position will relocate its owner and viceversa).
    Implements collidepoint, colliderect and collidecircle.
    """

    @property
    def right(self):
        """Point's rightmost x position."""
        return self._x
        
    @right.setter
    def right(self, value):
        self.x = value
        
    @property
    def bottom(self):
        """Point's bottommost y position."""
        return self._y
        
    @bottom.setter
    def bottom(self, value):
        self.y = value
        
    @property
    def centerx(self):
        """Point's center x position."""
        return self._x
        
    @centerx.setter
    def centerx(self, value):
        self.x = value
        
    @property
    def centery(self):
        """Point's center y position."""
        return self._y
        
    @centery.setter
    def centery(self, value):
        self.y = value
        
    @property
    def center(self):
        """Point's central point."""
        return tuple((self._x, self._y))
        
    @center.setter
    def center(self, value):
        self.x, self.y = value
        
    @property
    def width(self):
        """Point's width."""
        return 1
        
    @property
    def height(self):
        """Point's height."""
        return 1
        
    @property
    def dim(self):
        """Point's 2D dimensions."""
        return 1
            
    def collidepoint(self, hitbox):
        """Override Hitbox; test point-point collision."""
        return self.pos == hitbox.pos
        
    def colliderect(self, hitbox):
        """Override Hitbox; test point-rect collision."""
        return Rect(hitbox.pos, hitbox.dim).collidepoint(self.pos)
        
    def collidecircle(self, hitbox):
        """Override Hitbox; test point-circle collision."""
        return distance(self.pos, hitbox.center) <= hitbox.radius
            
class RectHB(Hitbox):
    """
    Extend Hitbox to represent a rectangle.
    
    Inherits position behaviour from Hitbox
    (changes to a Hitbox position will relocate its owner and viceversa).
    Implements collidepoint, colliderect and collidecircle.
    """

    def __init__(self, pos, dim, offset=(0,0)):
        """
        Extend Hitbox to store dimensions (width, height).
        
        dim is a tuple (width, height) or a single number (for a square hitbox).
        pos and offset are delegated to superclass.
        """
        super().__init__(pos, offset=offset)
        self.dim = dim
        """Rectangular hitbox' width and height."""

    @property
    def right(self):
        """Rect's rightmost x position."""
        return self._x + (self.width-1)
        
    @right.setter
    def right(self, value):
        self.x = value - (self.width-1)
        
    @property
    def bottom(self):
        """Rect's bottommost y position."""
        return self._y + (self.height-1)
        
    @bottom.setter
    def bottom(self, value):
        self.y = value - (self.height-1)
        
    @property
    def centerx(self):
        """Rect's center x position."""
        return self._x + int(self.width/2)
        
    @centerx.setter
    def centerx(self, value):
        self.x = value - int(self.width/2)
        
    @property
    def centery(self):
        """Rect's center y position."""
        return self._y + int(self.height/2)
        
    @centery.setter
    def centery(self, value):
        self.y = value - int(self.height/2)
        
    @property
    def center(self):
        """Rect's central point."""
        return tuple((self._x + int(self.width/2), self._y + int(self.height/2)))
        
    @center.setter
    def center(self, value):
        self.x, self.y = value[0] - int(self.width/2), value[1] - int(self.height/2)
        
    @property
    def dim(self):
        """Rect's 2D dimensions."""
        return tuple((self.width, self.height))
    
    @dim.setter
    def dim(self, value):
        self.width, self.height = repack2(value)
        
    def collidepoint(self, hitbox):
        """Override Hitbox; test rect-point collision."""
        return Rect(self.pos, self.dim).collidepoint(hitbox.pos)
        
    def colliderect(self, hitbox):
        """Override Hitbox; test rect-rect collision."""
        return Rect(self.pos, self.dim).colliderect(Rect(hitbox.pos, hitbox.dim))
        
    def collidecircle(self, hitbox):
        """Override Hitbox; test rect-circle collision."""
        return hitbox.colliderect(self)
            
class CircleHB(Hitbox):
    """
    Extend Hitbox to represent a circle.
    
    Inherits position behaviour from Hitbox
    (changes to a Hitbox position will relocate its owner and viceversa).
    Implements collidepoint, colliderect and collidecircle.
    """

    def __init__(self, pos, dim, offset=(0,0)):
        """
        Extend Hitbox to store dim (radius).
        
        dim is intended as a single number representing radius.
          This also accepts a tuple of two numbers, because hitbox dimensions can be
          calculated from a draw rect. In that case, we'll interpret width/2 as radius.
          Raises ValueError if dim doesn't fit any of these two formats.
        pos and offset are delegated to superclass.
        """
        super().__init__(pos, offset=offset)
        if isinstance(dim, (int, float)):
            self.radius = dim
            """Circular hitbox' radius."""
        elif isinstance(dim, tuple) and isinstance(dim[0], (int, float)) and dim[0] == dim[1]:
            self.radius = dim[0]*0.5
        else:
            raise ValueError("Tried to initialize a circular hitbox with radius {r}. \
                              Use either a number or the dimensions (side, side) of a square.".format(r=dim))

    @property
    def right(self):
        """Circle's rightmost x position."""
        return self._x + ((self.radius*2)-1)
        
    @right.setter
    def right(self, value):
        self.x = value - ((self.radius*2)-1)
        
    @property
    def bottom(self):
        """Circle's bottommost y position."""
        return self._y + ((self.radius*2)-1)
        
    @bottom.setter
    def bottom(self, value):
        self.y = value - ((self.radius*2)-1)
        
    @property
    def centerx(self):
        """Circle's center x position."""
        return self._x + self.radius
        
    @centerx.setter
    def centerx(self, value):
        self.x = value - self.radius
        
    @property
    def centery(self):
        """Circle's center y position."""
        return self._y + self.radius
        
    @centery.setter
    def centery(self, value):
        self.y = value - self.radius
        
    @property
    def center(self):
        """Circle's central point."""
        return tuple((self._x + self.radius, self._y + self.radius))
        
    @center.setter
    def center(self, value):
        self.x, self.y = value[0] - self.radius, value[1] - self.radius
        
    @property
    def width(self):
        """Circle's width."""
        return self.radius * 2

    @width.setter
    def width(self, value):
        self.radius = value / 2
        
    @property
    def height(self):
        """Circle's height."""
        return self.radius * 2

    @height.setter
    def height(self, value):
        self.radius = value / 2
        
    @property
    def dim(self):
        """Circle's dimensions (alias for radius)."""
        return self.radius
        
    @dim.setter
    def dim(self, value):
        self.radius = value
            
    def collidepoint(self, point):
        """Override Hitbox; test circle-point collision."""
        return distance(self.center, point.pos) <= self.radius
        
    def colliderect(self, rect):
        """Override Hitbox; test circle-rect collision."""
        # Find vertical and horizontal distances between object centers
        x_dist = abs(self.centerx - rect.centerx)
        y_dist = abs(self.centery - rect.centery)
        # Store half rect dimensions
        x_half_rect = rect.width/2
        y_half_rect = rect.height/2
        # Discard collision if any of these distances is greater than radius + half rect
        if x_dist > self.radius + x_half_rect or y_dist > self.radius + y_half_rect:
            return False
        # Confirm collision if any of these distances is less than or equal to half rect
        if x_dist <= x_half_rect or y_dist <= y_half_rect:
            return True
        # Check for corner collisions
        return distance((x_dist, y_dist), (x_half_rect, y_half_rect)) <= self.radius
        
    def collidecircle(self, circle):
        """Override Hitbox; test circle-circle collision."""
        return distance(self.center, circle.center) <= (self.radius + circle.radius)
        
####################
# COLLIDABLE CLASS #  
####################

class Collidable(Positional):
    """
    Extend Positional to have a collidable hitbox.
    
    Inherits all Component and Positional behaviour.
    Extends Component.add_component(component) and Component.remove_component(component).
    
    A component must be Collidable to propagate collision queries to its own components.
    Changes to this object's position will relocate its hitbox and viceversa.
    To code collision behaviours to a Collidable object, use tags on objects to check collisions with and
      implement on subclasses methods with name '_collided_[tag]' that accept an object as an argument.
      Tags used in these names can't have underscores in them.
    
    Public methods:
    collides(obj): return True if obj's hitbox collides with self's, False otherwise.
    get_collisions(obj, obj_tags): check self and components and return a set of colliding objects (route to get_collisions_hitbox if needed).
    get_collisions_hitbox(hitbox, obj_tags): check self and components and return a set of colliding objects.
    lock_hitbox(): disable the hitbox.
    unlock_hitbox(): enable the hitbox.
    
    Notes on setters:
    Setting hitbox, x or y will update the hitbox' position using this object's.
    """

    def __init__(self, hb_dim=None, Shape=RectHB, hb_offset=(0,0), **kwargs):
        """
        Extend Component to include a _collidable set and generate a hitbox if needed.
        
        hb_dim is a shape-dependent variable.
        Shape is a Hitbox subclass; defaults to RectHB.
        hb_offset is the 2D offset between the Component's position and its hitbox's.
        """
        self._collidable = set({})
        """A set of collidable components."""
        # Storing a hitbox will ask for its owner's position, which is only there after Positional init.
        # On the other hand, setting position will check whether there's a hitbox to relocate.
        # So: declare hitbox -> perform super init -> actually build hitbox.
        self._hitbox = None
        """The component's hitbox."""
        super().__init__(**kwargs)
        if hb_dim or Shape==PointHB:
            self.hitbox = Shape(self.pos, hb_dim, offset=hb_offset)
        self._hb_lock = False
        """Whether the hitbox is disabled or not."""
        self.collides_with = set([col.split("_")[2] for col in filter(lambda x: x[:10]=="_collided_", dir(self))])
        """
        A set of tags this component recognizes and tests collisions with.
        
        Constructed automatically from implemented methods with name "_collided_[tag]."
        """

    @property
    def collidable(self):
        """Public reference to this object's collidable components set (read-only)."""
        return self._collidable
    
    @property
    def hitbox(self):
        """Object's hitbox."""
        return self._hitbox
        
    @hitbox.setter
    def hitbox(self, value):
        """Set self as Hitbox' owner; move Hitbox to self.pos"""
        self._hitbox = value
        if value:
            self._hitbox.pos = self.x + self._hitbox.offset_x, self.y + self._hitbox.offset_y
            self._hitbox.owner = self
        
    def __setattr__(self, name, value):
        """
        Extend object setter to update hitbox position when position is changed.
        
        This method avoids overriding Positional; it's slower than using property decorators, though.
        """
        super().__setattr__(name, value)
        if name == "x":
            if self._hitbox and self._hitbox.x != self.x + self._hitbox.offset_x:
                self._hitbox.x = self.x + self._hitbox.offset_x
        elif name == "y" and self._hitbox and self._hitbox.y != self.y + self._hitbox.offset_y:
            self._hitbox.y = self.y + self._hitbox.offset_y
        
    def _collided(self, obj):
        """
        For every object tag, call its collision method if implemented.
        
        Return True if this entity needs to stop its collision checks (e.g if it has self-destroyed).
        Include returns on _collided_[tag] methods if needed for this purpose.
        """
        for tag in obj.tags.intersection(self.collides_with):
            if eval("self._collided_"+tag)(obj):
                return True
        
    def add_component(self, component):
        """Extend Component to add component to _collidable if successful."""
        if super().add_component(component):
            if isinstance(component, Collidable):
                self._collidable.add(component)
            return True
        return False

    def remove_component(self, component):
        """Extend Component to remove component from _collidable if successful."""
        if super().remove_component(component):
            if isinstance(component, Collidable):
                self._collidable.remove(component)
            return True
        return False
        
    def collides(self, obj):
        """Return True in case of collision, False otherwise."""
        return self._hitbox and obj.hitbox and self._hitbox.collides(obj.hitbox)
        
    def get_collisions(self, obj, obj_tags=None):
        """
        Return a set containing every collision between the given object and this entity or its components.
        
        Route the command to get_collisions_hitbox if obj is a hitbox.
        A collision is positive when hitboxes overlap and there's a match between obj_tags and entity tags.
        obj_tags default to the object's collides_with set, but a different set can be passed to check
          for a specific kind of collision (such as solid objects).
        """
        if isinstance(obj, Hitbox):
            return self.get_collisions_hitbox(obj, obj_tags)
        collisions = set({})
        obj_tags = obj_tags if obj_tags else obj.collides_with
        if not self._hb_lock and self.tags.intersection(obj_tags) and self.collides(obj):
            collisions.add(self)
        for component in self.collidable:
            if not component == obj:
                collisions.update(component.get_collisions(obj, obj_tags))
        return collisions
        
    def get_collisions_hitbox(self, hitbox, obj_tags):
        """
        Return a set containing every collision between the given hitbox and this entity or its components.
        
        A collision is positive when hitboxes overlap and there's a match between obj_tags and entity tags.
        """
        collisions = set({})
        if not self._hb_lock and self.tags.intersection(obj_tags) and self.hitbox.collides(hitbox):
            collisions.add(self)
        for component in self.collidable:
            collisions.update(component.get_collisions_hitbox(hitbox, obj_tags))
        return collisions
        
    def lock_hitbox(self):
        """Disable the hitbox."""
        self._hb_lock = True
        
    def unlock_hitbox(self):
        """Enable the hitbox."""
        self._hb_lock = False