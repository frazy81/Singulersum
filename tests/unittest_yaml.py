#!/usr/bin/python3

# 2021-03-23 ph Created
# 2021-03-24 ph up to date with current SingulersumYaml
# 2021-04-01 ph Function x,y,z => fx, fy, fz
# 2021-04-02 ph scale is float (before: tuple)

"""
    yaml.py

    Created:    2021-03-23 Philipp Hasenfratz

    unittests to create SingulersumYaml.py class
"""

import sys

sys.path.append('..')

from Singulersum.Singulersum import Singulersum
import unittest
import dumper

class Tests(unittest.TestCase):

    def callback(self, event, **args):
        if event=="set":
            setattr(self, args["name"], args["value"])

    def test_001(self):
        print("test_001:")
        sg = Singulersum(1.0)
        test = """
sg:
    scale: 5.0
animator:
    type: animation
    stop: 1.0
    start: 0.0
    camera: cam
    begin: [1.2, 2.0, 1.0]
    end: [1.6, 0.1, 0.5]
    x: begin[0] + (time*(end[0] - begin[0]))
    y: begin[1] + (time*(end[1] - begin[1]))
    z: begin[2] + (time*(end[2] - begin[2]))
        """
        sg.yaml(data=test)

        self.assertEqual(sg.scale, 5.0)

        print("test_001 end.")
        print()

        pass

    def test_002(self):
        print("test_002:")
        sg = Singulersum(1.0, callback=self.callback)
        test = """
gui:
    isPlaying: True
sg:
    scale: 5.0
    stop: 1.0
animator:
    type: animation
    stop: 1.0
    start: 0.0
    begin: [0, 0, 0]
    end: [1, 1, 1]
    x: begin[0] + (time*(end[0] - begin[0]))
    y: begin[1] + (time*(end[1] - begin[1]))
    z: begin[2] + (time*(end[2] - begin[2]))
cam:
    type: camera
    position: [1.0, 0.1, 0.2]
    lookat: [0.0, 0.0, 0.0]
    update: animator
f1:
    type: function
    visibility: True
    fx: x
    fy: y
    fz: sin(x)+sin(y)
    rel: z
    scale: 5.0
    size: 2.0
f2:
    type: function
    visibility: False
    fx: x
    fy: y
    fz: sin(x)+sin(y)
    rel: z
    scale: 5.0
    size: 2.0
p1:
    type: point
    point: [5.0, 5.0, 5.0]

        """

        data = sg.yaml(data=test)

        print(data)

        self.assertEqual(sg.scale, 5)

        self.assertEqual(sg.cameras["cam"].x, 1)
        self.assertEqual(sg.cameras["cam"].y, 0.1)
        self.assertEqual(sg.cameras["cam"].z, 0.2)

        self.assertEqual(sg.objects["f1"].visibility, True)

        self.assertEqual(sg.objects["f2"].visibility, False)

        sg.setTime(0.5)
        self.assertEqual(sg.time, 0.5)

        print("update 1 for time=0.5")
        sg.update()
        print(sg.cameras["cam"].x, "=?", 0.5)
        self.assertTrue(abs(sg.cameras["cam"].x-0.5)<0.1)
        print("done update 1")
        sg.setTime(0.9)
        print("update 2 for time=0.9")
        sg.update()
        print(sg.cameras["cam"].x, "=?", 0.9)
        self.assertTrue(abs(sg.cameras["cam"].x-0.9)<0.1)
        print("done update 2")

        print("test_002 end.")
        print()

    def test_003(self):
        print("test_003:")
        sg = Singulersum(1.0, callback=self.callback)
        file = "../yaml/sine_waves.yaml"

        self.animated=False

        data = sg.yaml(file=file)

        self.assertEqual(self.animated, True)

        print("test_003 end.")
        print()

    def test_004(self):
        print("test_004:")
        sg = Singulersum(1.0, callback=self.callback)
        file = "../yaml/tiny_house.yaml"

        self.animated=False

        data = sg.yaml(file=file)

        print(data)

        self.assertEqual(self.animated, True)
        self.assertEqual(self.camera, "cam1")
        print("test_004 end.")
        print()

    def test_005(self):
        print("test_005:")
        sg = Singulersum(1.0, callback=self.callback)
        file = "../yaml/singulersum.yaml"

        data = sg.yaml(file=file)

        self.assertEqual(sg.scale, 5.0)

        print("tangential_plane_e.x:", sg.objects["tangential_plane_e"].x)
        self.assertEqual(sg.objects["tangential_plane_e"].x, -1.0)

        print("test_005 end.")
        print()

def main():
    unittest.main()
    return 0

exit(main())
