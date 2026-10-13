import unittest
from tastetruce import is_dining_place

class DiningValidationTests(unittest.TestCase):
    def test_bridge_rejected(self):
        self.assertFalse(is_dining_place({"name":"Brooklyn Bridge","type":"urn:entity:place","tags":[{"name":"Landmark"}]}))
    def test_restaurant_accepted(self):
        self.assertTrue(is_dining_place({"name":"Bistro", "tags":[{"name":"Restaurant"}]}))
    def test_without_metadata_fail_closed(self):
        self.assertFalse(is_dining_place({"name":"A restaurant-looking title"}))

if __name__ == "__main__":
    unittest.main()
