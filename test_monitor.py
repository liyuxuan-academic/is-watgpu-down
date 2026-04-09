import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

import monitor


class MonitorTests(unittest.TestCase):
    def test_calculate_uptime_uses_only_ssh_status(self):
        now = datetime.now(timezone.utc)
        history = [
            {
                "timestamp": (now - timedelta(hours=1)).isoformat(),
                "http_up": False,
                "ssh_up": True,
                "ping_up": False,
            },
            {
                "timestamp": (now - timedelta(hours=2)).isoformat(),
                "http_up": True,
                "ssh_up": False,
                "ping_up": True,
            },
        ]

        self.assertEqual(monitor.calculate_uptime(history, 1), 50.0)

    def test_generate_html_marks_online_when_only_ssh_is_up(self):
        now = datetime.now(timezone.utc)
        history = [
            {
                "timestamp": now.isoformat(),
                "http_up": False,
                "ssh_up": True,
                "ping_up": False,
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_html = os.path.join(tmpdir, "index.html")
            original_output = monitor.OUTPUT_HTML
            monitor.OUTPUT_HTML = output_html
            try:
                monitor.generate_html(history)
            finally:
                monitor.OUTPUT_HTML = original_output

            with open(output_html, "r") as f:
                html = f.read()

        self.assertIn('<div class="status">ONLINE</div>', html)
        self.assertIn("100.0%", html)


if __name__ == "__main__":
    unittest.main()
