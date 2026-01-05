import unittest
from api_request.config import Config


class TestConfig(unittest.TestCase):

    def test_database_url(self):
        url = Config.get_database_url()
        self.assertIn(Config.DB_HOST, url)
        self.assertIn(Config.DB_NAME, url)
        self.assertIn(str(Config.DB_PORT), url)


if __name__ == "__main__":
    unittest.main()
