import unittest
from skytree.singleton import Singleton

class TestSingleton(unittest.TestCase):
    """Tests for the Singleton metaclass."""

    def test_singleton(self):
        """
        Tests for Singleton metaclass assignation and instantiation.
        
        - Metaclass is assigned correctly.
        - Instantiation of the same Singleton class result in the same object.
        - Instantiation of different Singleton classes result in different objects.
        """
        class Fnord(metaclass=Singleton):
            pass
        class Fnerd(metaclass=Singleton):
            pass
        fnord = Fnord()
        self.assertIs(type(type(fnord)), Singleton)
        fnerd = Fnord()
        self.assertIs(fnord, fnerd)
        fnerd = Fnerd()
        self.assertIsNot(fnord, fnerd)

if __name__ == "__main__":
    unittest.main()