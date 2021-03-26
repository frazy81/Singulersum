#!/usr/bin/python3

# 2021-03-26 ph Created

"""
    unittest_normalvector.py

    Created:    2021-03-26 Philipp Hasenfratz

    unittests for normalvector calculation
"""

import sys

sys.path.append('..')

from Singulersum.Singulersum import Singulersum
import unittest
import dumper

class Tests(unittest.TestCase):

    def test_001(self):
        sg = Singulersum()
        cam = sg.camera(1, 0, 0, 0, 0, 0, name="cam1")
        cube = sg.cube("test", 0,0,0,1)
        self.assertTrue("top1" in cube.objects)
        top = cube.objects["top1"]
        self.assertTrue(top)
        print(top.points)
        p0 = top.points[0]
        p1 = top.points[1]
        p2 = top.points[2]
        self.assertEqual(p0[0], 1.0)
        self.assertEqual(p0[1], -1.0)
        self.assertEqual(p0[2], 1.0)

        self.assertEqual(p1[0], 1.0)
        self.assertEqual(p1[1], 1.0)
        self.assertEqual(p1[2], 1.0)

        self.assertEqual(p2[0], -1.0)
        self.assertEqual(p2[1], 1.0)
        self.assertEqual(p2[2], 1.0)

        print("p0", p0)
        print("p1", p1)
        print("p2", p2)
        print("vector p0p1", cam.vec_sub(p1,p0))
        print("vector p0p2", cam.vec_sub(p2,p0))
        normalvector = cam.poly_normalvector(p0, p1, p2)
        print("normalvector", normalvector)

        self.assertEqual(normalvector[0], 0.0)
        self.assertEqual(normalvector[1], 0.0)
        self.assertEqual(normalvector[2], 1.0)

        # same for the second poly of "top"
        print("top2")
        top = cube.objects["top2"]
        self.assertTrue(top)
        print(top.points)
        p0 = top.points[0]
        p1 = top.points[1]
        p2 = top.points[2]
        self.assertEqual(p0[0], 1.0)
        self.assertEqual(p0[1], -1.0)
        self.assertEqual(p0[2], 1.0)

        self.assertEqual(p1[0], -1.0)
        self.assertEqual(p1[1], 1.0)
        self.assertEqual(p1[2], 1.0)

        self.assertEqual(p2[0], -1.0)
        self.assertEqual(p2[1], -1.0)
        self.assertEqual(p2[2], 1.0)

        print("p0", p0)
        print("p1", p1)
        print("p2", p2)
        print("vector p0p1", cam.vec_sub(p1,p0))
        print("vector p0p2", cam.vec_sub(p2,p0))
        normalvector = cam.poly_normalvector(p0, p1, p2)
        print("normalvector", normalvector)

        self.assertEqual(normalvector[0], 0.0)
        self.assertEqual(normalvector[1], 0.0)
        self.assertEqual(normalvector[2], 1.0)

        pass

def main():
    unittest.main()
    return 0

exit(main())
