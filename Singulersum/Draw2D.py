# 2021-03-11 ph Created
# 2021-03-12 ph first working solution with points, lines, polygons including anti-alias and poly_fill
# 2021-03-13 ph again using arrays instead of bytearray
# 2021-03-13 ph polygon_fill is now roughly 4 times faster. Forgot to min/max x/y
# 2021-03-13 ph clear() now using the way faster list comprehensions instead of this odd appending and for loops (the for's took 0.5s to zero the whole zBuf/data arrays)
# 2021-03-14 ph Vector Algebra is moved to VectorMath.py
# 2021-03-15 ph Performance Boost with new array method!
# 2021-03-27 ph alpha not part of color fix
# 2021-03-27 ph polygon stroke optional
# 2021-03-28 ph polygon wide out of range fix
# 2021-04-01 ph points(), the fast horizontal fill method for point(). polygons faster

"""
    class Singulersum.Draw2D()

    2021-03-11 ph Created by Philipp Hasenfratz

    Draw2D is a 2 dimensional painting class that is used in Singulersum to draw the 2D image. It features points, lines, polynom(-fill) with optional z-Buffering, color and alpha-channel (for instance planes may be half transparent and not changing the z-Index).

    To get something totally in front, use zIndex=0.0 (distance viewer->object = 0.0)

    Currently Alpha is not yet implemented...

    draw2d = Draw2D(width=1024, height=768)
    draw2d.point(5, 5, color="white")
    poly = (
        (10,10),
        (20,10),
        (20,20),
        (10,20)
    )
    draw2d.polygon_fill(*poly, fill="#0000ff", stroke="#ff0000", zIndex=5.0)

    img = draw2d.image()    # RGBA bytes() image, each color is 8-bit encoded.
"""

# TODO: zIndex for line is kind of undefined

import math
import struct
import array
import sys      # float.max

#from multiprocessing import Queue, Process
from queue import Empty

from Singulersum.Debug import Debug
from Singulersum.VectorMath import VectorMath

class Draw2D(Debug):

    maxFloat  = sys.float_info.max

    def __init__(self, width=1024, height=768):
        super().__init__()
        self.width  = width
        self.height = height
        self.data   = []
        self.zBuf   = []
        #self.poly_threads = 32      # None if no multithreading shall be used
        self.poly_end = False
        #self.poly_worker = []
        #self.poly_queue = []
        self.dataInit()

    def dataInit(self):
        # https://www.geeksforgeeks.org/python-which-is-faster-to-initialize-lists/
        # using * operator might even be faster (use for)
        self.debug("init data and zBuffer")
        timeit=self.timeit()
        self.data = [ [] for y in range(self.height) ]
        self.zBuf = [ [] for y in range(self.height) ]
        self.data0= array.array("B", [0 for t in range(self.width*4) ] )
        self.zBuf0= array.array("f", [Draw2D.maxFloat for t in range(self.width)] )
        for y in range(self.height):
            self.data[y] = array.array("B", self.data0 )
            self.zBuf[y] = array.array("f", self.zBuf0 )
        self.debug("init complete.", timeit=timeit)

    def clear(self):
        # this once needed 0.5s
        self.debug("reinit data and zBuffer")
        timeit=self.timeit()
        self.data = [ [] for y in range(self.height) ]
        self.zBuf = [ [] for y in range(self.height) ]
        for y in range(self.height):
            self.data[y] = array.array("B", self.data0 )
            self.zBuf[y] = array.array("f", self.zBuf0 )
        self.debug("reinit complete", timeit=timeit)

    def zIndex(self,x, y, zIndex=None):
        x=int(x)
        y=int(y)
        if x<0 or y<0:
            return 0.0  # outside the plane => show (TODO: this is a problem!)
        if x>=self.width or y>=self.height:
            return 0.0  # outside the plane => show (TODO: this is a problem!)
        if zIndex is not None:
            # set zIndex
            try:
                self.zBuf[y][x]=zIndex
                return True
            except IndexError:
                return False
        else:
            # get zIndex
            try:
                return self.zBuf[y][x]
            except IndexError:
                # TODO: better way?
                return -1

    def set(self, x, y, r, g, b):
        x=int(x)
        y=int(y)
        if x<0 or y<0:      # negative indexes are possible! But must be ignored!
            return False
        r=int(r)
        g=int(g)
        b=int(b)
        x = x << 2          # x = x*4
        try:
            self.data[y][x]=r
            self.data[y][x+1]=g
            self.data[y][x+2]=b
        except IndexError:
            return False
        return True

    def get(self, x, y):
        try:
            x = x << 2      # x = x*4
            return (self.data[y][x], self.data[y][x+1], self.data[y][x+2])
        except IndexError:
            return (-1, -1, -1)

    def getColor(self, color="white"):
        if color=="white":
            return (255, 255, 255)
        elif color=="black":
            return (255, 255, 255)
        elif color=="red":
            return (255, 0, 0)
        elif color=="green":
            return (0, 255, 0)
        elif color=="blue":
            return (0, 0, 255)
        elif isinstance(color, tuple) or isinstance(color, list):
            if len(color)==3:
                return ( int(color[0]), int(color[1]), int(color[2]) )
            else:
                print("Draw2D() expects 3 numbers (R,G,B) for a tuple defined color")
                exit(0)
        elif str(color)[0]=="#":
            if len(color)==7:
                return (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))
            else:
                print("Draw2D() expects 3 numbers (R,G,B) for a tuple defined color")
                exit(0)
        else:
            print(color, " is not a supported color")
            raise ValueError
            return (255, 255, 255)

    def point(self, x, y, color="white", alpha=0, zIndex=None):  # alpha=0: solid, alpha=255: transp.
        if color is None:
            return False
        color = self.getColor(color)
        if alpha!=0:
            # get the "old" point color
            (r,g,b) = self.get(x, y)
            # alpha it to "black", alpha=256: black (background), alpha=0 original color
            color0=int( alpha/255.0*r + (255-alpha)/255.0*color[0] )
            color1=int( alpha/255.0*g + (255-alpha)/255.0*color[1] )
            color2=int( alpha/255.0*b + (255-alpha)/255.0*color[2] )
            color=(color0, color1, color2)
        else:
            color=(color[0], color[1], color[2])
        show=True
        if zIndex is not None:
            if self.zIndex(x,y)<zIndex:
                show=False
        if show is True:
            self.set(x, y, *color)
            if zIndex is not None:
                self.zIndex(x, y, zIndex)

    def points(self, x1, x2, y, color="white", alpha=0, zIndex=None):
        # fill points between x1 and x2 in line y as fast as fast as possible. Optimizing
        # polygon throughput. This is basically the same code as point, but it does many
        # in a row at a time and this is much faster. Also because index checks are in
        # polygon_fill itself.
        if color is None:
            return False
        color = self.getColor(color)
        xd = x1 << 2     # x=x*4, x for data (color array)
        xi = x1          # x for zBuffer array
        xdend = x2 << 2
        while xd<=xdend:
            zIndexAt = self.zBuf[y][xi]
            if alpha!=0:
                # get old colors
                r = self.data[y][xd]
                g = self.data[y][xd+1]
                b = self.data[y][xd+2]
                # alpha it to "black", alpha=256: black (background), alpha=0 original color
                color0=int( alpha/255.0*r + (255-alpha)/255.0*color[0] )
                color1=int( alpha/255.0*g + (255-alpha)/255.0*color[1] )
                color2=int( alpha/255.0*b + (255-alpha)/255.0*color[2] )
                color=(color0, color1, color2)
            show=True
            if zIndex is not None:
                if zIndexAt<zIndex:
                    show=False
            if show is True:
                self.data[y][xd]=color[0]
                self.data[y][xd+1]=color[1]
                self.data[y][xd+2]=color[2]
                if zIndex is not None:
                    self.zBuf[y][xi]=zIndex
            xd+=4
            xi+=1

    def line(self, x0, y0, x1, y1, color="white", alpha=0, thickness=1, antialias=False, zIndex=None):
        if thickness==1:
            if antialias is True:
                return self.line_antialias(x0, y0, x1, y1, color=color, alpha=alpha, antialias=antialias, zIndex=zIndex)
            else:
                return self.line_bresenham(x0, y0, x1, y1, color=color, alpha=alpha, antialias=antialias, zIndex=zIndex)
        # draw edge-lines with antialias, then "center" lines with bresenham
        if antialias is True:
            self.line_antialias(x0-thickness/2, y0-thickness/2, x1-thickness/2, y1-thickness/2, color, alpha, zIndex=zIndex)
            self.line_antialias(x0+thickness/2, y0+thickness/2, x1+thickness/2, y1+thickness/2, color, alpha, zIndex=zIndex)
        orient = False
        while thickness/2>=1.0:
            tx=0
            if orient is False:
                adder=-1*thickness/2
                orient=True
            else:
                adder=thickness/2
                orient=False
            self.line_bresenham(x0+adder, y0+adder, x1+adder, y1+adder, color=color, alpha=alpha, zIndex=zIndex)
            thickness-=1

    def line_bresenham(self, x0, y0, x1, y1, color="white", alpha=0, antialias=False, zIndex=None):
        # Bresenham's line algorithm
        x0=int(x0)
        y0=int(y0)
        x1=int(x1)
        y1=int(y1)
        dx = abs(x1-x0)
        sx = -1
        if x0<x1:
            sx = 1
        dy = -abs(y1-y0)
        sy = -1
        if y0<y1:
            sy = 1
        err = dx+dy
        while True:
            self.point(x0, y0, color=color, alpha=alpha, zIndex=zIndex)
            if x0==x1 and y0==y1:
                break
            e2 = 2*err
            if e2>=dy:
                err += dy
                x0 += sx
            if e2<=dx:
                err += dx
                y0 += sy

    def line_antialias(self, x0, y0, x1, y1, color="white", alpha=0, antialias=True, zIndex=None):
        if antialias is False:
            print("line_antialias() got antialias=False: should not have come to here.")
            exit(0)
        if x0==x1 and y0==y1:
            # this brakes line_antialias, gradient=float(dy)/float(dx), div by 0
            return False
            pass
        # Xiaolin Wu's antialias line algorithm
        ipart = lambda x: math.floor(x)
        round = lambda x: ipart(x+0.5)
        fpart = lambda x: x-math.floor(x)
        rfpart = lambda x: 1-fpart(x)
        steep = False
        if abs(y1-y0)>abs(x1-x0):
            steep = True
        if steep:
            t=x0
            x0=y0
            y0=t
            t=y1
            y1=x1
            x1=t
        if x0>x1:
            t=x1
            x1=x0
            x0=t
            t=y1
            y1=y0
            y0=t
        dx = x1-x0
        dy = y1-y0
        gradient=float(dy)/float(dx)
        if dx==0.0:
            dx=1.0

        xend=round(x0)
        yend=y0+gradient*(xend-x0)
        xgap=rfpart(x0+0.5)
        xpxl1=xend
        ypxl1=ipart(yend)
        if steep:
            self.point(ypxl1, xpxl1, color=color, alpha=255-rfpart(yend)*xgap*255, zIndex=zIndex)
            self.point(ypxl1+1, xpxl1, color=color, alpha=255-fpart(yend)*xgap*255, zIndex=zIndex)
        else:
            self.point(xpxl1, ypxl1, color=color, alpha=255-rfpart(yend)*xgap*255, zIndex=zIndex)
            self.point(xpxl1, ypxl1+1, color=color, alpha=255-fpart(yend)*xgap*255, zIndex=zIndex)
        intery=yend+gradient

        xend=round(x1)
        yend=y1+gradient*(xend-x1)
        xgap=fpart(x1+0.5)
        xpxl2=xend
        ypxl2=ipart(yend)
        if steep:
            self.point(ypxl2, xpxl2, color=color, alpha=255-rfpart(yend)*xgap*255, zIndex=zIndex)
            self.point(ypxl2+1, xpxl2, color=color, alpha=255-fpart(yend)*xgap*255, zIndex=zIndex)
        else:
            self.point(xpxl2, ypxl2, color=color, alpha=255-rfpart(yend)*xgap*255, zIndex=zIndex)
            self.point(xpxl2, ypxl2+1, color=color, alpha=255-fpart(yend)*xgap*255, zIndex=zIndex)

        if steep:
            for x in range(xpxl1+1, xpxl2-1):
                self.point(ipart(intery), x, color=color, alpha=255-rfpart(intery)*255, zIndex=zIndex)
                self.point(ipart(intery)+1, x, color=color, alpha=255-fpart(intery)*255, zIndex=zIndex)
                intery=intery+gradient
        else:
            for x in range(xpxl1+1, xpxl2-1):
                self.point(x, ipart(intery), color=color, alpha=255-rfpart(intery)*255, zIndex=zIndex)
                self.point(x, ipart(intery)+1, color=color, alpha=255-fpart(intery)*255, zIndex=zIndex)
                intery=intery+gradient

    def polygon_fill(self, *kwargs, fill="white", alpha=0, zIndex=None, fast=False):
        # https://alienryderflex.com/polygon_fill/
        polyCorners=len(kwargs)
        # find min/max x, min/max y
        minx=self.width-1
        maxx=0
        miny=self.height-1
        maxy=0
        for p in kwargs:
            if p[0]<minx:
                minx=p[0]
            if p[0]>maxx:
                maxx=p[0]
            if p[1]<miny:
                miny=p[1]
            if p[1]>maxy:
                maxy=p[1]
        # polygon width out of range fixes:
        if minx<0:
            minx=0
        if maxx>self.width-1:
            maxx=self.width-1
        if miny<0:
            miny=0
        if maxy>self.height-1:
            maxy=self.height-1
        for y in range(miny, maxy):
            # build node list
            nodes=0
            nodeX=[]
            j=polyCorners-1
            for i in range(0, polyCorners):
                poly=kwargs[i]
                polyJ=kwargs[j]
                if (poly[1]<y and polyJ[1]>=y) or (polyJ[1]<y and poly[1]>=y):
                    nodeX.append( int(poly[0]+(y-poly[1])/(polyJ[1]-poly[1])*(polyJ[0]-poly[0])) )
                    nodes+=1
                j=i
            # sort the nodes, bubble sort
            i=0
            while i<nodes-1:
                if nodeX[i]>nodeX[i+1]:
                    swap=nodeX[i]
                    nodeX[i]=nodeX[i+1]
                    nodeX[i+1]=swap
                    if i>0:
                        i-=1
                else:
                    i+=1
            # fill the pixels between node pairs
            for i in range(0, nodes, 2):
                if nodeX[i] >= self.width-1:
                    break
                if nodeX[i+1] > 0:
                    if nodeX[i]<0:
                        nodeX[i]=0
                    if nodeX[i+1]>self.width-1:
                        nodeX[i+1]=self.width-1
                    self.points(nodeX[i], nodeX[i+1], y, fill, alpha, zIndex)

    def polygon(self, *kwargs, stroke="white", fill="white", alpha=0, antialias=False, zIndex=None):
        p0 = kwargs[0]
        pl = kwargs[0]
        # always fill for zIndex:
        self.polygon_fill(*kwargs, fill=fill, alpha=alpha, zIndex=zIndex)
        if stroke is not None:
            for i in range(1,len(kwargs)):
                p=kwargs[i]
                self.line(pl[0], pl[1], p[0], p[1], color=stroke, alpha=alpha, antialias=antialias, zIndex=zIndex)
                pl=p
            self.line(pl[0], pl[1], p0[0], p0[1], color=stroke, alpha=alpha, antialias=antialias, zIndex=zIndex)

    def polygon_end(self):
        # signal threads that they may end
        self.poly_end = True

    def magnify_testing(self, scalex, scaley):
        # take the left/top most 20 pixel and magnify them
        # TODO!
        pass

    def image(self):
        # return image as rawimage RGBA, 4 Byte (bytes() array) per pixel
        self.debug("draw2d.image() start", self.width, self.height)
        timeit = self.timeit()
        data = bytearray(0) # 4xbyte, R, G, B, A
        # we fake RGBA, because we use x = x << 2 bit shift operators to make
        # pixel calculus faster
        for y in range(0, self.height):
            data.extend(self.data[y])
            assert(len(self.data[y])==self.width*4)
            assert(len(data)==(y+1)*self.width*4)
        self.debug("draw2d.image() complete.", timeit=timeit)
        return bytes(data)
