import unittest
from skytree.singleton import Singleton

class TestSingleton(unittest.TestCase):
    """Tests for the Singleton metaclass."""

    @classmethod
    def setUpClass(cls):
        """Make sure Singleton is clean right after import."""
        assert len(Singleton._instances) == 0, "\n\nInstances dict is not empty right after import."

    @classmethod
    def tearDownClass(cls):
        """Reset Singleton after all tests in the class."""
        Singleton._instances = {}

    def setUp(self):
        """Reset Singleton before each test."""
        Singleton._instances = {}
            
    def test_singleton(self):
        """Tests for Singleton behaviour."""
        class Fnord(metaclass=Singleton):
            pass
        class Fnerd(metaclass=Singleton):
            pass
        self.assertEqual(len(Singleton._instances), 0, "\n\nInstances dict is not empty at the top of the Singleton behaviour test.")
        fnord = Fnord()
        self.assertIs(type(type(fnord)), Singleton, "\n\nTest class doesn't have the Singleton metaclass.")
        self.assertIn(Fnord, Singleton._instances, "\n\nTest cass isn't in the instances dict after instantiation.")
        fnerd = Fnord()
        self.assertIs(fnord, fnerd, "\n\nSame object was not returned after second instantiation.")
        fnerd = Fnerd()
        self.assertIsNot(fnord, fnerd, "\n\nInstantiation of different classes returned the same object.")
        
    def test_clear(self):
        """Tests for Singleton clear functionality."""
        class Fnord(metaclass=Singleton):
            pass
        fnord = Fnord()
        self.assertNotEqual(len(Singleton._instances), 0, "\n\nInstances dict is empty after test class was instantiated.")
        Singleton.clear()
        self.assertEqual(len(Singleton._instances), 0, "\n\nInstances dict wasn't reset after calling Singleton.clear() method.")
        fnerd = Fnord()
        self.assertIsNot(fnord, fnerd, "\n\nTest class instantiated after clearing returns same object as before clearing.")

if __name__ == "__main__":
    unittest.main()