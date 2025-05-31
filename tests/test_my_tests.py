import unittest
from unittest.mock import patch, mock_open

from shadow.polyedr import Polyedr


class TestPolyedr(unittest.TestCase):

    @staticmethod
    def procecc_file(path):
        p = Polyedr(f"data/{path}.geom")
        return p.modification()

    def test_1(self):
        self.assertAlmostEqual(self.procecc_file("test_1"), 2500.0)

    def test_2(self):
        self.assertAlmostEqual(self.procecc_file("test_2"), 0.0)
