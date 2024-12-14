"""
Definition of the Game class and the GameState interface.

Classes:
Game: the game manager singleton; the root of the tree.
GameState: interface for an object that can act as a game state.

Variables used from config: CANVAS_DIM, MIXER_FREQUENCY, MIXER_SIZE, MIXER_CHANNELS, MIXER_BUFFER, FPS_CAP,
                            WINDOW_MAGNIFY, START_FULLSCREEN, CAPTION, DEF_FADEOUT, MUSIC_PATH, GAME_BGCOLOR
"""

import warnings
from abc import ABC, abstractmethod
import pygame
from pygame.locals import QUIT, FULLSCREEN
from skytree.helpers import repack2, bake_obj
from skytree.singleton import Singleton
from skytree import config
from skytree.component import Component
from skytree.drawable import Drawable
from skytree.updateable import Updateable
from skytree.key_commands import KeyCommandReader, KeyboardReader
from skytree.resource_manager import ResourceManager
from skytree.stage import Stage

class Game(Updateable, Drawable, KeyCommandReader, metaclass=Singleton):
    """
    Game manager class. Extends WithState, Drawable and KeyboardPuppet. It is a Singleton.
    
    Inherits all behaviour from Component, Updateable, Positional, Drawable and KeyCommandReader.
    Overrides Drawable.draw(canvas).
    
    Deals with game loop, states and initial configuration.
    A reference to this object is passed to Component init, and will be propagated to all present
      and future components through init and add_component respectively.
    Being a singleton, it can also be accessed through further construction calls (i.e using Game()).
    The reasoning for this (admittedly cumbersome) approach to accessing the Game object is twofold:
    - Propagating a reference through the Component pipeline avoids circular import conflics, especially for command readers.
      Command readers need access to the Game; on the other hand, the game needs to be a Command reader itself.
      This method also ensures that every Component has a reference to the Game after being initialized and connected to the
      game tree without any further work and in a fairly transparent manner.
    - On the other hand, Singleton instantiation allows certain objects (such as a PauseState) to access the Game before
      Component initialization or being connected to the tree if they need to do so.
    
    Public methods:
    toggle_fullscreen(): Toggles fullscreen mode.
    set_event_controller(event, controller): Sets the given controller for the stated event.
    mark_for_destruction(*things): Marks entities passed for destruction at the end of the frame.
    hcf(): Quits the game.
    reset_stage(): program a stage reset to be performed at the bottom of the main loop.
    set_state(state, **kwargs): program a state transition to be performed at the bottom of the main loop.
    enter_active_stage(exit_state): call active_stage.enter() if present.
    exit_active_stage(): call active_stage.exit() if present; otherwise, quit the game.
    run(): Starts the game.
    
    Notes on setters:
    Setting fullscreen will trigger pygame.display.set_mode immediately.
    Setting music will call pygame.mixer to perform the appropriate operation.
    
    Key commands:
    fullscreen: toggles fullscreen mode.
    """
    
    def __init__(self):
        """
        Extend WithState, Updateable, Drawable and KeyboardPuppet to initialize the game.
        
        Initialize pygame, the game window and the event system; store FPS cap.
        Pass game=self for the Component init.
        """
        
        super().__init__(canvas=config.CANVAS_DIM, game=self)
        
        # Use the attributes in the following call to set the mixer before instantiating Game:
        pygame.mixer.pre_init(config.MIXER_FREQUENCY, config.MIXER_SIZE, config.MIXER_CHANNELS, config.MIXER_BUFFER)
        pygame.init()
        pygame.mixer.music.set_volume(config.MUSIC_VOLUME)
        self._music = None
        """The current music."""
        
        self._fps_cap = config.FPS_CAP
        """The maximum frames per second. FPS must always be capped."""

        # Set display.
        self._fullscreen_scale = 1
        """Window fullscreen scaling factor."""
        self.fullscreen = config.START_FULLSCREEN
        """Whether the game's running fullscreen or not."""
        
        # Caption.
        pygame.display.set_caption(config.CAPTION)
        pygame.display.set_icon(pygame.image.load(config.ICON_PATH).convert_alpha())

        # Event Controllers
        pygame.mouse.set_visible(False) # Might rethink how we deal with this when we implement mouse controllers.
        pygame.event.set_blocked(None) # Counterintuitively, this blocks ALL events
        pygame.event.set_allowed(QUIT)
        self._events = {}
        """A dictionary of event types to event controllers."""
        
        # Attributes for control of ingame changes.
        self.states = {}
        """A dictionary of state labels to state objects (baked or unbaked)."""
        self._state = None
        """The current state."""
        self.active_stage = None
        """The currently active stage."""
        self._transition = None
        """
        If present, a state transition programmed for the bottom of the main loop.
        
        Set through method set_state()
        """
        self._death_note = set()
        """
        A list of objects to be destroyed at the bottom of the main loop.
        
        Use mark_for_destruction method to put things here.
        """
        self._reset_stage = False
        """
        Whether the stage should be reset at the bottom of the main loop or not.
        
        Set through method reset_stage()
        """

    @property
    def state(self):
        """Public reference to the current state (read-only)."""
        return self._state

    @property
    def fullscreen(self):
        """Public reference to the current fullscreen status."""
        return self._fullscreen
    
    @fullscreen.setter
    def fullscreen(self, value):
        """Set fullscreen and activate pygame.display.set_mode."""
        self._fullscreen = value
        if value:
            self._screen = pygame.display.set_mode((self.width * config.WINDOW_MAGNIFY, self.height * config.WINDOW_MAGNIFY), (FULLSCREEN))
            display_info = pygame.display.Info()
            # Calculate and apply scaling factor
            self._fullscreen_scale = min(display_info.current_w / self.width, display_info.current_h / self.height)
            self._window = pygame.Surface((int(self.width * self._fullscreen_scale), int(self.height * self._fullscreen_scale)))
            # Center the window
            self._window_rect = self._window.get_rect()
            self._window_rect.center = (display_info.current_w // 2, display_info.current_h // 2)
        else:
            self._window = self.canvas if config.WINDOW_MAGNIFY == 1 else pygame.Surface((self.width * config.WINDOW_MAGNIFY, self.height * config.WINDOW_MAGNIFY))
            self._window_rect = self._window.get_rect()
            self._screen = pygame.display.set_mode((self._window_rect.width, self._window_rect.height))

    @property
    def music(self):
        """Public reference to the current music."""
        return self._music
        
    @music.setter
    def music(self, value):
        """
        Set music and use pygame.mixer to perform the appropriate operation.
        
        Allows: an audio file name, "stop" or "fade".
        """
        if value == self._music or not value:
            return
        elif value == "stop":
            pygame.mixer.music.stop()
            self._music = None
        elif value == "fade":
            pygame.mixer.music.fadeout(config.DEF_FADEOUT)
            self._music = None
        else:
            pygame.mixer.music.load(config.MUSIC_PATH + value)
            # In case of error, Pygame will handle it
            self._music = value
            pygame.mixer.music.play(loops=-1) # Play and loop indefinitely

    def _set_state(self):
        """Perform exit actions of current state, load another state and perform its enter actions."""
        state, kwargs = self._transition
        if isinstance(state, str):
            state_label = state
            state = self.states.get(state, None)
            if not state:
                raise KeyError("Game tried to load absent state '{s}'. Current states: {ss}".format(s=state_label, ss=tuple(self.states.keys())))
        state = bake_obj(state)
        if self._state:
            self._state.leave(new_state=state, **kwargs)
            self.remove_component(self._state)
        if not self.active_stage:
            self.active_stage = Stage(state, "start1" if "start1" in state._tagged else None)
        self._state = state
        if state:
            self.add_component(state)
            state.enter(**kwargs)
        
    def draw(self, canvas):
        """Override Drawable to use the background color and skip calling _render_self."""
        self.canvas.fill(config.GAME_BGCOLOR)
        self._render_components(self.canvas)
    
    def _command_fullscreen(self, press, **kwargs):
        """Set fullscreen mode if currently windowed and viceversa."""
        if press:
            self.toggle_fullscreen()
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        self.fullscreen = not self._fullscreen
    
    def set_event_controller(self, event, controller):
        """
        Set given controller for stated event by storing it on the events dictionary and marking it as allowed.
        
        Use a null controller to block the event.
        Events must have methods connect(owner), disconnect() and process(event). The former are called from this method.
        """
        if controller == None:
            pygame.event.set_blocked(event)
            if event in self._events:
                self._events[event].disconnect()
                del self._events[event]
        else:
            pygame.event.set_allowed(event)
            if event in self._events:
                self._events[event].disconnect()
            self._events[event] = controller
            controller.connect(self)
    
    def mark_for_destruction(self, *things):
        """Put the things in the list of stuff to destroy at the bottom of the main loop."""
        for thing in things:
            self._death_note.add(thing)
            
    def hcf(self):
        """Halt and catch fire! --Well, not really. More like terminate execution politely."""
        pygame.event.post(pygame.event.Event(QUIT))
    
    def reset_stage(self):
        """Program a stage reset to be performed at the bottom of the main loop."""
        self._reset_stage = True
            
    def set_state(self, state, **kwargs):
        """Program a state transition to be performed at the bottom of the main loop."""
        self._transition = (state, kwargs)
    
    def enter_active_stage(self, exit_state=None):
        """Call active_stage.enter() if present; otherwise, raise AttributeError."""
        if self.active_stage:
            self.active_stage.enter(exit_state)
        else:
            raise AttributeError("Game tried to enter active stage with no active stage.")
    
    def exit_active_stage(self):
        """Call active_stage.exit() if present; otherwise, quit the game."""
        if self.active_stage:
            self.active_stage.exit()
        else:
            self.hcf()
    
    def run(self):
        """
        Main loop. Call this method to start the game!
        
        Before starting the loop, define a clock and a delta time variable.
        Instantiate a pause state if missing.
        Loop goes like this:
          - Empty queue of events and process them as needed.
          - Update all updateables (passing delta time)
          - Draw all drawables (passing main canvas)
          - Scale the canvas if needed and render the screen.
          - Perform state transitions and object destructions if needed.
          - Tick the clock.
        """
        if not "pause" in self.states:
            from .user_interface import PauseState
            print("Pause State not found at game run time; using default.")
            PauseState()
        
        clock = pygame.time.Clock()
        dt = 0 # Delta time in milliseconds
        
        done = False
        while not done:
            
            ##########
            # EVENTS #
            ##########

            for event in pygame.event.get():
                if event.type in self._events:
                    self._events[event.type].process(event)
                elif event.type == QUIT: # Fallback for QUIT
                    done = True

            ##########
            # UPDATE #
            ##########
            
            self.update(dt)

            ########
            # DRAW #
            ########
            
            self.draw(self.canvas)
            
            # SCALE canvas into window; BLIT window into screen; FLIP display
            if self._fullscreen:
                pygame.transform.scale(self.canvas, (int(self.width * self._fullscreen_scale), 
                                                     int(self.height * self._fullscreen_scale)), self._window)
            elif config.WINDOW_MAGNIFY != 1:
                pygame.transform.scale(self.canvas, (self._window_rect.width, self._window_rect.height), self._window)
            self._screen.blit(self._window, self._window_rect)
            pygame.display.flip()
            
            ##############
            # LOOSE ENDS #
            ##############
            
            # DESTROY MARKED OBJECTS AND PERFORM STATE TRANSITION IF NEEDED
            if self._reset_stage:
                if self.active_stage.start_label:
                    self.enter_active_stage()
                else:
                    self.state.reset()
                self._reset_stage = False
            if self._transition:
                self._set_state()
                self._transition = None
            for thing in self._death_note:
                thing.destroy()
            self._death_note = set()

            # TICK THE CLOCK. Requires fps cap.
            dt = clock.tick(self._fps_cap)
        
        # On exit, clear all singletons and quit pygame
        Singleton.clear()
        pygame.quit()

class GameState(ABC, Component):
    """
    Extend Component to represent an object that can be set as a game state.

    Inherits all behaviours from Component.
    Subclasses must implement board property.
    
    Can be added to the game manager's states dictionary and/or set as first active state on instantiation.
    """
    
    def __init__(self, first_state=False, **kwargs):
        """
        Extend Component to update the game manager's states dictionary and/or set first active state.
        
        This object will be added to the states dictionary if it's instantiated with a name.
        Argument first_state can be used to set this object as the game's first active state.
          Do not rely on the latter if the first state of the game is a Board that belongs to a Stage.
          Active stage should be manually set in that case.
        """
        super().__init__(**kwargs)
        game = Game()
        if self._name:
            if self._name in game.states:
                warnings.warn("State {s} has been replaced".format(s=self._name), RuntimeWarning)
            game.states[self._name] = self
        if first_state:
            game.set_state(self)
    
    @property
    @abstractmethod
    def board(self):
        """Reference the active board."""
        return None
    
    def enter(self, **kwargs):
        """Actions to be done when state is set."""
        pass
    
    def leave(self, **kwargs):
        """Actions to be done when state is left."""
        pass
