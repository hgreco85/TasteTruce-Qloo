import json
import unittest
from io import BytesIO
from pathlib import Path
from sys import path
path.insert(0, str(Path(__file__).parent))
from tastetruce import Qloo, QlooError, plan

class Response(BytesIO):
    def __enter__(self): return self
    def __exit__(self, *args): self.close()

class FakeTransport:
    def __init__(self): self.calls = []
    def __call__(self, req, timeout):
        self.calls.append(req)
        assert timeout == 8
        assert req.get_header("X-api-key") == "test-only"
        from urllib.parse import urlparse
        path = urlparse(req.full_url).path
        if path == "/search":
            data = {"results": {"entities": [{"id": "seed", "name": "Seed"}]}}
        else:
            data = {"results": {"entities": [
                {"id": "shared", "name": "Shared choice", "affinity": .8},
                {"id": "other", "name": "Other", "affinity": .2}]}}
        return Response(json.dumps(data).encode())

class AgentTests(unittest.TestCase):
    def test_fixture_is_marked_and_never_calls_api(self):
        result = plan([["A"],["B"]], offline=True)
        self.assertEqual(result["mode"], "OFFLINE_FIXTURE_NOT_REAL_QLOO")

    def test_live_group_consensus_and_auth_header(self):
        wire = FakeTransport()
        result = plan([["A"],["B"]], client=Qloo(key="test-only", transport=wire))
        self.assertEqual(result["mode"], "LIVE_QLOO")
        self.assertEqual(result["choices"][0]["name"], "Shared choice")
        self.assertEqual(len(wire.calls), 8)
        self.assertTrue(all("test-only" not in x.full_url for x in wire.calls))

    def test_missing_key_does_not_leak(self):
        with self.assertRaisesRegex(QlooError, "missing"):
            Qloo(key="").search("X", "urn:entity:artist")

    def test_invalid_profiles(self):
        with self.assertRaises(ValueError): plan([["Solo"]], offline=True)
        with self.assertRaises(ValueError): plan([["A"],["B"]], categories=["invalid"], offline=True)

if __name__ == "__main__":
    unittest.main()
