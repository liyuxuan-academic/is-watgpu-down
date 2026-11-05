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

    def test_calculate_all_time_uptime_uses_only_ssh_status(self):
        history = [
            {"timestamp": "2026-01-01T00:00:00+00:00", "http_up": False, "ssh_up": True, "ping_up": False},
            {"timestamp": "2026-01-01T01:00:00+00:00", "http_up": True, "ssh_up": True, "ping_up": False},
            {"timestamp": "2026-01-01T02:00:00+00:00", "http_up": True, "ssh_up": False, "ping_up": True},
        ]

        self.assertAlmostEqual(monitor.calculate_all_time_uptime(history), 66.66666666666666)

    def test_generate_html_marks_online_when_only_ssh_is_up(self):
        now = datetime(2026, 10, 26, 1, 42, 20, tzinfo=timezone.utc)
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

        expected_start_date = "2026-10-25"

        self.assertIn('<div class="status">ONLINE</div>', html)
        self.assertIn("100.00%", html)
        self.assertIn(f"All-Time Uptime (since {expected_start_date})", html)

    def test_generate_html_converts_toronto_timestamps(self):
        # These literal expectations cover both sides of the actual UTC
        # transition instants, rather than midnight on the transition dates.
        cases = [
            ("2026-11-01T03:34:41+00:00", "2026-10-31 23:34:41"),
            ("2026-11-01T05:59:59+00:00", "2026-11-01 01:59:59"),
            ("2026-11-01T06:00:00+00:00", "2026-11-01 01:00:00"),
            ("2027-03-14T03:34:41+00:00", "2027-03-13 22:34:41"),
            ("2027-03-14T06:59:59+00:00", "2027-03-14 01:59:59"),
            ("2027-03-14T07:00:00+00:00", "2027-03-14 03:00:00"),
            ("2027-01-15T17:30:00Z", "2027-01-15 12:30:00"),
            ("2027-07-15T16:30:00+00:00", "2027-07-15 12:30:00"),
            # Legacy timestamps without an offset are UTC, not host local time.
            ("2025-11-22T03:28:21.387169", "2025-11-21 22:28:21"),
            ("2026-11-01T03:34:41", "2026-10-31 23:34:41"),
            ("2027-03-14T06:59:59", "2027-03-14 01:59:59"),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            output_html = os.path.join(tmpdir, "index.html")
            original_output = monitor.OUTPUT_HTML
            monitor.OUTPUT_HTML = output_html
            self.addCleanup(setattr, monitor, "OUTPUT_HTML", original_output)
            for timestamp, expected in cases:
                with self.subTest(timestamp=timestamp):
                    history = [{
                        "timestamp": timestamp,
                        "http_up": False,
                        "ssh_up": True,
                        "ping_up": False,
                    }]
                    monitor.generate_html(history)
                    with open(output_html) as f:
                        html = f.read()
                    self.assertIn(f"Last checked: {expected} ET", html)
                    self.assertIn(f"Statistics start from {expected[:10]}", html)

    def test_naive_history_is_utc_for_uptime_and_pruning(self):
        now = datetime.now(timezone.utc)
        recent = now - timedelta(hours=1)
        old = now - timedelta(days=2)
        history = [
            {"timestamp": old.replace(tzinfo=None).isoformat(), "ssh_up": False},
            {"timestamp": recent.replace(tzinfo=None).isoformat(), "ssh_up": True},
            {"timestamp": recent.isoformat(), "ssh_up": False},
        ]
        self.assertEqual(monitor.calculate_uptime(history, 1), 50.0)
        with tempfile.TemporaryDirectory() as tmpdir:
            original_file = monitor.HISTORY_FILE
            original_days = monitor.MAX_HISTORY_DAYS
            monitor.HISTORY_FILE = os.path.join(tmpdir, "history.json")
            monitor.MAX_HISTORY_DAYS = 1
            try:
                saved = monitor.save_history(history)
                self.assertEqual(saved, history[1:])
                self.assertEqual(monitor.load_history(), history[1:])
            finally:
                monitor.HISTORY_FILE = original_file
                monitor.MAX_HISTORY_DAYS = original_days


if __name__ == "__main__":
    unittest.main()
