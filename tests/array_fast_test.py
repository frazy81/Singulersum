#!/usr/bin/python3

# 2021-03-15 ph Created

"""
    array_fast_test.py

    2021-03-15 ph Created by Philipp Hasenfratz

    Used to find the best way to initialize and reinitialize the Draw2D() image buffer.
    The first version was incredibly slow (needed 0.5s for each image/frame). So I needed a fast and easy performance improvement in array reinitializing.
"""

# need a very fast way to reinitialize an array. Current method takes up to 0.5s for each
# new "frame" or picture. Busting down FPS to 2 (not to mention all drawing tasks)...

import sys
sys.path.append("..")
from Singulersum.Debug import Debug
import sys
import array
import copy

class ArrayTest(Debug):

    maxFloat  = sys.float_info.max

    def __init__(self, width=2048, height=2048):
        super().__init__()
        self.width  = width
        self.height = height
        self.data   = []
        self.zBuf   = []

    def dataInit1(self):
        # https://www.geeksforgeeks.org/python-which-is-faster-to-initialize-lists/
        # using * operator might even be faster (use for)
        self.debug("init data and zBuffer")
        timeit=self.timeit()
        self.data = [ [ [0,0,0] for x in range(self.width) ] for y in range(self.height) ]
        self.zBuf = [ [ ArrayTest.maxFloat for x in range(self.width) ] for y in range(self.height) ]
        self.data0 = [ [ [0,0,0] for x in range(self.width) ] for y in range(self.height) ]
        self.zBuf0 = [ [ ArrayTest.maxFloat for x in range(self.width) ] for y in range(self.height) ]
        self.debug("init complete.", timeit=timeit)

    def clear1(self):
        # this needs 0.5s!!!
        self.debug("test1: reinit data and zBuffer")
        timeit=self.timeit()
        self.data = self.data0
        self.zBuf = self.zBuf0
        self.debug("test1: reinit complete", timeit=timeit)

    def set1(self, x, y, r, g, b):
        x=int(x)
        y=int(y)
        if x<0 or y<0:      # negative indexes are possible! But must be ignored!
            return False
        r=int(r)
        g=int(g)
        b=int(b)
        try:
            self.data[y][x][0]=r
            self.data[y][x][1]=g
            self.data[y][x][2]=b
        except IndexError:
            return False
        return True

    def access1(self):
        self.debug("test1: access")
        timeit=self.timeit()
        for y in range(0,self.height):
            for x in range(0,self.width):
                self.set1(x, y, 1, 1, 1)
        self.debug("test1: access complete", timeit=timeit)

    def dataInit2(self):
        # https://www.geeksforgeeks.org/python-which-is-faster-to-initialize-lists/
        # using * operator might even be faster (use for)
        self.debug("init data and zBuffer")
        timeit=self.timeit()
        self.data = array.array("B", [0 for t in range(self.width*self.height*8) ] )
        self.zBuf = array.array("B", [0 for t in range(self.width*self.height) ] )
        self.data0= array.array("B", [0 for t in range(self.width*self.height*8) ] )
        self.zBuf0= array.array("B", [0 for t in range(self.width*self.height) ] )
        self.debug("init complete.", timeit=timeit)

    def clear2(self):
        self.debug("test1: reinit data and zBuffer")
        timeit=self.timeit()
        self.data = array.array("B", self.data0)
        self.zBuf = array.array("B", self.zBuf0)
        self.debug("test1: reinit complete", timeit=timeit)

    def set2(self, x, y, r, g, b):
        x=int(x)
        y=int(y)
        if x<0 or y<0:      # negative indexes are possible! But must be ignored!
            return False
        #pos = (y*self.height*3+x*3)
        pos = y << 12
        pos += x<<2
        r=int(r)
        g=int(g)
        b=int(b)
        try:
            self.data[pos]=r
            self.data[pos+1]=g
            self.data[pos+2]=b
        except IndexError:
            return False
        return True

    def access2(self):
        self.debug("test2: access")
        timeit=self.timeit()
        for y in range(0,self.height):
            for x in range(0,self.width):
                self.set2(x, y, 1, 1, 1)
        self.debug("test2: access complete", timeit=timeit)

    def dataInit3(self):
        # https://www.geeksforgeeks.org/python-which-is-faster-to-initialize-lists/
        # using * operator might even be faster (use for)
        self.debug("init data and zBuffer")
        timeit=self.timeit()
        self.data = [ [] for y in range(self.height) ]
        self.zBuf = [ [] for y in range(self.height) ]
        self.data0= array.array("B", [0 for t in range(self.width*3) ] )
        self.zBuf0= array.array("B", [0 for t in range(self.width)] )
        for y in range(self.height):
            self.data[y] = array.array("B", [0 for t in range(self.width*3) ] )
            self.zBuf[y] = array.array("B", [0 for t in range(self.width)] )
        self.debug("init complete.", timeit=timeit)

    def clear3(self):
        self.debug("test3: reinit data and zBuffer")
        timeit=self.timeit()
        self.data = [ [] for y in range(self.height) ]
        self.zBuf = [ [] for y in range(self.height) ]
        for y in range(self.height):
            self.data[y] = array.array("B", self.data0 )
            self.zBuf[y] = array.array("B", self.zBuf0 )
        self.debug("test1: reinit complete", timeit=timeit)

    def set3(self, x, y, r, g, b):
        x=int(x)
        y=int(y)
        if x<0 or y<0:      # negative indexes are possible! But must be ignored!
            return False
        r=int(r)
        g=int(g)
        b=int(b)
        try:
            self.data[y][3*x]=r
            self.data[y][3*x+1]=g
            self.data[y][3*x+2]=b
        except IndexError:
            return False
        return True

    def access3(self):
        self.debug("test3: access")
        timeit=self.timeit()
        for y in range(0,self.height):
            for x in range(0,self.width):
                self.set3(x, y, 1, 1, 1)
        self.debug("test3: access complete", timeit=timeit)

def test1():
    t = ArrayTest()
    print("test1:")
    print()
    t.dataInit1()
    #t.set1(1,1,1,1,1)
    t.clear1()
    assert(t.data[1][1][0]==0)
    t.access1()

    # test1 results:
    # - takes long to initialize initially: 3.94s
    # - takes long to zero again clear(): 0.11s
    # - is fast in access: 1.5s
    # - does overwrite self.data0! and data.zBuf!

    print()
    print("test2:")
    print()

    t.dataInit2()
    t.set2(1,1,1,1,1)
    t.clear2()
    pos = 1 << 12
    pos += 1<<2
    assert(t.data[pos]==0)
    t.access2()

    # test2 results:
    # - faster in initial initialize: 2.75s
    # - reinit is super fast: 0.0087s
    # - access is slower: 2.024s (even with bit-shift!)

    print()
    print("test3:")
    print()

    t.dataInit3()
    t.set3(1,1,1,1,1)
    t.clear3()
    assert(t.data[1][1]==0)
    t.access3()

    # test3 results:
    # - fast initialization!: 0.598s
    # - reinit is super fast: 0.00212s
    # - access is ok: 1.777s
    # this test is so far best!

def main():
    test1()

exit(main())
