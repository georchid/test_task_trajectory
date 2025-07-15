import unittest
from schedule import WorkerSchedule


class TestWorkerSchedule(unittest.TestCase):
    def setUp(self):
        self.sample_data = {
            "days": [
                {
                    "id": 1,
                    "date": "2025-07-14",
                    "start": "09:00",
                    "end": "18:00"
                },
                {
                    "id": 2,
                    "date": "2025-07-15",
                    "start": "10:00",
                    "end": "17:00"
                },
            ],
            "timeslots": [
                {
                    "id": 1,
                    "day_id": 1,
                    "start": "10:00",
                    "end": "11:30"
                },
                {
                    "id": 2,
                    "day_id": 1,
                    "start": "13:00",
                    "end": "14:00"
                },
                {
                    "id": 3,
                    "day_id": 2,
                    "start": "12:00",
                    "end": "15:00"
                },
            ]
        }

        self.ws = WorkerSchedule(self.sample_data)

    def test_get_busy_slots_str(self):
        result = self.ws.get_busy_slots_str("2025-07-14")
        expected = [
            {"start": "10:00", "end": "11:30"},
            {"start": "13:00", "end": "14:00"},
        ]

        self.assertEqual(result, expected)

    def test_get_free_slots_str(self):
        result = self.ws.get_free_slots_str("2025-07-14")
        expected = [
            {"start": "09:00", "end": "10:00"},
            {"start": "11:30", "end": "13:00"},
            {"start": "14:00", "end": "18:00"},
        ]
        self.assertEqual(result, expected)

    def test_is_available(self):
        cases = [
            ("2025-07-14", "11:30", "12:30", True),
            ("2025-07-14", "10:30", "11:00", False),
            ("2025-07-14", "09:00", "10:00", True),
            ("2025-07-14", "13:30", "14:30", False),
            ("2025-07-15", "10:00", "11:00", True),
        ]
        for d, start, end, expected in cases:
            with self.subTest(date=d, start=start, end=end):
                self.assertEqual(self.ws.is_available(d, start, end), expected)

    def test_find_free_slot(self):
        test_cases = [
            (30, {"date": "2025-07-14", "start": "09:00", "end": "09:30"}),
            (60, {"date": "2025-07-14", "start": "09:00", "end": "10:00"}),
            (120, {"date": "2025-07-14", "start": "14:00", "end": "16:00"}),
            (300, None),
        ]
        for duration, expected in test_cases:
            with self.subTest(duration=duration):
                result = self.ws.find_free_slot(duration)
                if expected is None:
                    self.assertIsNone(result)
                else:
                    self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
