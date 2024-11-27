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
        
        self.assertIsInstance(component, Component)
        self.assertEqual(component._owner, None)
        self.assertEqual(component._components, set({}))
        self.assertEqual(component._name, None)
        self.assertEqual(component._named, {})
        self.assertEqual(component._tags, set({}))
        self.assertEqual(component._tagged, {})
        self.assertEqual(component._reset_data, {"attributes":{}, "tags":set({}), "components":set({})})

if __name__ == "__main__":
    unittest.main()