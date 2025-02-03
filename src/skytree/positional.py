"""Definition of a Component subclass that can have a presence in a 2d space."""

from skytree.component import Component

class Positional(Component):
    """
    A Component that holds 2D position and velocity information.
    
    Inherits all Component behaviour.
    
    Velocity can be descriptive or prescriptive. Implement on subclasses
    whether velocity affects position or viceversa.
    
    Public methods:
    get_position_of(label): return the position of the component with name matching given label.
    """
    
    def __init__(self, pos=(0,0), vel=(0,0), **kwargs):
        """Store position and velocity; set reset data."""
        super().__init__(**kwargs)
        self.pos = pos
        """The component's 2D position."""
        self.vel = vel
        """The component's 2D velocity."""
        self._reset_data["attributes"].update({"pos": pos, "vel": vel})
        
    @property
    def pos(self):
        """Object 2D position."""
        return tuple((self.x, self.y))
        
    @pos.setter
    def pos(self, value):
        self.x, self.y = value
    
    @property
    def vel(self):
        """Object 2D velocity."""
        return tuple((self.vel_x, self.vel_y))
        
    @vel.setter
    def vel(self, value):
        self.vel_x, self.vel_y = value
    
    def get_position_of(self, label):
        """Return the position of the component with name matching given label; return None if absent."""
        return self.named[label].pos if label in self.named else None