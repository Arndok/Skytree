"""Definition of a Positional Component that can be drawn into a canvas or hold other components that do so."""

from pygame import Rect, Surface, SRCALPHA
from .helpers import repack2
from .positional import Positional
from .resource_manager import ResourceManager

class Drawable(Positional):
    """
    Extend Positional to draw on every frame.
    
    Inherits all Component and Positional behaviour.
    Extends Component.add_component(component) and Component.remove_component(component).
    
    A component must be Drawable for its own components to be drawn.
    
    Public methods:
    draw(canvas): renders self and components on canvas; called from root on every frame.
    Draw layer manipulation (for these methods, pass a component to apply to them or don't to apply to self):
        get_draw_layer(component): return index on _drawable
        set_draw_layer(idx, component): move to stated index on _drawable
        move_forward(component): move to next position on _drawable
        move_backward(component): move to previous position on _drawable
        move_to_front(component): move to last position on _drawable
        move_to_back(component): move to first position on _drawable
    One-time alignment (for these methods, pass a canvas to use as reference or don't to try and use owner canvas):
        align_left(canvas): align left to given canvas
        align_top(canvas): align top to given canvas
        align_right(canvas): align right to given canvas
        align_bottom(canvas): align bottom to given canvas
        align_center_x(canvas): align horizontal center to given canvas
        align_center_y(canvas): align vertical center to given canvas
        align_center(canvas): align center to given canvas
        align_proportion_x(proportion, canvas): align horizontally to given canvas following proportion
        align_proportion_y(proportion, canvas): align vertically to given canvas following proportion
        align_proportion(proportion, canvas): align to given canvas following proportion
    Alignment on draw time:
        set_align_left(): align left on draw time
        set_align_top(): align top on draw time
        set_align_right(): align right on draw time
        set_align_bottom(): align bottom on draw time
        set_align_center_x(): align horizontal center on draw time
        set_align_center_y(): align vertical center on draw time
        set_align_center(): align center on draw time
        set_align_proportion_x(proportion): align horizontally on draw time following proportion
        set_align_proportion_y(proportion): align vertically on draw time following proportion
        set_align_proportion(proportion): align on draw time following proportion
        clear_alignment_x(): cancel horizontal alignment on draw time
        clear_alignment_y(): cancel vertical alignment on draw time
        clear_alignment(): cancel alignment on draw time
        
    Notes on setters:
    canvas can be set as 2D dimensions (tuple or single number), a Pygame Surface, an image filename or None.
    It will also update this object's draw rectangle.
    frame can be set as 2D dimensions (tuple or single number), a Pygame Rect or None.
    """
    
    def __init__(self, canvas=None, frame=None, subsurface=False, bgcolor=(0,0,0,0), **kwargs):
        """
        Extend Component to include a _drawable list and generate a canvas \
        and/or frame if needed.
        
        canvas can be None, Pygame Surface, image filename or dimensions (single or (width, height)).
        Pygame draw methods can be used to build an image on a Surface.
        frame can be None or dimensions (single or (width, height)).
        subsurface can be set as True to have this object draw its components on its canvas on main draw.
        bgcolor can be set for subsurfaces (transparent by default).
        """
        self._drawable = []
        """
        A list of drawable components.
        
        Manageable through draw layer manipulation methods (see below).
        """
        super().__init__(**kwargs)
        self._align_x = None
        """An attribute that can hold a proportion in [0,1] for horizontal alignment on draw time."""
        self._align_y = None
        """An attribute that can hold a proportion in [0,1] for vertical alignment on draw time."""
        self._draw_rect = None
        """The draw rectangle of this component."""
        self.canvas = canvas
        """The drawable surface of this component."""
        self.frame = frame if frame else self.dim
        """The drawing frame of this component. Defaults to canvas dimensions."""
        self._subsurface = subsurface
        """
        When True, this component'll draw its own components on its canvas instead of passing them down the tree.
        
        Defaults to False.
        """
        self.bgcolor = bgcolor
        """Background colour, mainly for subsurfaces. Defaults to transparent."""
    
    @property
    def drawable(self):
        """Public reference to this object's drawable components list (read-only)."""
        return self._drawable
        
    @property
    def canvas(self):
        """This object's drawable surface (Pygame Surface)."""
        return self._canvas
        
    @canvas.setter
    def canvas(self, value):
        """
        Build canvas if needed and update draw rect.
        
        value can be:
          - None (empty canvas and dimensionless draw rect)
          - Pygame Surface
          - Image filename (try to load it)
          - Dimensions (single number for square or (width, height) for rectangle)
        """
        if not value or isinstance(value, Surface): # Empty canvas or Pygame Surface
            self._canvas = value
        elif isinstance(value, str): # Image file name
            self._canvas = ResourceManager().get_image(value)
        elif isinstance(value, (int, float)): # Single number
            self._canvas = Surface((int(value), int(value)), SRCALPHA)
        else:
            try: # (width, height)
                self._canvas = Surface((int(value[0]), int(value[1])), SRCALPHA)
            except (IndexError, ValueError) as err:
                print ("Drawable tried to set canvas {c}. Canvas may be number, (width, height), image, file name or None. --".format(c=value), err)
                raise
        self._draw_rect = self._canvas.get_rect() if self._canvas else Rect(0,0,0,0)
        
    @property
    def draw_rect(self):
        """Draw rect for object canvas (Pygame Rect)."""
        return self._draw_rect
        
    @property
    def frame(self):
        """Object frame (Pygame Rect)."""
        return self._frame
        
    @frame.setter
    def frame(self, value):
        """
        Build frame if needed.
        
        value can be:
         - None (dimensionless rect)
         - Pygame Rect
         - Dimensions (single number for square or (width, height) for rectangle)
        """
        if value is None or isinstance(value, Rect):
            self._frame = value
        else:
            try:
                self._frame = Rect((0,0), repack2(value))
            except Exception as err:
                print(("Drawable tried to set frame with dimensions {d} --".format(d=value)), err)
                raise
        
    @property
    def width(self):
        """Object width (from its draw_rect)."""
        return self._draw_rect.width
        
    @property
    def height(self):
        """Object height (from its draw_rect)"""
        return self._draw_rect.height
        
    @property
    def dim(self):
        """Object 2D dimensions (from its draw_rect)."""
        return tuple((self._draw_rect.width, self._draw_rect.height))
        
    @property
    def frame_width(self):
        """Object's frame's width."""
        return self.frame.width
        
    @property
    def frame_height(self):
        """Object's frame's height."""
        return self.frame.height
        
    @property
    def frame_dim(self):
        """Object's frame's 2D dimensions."""
        return tuple((self.frame.width, self.frame.height))
            
    def add_component(self, component):
        """Extend Component to add component to _drawable if successful."""
        if super().add_component(component):
            if isinstance(component, Drawable):
                self._drawable.append(component)
            return True
        return False

    def remove_component(self, component):
        """Extend Component to remove component from _drawable if successful."""
        if super().remove_component(component):
            if isinstance(component, Drawable):
                self._drawable.remove(component)
            return True
        return False

    def _get_owner_canvas(self):
        """
        Return this object's owner's canvas.
        
        Raise LookupError if this object has no owner.
        """
        if self._owner and self._owner._canvas:
            return self._owner._canvas
        else:
            raise LookupError("Unowned drawable tried to access its owner.")
        
    def _render_canvas(self, canvas):
        """Apply alignment settings, update draw_rect position and render own canvas on given one."""
        # These values can be 0 (so can't use "if self._align_x")
        if not (self._align_x is None):
            self.align_proportion_x(canvas, self._align_x)
        if not (self._align_y is None):
            self.align_proportion_y(canvas, self._align_y)
        self._draw_rect.x, self._draw_rect.y = self.pos
        canvas.blit(self.canvas, self._draw_rect, self.frame)
            
    def _render_components(self, canvas):
        """Propagate draw command through all drawable components."""
        for component in self._drawable: component.draw(canvas)
            
    def draw(self, canvas):
        """
        Render own canvas if present, then render components. 
        
        Component positions are relative to root canvas (or closest subsurface).
        """
        if self._subsurface: 
            self.canvas.fill(self.bgcolor)
            self._render_components(self.canvas)
        if self.canvas:
            self._render_canvas(canvas)
        if not self._subsurface:
            self._render_components(canvas)

    ###########################
    # DRAW LAYER MANIPULATION #
    ###########################
    
    def get_draw_layer(self, component=None):
        """
        Return component/self draw layer index.
        
        Pass a component to use the method on it (over drawable);
        don't pass a component to use the method on self (over owner.drawable).
        """
        if not component:
            if not self._owner:
                raise AttributeError("{s} tried to get its draw layer while having no owner. --".format(s=self))
            return self._owner.get_draw_layer(self)

        try:
            return self._drawable.index(component)
        except ValueError as err:
            print("Drawable tried to get draw layer of absent component {c} --".format(c=component), err)
            raise

    def set_draw_layer(self, idx, component=None):
        """
        Set component/self draw layer index.
        
        Pass a component to use the method on it (over drawable);
        don't pass a component to use the method on self (over owner.drawable).
        """
        if not component:
            if not self._owner:
                raise AttributeError("{s} tried to set its draw layer while having no owner. --".format(s=self))
            self._owner.set_draw_layer(idx, self)
            return

        if idx >= len(self._drawable):
            raise IndexError("Drawable tried to set illegal draw layer {i} --".format(i=idx))
        if not component in self.drawable:
            raise ValueError("Drawable tried to set draw layer of absent component {c}".format(c=component))

        self._drawable.remove(component)
        self._drawable.insert(idx, component)

    def move_forward(self, component=None):
        """
        Move component/self forwards one position.
        
        Pass a component to use the method on it (over drawable);
        don't pass a component to use the method on self (over owner.drawable).
        """
        if not component:
            if not self._owner:
                raise AttributeError("{s} tried to increase its drawing priority while having no owner. --".format(s=self))
            self._owner.move_forward(self)
            return
            
        try:
            idx = self._drawable.index(component)
        except ValueError as err:
            print("Drawable tried to move forward absent component {c} --".format(c=component), err)
            raise

        self.set_draw_layer(idx+1, component)

    def move_backward(self, component=None):
        """
        Move component/self backwards one position.
        
        Pass a component to use the method on it (over drawable);
        don't pass a component to use the method on self (over owner.drawable).
        """
        if not component:
            if not self._owner:
                raise AttributeError("{s} tried to decrease its drawing priority while having no owner. --".format(s=self))
            self._owner.move_backward(self)
            return

        try:
            idx = self._drawable.index(component)
        except ValueError as err:
            print("Drawable tried to move backward absent component {c} --".format(c=component), err)
            raise
            
        self.set_draw_layer(idx-1, component)

    def move_to_front(self, component=None):
        """
        Move component/self to front.
        
        Pass a component to use the method on it (over drawable);
        don't pass a component to use the method on self (over owner.drawable).
        """
        if not component:
            if not self._owner:
                raise AttributeError("{s} tried to get max drawing priority while having no owner. --".format(s=self))
            self._owner.move_to_front(self)
            return

        self.set_draw_layer(len(self._drawable)-1, component)
        
    def move_to_back(self, component=None):
        """
        Move component/self to back.
        
        Pass a component to use the method on it (over drawable);
        don't pass a component to use the method on self (over owner.drawable).
        """
        if not component:
            if not self._owner:
                raise AttributeError("{s} tried to get min drawing priority while having no owner. --".format(s=self))
            self._owner.move_to_back(self)
            return
            
        self.set_draw_layer(0, component)

    ################################
    # IMMEDIATE ONE-TIME ALIGNMENT #
    ################################
    
    def align_left(self, canvas=None):
        """
        Align self to canvas left.
        
        Pass a canvas to use as a reference; 
        don't pass a canvas to try to use owner's.
        """
        if not canvas:
            canvas = self._get_owner_canvas()
        self.x = canvas.get_rect().left
    
    def align_top(self, canvas=None):
        """
        Align self to canvas top.
        
        Pass a canvas to use as a reference; 
        don't pass a canvas to try to use owner's.
        """
        if not canvas:
            canvas = self._get_owner_canvas()
        self.y = canvas.get_rect().top
        
    def align_right(self, canvas=None):
        """
        Align self to canvas right.
        
        Pass a canvas to use as a reference; 
        don't pass a canvas to try to use owner's.
        """
        if not canvas:
            canvas = self._get_owner_canvas()
        self.x = canvas.get_rect().right - self._draw_rect.width
        
    def align_bottom(self, canvas=None):
        """
        Align self to canvas bottom.
        
        Pass a canvas to use as a reference; 
        don't pass a canvas to try to use owner's.
        """
        if not canvas:
            canvas = self._get_owner_canvas()
        self.y = canvas.get_rect().bottom - self._draw_rect.height
        
    def align_center_x(self, canvas=None):
        """
        Align self to canvas center horizontally.
        
        Pass a canvas to use as a reference; 
        don't pass a canvas to try to use owner's.
        """
        if not canvas:
            canvas = self._get_owner_canvas()
        self.x = int((canvas.get_rect().width - self._draw_rect.width)/2)
        
    def align_center_y(self, canvas=None):
        """
        Align self to canvas center vertically.
        
        Pass a canvas to use as a reference; 
        don't pass a canvas to try to use owner's.
        """
        if not canvas:
            canvas = self._get_owner_canvas()
        self.y = int((canvas.get_rect().height - self._draw_rect.height)/2)
        
    def align_center(self, canvas=None):
        """
        Align self to canvas center.
        
        Pass a canvas to use as a reference; 
        don't pass a canvas to try to use owner's.
        """
        if not canvas:
            canvas = self._get_owner_canvas()
        canvas_rect = canvas.get_rect()
        self.pos = [int((canvas_rect.width - self._draw_rect.width)/2),
                    int((canvas_rect.height - self._draw_rect.height)/2)]
                    
    def align_proportion_x(self, proportion, canvas=None):
        """
        Align self to canvas horizontally following a proportion.
        
        Pass a canvas to use as a reference; 
        don't pass a canvas to try to use owner's.
        proportion clamps between 0 and 1.
        """
        if not canvas:
            canvas = self._get_owner_canvas()
        proportion = min(max(proportion,0), 1)
        self.x = int((canvas.get_rect().width - self._draw_rect.width)*proportion)
        
    def align_proportion_y(self, proportion, canvas=None):
        """
        Align self to canvas vertically following a proportion.
        
        Pass a canvas to use as a reference; 
        don't pass a canvas to try to use owner's.
        proportion clamps between 0 and 1.
        """
        if not canvas:
            canvas = self._get_owner_canvas()
        proportion = min(max(proportion,0), 1)
        self.y = int((canvas.get_rect().height - self._draw_rect.height)*proportion)
        
    def align_proportion(self, proportion, canvas=None):
        """
        Align self to canvas vertically following a proportion.
        
        Pass a canvas to use as a reference; 
        don't pass a canvas to try to use owner's.
        proportion clamps between 0 and 1 and can be passed as single value.
        """
        if not canvas:
            canvas = self._get_owner_canvas()
        proportion = repack2(proportion)
        proportion = (min(max(proportion[0],0), 1), min(max(proportion[1],0), 1))
        self.pos = [int((canvas.get_rect().width - self._draw_rect.width)*proportion[0]),
                    int((canvas.get_rect().height - self._draw_rect.height)*proportion[1])]
    
    #######################
    # DRAW-TIME ALIGNMENT #
    #######################
    
    def set_align_left(self):
        """Align self to canvas left on draw time."""
        self._align_x = 0
        
    def set_align_top(self):
        """Align self to canvas top on draw time."""
        self._align_y = 0
        
    def set_align_right(self):
        """Align self to canvas right on draw time."""
        self._align_x = 1
        
    def set_align_bottom(self):
        """Align self to canvas bottom on draw time."""
        self._align_y = 1
        
    def set_align_center_x(self):
        """Align self to canvas center horizontally on draw time."""
        self._align_x = 0.5
        
    def set_align_center_y(self):
        """Align self to canvas center vertically on draw time."""
        self._align_y = 0.5
        
    def set_align_center(self):
        """Align self to canvas center on draw time."""
        self._align_x, self._align_y = 0.5, 0.5
        
    def set_align_proportion_x(self, proportion):
        """
        Align self to canvas horizontally following a proportion on draw time.
        
        proportion clamps between 0 and 1.
        """
        self._align_x = min(max(proportion,0), 1)
        
    def set_align_proportion_y(self, proportion):
        """
        Align self to canvas vertically following a proportion on draw time.
        
        proportion clamps between 0 and 1.
        """
        self._align_y = min(max(proportion,0), 1)
        
    def set_align_proportion(self, proportion):
        """
        Align self to canvas following a proportion on draw time.
        
        proportion clamps between 0 and 1 and can be passed as single value
        """
        proportion = repack2(proportion)
        proportion = (min(max(proportion[0],0), 1), min(max(proportion[1],0), 1))
        self._align_x, self._align_y = proportion
        
    def clear_alignment_x(self):
        """Cancel horizontal alignment on draw time."""
        self._align_x = None
        
    def clear_alignment_y(self):
        """Cancel vertical alignment on draw time."""
        self._align_y = None
        
    def clear_alignment(self):
        """Cancel alignment on draw time."""
        self._align_x, self._align_y = None, None