"""Definition of a class to help keep track of a group of boards."""

from skytree import game
from skytree import config
from skytree.resource_manager import ResourceManager

class Stage:
    """
    A class to keep track of a group of Boards.
    
    Instances are stored on the Game instance as a complement
    to the game state system. They are not components.
    The Stage class stores points of entry into a group of Boards
    (both initial and for the current checkpoint).
    Also keeps track of states to exit to.
    Both entry and exit points include a state to transition to and a label
    to signal the new state with.
    
    Public methods:
    enter(exit_state): transition state with entry information; optionally, update exit_state.
    exit(): transition state to exit_state if present; otherwise, quit the game.
    beat(entry_state, start_label, exit_label): exit the stage with exit information and reset checkpoint.
    
    Notes on setters:
    Setting the checkpoint will deactivate the old one and update point of entry (entry_state and start_label).
    """
    
    def __init__(self, entry_state, start_label=None, exit_state=None, exit_label=None):
        """
        Store arguments and a reference to the active game.
        
        Labels are optional; a state should be able to default if it receives no labels on transitions.
        Exit state is also optional; exit() method will quit the game if there's no exit state.
        """
        self.entry_state = entry_state
        """The state to transition to on stage enter."""
        self.start_label = start_label
        """The label to signal the transition with, pointing to how to start the next state (to be interpreted by the state)."""
        self.default_start = (entry_state, start_label)
        """The initial point of entry."""
        self.exit_state = exit_state
        """The state to transition to on stage exit."""
        self.exit_label = exit_label
        """The label to signal the transition with, pointing to how the previous state was exited (to be interpreted by the state)."""
        self._checkpoint = None
        """The object holding the current point of entry (entry_state and start_label)."""
        self.game = game.Game()
        """The active Game instance."""
        self._beat_sound = ResourceManager().get_sound(config.SOUND_ENTER_STAGE)
        """A sound to be played on beating a stage."""

    @property
    def checkpoint(self):
        """Public reference to the object holding the current point of entry."""
        return self._checkpoint
        
    @checkpoint.setter
    def checkpoint(self, value):
        """Set checkpoint object, deactivate old checkpoint and update point of entry."""
        if self._checkpoint == value:
            return
        old_checkpoint = self._checkpoint
        self._checkpoint = value
        if old_checkpoint:
            old_checkpoint.active = False
        if value:
            self.entry_state, self.start_label = value.board, value.name
        else:
            self.entry_state, self.start_label = self.default_start
            
    def enter(self, exit_state=None):
        """Tell the Game to enter entry_state with start_label. Optionally, update exit_state."""
        if exit_state:
            self.exit_state = exit_state
        self.game.set_state(self.entry_state, start_label=self.start_label)
        
    def exit(self):
        """Activate a transition towards exit_state if present; otherwise, quit the game."""
        if self.exit_state:
            self.game.set_state(self.exit_state, start_label=self.exit_label)
            self.game.active_stage = Stage(self.game.state)
        else:
            self.game.hcf()
            
    def beat(self, exit_state=None, start_label=None, exit_label=None):
        """Exit the stage, signal the transition with given exit_label if any and reset checkpoint."""
        # Default to stored values for exiting stage
        if not exit_state:
            exit_state = self.exit_state
        if not start_label:
            start_label = self.exit_label
        # Exit stage, pass exit label if present
        self._beat_sound.play()
        self.game.set_state(exit_state, start_label=start_label, exit_label=exit_label)
        self.game.active_stage = Stage(self.game.state)
        # Reset stage checkpoint
        self.checkpoint = None