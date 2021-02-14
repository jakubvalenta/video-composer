from unittest import TestCase

from video_composer.meta import Timestamp


class TestTimestamp(TestCase):
    def test_from_string(self):
        timestamp = Timestamp.from_string('01:15:30.670')
        self.assertEqual(timestamp.total_seconds(), 4530.67)

    def test_to_string(self):
        timestamp = Timestamp.from_string('01:15:30.670')
        self.assertEqual(str(timestamp), '01:15:30.670')
