import unittest
from pathlib import Path
from sys import path
path.insert(0, str(Path(__file__).parent))
import web

class BrowserTests(unittest.TestCase):
    def test_ui_does_not_embed_secret(self):
        self.assertIn("Find common ground", web.HTML)
        self.assertNotIn("QLOO_API_KEY", web.HTML)
        self.assertNotIn("X-Api-Key", web.HTML)
    def test_only_offline_by_default(self):
        self.assertTrue(web.Handler.offline)

if __name__ == "__main__":
    unittest.main()
