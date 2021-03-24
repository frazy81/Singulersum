#!/usr/bin/python3

# 2021-03-21 ph Created
# 2021-03-24 ph up to date with Camera()

"""
    unittests.py

    Created:    2021-03-21 Philipp Hasenfratz

    some unittests. Needs a lot more here... ;-)
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
        P = (1, 0, 0)
        print("P:", cam.vec_show(P))
        P_prime = cam.rotate(P, 90, 0)
        print("P_prime:", cam.vec_show(P_prime))
        self.assertTrue(P_prime[0]-0.0<1e-6)  # x=0, y=1, z=0
        self.assertTrue(P_prime[1]-1.0<1e-6)
        self.assertTrue(P_prime[2]-0.0<1e-6)
        P_prime = cam.rotate(P, 90, 90)
        print("P_prime:", cam.vec_show(P_prime))
        # what here? (0,1,0) 90° on Y-axis???
        #self.assertTrue(P_prime[0]-0.0<1e-6)  # x=0, y=1, z=1
        #self.assertTrue(P_prime[1]-1.0<1e-6)
        #self.assertTrue(P_prime[2]-0.0<1e-6)

        pass

def main():
    unittest.main()
    return 0

exit(main())
