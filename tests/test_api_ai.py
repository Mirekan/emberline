"""Tests for the AI satellite telemetry context analyzer endpoint (POST /api/ai/analyze-hotspot)."""
import unittest
from fastapi.testclient import TestClient

from api.app import app, _analyze_hotspot_heuristic


class TestAIHotspotAnalyzer(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_heuristic_generator_riau_peatland(self):
        res = _analyze_hotspot_heuristic(
            lat=0.73494,
            lon=102.88028,
            date="2017-09-28",
            frp=69.52,
            sensor="viirs",
            conf="h",
            daynight="N",
            question="kenapa kebakarannya?",
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["provider"], "heuristic")
        self.assertIn("Pesisir Timur Sumatra", res["analysis"])
        self.assertIn("FRP", res["analysis"])
        self.assertIn("telemetry_context", res)
        self.assertIn("biome", res["telemetry_context"])
        self.assertIn("Gambut", res["telemetry_context"]["biome"])

    def test_api_endpoint_success_heuristic_fallback(self):
        from unittest.mock import patch
        with patch("api.app._get_grok_key", return_value=(None, "heuristic")):
            resp = self.client.post("/api/ai/analyze-hotspot", json={
                "lat": -1.8,
                "lon": 113.8,
                "date": "2019-09-15",
                "frp": 35.4,
                "sensor": "viirs",
                "conf": "h",
                "daynight": "D",
                "question": "Apakah ini lahan gambut?"
            })
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["status"], "success")
            self.assertEqual(data["provider"], "heuristic")
            self.assertIn("Kalimantan Tengah", data["analysis"])
            self.assertIn("telemetry_context", data)

    def test_api_endpoint_bad_coordinates(self):
        resp = self.client.post("/api/ai/analyze-hotspot", json={
            "lat": "not-a-number",
            "lon": 102.0,
            "frp": 10.0
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertEqual(data["detail"]["code"], "bad_coordinates")

    def test_api_endpoint_invalid_grok_key_graceful_fallback(self):
        resp = self.client.post("/api/ai/analyze-hotspot", json={
            "lat": 0.5,
            "lon": 101.5,
            "date": "2023-08-20",
            "frp": 15.2,
            "sensor": "modis",
            "conf": "80",
            "daynight": "D",
            "api_key": "invalid-dummy-key"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # Should gracefully fall back to heuristic
        self.assertEqual(data["provider"], "heuristic")
        self.assertIn("dialihkan ke telemetri satelit", data["note"])

    def test_api_endpoint_english_language_support(self):
        from unittest.mock import patch
        with patch("api.app._get_grok_key", return_value=(None, "heuristic")):
            resp = self.client.post("/api/ai/analyze-hotspot", json={
                "lat": 0.73494,
                "lon": 102.88028,
                "date": "2017-09-28",
                "frp": 69.52,
                "sensor": "viirs",
                "conf": "h",
                "daynight": "N",
                "question": "why was this hotspot detected?",
                "lang": "en",
            })
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["status"], "success")
            self.assertEqual(data["provider"], "heuristic")
            self.assertIn("Eastern Coast of Sumatra", data["analysis"])
            self.assertIn("Tropical Deep Peatland", data["telemetry_context"]["biome"])
            self.assertIn("NASA FIRMS Satellite Telemetry Report", data["analysis"])

    def test_api_endpoint_indonesian_language_default(self):
        from unittest.mock import patch
        with patch("api.app._get_grok_key", return_value=(None, "heuristic")):
            resp = self.client.post("/api/ai/analyze-hotspot", json={
                "lat": 0.73494,
                "lon": 102.88028,
                "date": "2017-09-28",
                "frp": 69.52,
                "sensor": "viirs",
                "conf": "h",
                "daynight": "N",
                "lang": "id",
            })
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["status"], "success")
            self.assertEqual(data["provider"], "heuristic")
            self.assertIn("Pesisir Timur Sumatra", data["analysis"])
            self.assertIn("Lahan Gambut Tropis", data["telemetry_context"]["biome"])


if __name__ == "__main__":
    unittest.main()
