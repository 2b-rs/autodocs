import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import ai_agent_bridge


class TestAiAgentBridge(unittest.TestCase):
    def test_load_policy_and_config(self):
        cfg = ai_agent_bridge.get_agent_config()
        self.assertIn("primary", cfg)
        self.assertIn("fallback", cfg)
        self.assertEqual(cfg["primary"]["cli"], "agy")
        self.assertEqual(cfg["primary"]["modell"], "gemini-3.8-flash-high")
        self.assertEqual(cfg["primary"]["thinking_effort"], "high")
        self.assertEqual(cfg["primary"]["subscription"], "gemini")

        self.assertEqual(cfg["fallback"]["cli"], "agent")
        self.assertEqual(cfg["fallback"]["modell"], "composer-2.5")
        self.assertEqual(cfg["fallback"]["subscription"], "cursor")

    def test_check_subscriptions(self):
        subs = ai_agent_bridge.check_subscriptions()
        self.assertIn("gemini", subs)
        self.assertIn("cursor", subs)
        self.assertTrue(subs["gemini"]["subscription_active"])
        self.assertTrue(subs["cursor"]["subscription_active"])
        self.assertIsNotNone(subs["gemini"]["cli_path"])
        self.assertIsNotNone(subs["cursor"]["cli_path"])

    def test_discover_models(self):
        disc = ai_agent_bridge.discover_models()
        self.assertIn("agy", disc)
        self.assertIn("cursor", disc)
        # agy checks
        self.assertTrue(disc["agy"]["available"])
        self.assertEqual(disc["agy"]["selected_model"], "gemini-3.8-flash-high")
        self.assertIn("1.2.14", str(disc["agy"]["cli_version"]))
        # cursor checks
        self.assertTrue(disc["cursor"]["available"])
        self.assertEqual(disc["cursor"]["selected_model"], "composer-2.5")
        self.assertIsNotNone(disc["cursor"]["cli_version"])

    def test_health_monitor_status(self):
        status = ai_agent_bridge.get_health_status()
        self.assertTrue(status["ok"])
        self.assertIn("providers", status)
        self.assertIn("agy", status["providers"])
        self.assertIn("cursor", status["providers"])

    def test_health_monitor_cycle_mocked(self):
        from unittest.mock import patch

        monitor = ai_agent_bridge.AIHealthMonitor(interval_seconds=60)
        with patch.object(ai_agent_bridge, "ping_agy", return_value=(True, 320, None)):
            with patch.object(ai_agent_bridge, "ping_cursor", return_value=(True, 450, None)):
                res = monitor.run_check_cycle()
                self.assertEqual(res["active_provider"], "agy")
                self.assertEqual(res["providers"]["agy"]["status"], "healthy")
                self.assertEqual(res["providers"]["agy"]["latency_ms"], 320)
                self.assertEqual(res["providers"]["cursor"]["status"], "healthy")
                self.assertEqual(res["providers"]["cursor"]["latency_ms"], 450)

    def test_health_monitor_failover_to_cursor(self):
        from unittest.mock import patch

        monitor = ai_agent_bridge.AIHealthMonitor(interval_seconds=60)
        with patch.object(ai_agent_bridge, "ping_agy", return_value=(False, 1200, "Gemini quota exhausted")):
            with patch.object(ai_agent_bridge, "ping_cursor", return_value=(True, 410, None)):
                res = monitor.run_check_cycle()
                self.assertEqual(res["active_provider"], "cursor")
                self.assertEqual(res["providers"]["agy"]["status"], "error")
                self.assertEqual(res["providers"]["cursor"]["status"], "healthy")
                self.assertEqual(res["active_model"]["provider"], "cursor")
                self.assertEqual(res["active_model"]["model"], "composer-2.5")



if __name__ == "__main__":
    unittest.main()
