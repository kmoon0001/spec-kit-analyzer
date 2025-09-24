import unittest
from src.utils import generate_key, validate_key

class TestUtils(unittest.TestCase):

    def test_generate_key(self):
        """
        Tests that the generate_key function returns a string of the correct length.
        """
        key = generate_key()
        self.assertIsInstance(key, str)
        self.assertEqual(len(key), 64)

    def test_validate_key(self):
        """
        Tests that the validate_key function raises a ValueError for the default key.
        """
        with self.assertRaises(ValueError):
            validate_key("{{GENERATE_YOUR_OWN_KEY}}")

    def test_validate_key_with_valid_key(self):
        """
        Tests that the validate_key function returns the key if it is valid.
        """
        key = "my_valid_key"
        self.assertEqual(validate_key(key), key)

if __name__ == '__main__':
    unittest.main()