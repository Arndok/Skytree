"""
Definition of the base class for tree nodes --the core of the framework.

Component subclasses generally propagate their basic functionalities to their components with shared subclasses.
More specifically:
All Components propagate the game attribute and reset command.
Updateable components propagate update command and delta time.
Drawable components propagate draw command and canvas.
Collidable components propagate collision checks.
CommandReader components propagate commands (but only when they cannot process them themselves).
"""

from .helpers import bake_obj
from . import game

class Component:
    """
    An object that can be owned by another object and own others itself.
    
    This is the core of the framework. Most of a game's object structure is a tree graph
    and this class handles how the nodes are related. It includes functionality for
    adding name and tags to each object and keeping tracks of its components' name and tags.
    It also includes a data structure for handling object restoration on reset.
    
    Public methods:
    add_component(component): add a component to _component; set self as component's owner.
    remove_component(component): remove a component from _component; set None as component's owner.
    add_persistent_component(component): add a component that will persist on reset.
    remove_persistent_component(component): remove a component and stop it from persisting on reset.
    add_tag(tag): add tag and update owner.
    remove_tag(tag): remove tag and update owner.
    destroy(): remove this object from its previous owner and destroy its components. Use with caution.
    reset(): restore the component's established initial state (see init and reset for details).
    
    Notes on setters:
    Setting owner will call add_component and remove_component as needed.
    Setting name will update owner and raise an exception if the new name's already in use.
    Setting game will propagate through components.
    """
    
    def __init__(self, tags=(), name=None, components=(), game=None, **kwargs):
        """
        Component Constructor.
        
        tags is a collection of identifiers (intended for strings, but any hashable will do).
        name is a unique identifier (in the namespace of this component's owner).
        components is a collection of Component objects to be added as persistent on init.
          These objects can be passed pre-built or as (Type, {kwargs}) tuples.
          If passing pre-built objects that might be reused, be aware that adding them as
          components to another object will remove them from this one.
        """
        self._owner = None
        """The Component that owns this object."""
        self._components = set({})
        """The set of Components that are owned by this object."""
        self._name = name
        """A label that identifies this object for its owner (unique in that context)."""
        self._named = {}
        """A dictionary of components referenced by name."""
        self._tags = set(tags)
        """A set of tags that describe this object for its owner."""
        self._tagged = {}
        """A dictionary of sets of components referenced by tag."""
        self._reset_data = {"attributes":{}, "tags":set(tags), "components":set({})}
        """
        A dictionary of values and objects to be restored on component reset.
        
        To have an attribute be restored to a value on reset, add its name and desired
        value to reset_data["attributes"].
        To prevent a tag from being deleted on reset, and to have it restored if
        previously deleted, use the method add_tag with kwarg "persistent" set as True.
        To prevent a component from being destroyed on reset, and also to have it
        be restored if previously destroyed, include on them the tag "persistent"
        or add them with the method add_persistent_component.
        """
        self.game = game
        """
        A reference to the Game instance, which is the root of the Component tree.
        
        This will be set from the Game init and propagated through all present and future connected Components.
        """
        if name:
            self._reset_data["attributes"]["name"] = name
        for component in components:
            # Components passed on init are added as persistent.
            self.add_persistent_component(bake_obj(component))
        
    @property
    def owner(self):
        """Public reference to this object's owner."""
        return self._owner
        
    @owner.setter
    def owner(self, value):
        """Set owner; call remove_component on previous owner and add_component on new one."""
        if self._owner == value:
            return
            # Short out if value is already this Component's owner
        if self._owner and self in self._owner:
            self._owner.remove_component(self)
        self._owner = value
        if value:
            if not self in value:
                value.add_component(self)
        
    @property
    def tags(self):
        """Object tags (read-only)."""
        return self._tags
        
    @property
    def tagged(self):
        """Object components referenced by tag (read-only)."""
        return self._tagged
        
    @property
    def name(self):
        """Public reference to this object's name."""
        return self._name
        
    @name.setter
    def name(self, value):
        """
        Change this object's name if possible.
        
        Raise AttributeError if the new name is already
        in use on the object's owner's namespace.
        """
        if value == self._name:
            return
        if self._owner:
            if value in self._owner.named:
                raise AttributeError("Component tried to use a name that's already in use.")
            del self._owner.named[self._name]
        self._name = value
        if self._owner:
            self._owner.named[value] = self
        
    @property
    def named(self):
        """Object components referenced by name (read-only)."""
        return self._named
        
    @property
    def game(self):
        """The Game instance (the root of the tree)."""
        return self._game
    
    @game.setter
    def game(self, value):
        """Propagate value through all present components."""
        self._game = value
        for component in self:
            component.game = value
    
    def _add_component_to_tagged(self, component, tag):
        """Add the component to _tagged[tag]; add tag to _tagged if needed."""
        if tag in self._tagged:
            self._tagged[tag].add(component)
        else:
            self._tagged[tag] = set({component})
    
    def _remove_component_from_tagged(self, component, tag):
        """Remove the component from _tagged[tag]; remove tag from _tagged if needed."""
        if len(self._tagged[tag]) == 1:
            del self._tagged[tag]
        else:
            self._tagged[tag].remove(component)
    
    def add_component(self, component):
        """
        Add component to _components and set self as component's owner.
        
        Raise TypeError if the given object is not a Component.
        Add component to the named and tagged dictionaries as needed.
        Raise AttributeError if the object's name is already in use.
        Propagate reference to the Game instance.
        Return True if the component has been added; False otherwise.
        """
        if not isinstance(component, Component):
            raise TypeError(str(self) + " tried to add a component that's not a Component: " + str(component))
        if component in self._components:
            return False # Short out if component already present
        self._components.add(component)
        if component.name:
            if component.name in self._named:
                raise AttributeError("Component tried to use a name that's already in use.")
            else:
                self._named[component.name] = component
        for tag in component.tags:
            self._add_component_to_tagged(component, tag)
        if component.owner != self:
            component.owner = self
        if self._game:
            component.game = self._game
        return True

    def remove_component(self, component):
        """
        Remove component from _components and set None as component's owner.
        
        Raise TypeError if the given object is not a Component.
        Add component to the named and tagged dictionaries as needed.
        Return True if the component has been removed; False otherwise.
        """
        if not isinstance(component, Component):
            raise TypeError(str(self) + " tried to remove a component that's not a Component: " + str(component))
        if not (component in self._components):
            return False # Short out if component is absent
        self._components.remove(component)
        if component.name in self._named:
            del self._named[component.name]
        for tag in component.tags:
            self._remove_component_from_tagged(component, tag)
        if component.owner == self:
            component.owner = None
        return True

    def add_persistent_component(self, component):
        """
        Add the tag 'persistent' to the object and add it as a component.
        
        This tag will prevent the component from being destroyed on reset
        and also have it restored if it was previously destroyed.
        """
        component.add_tag("persistent", persistent=True)
        return self.add_component(component)
        
    def remove_persistent_component(self, component):
        """
        Remove the tag 'persistent' from the object and remove it as a component.
        
        This will remove a persistent object permanently.
        """
        component.remove_tag("persistent", persistent=True)
        return self.remove_component(component)

    def add_tag(self, tag, persistent=False):
        """
        Add a tag and update owner about it.
        
        Setting persistent to True will have the component keep this tag on reset.
        """
        if tag in self._tags:
            return
            # Short out if tag already in self._tags
        self._tags.add(tag)
        if persistent:
            self._reset_data["tags"].add(tag)
        if self._owner:
            self._owner._add_component_to_tagged(self, tag)

    def remove_tag(self, tag, persistent=False):
        """
        Remove a tag and update owner about it.
        
        Setting persistent to True will have the component not restore this tag on reset.
        """
        if not (tag in self._tags):
            return
            # Short out if tag not in self._tags
        self._tags.remove(tag)
        if persistent and tag in self._reset_data["tags"]:
            self._reset_data["tags"].remove(tag)
        if self._owner:
            self._owner._remove_component_from_tagged(self, tag)
        
    def destroy(self):
        """
        Remove this component from its current owner and propagate the command through its own components.
        
        Avoid calling this method directly, as destroying objects in the middle of the game loop
        will often yield unexpected (not the fun kind) behaviours. 
        Use Game.mark_for_destruction instead and let the game manager do the dirty work for you.
        """
        if "persistent" in self.tags:
            self.owner._reset_data["components"].add(self)
        self.owner = None
        for component in self._components.copy():
            component.destroy()
            
    def reset(self):
        """
        Restore initial data and propagate command through components.
        
        Restore value of attributes on reset_data["attributes"].
        Restore deleted tags from reset_data["tags"] and delete added tags not registered there.
        Restore removed components from reset_data["components"] and remove added components
        not registered there.
        Extend on subclasses to recover initial state as needed.
        """
        # Restore attribute values.
        # Account for float('inf') (it gets stored in a dict as inf).
        inf = float('inf')
        for item in self._reset_data["attributes"]:
            # Account for string values.
            reset_val = "'{v}'".format(v=self._reset_data["attributes"][item]) if isinstance(self._reset_data["attributes"][item], str) else self._reset_data["attributes"][item]
            exec("self.{i} = {d}".format(i=item, d=reset_val))
        
        # Restore tags.
        for tag in self.tags.difference(self._reset_data["tags"]):
            self.remove_tag(tag)
        for tag in self._reset_data["tags"].difference(self.tags):
            self.add_tag(tag)
        
        # Restore components.
        for item in self._reset_data["components"]:
            self.add_component(item)
        self._reset_data["components"].clear()
        
        for component in self._components:
            if "persistent" in component.tags:
                # Propagate command through persistent components.
                component.reset()
            else:
                # Destroy non-persistent components.
                # Again, better destroy objects at the bottom of the loop.
                if self.game:
                    self.game.mark_for_destruction(component)
                else:
                    component.destroy()
    
    def __iter__(self):
        """Iterate over self._components."""
        return iter(self._components)