"""A Singleton metaclass."""

class Singleton(type):
    """A Singleton type to use as a metaclass. Not thread-safe."""

    _instances = {}
    """A dictionary that maps every instantiated singleton class to its instance."""

    def __call__(cls, *args, **kwargs):
        """Return the instance after building it if needed."""
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
        
    @classmethod
    def clear(self):
        self._instances = {}