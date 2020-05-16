from __future__ import print_function
import unittest
import sys
import os

import numpy as np

pardir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, pardir)

import channelpack.datautils as du

print('Testing datautils module:', du)
print('Testing with', unittest)
print()


class TestStartStopBool(unittest.TestCase):
    """Test the startstop_bool function."""

    def setUp(self):
        self.t_height = (1, 2, 3, 4, 5, 4, 3, 2, 1, 2, 3, 4, 5, 4, 3, 2, 1)
        self.a_height = np.array(self.t_height)
        self.expected = (5, 4, 3, 2, 5, 4, 3, 2)

    def test_with_numpy_arrays_as_args(self):

        descends = np.array(tuple(du.startstop_bool(self.a_height == 5,
                                                 self.a_height == 1)))
        self.assertTrue(np.all(self.a_height[descends] == self.expected))

    def test_with_lists_as_args(self):

        startlist = [True if el == 5 else False for el in self.t_height]
        stoplist = [True if el == 1 else False for el in self.t_height]

        truefalse = list(du.startstop_bool(startlist, stoplist))

        self.assertTrue(np.all(self.a_height[truefalse] == self.expected))

    def test_with_empty_sequences(self):

        count = 0
        for truefalse in du.startstop_bool((), ()):
            count += 1
        self.assertEqual(count, 0)

    def test_start_no_stop(self):

        startb = (0, 1, 0, 0)
        stopb = (0, 0, 0, 0)
        expected = (0, 1, 1, 1)

        for b, compare in zip(du.startstop_bool(startb, stopb), expected):
            if b:
                self.assertTrue(compare)
            else:
                self.assertFalse(compare)

    def test_stop_no_start(self):

        startb = (0, 0, 0, 0)
        stopb = (0, 1, 0, 0)
        expected = (0, 0, 0, 0)

        for b, compare in zip(du.startstop_bool(startb, stopb), expected):
            if b:
                self.assertTrue(compare)
            else:
                self.assertFalse(compare)

    def test_start_stop_same(self):

        startb = (0, 0, 1, 0)
        stopb = (0, 0, 1, 0)
        expected = (0, 0, 0, 0)

        for b, compare in zip(du.startstop_bool(startb, stopb), expected):
            if b:
                self.assertTrue(compare)
            else:
                self.assertFalse(compare)

    def test_one_start_one_stop(self):

        startb = (0, 1, 0, 0)
        stopb = (0, 0, 0, 1)
        expected = (0, 1, 1, 0)

        for b, compare in zip(du.startstop_bool(startb, stopb), expected):
            if b:
                self.assertTrue(compare)
            else:
                self.assertFalse(compare)

    def test_start_all_true_one_stop(self):

        startb = (1, 1, 1, 1)
        stopb = (0, 1, 0, 0)
        expected = (1, 0, 1, 1)

        for b, compare in zip(du.startstop_bool(startb, stopb), expected):
            if b:
                self.assertTrue(compare)
            else:
                self.assertFalse(compare)
