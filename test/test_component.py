import unittest
from skytree.component import Component

class TestComponent(unittest.TestCase):
    """Tests for the Component class."""

    def test_component_creation(self):
        """
        Tests for component creation.
        
        - Empty arguments component have their private fields set up correctly
        """
        component = Component()
        
        self.assertIsInstance(component, Component, "\n\nTest object is not a Component")
        self.assertEqual(component._owner, None, "\n\nTest object _owner field is not None")
        self.assertEqual(component._components, set({}), "\n\nTest object _component field is not an empty set")
        self.assertEqual(component._name, None, "\n\nTest object _name field is not None")
        self.assertEqual(component._named, {}, "\n\nTest object _named field is not an empty dict")
        self.assertEqual(component._tags, set({}), "\n\nTest object _tags field is not an empty set")
        self.assertEqual(component._tagged, {}, "\n\nTest object _tagged field is not an empty dict")
        self.assertEqual(component._reset_data, {"attributes":{}, "tags":set({}), "components":set({})}, "\n\nTest object _reset_data field is not set correctly.")

if __name__ == "__main__":
    unittest.main()