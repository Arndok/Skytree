"""Definition of a Component subclass that can keep track of time and do some work on every frame, or hold other components that do so."""

from .component import Component

class Updateable(Component):
    """
    Extend Component to update on every frame.
    
    Inherits all Component behaviour.
    Extends Component.add_component(component) and Component.remove_component(component).
    
    A component must be Updateable for its own components to be updated.
    
    Public method
    update(dt): receive delta time and do whatever work needs to be done on every frame.
    """
    def __init__(self, **kwargs):
        """Extend Component to include an _updateable list."""
        self._updateable = []
        """
        A list of updateable components.
        
        The use of an indexable collection will let us extend the class
        in the future to keep track of component update order if needed.
        """
        super().__init__(**kwargs)
        
    @property
    def updateable(self):
        """Public reference to this object's updateable components list (read-only)."""
        return self._updateable
        
    def add_component(self, component):
        """Extend Component to add component to _updateable if successful."""
        if super().add_component(component):
            if isinstance(component, Updateable):
                self._updateable.append(component)
            return True
        return False

    def remove_component(self, component):
        """Extend Component to remove component from _updateable if successful."""
        if super().remove_component(component):
            if isinstance(component, Updateable):
                self._updateable.remove(component)
            return True
        return False
        
    def update(self, dt):
        """
        Template to be extended by subclasses that need to do some work on every frame.
        
        Propagate through components.
        dt is delta time (time elapsed since previous frame),
        passed by Game at the root level.
        """
        for component in self._updateable: component.update(dt)