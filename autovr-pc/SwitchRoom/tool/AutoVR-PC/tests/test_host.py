import unittest
from pc import explore


class Player:
    def __init__(self):
        self.calls = []

    async def scan(self):
        ids = ["A", "B"] + (["panel"] if "A" in self.calls else [])
        return {"ok": True, "value": {"scene": "Main", "sceneHandle": 10,
                "events": [{"id": id_, "callable": True} for id_ in ids]}}

    async def trigger(self, event):
        self.calls.append(event)
        return {"ok": True, "value": {"id": event, "status": "Invoke returned"}}


class Exploration(unittest.IsolatedAsyncioTestCase):
    async def test_limit_and_rescan(self):
        for limit, expected in [(0, []), (1, ["A"]), (8, ["A", "B", "panel"])]:
            player, log = Player(), []
            await explore(player, limit, 0, log.append)
            self.assertEqual(player.calls, expected)
            self.assertEqual(log[-1]["type"], "scan")
            if "panel" in expected:
                action = next(r for r in log if r["type"] == "attempt" and r["event"]["id"] == "panel")
                self.assertEqual(action["firstSeenAfter"], "A")

    async def test_failed_call_is_recorded_as_attempt_only(self):
        player, log = Player(), []
        async def fail(event):
            return {"ok": False, "error": "no longer active"}
        player.trigger = fail
        with self.assertRaisesRegex(RuntimeError, "no longer active"):
            await explore(player, 1, 0, log.append)
        self.assertEqual(log[-1]["type"], "attempt")
