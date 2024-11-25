"""
Definition of classes that deal with routing and processing events.

EventController(ABC): interface for an object that can process events.
  An object doesn't have to actually be an EventController to be set as such; it just has to implement its methods.
KeyboardReader(EventController): an EventController that can process key presses and releases.
KeyCommandReader(Component): a Component that can process commands comming from a KeyboardReader or hold other components that do so.

EventControllers can send commands for CommandReaders to process.
In order to do that:
- Decide a shared list of argument names and types for commands to recognize.
- Code an EventController that interprets an event and sends a command to its owner (typically, the game manager).
- Code CommandReaders that have methods with name '_command_[command_name]' that define that object's behaviour when receiving such command.
CommandReaders will propagate received commands through their components ONLY WHEN they don't have a corresponding method to process the command.
"""

from pygame.locals import KEYDOWN, KEYUP
import warnings
from abc import ABC, abstractmethod
from skytree.component import Component

class EventController(ABC):
    """
    Interface for an object that can be set as an event controller by the Game.
    
    If the process method is going to send a command to command readers,
      be sure commands follow the format (command, {command_arguments}) and command
      arguments are documented on subclasses, as well as objects that receive them.
    
    Public methods:
    process(event): read the key event and act appropriately.
    connect(owner): set owner and perform controller activation actions.
    disconnect(): set owner as None and perform controller deactivation actions.
    """
    
    @abstractmethod
    def process(self, event):
        """
        Actions to be done when receiving the event.
        
        If this method is going to send a command to command readers,
        be sure commands follow the format (command, {command_args})
        """
        pass
    
    def connect(self, owner):
        """Actions to be done when controller is set."""
        pass
    
    def disconnect(self):
        """Actions to be done when controller is disconnected."""
        pass

class KeyboardReader(EventController):
    """
    A simple keyboard input controller.
    
    Implements game.EventController interface.
    
    Allows KEYUP and KEYDOWN events.
    Translates keys to commands and sends them to its owner. Passes key modifiers along, but doesn't process them.
    Key command arguments can be:
    press: boolean indicating whether the command comes from a keydown or keyup event
    mods: bitmask of all the modifier keys being pressed when the event occurred (see key modifier constants in pygame.locals).
    
    Public methods:
    process(event): read the key event and send a command to owner if the key is bound.
    bind(key, command): add an entry to the key dictionary.
    unbind(key): remove an entry from the key dictionary.
    connect(owner): set owner and declare a set in it to store commands whose associated keys are being pressed.
    disconnect(): set owner as None and remove "pressing" set from previous owner.
    """
    
    def __init__(self, keys={}):
        """
        Define a dictionary for key events.
        
        keys is a dictionary with entries in the form {key:command, ...}. Example: {K_SPACE: "shoot"}.
          Constants labeling keycodes are taken from pygame.locals.
        """
        self._owner = None
        """The KeyCommandReader that owns this object."""
        self._keys = dict(keys)
        """The dictionary that maps keys to commands."""
        
    @property
    def owner(self):
        """Public reference to this object's owner (read-only)."""
        return self._owner
        
    def process(self, event):
        """
        Read the key event and send a command to the appropriate object.
        
        Should only receive KEYDOWN or KEYUP events.
        Append True to the command if the key is pressed or False if it is released.
        """
        if not event.type in (KEYDOWN, KEYUP):
            warnings.warn("Event {e} not recognized by object {s}".format(e=event, s=self), RuntimeWarning)
            return
        if not event.key in self._keys:
            return # Key unbound, move along
            
        press = True if event.type == KEYDOWN else False
        self._owner.process(self._keys[event.key], **{"press": press, "mods": event.mod})
        if press:
            self._owner.pressing.add(self._keys[event.key])
        else:
            self._owner.pressing.discard(self._keys[event.key])
            
    def bind(self, key, command):
        """Add an entry to the dictionary or update an existing one."""
        self._keys[key] = command
            
    def unbind(self, key):
        """Remove an entry from the dictionary."""
        if key in self._keys:
            del self._keys[key]
        
    def connect(self, owner):
        """
        Set owner and declare a set in it to store commands whose associated keys are being pressed.
        
        owner must be a KeyCommandReader; a TypeError will be raised if it is not.
        """
        if not isinstance(owner, KeyCommandReader):
            raise TypeError("Object {o} tried to register a KeyboardReader without being a KeyCommandReader".format(o=owner))
        self._owner = owner
        self._owner.pressing = set({})
        
    def disconnect(self):
        """Set owner as None and remove "pressing" set from previous owner."""
        if self._owner:
            del self._owner.pressing
            self._owner = None

class CommandReader(Component):
    """
    Extend Component to be able to receive and process commands.
    
    Inherits all Component behaviour.
    Extends Component.add_component(component) and Component.remove_component(component).
    
    Commands that can't be processed by this object are propagated through its own CommandReader components.
    
    To code commands to a CommandReader object, use methods with name '_command_[command_name]'.
      Command names can't have underscores in them.
    Command method arguments should specify used arguments and include **kwargs after that.
    To activate commands in a CommandReader object, call object.process(command).
      Command can be either a command_name or a tuple (command_name, {command_args})
    Valid arguments for a type of command should be documented on subclasses, as well as objects that generate them
      (such as event controllers).
    
    Public methods:
    process(command): call appropriate method if implemented, otherwise propagate to components.
    allow_command(command): enable processing for given command.
    block_command(command): disable processing for given command.
    allow_commands(*commands): call allow_command(command) for given commands.
    block_commands(*commands): call block_command(command) for given commands.
    lock_controller(): disable command processing.
    unlock_controller(): enable command processing.
    """
    
    def __init__(self, **kwargs):
        """Extend Component to include a _cmd_readers set and build the necessary data structures for handling commands."""
        self._cmd_readers = set({})
        """A set of command reading components."""
        super().__init__(**kwargs)
        self._commands = {command: True for command in [methodname.split("_")[2] for methodname in filter(lambda x: x[:9]=="_command_", dir(self))]}
        """A dictionary that maps command names to allowed status (boolean)"""
        self._ctrl_lock = False
        """Whether command processing is disabled or not."""
    
    @property
    def command_readers(self):
        """Public reference to this object's command reading components set (read-only)."""
        return self._cmd_readers

    def add_component(self, component):
        """Extend Component to add component to _cmd_readers if successful."""
        if super().add_component(component):
            if isinstance(component, KeyCommandReader):
                self._cmd_readers.add(component)
            return True
        return False

    def remove_component(self, component):
        """Extend Component to remove component from _cmd_readers if successful."""
        if super().remove_component(component):
            if isinstance(component, KeyCommandReader):
                self._cmd_readers.remove(component)
            return True
        return False

    def process(self, command, **kwargs):
        """Perform appropriate method if implemented, otherwise propagate command to components."""
        if command in self._commands:
            if not self._ctrl_lock and self._commands[command]:
                # Activate command method with command args.
                eval("self._command_"+command)(**kwargs)
        else:
            for component in self._cmd_readers:
                component.process(command, **kwargs)
    
    def allow_command(self, command):
        """Allow execution of given command."""
        if not (command in self._commands):
            warnings.warn("{s} tried to allow an absent command: {c}".format(s=self, c=command), RuntimeWarning)
            return
        self._commands[command] = True
    
    def block_command(self, command):
        """Block execution of given command."""
        if not (command in self._commands):
            warnings.warn("{s} tried to block an absent command: {c}".format(s=self, c=command), RuntimeWarning)
            return
        self._commands[command] = False
    
    def allow_commands(self, *commands):
        """Allow execution of given commands. Default to all commands."""
        if not commands:
            commands = self._commands
        for com in commands:
            self.allow_command(com)
    
    def block_commands(self, *commands):
        """Block execution of given commands. Default to all commands."""
        if not commands:
            commands = self._commands
        for com in commands:
            self.block_command(com)
    
    def lock_controller(self):
        """Lock command processing."""
        self._ctrl_lock = True
        
    def unlock_controller(self):
        """Unlock command processing."""
        self._ctrl_lock = False

class KeyCommandReader(CommandReader):
    """
    Extend CommandReader to add some functionality related to key presses and releases.
    
    Inherits all CommandReader behaviour.
    Extends allow_command(command) to activate specified command if their associated keys are being pressed.
    Extends block_command(command) to deactivate specified command.
    
    This command reader assumes key pressed mean activation and releases mean deactivation.
    Key command arguments can be:
    press: boolean indicating whether the command comes from a keydown or keyup event
    mods: bitmask of all the modifier keys being pressed when the event occurred (see key modifier constants in pygame.locals).
    
    Public methods:
    check_commands(): for every registered command, activate if pressing and deactivate otherwise.
    activate_if_pressing(*commands): activate commands if their keys are being pressed.
    deactivate_unless_pressing(*commands): deactivate commands if their keys aren't being pressed.
    deactivate_all(): deactivate all commands.
    """
    
    def check_commands(self):
        """For every command, activate it if its associated keys are being pressed; deactivate it otherwise."""
        if not self.game:
            print(self, "here")
            return
        try:
            for com in self._commands:
                if com in self.game.pressing:
                    self.process(com, **{"press": True})
                else:
                    self.process(com, **{"press": False})
            for component in self._cmd_readers:
                component.check_commands()
        except AttributeError:
            warnings.warn("A KeyCommandReader is running without a KeyboardReader in Game.", RuntimeWarning)
            return
    
    def allow_command(self, command):
        """Set command as allowed, then activate if associated key is being pressed."""
        super().allow_command(command)
        self.activate_if_pressing(command)
    
    def block_command(self, command):
        """Set command as blocked, then deactivate it."""
        super().block_command(command)
        self.process(command, **{"press": False})
    
    def activate_if_pressing(self, *commands):
        """Activate commands if their associated keys are being pressed. Default to all commands."""
        if not commands:
            commands = self._commands
        try:
            for com in set(commands).intersection(self.game.pressing):
                self.process(com, **{"press": True})
        except AttributeError:
            warnings.warn("A KeyCommandReader is running without a KeyboardReader in Game.", RuntimeWarning)
            return

    def deactivate_unless_pressing(self, *commands):
        """Deactivate commands if their associated keys are not being pressed. Default to all commands."""
        if not commands:
            commands = self._commands
        try:
            for com in set(commands).difference(self.game.pressing):
                self.process(com, **{"press": False})
        except AttributeError:
            warnings.warn("A KeyCommandReader is running without a KeyboardReader in Game.", RuntimeWarning)
            return
    
    def deactivate_all(self):
        """Deactivate all commands."""
        for com in self._commands:
            self.process(com, **{"press": False})