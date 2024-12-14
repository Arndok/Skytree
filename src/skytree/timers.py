"""
Definition of Updateable Components that keep track of time.

Classes:
Timer(Updateable): keep track of time.
Countdown(Timer): a Timer that counts backwards and has the ability to do something when reaching zero.
Delay(Countdown): a Delay that self-destructs when reaching zero.
Cycle(Countdown): a Countdown that resets itself when reaching zero.
"""

from skytree.helpers import nop
from skytree.updateable import Updateable

class Timer(Updateable):
    """
    Extend Updateable to keep track of time.
    
    Inherits all Updateable behaviour.
    Extends Updateable.update(dt).
    
    Public methods:
    start(dt): starts keeping track of elapsed time
    pause(dt): stops keeping track of elapsed time
    stop(dt): performs a pause and then a reset (sets "time" attribute to 0)
    """
    
    def __init__(self, **kwargs):
        """Set time to 0, add this to reset data and start the timer."""
        super().__init__(**kwargs)
        self.time = 0
        """Time elapsed since start or reset."""
        self._reset_data["attributes"]["time"] = 0
        self.running = True
        """Whether this object's currently keeping track of time or not."""
        
    def update(self, dt):
        """Extend Updateable to add delta time to 'time' attribute."""
        if self.running: self.time += dt
        
    def start(self):
        """Start keeping track of elapsed time."""
        self.running = True
        
    def pause(self):
        """Stop keeping track of elapsed time."""
        self.running = False
        
    def stop(self):
        """Pause and reset (set 'time' attribute to 0)."""
        self.pause()
        self.reset()

class Countdown(Timer):
    """
    Extend Timer to go backwards and have the ability to do something when time reaches 0.
    
    Inherits all Timer and Updateable behaviour.
    Extends Timer.update(dt).
    
    Public methods:
    _on_time(): performs trigger action.
    """
    
    def __init__(self, init_time, trigger=nop, **kwargs):
        """
        Initialize timer and store a trigger action.
        
        init_time is the time to count down from.
        trigger may be either a function or a tuple (function, {kwargs}). Defaults to doing nothing.
        """
        super().__init__(**kwargs)
        self.time = init_time
        """Time left until reaching 0."""
        self._reset_data["attributes"]["time"] = init_time
        self._trigger = trigger
        """Function to execute when time reaches 0."""
        
    @property
    def init_time(self):
        """Initial time from which to count back."""
        return self._reset_data["attributes"]["time"]
        
    def _on_time(self):
        """Perform trigger action."""
        if isinstance(self._trigger, tuple):
            self._trigger[0](**self._trigger[1])
        else:
            self._trigger()
        
    def update(self, dt):
        """Extend Timer to count time backwards and call self._on_time() when time reaches 0."""
        super().update(-dt)
        if self.time <= 0:
            self._on_time()

class Delay(Countdown):
    """
    A countdown that destroys itself when time reaches 0.
    
    Extends Countdown._on_time()
    """
    
    def _on_time(self):
        """Extend Countdown to self-destroy when reaching 0."""
        super()._on_time()
        self.destroy()
            
class Cycle(Countdown):
    """
    A countdown that resets when time reaches 0.
    
    Extends Countdown._on_time()
    """
    
    def _on_time(self):
        """Extend Countdown to add init_time to time when reaching 0."""
        super()._on_time()
        self.time += self.init_time