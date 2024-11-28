import unittest
from skytree import game
print()

class SkytreeTestRunner(unittest.TextTestRunner):
    """Test runer that uses custom TextTestResult"""
    
    def _makeResult(self):
        """Override to inject custom TextTestResult."""
        return SkytreeTestResult(self.stream, self.descriptions, self.verbosity)

class SkytreeTestResult(unittest.TextTestResult):
    """Custom TextTestResult to print an OK message when all tests in a class pass."""
    
    def __init__(self, stream, descriptions, verbosity):
        """Extend to initialize appropriate attributes."""
        super().__init__(stream, descriptions, verbosity)
        self.current_test_class = None
        self.remaining_class_tests = 0

    def startTest(self, test):
        """Extend to keep track of when the test class changes and set number of remaining tests in this class."""
        super().startTest(test)
        if test.__class__ != self.current_test_class:
            self.current_test_class = test.__class__
            self.remaining_class_tests = len([attr for attr in dir(test.__class__) if attr.startswith("test_")])

    def stopTest(self, test):
        """Extend to decrease number of remaining tests and print an OK message when it reaches 0."""
        super().stopTest(test)
        self.remaining_class_tests -= 1
        if self.remaining_class_tests == 0:
            print("\t" + self.current_test_class.__name__ + ": All tests passed.")
        
            
if __name__ == "__main__":
    # Set SkytreeTestRunner(verbosity = 2) to have an ok message for every test
    SkytreeTestRunner().run(unittest.TestLoader().discover('test', pattern='*.py'))
