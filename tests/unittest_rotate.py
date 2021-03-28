#!/usr/bin/python3

# 2021-03-21 ph Created
# 2021-03-24 ph up to date with Camera()

"""
    unittest_rotate.py

    Created:    2021-03-21 Philipp Hasenfratz

    unittests to test rotation
"""

import sys

sys.path.append('..')

from Singulersum.Singulersum import Singulersum
import unittest
import dumper
from math import *

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

        P_prime = cam.rotate(P, 10, 0)
        print("P_prime 10° rotated: ", cam.vec_show(P_prime))
        P_prime = cam.rotate(P_prime, -10, 0)
        print("P_prime 10° rotated back again: ", cam.vec_show(P_prime))
        self.assertTrue(abs(P_prime[0]-P[0])<1e-6)
        self.assertTrue(abs(P_prime[1]-P[1])<1e-6)
        self.assertTrue(abs(P_prime[2]-P[2])<1e-6)

        pass

    def test_002(self):
        sg = Singulersum()
        cam = sg.camera(1, 0, 0, 0, 0, 0, name="cam1")

        self.V = [-1, 0, 0]
        print("V initial:", cam.vec_show(self.V))
        self.V = cam.rotate(self.V, 40)
        self.V = cam.rotate(self.V, 0, 60)
        print("V rotated:", cam.vec_show(self.V))
        self.lV = cam.vec_len(self.V)
        self.T = self.V
        self.T = cam.rotate(self.T, 0, -60)
        self.T = cam.rotate(self.T, -40, 0)
        print("V test reversed:", cam.vec_show(self.T))
        # ah, not commutative!

        print("testing V:")

        azimuth = atan2(self.V[1], self.V[0])
        #if azimuth<0.0:
        #    azimuth = 2*pi+azimuth
        
        self.view_azimuth = azimuth/pi*180
        self.view_radius  = self.lV
        self.view_altitude = atan2(self.V[2], sqrt(self.V[0]**2+self.V[1]**2))/pi*180
        print("View vector azimuth             ", "{:4f}".format(self.view_azimuth))
        print("View vector altitude:           ", "{:4f}".format(self.view_altitude))
        print("View vector 'radius'=length(V): ", "{:4f}".format(self.view_radius))

        print("after rotation:")

        # now we back transform View Vector and Camera position
        print("rotate back")
        print(180-self.view_azimuth)
        print(-1*self.view_altitude)
        self.V_prime = cam.rotate(self.V, 180-self.view_azimuth, -1*self.view_altitude, 0.0)
        print("Camera View Vector V_prime:     ", cam.vec_show(self.V_prime))
        print("Camera V_prime length:          ", "{:4f}".format(cam.vec_len(self.V_prime)))
        assert(abs(self.V_prime[0]-(-1.0))<0.5)
        assert(abs(self.V_prime[1]-0.0)<0.5)
        assert(abs(self.V_prime[2]-0.0)<0.5)
        self.V_prime = (-1.0, 0, 0)

def main():
    unittest.main()
    return 0

exit(main())
