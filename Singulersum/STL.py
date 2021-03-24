# 2021-03-11 ph Created
# 2021-03-13 ph Normalvector readin
# 2021-03-21 ph Bug in STL: z coordinates were lost!

"""
    class Singulersum.STL()

    2021-03-11 ph Created by Philipp Hasenfratz

    STL() reads an STL file and returns the maximal x/y/z coordinates in the STL file as well as the poligon count. The __init__ method automatically detects wether the STL file to be loaded is textual or in binary format.

    self.polygons is a list containing all read polygons.

    at the moment STL does not yet read colors in STL files.

    I wrote STL as part of the Singulersum 3D project.
"""

import re
import struct

from Singulersum.Debug import Debug

# TODO: read colors from binary STL

class STL(Debug):

    def __init__(self, sg, file):
        super().__init__()
        self.file = file
        self.sg = sg
        self.type = "textual"       # "textual" STL or "binary" STL
        self.polygons = []
        self.normalvectors = []
        f = open(file, "rb")
        name = f.read(30).decode('ascii')
        self.debug("STL name", name)
        namere = re.compile("\s*solid\s+")
        f.close()
        match = namere.match(name)
        if match is not None:
            self.debug(self.file, "is a textual STL")
            self.type = "textual"
        else:
            self.debug(self.file, "is a binary STL")
            self.type = "binary"

    def addPolygon(self, *kwargs, **args):
        self.polygons.append( [*kwargs] )
        if "normalvector" in args:
            self.normalvectors.append(args["normalvector"])
        else:
            self.normalvectors.append( None )

    def getPolygons(self):
        return self.polygons

    def getNormalvectors(self):
        return self.normalvectors

    def read(self):
        self.debug("read the STL file")
        timeit = self.timeit()
        if self.type=="textual":
            ret = self.readAsciiStl()
        else:
            ret = self.readBinaryStl()
        self.debug("STL file is read", timeit=timeit)
        return ret

    # return (maxX, maxY, maxZ, polygon_count)
    def readAsciiStl(self):
        file = self.file
        max=[0,0,0]
        f = open(file, "r")
        name = f.readline()
        namere = re.compile("\s*solid\s+(.*)")
        match = namere.match(name)
        if match is not None:
            name = match.group(1)
        line = f.readline().rstrip()
        facetre = re.compile(r"^\s*facet normal (.*?) (.*?) (.*)", re.IGNORECASE & re.DOTALL)
        vertexre = re.compile(r"^\s*vertex (.*?) (.*?) (.*)", re.IGNORECASE & re.DOTALL)
        cur_poly = []
        normalvector = None
        polygon=0
        while line:
            #facet normal 0.70675 -0.70746 0
            #outer loop
            #vertex 1000 0 0
            #vertex 0 -1000 0
            #vertex 0 -999 -52
            #endloop
            #endfacet
            #endsolid ASCII_STL_of_a_sphericon_by_CMG_Lee
            if line[0:8]=="endsolid":
                break
            if line.find("outer loop")!=-1:
                if len(cur_poly)>0:
                    # close previous poly (how ever should not be)
                    print("WARN: close old polygon. Not STL conform!")
                    polygon+=1
                    self.addPolygon(*cur_poly, normalvector=normalvector)
                cur_poly=[]
            if line.find("endloop")!=-1:
                if len(cur_poly)>0:
                    self.addPolygon(*cur_poly, normalvector=normalvector)
                    polygon+=1
                    cur_poly=[]
            match=facetre.match(line)
            if match is not None:
                normalvector = (float(match.group(1)), float(match.group(2)), float(match.group(3)))
            match=vertexre.match(line)
            if match is not None:
                x=float(match.group(1))
                y=float(match.group(2))
                z=float(match.group(3))
                if abs(x)>max[0]:
                    max[0]=abs(x)
                if abs(y)>max[1]:
                    max[1]=abs(y)
                if abs(z)>max[2]:
                    max[2]=abs(z)
                cur_poly.append( (x, y, z) )
            line=f.readline().rstrip()
        f.close()
        self.debug("import of ", file, " completed.")
        self.debug("max +/-: {:0.2f} x {:0.2f} x {:0.2f}".format(max[0], max[1], max[2]))
        self.debug(polygon, " poligones read.")
        return (max[0], max[1], max[2], polygon)

    # return (maxX, maxY, maxZ, triangles)
    def readBinaryStl(self):
        file = self.file
        max=[0,0,0]
        f = open(file, "rb")
        name = f.read(80)
        self.debug("STL name", name)
        colorschema=0
        if re.search(r"color=", str(name), re.IGNORECASE):
            colorschema=16
        polygon = f.read(4)
        polygon = int.from_bytes(polygon, byteorder="little", signed=False)
        while True:
            data = f.read(50)
            if len(data)<50:
                break
            normal  = data[0:12]
            vertex1 = data[12:24]
            vertex2 = data[24:36]
            vertex3 = data[36:48]
            attr    = data[48:]
            x       = normal[0:4]
            y       = normal[4:8]
            z       = normal[8:12]
            normal  = ( struct.unpack('<f', x)[0], struct.unpack('<f', y)[0], struct.unpack('<f', z)[0] )
            x       = vertex1[0:4]
            y       = vertex1[4:8]
            z       = vertex1[8:12]
            vertex1 = ( struct.unpack('<f', x)[0], struct.unpack('<f', y)[0], struct.unpack('<f', z)[0] )
            x       = vertex2[0:4]
            y       = vertex2[4:8]
            z       = vertex2[8:12]
            vertex2 = ( struct.unpack('<f', x)[0], struct.unpack('<f', y)[0], struct.unpack('<f', z)[0] )
            x       = vertex3[0:4]
            y       = vertex3[4:8]
            z       = vertex3[8:12]
            vertex3 = ( struct.unpack('<f', x)[0], struct.unpack('<f', y)[0], struct.unpack('<f', z)[0] )
            attr    = int.from_bytes(attr, byteorder="little", signed=False)
            for vertex in (vertex1,vertex2,vertex3):
                if abs(vertex[0])>max[0]:
                    max[0]=abs(vertex[0])
                if abs(vertex[1])>max[1]:
                    max[1]=abs(vertex[1])
                if abs(vertex[2])>max[2]:
                    max[2]=abs(vertex[2])
            self.addPolygon( vertex1, vertex2, vertex3, normalvector=normal )
        f.close()
        self.debug("import of ", file, " completed.")
        self.debug("max +/-: {:0.2f} x {:0.2f} x {:0.2f}".format(max[0], max[1], max[2]))
        self.debug(polygon, " poligones read.")
        return (max[0], max[1], max[2], polygon)
