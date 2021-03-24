#!/usr/bin/python3

# 2021-03-23 ph Created
# 2021-03-24 ph up to date with current SingulersumYaml

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
        sg = Singulersum(1.0, 1.0, 1.0)
        test = """
sg:
    scale: [25.0, 20.0, 15.0]
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

        self.assertEqual(sg.scale[0], 25)
        self.assertEqual(sg.scale[1], 20)
        self.assertEqual(sg.scale[2], 15)

        print("test_001 end.")
        print()

        pass

    def test_002(self):
        print("test_002:")
        sg = Singulersum(1.0, 1.0, 1.0, callback=self.callback)
        test = """
gui:
    isPlaying: True
    stop: 1.0
sg:
    scale: [5.0, 5.0, 5.0]
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
animator2:
    type: animation
    stop: 1.0
    start: 0.0
    camera: cam
    begin: [0, 0, 0]
    end: [1, 1, 1]
    x: begin[0] + (time*(end[0] - begin[0]))
    y: begin[1] + (time*(end[1] - begin[1]))
    z: begin[2] + (time*(end[2] - begin[2]))
cam:
    type: camera
    position: [1.0, 0.1, 0.2]
    lookat: [0.0, 0.0, 0.0]
    update: animator2
f1:
    type: function
    visibility: True
    x: x
    y: y
    z: sin(x)+sin(y)
    rel: z
    scale: [5.0, 5.0, 5.0]
    size: 2.0
f2:
    type: function
    visibility: False
    x: x
    y: y
    z: sin(x)+sin(y)
    rel: z
    scale: [5.0, 5.0, 5.0]
    size: 2.0
p1:
    type: point
    point: [5.0, 5.0, 5.0]
stl:
    type: stl
    visibility: False
    file: ../stl/Utah_teapot.stl
    place: [-1.0, -1.0, 0]
default: cam

        """

        data = sg.yaml(data=test)

        print(data)

        self.assertEqual(sg.scale[0], 5)
        self.assertEqual(sg.scale[1], 5)
        self.assertEqual(sg.scale[2], 5)

        self.assertEqual(sg.cameras["cam"].x, 1)
        self.assertEqual(sg.cameras["cam"].y, 0.1)
        self.assertEqual(sg.cameras["cam"].z, 0.2)

        self.assertEqual(sg.objects["f1"].visibility, True)

        self.assertEqual(sg.objects["f2"].visibility, False)

        sg.setTime(0.5)
        self.assertEqual(sg.time, 0.5)

        sg.cameras["cam"].update()
        self.assertEqual(sg.cameras["cam"].x, 0.5)
        sg.setTime(1.0)
        sg.cameras["cam"].update()
        self.assertEqual(sg.cameras["cam"].x, 1.0)

        print("test_002 end.")
        print()

    def test_003(self):
        print("test_003:")
        sg = Singulersum(1.0, 1.0, 1.0, callback=self.callback)
        file = "../yaml/sine_waves.yaml"

        self.animated=False

        data = sg.yaml(file=file)

        self.assertEqual(self.animated, True)

        print("test_003 end.")
        print()

    def test_004(self):
        print("test_004:")
        sg = Singulersum(1.0, 1.0, 1.0, callback=self.callback)
        file = "../yaml/tiny_house.yaml"

        self.animated=False

        data = sg.yaml(file=file)

        print(data)

        self.assertEqual(self.animated, True)
        self.assertEqual(self.camera, "cam1")
        print("test_004 end.")
        print()

def main():
    unittest.main()
    return 0

exit(main())
