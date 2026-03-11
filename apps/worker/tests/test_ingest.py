import unittest
from datetime import date

from apps.worker.app.services.ingest import _history_windows


class IngestTests(unittest.TestCase):
    def test_history_windows_slice_into_weeks(self):
        windows = _history_windows(date(2026, 1, 1), date(2026, 1, 20))

        self.assertEqual(len(windows), 3)
        self.assertEqual(windows[0][0].date().isoformat(), "2026-01-01")
        self.assertEqual(windows[0][1].date().isoformat(), "2026-01-07")
        self.assertEqual(windows[-1][0].date().isoformat(), "2026-01-15")
        self.assertEqual(windows[-1][1].date().isoformat(), "2026-01-20")


if __name__ == "__main__":
    unittest.main()
