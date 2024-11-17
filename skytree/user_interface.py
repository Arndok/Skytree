"""
Definition of UI objects and states.

Classes:
Menu(Drawable, KeyCommandReader): a list of selectable options with associated actions.
PauseState(Drawable, KeyCommandReader, GameState): a game state that freezes the current board and can
  go back to it, either to unfreeze it or to exit from it.

Variables used from config: CANVAS_DIM
"""

from functools import reduce
import pygame
from . import config
from .drawable import Drawable
from .key_commands import KeyCommandReader
from .resource_manager import ResourceManager
from .game import Game, GameState

class Menu(Drawable, KeyCommandReader):
    """
    Extend Drawable and KeyCommandReader to represent a menu with selectable options.
    
    Inherits all behaviour from Component, Positional, KeyCommandReader and Drawable.
    
    Options are paired with functions. Currently highlighted option is indicated
    by an arrow pointing right on the left side of the menu.
    
    Extra behaviour on setters:
    Setting selected will move the arrow to the appropriate y position.
    
    Key commands:
    up and down: change the selected option.
    enter: confirm the option; perform its associated function.
    """
    
    def __init__(self, title, options, font, fsize=None, color=(255,255,255), **kwargs):
        """
        Extend superclasses to build the drawable objects needed to represent the menu.
        
        title is a string that's going to be used to build a text object with the given font, font size and color.
        options is a list of tuples (label, function) in which each label will also be used to build a text object,
          and the function is going to be called when its associated option is selected and confirmed.
        The color is used for building the arrow as well.
        """
        font = ResourceManager().get_font(font, fsize)
        self._title = Drawable(font.render(title, 0, color))
        """The text object that serves as a menu header."""
        self._options = tuple(Drawable(font.render(option[0], 0, color)) for option in options)
        """A tuple holding one text object for each option."""
        self._functions = tuple((option[1] for option in options))
        """A tuple holding one function for each option."""
        # Calculate some measures and pass them to super init to build canvas.
        lines = (self._title,)+self._options
        arrow_length = self._title.height*0.6
        width = reduce(lambda x,y: x if x.width>y.width else y, lines).width + arrow_length*3
        height = self._title.height * (len(self._options) + 1)
        super().__init__(canvas=(width,height), subsurface=True)
        # Add text objects as persistent.
        for i, line in enumerate(lines):
            self.add_persistent_component(line)
            line.align_center_x()
            line.y += line.height*i
        self._arrow = Drawable((arrow_length, arrow_length+1))
        """A drawable arrow that points to the currently selected option."""
        # Draw the arrow.
        pygame.draw.polygon(self._arrow.canvas, color, ((0,0), (arrow_length, arrow_length/2), (0, arrow_length)))
        self.add_persistent_component(self._arrow)
        self.selected = 0
        """An index that points to the currently selected option."""
        
    @property
    def selected(self):
        """Public reference to the index of the currently selected option."""
        return self._selected
        
    @selected.setter
    def selected(self, value):
        """Update self._selected and the arrow position."""
        self._selected = value
        # Align arrow
        self._arrow.y = self._options[self.selected].y + (self._title.height - self._arrow.height)/2
        self._arrow.x = self._options[self.selected].x - self._arrow.width * 1.5

    def _command_up(self, press, **kwargs):
        """Change selected option upwards."""
        if press:
            self.selected = (self.selected - 1) % len(self._options)
        
    def _command_down(self, press, **kwargs):
        """Change selected option downwards."""
        if press:
            self.selected = (self.selected + 1) % len(self._options)
        
    def _command_enter(self, press, **kwargs):
        """Perform selected option's associated function."""
        if press:
            self._functions[self.selected]()

class PauseState(Drawable, KeyCommandReader, GameState):
    """
    Extend Drawable and KeyCommandReader to represent a pause state.
    
    Inherits all behaviours from Component, Positional, Drawable and KeyCommandReader.
    Implements game.GameState interface.
    Extends Drawable.draw(canvas).
    
    Draws, but doesn't update, current board in its last state before pausing.
    On CONTINUE, transitions back to the board.
    On END, exits the board.
    
    Public methods:
    enter(exit_state, **kwargs): store the exit state and reset the menu.
    leave(**kwargs): if there's an active player on the exit state, tell them to check their commands.
    
    Key commands:
    esc: go back to the exit state.
    """
    def __init__(self, commands=(), **kwargs):
        """
        Extend superclasses to build a pause menu and presentation.
        
        Menu is hardcoded to the two options "CONTINUE" (go back to the board) and "END" (exit the board).
        Menu is drawn over this object's canvas, which is a translucid grey which is in turn drawn over the board's last state.
        Name of this class is hardcoded to "pause", and will be automatically added to the game states dictionary on instantiation.
        """
        super().__init__(name="pause", canvas=config.CANVAS_DIM, commands=commands+("esc",), **kwargs)
        self.canvas.fill((0,0,0,100))
        self._menu = Menu("PAUSE",
                               (("CONTINUE", self._command_esc), ("END", self.exit_stage)),
                               "ArcadeClassic.ttf")
        """The pause menu."""
        self.add_persistent_component(self._menu)
        self._menu.align_center()
        self._exit_state = None
        """The state to exit to; i.e the board we're coming from."""
        
    @property
    def board(self):
        """Alias for the exit state, for the sake of generalizing board access from game state."""
        return self._exit_state
        
    def enter(self, exit_state, **kwargs):
        """Store the exit state; reset the menu."""
        self._exit_state = exit_state
        self._menu.selected = 0
        
    def leave(self, **kwargs):
        """If there's an active player, tell them to check their pending commands."""
        if "player" in self._exit_state.named:
            self._exit_state.named["player"].unpause()
    
    def exit_stage(self):
        """Execute leave actions from current board, then exit active stage."""
        self._exit_state.leave()
        Game().exit_active_stage()
        
    def _command_esc(self, press=True, **kwargs):
        """Go back to the exit state."""
        # Setting press=True by default allows us to call this method with no arguments
        if press:
            self.game.set_state(self._exit_state)
        
    def draw(self, canvas):
        """Extend Drawable to draw the board's last state before entering pause under this object's canvas (translucid grey)."""
        self._exit_state.draw(canvas)
        super().draw(canvas)