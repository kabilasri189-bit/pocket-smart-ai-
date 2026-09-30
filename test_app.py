import unittest
from app import app

class PocketSmartTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_home(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"PocketSmart AI", response.data)

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")

    def test_home_planner(self):
        response = self.client.post("/api/recommend", data={
            "planner": "home", "budget": "10000",
            "rooms": "Living Room", "style": "Modern"
        })
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json["recommendations"]), 0)

    def test_party_planner(self):
        response = self.client.post("/api/recommend", data={
            "planner": "party", "budget": "20000",
            "event_type": "Birthday", "guests": "30"
        })
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json["recommendations"]), 0)

    def test_jewelry_planner(self):
        response = self.client.post("/api/recommend", data={
            "planner": "jewelry", "budget": "5000",
            "occasion": "Wedding", "jewelry_style": "Elegant"
        })
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json["recommendations"]), 0)

if __name__ == "__main__":
    unittest.main(verbosity=2)
