#!/usr/bin/python3

# 2021-03-25 ph Created

"""
    unittest_gui.py

    Created:    2021-03-23 Philipp Hasenfratz

    unittests to run all yaml files in the GUI and see if one crashes.
"""

# TODO: auto-quit after 10s runtime
# TODO: run-tests.sh script to execute all unittests
# TODO: unittest for singulersum_video.py

import sys
import os

sys.path.append('..')

from Singulersum.Singulersum import Singulersum
import unittest
import dumper

class Tests(unittest.TestCase):

    def test_001(self):
        print("test_001:")

        os.chdir("../scripts")
        for file in os.listdir("../yaml"):
            print("yaml file", file)
            ret = os.system("python3 ./singulersum_gui.py -qvi ../yaml/"+file)
            ret = ret>>8
            self.assertEqual(ret, 0)

        os.chdir("../tests")

        print("test_001 end.")
        print()

        pass

def main():
    unittest.main()
    return 0

exit(main())
