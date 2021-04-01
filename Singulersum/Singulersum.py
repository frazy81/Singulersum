# 2021-03-05 ph Created
# 2021-03-08 ph first working solution with a predefined camera position
# 2021-03-11 ph second working solution with variable camera position
# 2021-03-12 ph raw Tk drawing to Draw2D (to enable zBuffering)
# 2021-03-13 ph lines/points now drawn AFTER polygons, so that they're in Front
# 2021-03-14 ph new algorithm for (x', y', z')->(x", y") transformations
# 2021-03-15 ph Function now only creates polygons in two dimensions where the third is calculated.
# 2021-03-16 ph Camera detects changes itself and calls setupCamera() if needed.
# 2021-03-16 ph Singulersum (and all Objects) are itself a Miniverse
# 2021-03-17 ph Miniverse first works
# 2021-03-21 ph new algorithm is now using rotation matrices. The old algorithm can
#               be found in /5th
# 2021-03-21 ph Model3D renamed to Singulersum
# 2021-03-21 ph Made it Miniverse capable (recursively go through all Miniverses and
#               apply transformations)
# 2021-03-21 ph line_plane_intersection had a bug and reported C-P_prime instead of C-P
#               (the actual distance from camera to point P), still some z-fighting
# 2021-03-23 ph miniverse.objects is now a dict (name=>object) not a list (changed for
#               SingulersumYaml)
# 2021-03-23 ph Singulersum got YAML support
# 2021-03-24 ph Camera is now also a Miniverse and Miniverse inherits from VectorMath
# 2021-03-24 ph Animation is now shared (defined in Miniverse and Camera can use it, as
#               Camera is inheriting from Miniverse)
# 2021-03-25 ph Camera class is now in it's own file /Singulersum/Camera.py for
#               readability
# 2021-03-25 ph default camera always stays (and reported back to GUI using callback)
# 2021-03-26 ph polygon normal vector calculus corrected
# 2021-03-26 ph cube fixes (colors, less z-fighting, normal vectors corrected)
# 2021-03-27 ph close sphere fix (sphere was not "closed")
# 2021-03-27 ph animation did not recognize radius fix
# 2021-03-27 ph stl maxX,maxY,maxZ -> scale fix. scale needs to be the absolute maximum
# 2021-03-27 ph polygon color now fill=<color>, stroke=<color>
# 2021-03-28 ph plane
# 2021-03-28 ph Point->Dot rename
# 2021-03-28 ph sg.showOnlyBoundingBox
# 2021-03-29 ph update function in Miniverse
# 2021-03-29 ph objects relatively positioned to their parent (x,y,z is place in parent)
# 2021-04-01 ph Miniverse time fix (Miniverse time relative to Singulersum time)
# 2021-04-01 ph Camera now part of Miniverse instead of Singulersum
# 2021-04-01 ph Function class: time as variable so that func. may depend on time
# 2021-04-01 ph faster polygon_fill (using points()) in Draw2D

"""
    class Singulersum.Singulersum()

    2021-03-05 ph Created by Philipp Hasenfratz

    Singulersum() is the "universe" of Singulersum where all 3D objects are placed in.

    sg = Singulersum(scale=(5.0, 5.0, 5.0))
    sg.logfile("./singulersum.log")                 # debugging

    # make a camera to look at the scene:
    self.cam = sg.camera( 1.3, 0.2, 0.3, 0.0, 0.0, 0.0, fov=140, width=1024, height=768)
    sg.coordinateSystem()                           # show initial reference coord-system

    # define objects
    obj1 = sg.function(x="x", y="y", z="sin(x)+sin(y)", scale=(5.0, 5.0, 5.0), size=2.0)
    obj2 = sg.fromSTL("./STLs/Sphericon-ascii.stl")

    sg.update()             # update the scene/singulersum

    img = cam.image()       # returns an RGBA bytes() with each color 8-bit encoded.
                            # note that alpha channel is NOT used, I just needed 4 bytes
                            # to improve index speed (using byte-shift instead of
                            # multiply operations)

    Singulersum dependencies:
     - pyyaml
     - Tkinter
     - PIL (Pillow)
"""

# TODO: zIndex of polygons. What's the zIndex of a line (currently unimplemented).
#       Problem here is that currently all polygon pixels share the very same zIndex. How
#       ever the zIndex changes within the polygon. Need a per pixel zIndex calculus
# TODO: tiny_house.yaml: size=2.0 stuff get out of universe, but should not. Rescale into
#       parent scale context wrong I assume. Need to check where and how I did that.
# NOTE: Naming convention: always use named parameters instead of something like
#       point=(x,y,z). Easier for GUI (edit objects) and YAML

# Main TODO:
# - z-Index problems, z-fighting (example: cube.yaml)
# - Rotation fix needed?
# - True BoundingBox algorithm (and add cross-lines, too)
# - camera may be child of Miniverse (check functionality)
# - Enter a room check (are walls done correctly?)
# - ObjectBrowser implementation
# - I guess there are still lots of bugs in the Miniverse placing (recursively place,
#   rotate, translate and resize other Miniverses (such as Function() or Sphere()) into
#   Singulersum)
# - Maybe don't use polys at all, use a SurroundingPoly only.
# - Game and Mobile version of Singulversum
# - singulersum_video scenery.yaml -fps 30 scenery.mp4
# - singulersum_animatedgif scenery.yaml -fps 30 scenery.gif
# - singulersum_jpg scenery.yaml -time 0:20.5 -cam 1.0x0.1x0.3x0x0x0 scenery_20_5.jpg

# TODO later:
# - Debug verbousity
# - Test suite (in progress)
# - colors in STL's
# - texture mapping
# - 3D text
# - 3D sphere/camera illustration
# - 3D solar system Euler+ simulation
# - iPhone X 3D face STL test
# - Binocular tests, stereoview with two cameras
# - VR360° videos

# LEARNINGS:
# - The performance killer (at least using python) is filling polygons. Current status: a
#   bit improved
# - fast array init essential: array.array("B", [0 for t in range(self.width*4) ] )
# - STL is easy to read (both binary and textual)

from PIL import Image
from PIL import ImageDraw
from math import *
import re
import struct
import time

from Singulersum.STL import STL
from Singulersum.SingulersumYaml import SingulersumYaml
from Singulersum.Debug import Debug
from Singulersum.VectorMath import VectorMath

class Miniverse(VectorMath, Debug):

    def __init__(self, parent, *kwargs, **args):
        super().__init__()
        self.parent=parent
        if isinstance(parent, Singulersum):
            self.sg = parent
        else:
            self.sg=parent.sg
        self.startTime = time.time()
        self.scale     = (1.0, 1.0, 1.0)
        self.x         = 0.0
        self.y         = 0.0
        self.z         = 0.0
        self.size      = 1.0
        self.azimuth   = 0.0
        self.altitude  = 0.0
        self.roll      = 0.0
        self.object_count = 0
        self.objects   = {}
        self.cameras   = {}
        self.lights    = {}
        self.id        = ""
        self.name      = None
        self.visibility = True
        self.updateFunction = None
        if "x" in args:
            self.x = args["x"]
        if "y" in args:
            self.y = args["y"]
        if "z" in args:
            self.z = args["z"]
        if "update" in args:
            self.debug("set update function")
            self.setUpdate(args["update"])
        if "visibility" in args:
            self.visibility = args["visibility"]
        self.name = "AnonymousObject"
        auto_fill = ["name", "scale", "size", "place", "azimuth", "altitude", "roll", "fill", "stroke", "alpha"]
        for name in auto_fill:
            if name in args and hasattr(self, name):
                self.debug("auto fill "+name+" with "+str(args[name]))
                setattr(self, name, args[name])

    def reset(self):
        self.debug("Miniverse.reset(), delete all objects")
        self.objects={}         # forget all objects
        self.startTime = time.time()
        self.time = 0.0

    # basic shaders (inherit from BasicObject)

    def line(self, *kwargs, **args):
        self.object_count += 1
        name = "line#"+str(self.object_count)
        if "name" in args:
            name = args["name"]
        obj = Line(self, *kwargs, **args)
        self.objects[name]=obj
        return obj

    def dot(self, *kwargs, **args):
        self.object_count += 1
        name = "dot#"+str(self.object_count)
        if "name" in args:
            name = args["name"]
        obj = Dot(self, *kwargs, **args)
        self.objects[name]=obj
        return obj

    def polygon(self, *kwargs, **args):
        self.object_count += 1
        name = "poly#"+str(self.object_count)
        if "name" in args:
            name = args["name"]
        obj = Polygon(self, *kwargs, **args)
        self.objects[name]=obj
        return obj

    def coordinateSystem(self, *kwargs, **args):
        self.object_count += 1
        name = "cs#"+str(self.object_count)
        if "name" in args:
            name = args["name"]
        obj = CoordinateSystem(self, *kwargs, **args)
        self.objects[name]=obj
        return obj

    # shaders that create a new Miniverse (inherit from Object)

    def function(self, name=None, *kwargs, **args):
        self.object_count += 1
        if name is None:
            name = "func#"+str(self.object_count)
        obj = Function(self, *kwargs, **args)
        self.objects[name]=obj
        return obj

    def sphere(self, name=None, *kwargs, **args):
        self.object_count += 1
        if name is None:
            name = "sphere#"+str(self.object_count)
        obj = Sphere(self, *kwargs, **args)
        self.objects[name]=obj
        return obj

    def cube(self, name=None, *kwargs, **args):
        self.object_count += 1
        if name is None:
            name = "cube#"+str(self.object_count)
        obj = Cube(self, *kwargs, **args)
        self.objects[name]=obj
        return obj

    def plane(self, name=None, *kwargs, **args):
        self.object_count += 1
        if name is None:
            name = "plane#"+str(self.object_count)
        obj = Plane(self, *kwargs, **args)
        self.objects[name]=obj
        return obj

    def point(self, name=None, *kwargs, **args):
        self.object_count += 1
        if name is None:
            name = "point#"+str(self.object_count)
        obj = Point(self, *kwargs, **args)
        self.objects[name]=obj
        return obj

    def object(self, name=None, *kwargs, **args):
        self.object_count += 1
        if name is None:
            name = "obj#"+str(self.object_count)
        obj = Object(self, *kwargs, **args)
        self.objects[name]=obj
        return obj

    # camera and light

    def camera(self, *kwargs, **args):
        assert("name" in args)
        from Singulersum.Camera import Camera
        camera = Camera(self, *kwargs, **args)
        self.cameras[args["name"]]=camera
        return camera

    # light not yet implemented!
    #def light(self, name=None, *kwargs, **args):
    #    light = Light(self, *kwargs, **args)
    #    self.lights[name]=light
    #    return light

    # timing and animate SG

    # stringifier
    def __str__(self):
        string = type(self).__name__
        if self.name is not None:
            string = string + "(" + self.name + ")"
        return string

    # external file interface for STL (both text and binary)

    def stl(self, file, *kwargs, **args):
        anonymousObject = self.object(*kwargs, **args)
        stl = STL(self, file)
        (maxX, maxY, maxZ, polygon_count) = stl.read()
        self.debug("importing polygons from stl")
        importer = self.timeit()
        max = 0
        if maxX>max:
            max=maxX
        if maxY>max:
            max=maxY
        if maxZ>max:
            max=maxZ
        anonymousObject.scale = (max, max, max)
        polys = stl.getPolygons()
        norms = stl.getNormalvectors()
        for i in range(0, len(polys)):
            poly = polys[i]
            norm = norms[i]
            anonymousObject.polygon( *poly, normalvector=norm, stroke=None, fill=(255,255,255) )
        self.debug("import completed.", timeit=importer)
        return anonymousObject

    def yaml(self, file=None, data=None, *kwargs, **args):
        anonymousObject = self.object(*kwargs, **args)
        yaml = SingulersumYaml(self, file=file, data=data)
        # now fire all gui settings via the callback to the GUI. AFTER the objects have
        # been initialized. So that for example "gui.camera=cam1", cam1 is actually
        # directly accessible by the GUI
        if yaml.namespace["gui"] is not None:
            for name, value in yaml.namespace["gui"].items():
                # fire event for GUI
                self.debug("in 'gui' namespace, calling the GUI callback. event=set, name=", name, "value=", value)
                self.callback("set", name=name, value=value)
        return anonymousObject

    def setPlace(self, x, y, z):
        x0=self.x
        y0=self.y
        z0=self.z
        self.x=x
        self.y=y
        self.z=z
        if x0!=x or y0!=y or z0!=z:
            return True
        else:
            return False

    def setPlaceSpherical(self, azimuth, altitude, r):
        x0=self.x
        y0=self.y
        z0=self.z
        C = (r, 0, 0)
        C = self.rotate(C, azimuth)
        C = self.rotate(C, 0.0, -1*altitude)
        (x, y, z) = C
        if altitude>0:
            # TODO: check
            #assert(z>0)
            pass
        self.x = x
        self.y = y
        self.z = z
        assert(self.x**2+self.y**2+self.z**2-r**2<1e-06)
        Aazimuth = atan2(self.y, self.x)
        if Aazimuth<0.0:
            Aazimuth = 2*pi+azimuth
        Aazimuth = Aazimuth/pi*180
        Aradius = sqrt(self.x**2+self.y**2+self.z**2)
        Aaltitude = atan2(self.z, sqrt(self.x**2+self.y**2))/pi*180
        #print("azimuth:", azimuth, Aazimuth)
        #print("altitude:", altitude, Aaltitude)
        #print("radius:", r, Aradius)
        # TODO: fails, need to check
        #assert(abs(self.azimuth-Aazimuth)<0.1)
        #assert(abs(self.altitude-Aaltitude)<0.1)
        #assert(abs(self.radius-Aradius)<0.1)
        if x0!=x or y0!=y or z0!=z:
            return True
        else:
            return False

    # animate the Miniverse
    def animation(self, **args):
        sg = self.sg
        args["time"] = self.getTime()
        self.debug("next animation cycle for {:s}, time:{:0.2f}".format(str(self), args["time"]))
        ox = self.x
        oy = self.y
        oz = self.z

        """
        type: animation
        stop: time>1.0
        start:time>0.0
        begin: [1.2, 2.0, 1.0]
        end: [1.6, 0.1, 0.5]
        x: begin[0] + (time*(end[0] - begin[0]))
        y: begin[1] + (time*(end[1] - begin[1]))
        z: begin[2] + (time*(end[2] - begin[2]))
        """
        if "start" in args:
            if self.getTime()<args["start"]:
                return False
        if "stop" in args:
            if self.getTime()>args["stop"]:
                self.sg.callback("animation_stop", object=self)
                return False

        type = "unknown"
        if "x" in args:
            type="absolute"
            self.x = eval(args["x"], args)
        if "y" in args:
            type="absolute"
            self.y = eval(args["y"], args)
        if "z" in args:
            type="absolute"
            self.z = eval(args["z"], args)

        if "radius" in args:
            if type=="absolute":
                self.debug("animation() got absolute and spherical information! Only have x,y,z set OR r,azimuth,altitude!")
                exit(0)
            type="spherical"
            self.radius = eval(str(args["radius"]), args)
        if "azimuth" in args:
            if type=="absolute":
                self.debug("animation() got absolute and spherical information! Only have x,y,z set OR r,azimuth,altitude!")
                exit(0)
            type="spherical"
            self.azimuth = eval(str(args["azimuth"]), args)
        if "altitude" in args:
            if type=="absolute":
                self.debug("animation() got absolute and spherical information! Only have x,y,z set OR r,azimuth,altitude!")
                exit(0)
            type="spherical"
            self.altitude = eval(str(args["altitude"]), args)

        if type=="unknown":
            self.debug("animation() got no spherical or absolute information!")
            exit(0)
            return False

        if type=="spherical":
            self.debug("animation(), setPlaceSpherical(", self.azimuth, self.altitude, self.radius, ")")
            self.setPlaceSpherical(self.azimuth, self.altitude, self.radius)
        else:
            self.debug("animation(), setPlace(", self.x, self.y, self.z, ")")
            self.setPlace(self.x, self.y, self.z)

        if ox==self.x and oy==self.y and oz==self.z:
            # no change, return False
            # turned out to be wrong because of mathematical precision, sometimes there's
            # no change, as the mantissa of floats does not reflect any change
            return True
        else:
            return True

    def isSpecialContext(self, context):
        if "altitude" in context:
            if context["altitude"]!=0.0:
                return True
        if "azimuth" in context:
            if context["azimuth"]!=0.0:
                return True
        if "roll" in context:
            if context["roll"]!=0.0:
                return True
        if "x" in context and context["x"]!=0.0:
            return True
        if "y" in context and context["y"]!=0.0:
            return True
        if "z" in context and context["z"]!=0.0:
            return True
        if "size" in context:
            if context["size"]!=1.0:
                return True
        return False

    # NOTE: the camera induced rotation/translation is done directly in project_p2d()
    def applyContext(self, context, *kwargs, **args):
        list = []
        size = context["size"]
        for p in kwargs:
            if size!=1.0:
                p = self.stretch(p, size, size, size)
            p = self.rotate(p, context["azimuth"])
            p = self.rotate(p, 0.0, context["altitude"])
            p = self.rotate(p, 0.0, 0.0, context["roll"])
            # translate to place
            p = self.vec_add(p, (context["x"], context["y"], context["z"]))
            list.append(p)
        return list

    def setUpdate(self, func):
        self.updateFunction = func

    def update(self):
        changed = False
        self.debug("Miniverse().update() for "+str(self))
        if self.updateFunction is not None:
            self.debug("updateFunction for "+str(self)+" not None. Calling the function.")
            if self.updateFunction(self) is True:
                changed = True
        for name, obj in self.objects.items():
            if obj.update() is True:
                changed = True
        # light not yet implemented...
        #for light in self.lights:
        #    if light.update() is True:
        #        changed = True
        for name, cam in self.cameras.items():
            if cam.update() is True:
                changed = True
        return changed

    def getTime(self):
        # this Miniverse time is:
        # thisMiniverse.startTime-Singulersum.startTime+Singulersum.time
        # for making it Multithreading capable, must use function, not object property.
        return self.startTime-self.sg.startTime+self.sg.time

class Singulersum(Miniverse):

    version = 0.1

    # the whole universe is (-1,-1,-1) to (1,1,1) how ever a scale can be used
    # this only changes Functions and Objects, not Cameras and Lights!

    # total number of dimensions: 5 (x, y, z, 4thDim_T, 5thDim_U), t and u can be what
    # they want. Usually interpreted as colors(t) and illuminessence (u)
    # the dimension t has nothing to do with the time used to process functions/objects
    # movements.    # TODO: this is not implemented.

    def __init__(self, *kwargs, **args):
        super().__init__(self, *kwargs, **args)
        self.fps       = 0
        self.timing    = "fix"  # rt=realtime or fix
        self.timingFps = 30     # for timing=fix, choose framerate
        self.time      = 0.0    # relative time in Singulversum
        self.zBuffering= True   # hide polygons in background

        if "callback" in args:
            self.callback = args["callback"]
        else:
            self.callback = lambda event, **args: None

        self.showCoordinateSystem   = True
        self.showCenterOfView       = True
        self.showBackside           = True       # highlight polygons if viewed from back
        self.showOnlyBoundingBox    = False      # for quick GUI animation, only BB'es
        self.useFastHiddenPolyCheck = False      # this is lossy!
        self.polyOnlyGrid           = False      # show only lines of polynoms
        self.polyOnlyPoint          = False      # show only point clouds
        self.polyGrid               = False

        # update() function updates the Singulersum.time and then computes all absolute
        # positions of all objects (and subobjects) at that time and throws them in a
        # linear (not nested) list with key {time} into self.allObjects. This is then used
        # in the Camera.image() method to compute the camera picture and render it using
        # Draw2D
        self.allObjects = {}
        pass

    def reset(self):
        self.debug("Singulersum.reset(), delete all objects")
        defaultCam = None
        if "default" in self.cameras:
            defaultCam = self.cameras["default"]
        self.cameras={}         # delete all cameras
        if defaultCam is not None:
            self.cameras["default"] = defaultCam
            self.callback("set", name="camera", value="default")
        self.lights={}         # delete all lights
        super().reset()

    def setTime(self, t):
        self.time=t

    def timeAdvance(self):
        if self.timing=="rt":
            self.time = time.time()-self.startTime
        elif self.timing=="fix":
            self.time += 1.0/self.timingFps
        return self.time

    def boundingBoxShow(self, versum, context):
        self.debug("showBoundingBox")
        bb_lines = []

        r = versum.size
        x = versum.x
        y = versum.y
        z = versum.z

        # front
        p0 = (r, 0-r, r)
        p1 = (r, r, r)
        p2 = (r, r, 0-r)
        p3 = (r, 0-r, 0-r)
        # back
        p4 = (0-r, 0-r, r)
        p5 = (0-r, r, r)
        p6 = (0-r, r, 0-r)
        p7 = (0-r, 0-r, 0-r)

        line_points = [
            [p0, p1, p2, p3],
            [p0, p1, p5, p4],
            [p1, p2, p6, p5],
            [p0, p3, p7, p4],
            [p3, p2, p6, p7],
            [p4, p5, p6, p7],
        ]
        for lines in line_points:
            # TODO: better way?
            lines = self.applyContext(context, *lines)
            bb_lines.append( [ lines[0], lines[1], "white", 0 ] )
            bb_lines.append( [ lines[1], lines[2], "white", 0 ] )
            bb_lines.append( [ lines[2], lines[3], "white", 0 ] )
            bb_lines.append( [ lines[3], lines[0], "white", 0 ] )

        return bb_lines

    def object_iterator(self, versum):
        # we first calculate all polygons and process them later using different
        # algorithms
        # polys = [ {points=>[], distance=>1.2, normalvector=>()}, {...} ]
        # basic object lists:
        self.debug("object_iterator for "+str(versum))
        polys = []
        lines = []  # [ (p1, p2, color), ... ]
        dots  = []  # [ (p1, color), ...]
        context = {
            "x"       : versum.x,
            "y"       : versum.y,
            "z"       : versum.z,
            "size"    : versum.size,
            "azimuth" : versum.azimuth,
            "altitude": versum.altitude,
            "roll"    : versum.roll,
        }
        isSpecialContext = self.isSpecialContext(context)

        for name, obj in versum.objects.items():
            # use K-means and implement multi core processing?

            if obj.visibility is False:
                continue

            if self.parent.showOnlyBoundingBox is True:
                if isinstance(obj, Line) or isinstance(obj, Dot) or isinstance(obj, Polygon) or isinstance(obj, CoordinateSystem):
                    continue
                lines.extend(self.boundingBoxShow(obj, context))

            # BasicObjects
            if isinstance(obj, Line):
                p1 = (obj.x1, obj.y1, obj.z1)
                p2 = (obj.x2, obj.y2, obj.z2)
                if isSpecialContext:
                    (p1, p2) = self.applyContext(context, p1, p2)
                lines.append( [p1, p2, obj.color, obj.thickness] )
            elif isinstance(obj, Dot):
                p = (obj.x, obj.y, obj.z)
                if isSpecialContext:
                    p = self.applyContext(context, p)[0]
                dots.append( [p, obj.color] )
            elif isinstance(obj, Polygon):
                poly = []
                normalvector = None
                colorize = 0
                for i in range(0, len(obj.points)):
                    p = [ obj.points[i][0], obj.points[i][1], obj.points[i][2] ]
                    if isSpecialContext:
                        p = self.applyContext(context, p)[0]
                    poly.append( p )
                normalvector = obj.normalvector
                if isSpecialContext:
                    normalvector = self.applyContext(context, normalvector)[0]

                polys.append( { "points":poly, "normalvector":normalvector, "fill":obj.fill, "stroke":obj.stroke, "alpha":obj.alpha, "name":obj.name } )
            elif isinstance(obj, CoordinateSystem):
                # ignore it! It added Lines to the parent context
                pass

            elif issubclass(type(obj), Object):
                (ndots, nlines, npolys) = self.object_iterator(obj)
                for d in ndots:
                    (dot, color) = d
                    if isSpecialContext:
                        dot = self.applyContext(context, dot)[0]
                    dots.append( [dot, color] )
                for l in nlines:
                    (p1, p2, color, thickness) = l
                    if isSpecialContext:
                        # TODO: does the list expansion work here? Or do I need indexing?
                        # maybe I need: ps = self.applyContext...
                        # p1 = ps[0]; p2 = ps[1]; !!! Seems to work I see grid when rotate
                        (p1, p2) = self.applyContext(context, p1, p2)
                    lines.append( [p1, p2, color, thickness] )
                for p in npolys:
                    ppoints = p["points"]   # points reserved for points not polys!
                    normalvector = [ p["normalvector"][0], p["normalvector"][1], p["normalvector"][2] ]
                    if isSpecialContext:
                        # TODO: no stretch, no translate, just rotate
                        normalvector = self.applyContext(context, normalvector)[0]
                    npoints = []
                    for pt in ppoints:
                        if isSpecialContext:
                            pt = self.applyContext(context, pt)[0]
                        npoints.append(pt)
                    poly = { "points":npoints, "normalvector":normalvector, "fill":p["fill"], "stroke":p["stroke"], "alpha":p["alpha"], "name":p["name"] }
                    polys.append( poly )
                pass
            else:
                print("object type not known!")
                exit(0)

        return (dots, lines, polys)

    def update(self):
        changed = False
        self.debug("step 0: Singulersum().update() is updating the Singulersum for time="+str(self.time))
        timeit = self.timeit()
        changed = super().update()
        if self.stop<=self.time:
            # force animation end
            changed = False
        if changed is False:
            self.debug("nothing has changed in the Singulersum: callback animation_stop")
            self.callback("animation_stop", object=self)
        self.debug("step 0 Singulersum().update() is calculating absolute positions.")
        (dots, lines, polys) = self.object_iterator(self)
        self.allObjects[self.time] = [dots, lines, polys]
        self.debug("step 0 complete", timeit=timeit)
        return changed

    def frameDone(self, time):
        # done with frame at time "time", forget this time in self.allObjects
        # this call is needed for Garbage Collection, otherwise the mem fills up.
        self.allObjects.pop(time, None)
        return True

    def quit(self):
        super().quit()

class Light():

    def __init__(self, sg, x=.5, y=.5, z=1.0, type="parallel", intensity=1.0):
        self.parent=sg
        self.x=x
        self.y=y
        self.z=z
        self.type=type
        if type not in ("parallel", "radial"):
            print("light type '{:s}' not understood".format(type))
            type="parallel"
        self.intensity=intensity

    def update(self):
        return False

class BasicObject(Debug):

    def __init__(self, parent, *kwargs, **args):
        super().__init__()
        self.visibility = True
        self.name = None
        if "visibility" in args:
            self.visibility = args["visibility"]
        if "name" in args:
            self.name = args["name"]
        if issubclass(type(parent).__class__, Miniverse):
            self.debug("BasicObject parent must be either Miniverse or Singulersum, not", type(parent))
            raise ObjectError       # TODO
        self.parent=parent

    def update(self):
        return False

class Object(Miniverse):

    """
        Object().__init__(x, y, z)

        x, y, z is where the object will be placed into the parent context
    """
    def __init__(self, parent, x=0.0, y=0.0, z=0.0, *kwargs, **args):
        super().__init__(parent, *kwargs, **args)
        self.x = x
        self.y = y
        self.z = z

# some basic drawers

class Line(BasicObject):

    def __init__(self, parent, x1, y1, z1, x2, y2, z2, *kwargs, **args):
        super().__init__(parent, x=0.0, y=0.0, z=0.0)
        scale = self.parent.scale
        if "color" in args:
            self.color = args["color"]
        else:
            self.color = "white"
        if "thickness" in args:
            self.thickness=args["thickness"]
        else:
            self.thickness=1
        self.x1=x1/scale[0]
        self.y1=y1/scale[1]
        self.z1=z1/scale[2]
        self.x2=x2/scale[0]
        self.y2=y2/scale[1]
        self.z2=z2/scale[2]

class Dot(BasicObject):

    # singulersum_gui.py requires explicit parameters x, y, z. Easier this way.
    def __init__(self, parent, x=0.0, y=0.0, z=0.0, *kwargs, **args):
        super().__init__(parent)
        self.x = x
        self.y = y
        self.z = z
        if "color" in args:
            self.color=args["color"]
        else:
            self.color="white"

class Polygon(BasicObject, VectorMath):

    vec = None

    def __init__(self, sg, *kwargs, normalvector=None, fill="white", stroke=None, alpha=0, **args):
        self.fill=fill
        self.stroke=stroke
        self.alpha=alpha
        super().__init__(sg, **args)
        VectorMath.__init__(self)
        self.normalvector = normalvector        # normal vector of the poly
        scale = sg.scale
        self.points = []
        for point in kwargs:
            self.points.append( (point[0]/scale[0], point[1]/scale[1], point[2]/scale[2] ))
        if normalvector is not None:
            return None # __init__ shall return None, but all ok.

        # calculate the normalvector to this polygon
        p0 = self.points[0]
        p1 = self.points[1]
        p2 = self.points[2]
        self.normalvector = self.poly_normalvector(p0, p1, p2)

# other drawers

class Function(Object):

    def __init__(self, parent, fx="x", fy="y", fz="z", rel=None, amount=20, alpha=0, fill="white", stroke=None, *kwargs, **args):
        self.amount=amount
        self.rel=rel
        self.alpha=alpha
        # if function uses parameter time, it must be recalculated for each new "time"
        self.dependsOnTime = False
        self.fill = fill
        self.stroke = stroke
        self.fx=fx
        self.fy=fy
        self.fz=fz
        super().__init__(parent, *kwargs, **args)
        if rel is None:
            # check for x in x
            if fx.find("x")==-1:
                rel=0
            elif fy.find("y")==-1:
                rel=1
            elif fz.find("z")==-1:
                rel=2
            else:
                print("Function(): either x, y or z must depend on the others!")
                exit(0)
            self.rel=rel
        else:
            if rel=="x":
                rel=0
            elif rel=="y":
                rel=1
            elif rel=="z":
                rel=2
            else:
                print("unsupported Function.rel=", rel, "must be x,y or z")
                exit(0)
            self.rel=rel
        # check if time is used and set dependsOnTime accordingly
        if self.fx.find("time")!=-1 or self.fy.find("time")!=-1 or self.fz.find("time")!=-1:
            self.dependsOnTime=True
        self.createPolygons()

    def update(self):
        changed = False
        # TODO: if x,y or z depend on time, then change polys here and return True!
        if self.dependsOnTime is True:
            # forget previous polygons and create new ones.
            self.objects = {}
            self.createPolygons()
            changed = True
        else:
            changed = False
        changed_child = super().update()
        if changed_child is True:
            changed = True
        return changed

    def createPolygons(self):
        i=-1
        j=-1
        amount = self.amount
        stepper = 1.0/amount
        corps = []
        for i in range(0, amount):
            corps.append([])
            for j in range(0, amount):
                corps[i].append([])
        for i in range(0,amount):
            for j in range(0, amount):
                p = ()
                if self.rel==2:
                    nx=(float(i)/amount*2.0-1.0)*self.scale[0]
                    ny=(float(j)/amount*2.0-1.0)*self.scale[1]
                    p = self.eval(nx,ny,0)
                elif self.rel==0:
                    ny=(float(i)/amount*2.0-1.0)*self.scale[1]
                    nz=(float(j)/amount*2.0-1.0)*self.scale[2]
                    p = self.eval(0,ny,nz)
                elif self.rel==1:
                    nx=(float(i)/amount*2.0-1.0)*self.scale[0]
                    nz=(float(j)/amount*2.0-1.0)*self.scale[2]
                    p = self.eval(nx,0,nz)
                else:
                    self.debug("unsupported!")
                    exit(0)
                corps[i][j] = p
        # make polis
        cnt=0
        for i in range(0,amount-1):
            for j in range(0, amount-1):
                cnt+=1
                poly = self.polygon( corps[i][j], corps[i+1][j], corps[i+1][j+1], alpha=self.alpha, fill=self.fill, stroke=self.stroke)
                poly2= self.polygon( corps[i][j], corps[i+1][j+1], corps[i][j+1], alpha=self.alpha, fill=self.fill, stroke=self.stroke)
                pass

        self.debug("polygon count for this function: ", cnt)

    def eval(self, x, y, z):
        nx=eval(self.fx, globals(), {"x":x, "y":y, "z":z, "time":self.sg.time} )
        ny=eval(self.fy, globals(), {"x":x, "y":y, "z":z, "time":self.sg.time} )
        nz=eval(self.fz, globals(), {"x":x, "y":y, "z":z, "time":self.sg.time} )
        return (nx,ny,nz)

class Sphere(Object):

    def __init__(self, parent, x=0.0, y=0.0, z=0.0, r=1.0, amount=20, alpha=0, *kwargs, **args):
        self.alpha = alpha
        self.fill = [255, 255, 255]
        self.stroke = [255, 255, 255]
        super().__init__(parent, x=x, y=y, z=z, *kwargs, **args)
        self.amount=amount
        self.x = x
        self.y = y
        self.z = z
        self.r = r
        self.createPolygons()

    def update(self):
        # TODO: if x,y or z depend on time, then change polys here and return True!
        return False

    def createPolygons(self):
        corps = []
        for i in range(0, self.amount):
            corps.append([])
            for j in range(0, self.amount):
                corps[i].append([])
        for the in range(0, self.amount):
            for alp in range(0, self.amount):
                # 2021-03-21 ph without +1e-05 we have collinear points and normal can't
                #               be calculated.
                theta = (the/(self.amount-1))*2*pi+1e-05
                alpha = (alp/(self.amount-1))*pi+1e-05
                x = self.r*cos(theta)*sin(alpha)
                y = self.r*sin(theta)*sin(alpha)
                z = self.r*cos(alpha)
                corps[the][alp] = (x,y,z)
        # make polis
        cnt=0
        # 2021-03-27 ph range begins at -1, so that sphere is closed.
        for i in range(-1,self.amount-1):
            for j in range(0, self.amount-1):
                cnt+=1
                poly = self.polygon( corps[i][j], corps[i+1][j], corps[i+1][j+1], alpha=self.alpha, fill=self.fill, stroke=self.stroke)
                poly2= self.polygon( corps[i][j], corps[i+1][j+1], corps[i][j+1], alpha=self.alpha, fill=self.fill, stroke=self.stroke)
        # need to fix normal vectors.
        self.debug("polygon count for this sphere: ", cnt)

class Cube(Object):

    def __init__(self, parent, x=0.0, y=0.0, z=0.0, r=1.0, alpha=0, *kwargs, **args):
        super().__init__(parent, *kwargs, **args)
        self.x = x
        self.y = y
        self.z = z
        self.r = r
        self.alpha = alpha
        self.createPolygons()

    def update(self):
        # TODO: if x,y or z depend on time, then change polys here and return True!
        return False

    def createPolygons(self):
        x = self.x
        y = self.y
        z = self.z
        r = self.r

        # front
        p0 = (r, 0-r, r)
        p1 = (r, r, r)
        p2 = (r, r, 0-r)
        p3 = (r, 0-r, 0-r)
        # back
        p4 = (0-r, 0-r, r)
        p5 = (0-r, r, r)
        p6 = (0-r, r, 0-r)
        p7 = (0-r, 0-r, 0-r)

        # front
        self.polygon( p3, p1, p0, name="front1", fill="white", alpha=self.alpha )
        self.polygon( p3, p2, p1, name="front2", fill="white", alpha=self.alpha )
        # top
        self.polygon( p0, p1, p5, name="top1", fill="#ff0000", alpha=self.alpha )
        self.polygon( p0, p5, p4, name="top2", fill="#ff0000", alpha=self.alpha )
        # left
        self.polygon( p0, p4, p7, name="left1", fill="#00f000", alpha=self.alpha )
        self.polygon( p0, p7, p3, name="left2", fill="#00f000", alpha=self.alpha )
        # right
        self.polygon( p1, p6, p5, name="right1", fill="#0000ff", alpha=self.alpha )
        self.polygon( p1, p2, p6, name="right2", fill="#0000ff", alpha=self.alpha )
        # bottom
        self.polygon( p3, p7, p6, name="bottom1", fill="#ffff00", alpha=self.alpha )
        self.polygon( p3, p6, p2, name="bottom2", fill="#ffff00", alpha=self.alpha )
        # back
        self.polygon( p4, p5, p6, name="back1", fill="#00ffff", alpha=self.alpha )
        self.polygon( p4, p6, p7, name="back2", fill="#00ffff", alpha=self.alpha )

class Plane(Object):

    def __init__(self, parent, x=0.0, y=0.0, z=0.0, v1x=0.0, v1y=1.0, v1z=0.0, v2x=0.0, v2y=0.0, v2z=1.0, amount=20, alpha=0, fill="white", stroke=None, *kwargs, **args):
        # define plane as xf*x+yf*y+zf*z+df=0
        self.amount = amount
        self.alpha = alpha
        self.fill = fill
        self.stroke = stroke

        super().__init__(parent, *kwargs, **args)

        self.x = x
        self.y = y
        self.z = z
        self.v1x = v1x
        self.v1y = v1y
        self.v1z = v1z
        self.v2x = v2x
        self.v2y = v2y
        self.v2z = v2z

        self.createPolygons()

    def createPolygons(self):
        i=-1
        j=-1
        amount = self.amount
        stepper = 1.0/amount
        corps = []
        for i in range(0, amount):
            corps.append([])
            for j in range(0, amount):
                corps[i].append([])
        v = [self.v1x, self.v1y, self.v1z]
        s = [self.v2x, self.v2y, self.v2z]
        for i in range(0,amount):
            for j in range(0, amount):
                p = (0.0, 0.0, 0.0)
                p = self.vec_add(p, self.vec_mul_scalar(v, i/amount) )
                p = self.vec_add(p, self.vec_mul_scalar(s, j/amount) )
                corps[i][j] = p
        # make polis
        cnt=0
        for i in range(0,amount-1):
            for j in range(0, amount-1):
                cnt+=1
                poly = self.polygon( corps[i][j], corps[i+1][j], corps[i+1][j+1], alpha=self.alpha, fill=self.fill, stroke=self.stroke)
                poly2= self.polygon( corps[i][j], corps[i+1][j+1], corps[i][j+1], alpha=self.alpha, fill=self.fill, stroke=self.stroke)
                pass

        self.debug("polygon count for this plane: ", cnt)

class Point(Object):

    def __init__(self, parent, x=0.0, y=0.0, z=0.0, alpha=0, fill="white", stroke=None, *kwargs, **args):
        self.alpha = alpha
        self.fill = fill
        self.stroke = stroke

        super().__init__(parent, *kwargs, **args)

        self.x = x
        self.y = y
        self.z = z

        self.sphere(0.0, 0.0, 0.0, r=self.scale[0]/200, fill=fill, stroke=None, amount=10)
        pass

class CoordinateSystem(BasicObject):

    # coordinate system injects lines into the PARENT! It's a BasicObject (no Miniverse!)
    # TODO: thickness is wrongly implemented

    def __init__(self, parent, *kwargs, **args):
        super().__init__(parent, *kwargs, **args)
        scale = self.parent.scale
        self.lineX = self.parent.line( 0.0, 0.0, 0.0, scale[0], 0, 0, color="green", thickness=1 )
        self.lineY = self.parent.line( 0.0, 0.0, 0.0, 0, scale[1], 0, color="blue", thickness=1 )
        self.lineZ = self.parent.line( 0.0, 0.0, 0.0, 0, 0, scale[2], color="red", thickness=1 )
        points = None
        if "points" in args:
            points = args["points"]
        if points is not None:
            for i in range(points):
                for j in range(points):
                    for k in range(points):
                        nx=(float(i)/points*2.0-1.0)*scale[0]
                        ny=(float(j)/points*2.0-1.0)*scale[1]
                        nz=(float(k)/points*2.0-1.0)*scale[2]
                        self.parent.dot( nx,ny,nz, color="red" )


    def update(self):
        scale = self.parent.scale
        changed = False
        if self.parent.showCoordinateSystem is True:
            # TODO: delete old lines first!
            #sg.line( 0.0, 0.0, 0.0, scale[0], 0, 0, color="green", tickness=5 )
            #sg.line( 0.0, 0.0, 0.0, 0, scale[1], 0, color="blue", thickness=5 )
            #sg.line( 0.0, 0.0, 0.0, 0, 0, scale[2], color="red", thickness=5 )
            changed = False
        return changed

    # OLD IMAGE code that was part of Camera() class:
    def oldimage(self):
        time = self.sg.time
        img = Image.new("RGBA", (self.width, self.height), (0,0,0))
        draw = ImageDraw.Draw(img)
        scale = self.sg.scale
        # find azimuth and altitude angles of camera and derive rotationMatrix
        rotationMatrix = (1, 0, 0, 0, 1, 0, 0, 0, 1)    # identity
        # now the camera's rotated position C' is roughly at (x',0,0) and the Origin
        # O' at (x'', 0, 0)
        # make lambdas to calculate angles of each point P' (x'', y'', z'')->(x''', y''')

        Px = lambda x, y, z: (x-self.x,y-self.y,0)
        Py = lambda x, y, z: (x-self.x,0,z-self.z)
        CO = lambda x: (x-self.x+.00000000001,0,0)    # Camera to Origin in plane of point
        vec_length = lambda vec: abs( sqrt(vec[0]**2+vec[1]**2+vec[2]**2) )
        # orient_x|y we need.
        orient_x = lambda x,y,z: 1 if y>=0 else -1
        orient_y = lambda x,y,z: 1 if z>=0 else -1
        theta_x = lambda x,y,z: atan( vec_length(Px(x,y,z)) / vec_length(CO(x)) ) / pi*180 * orient_x(x,y,z)
            # 0 if y==0 else
        theta_y = lambda x,y,z: atan( vec_length(Py(x,y,z)) / vec_length(CO(x)) ) / pi*180 * orient_y(x,y,z)
            # if z==0 else
        # from theta_x/theta_y calculate the new P position on the 2D plane
        x_three = lambda theta_x: theta_x/(self.fov/2)
        y_three = lambda theta_y: theta_y/(self.fov/2)
        scaling = lambda vec: ( vec[0]/scale[0], vec[1]/scale[1], vec[2]/scale[2] )
        x_2D = lambda vector: x_three(theta_x(vector[0], vector[1], vector[2]))
        y_2D = lambda vector: y_three(theta_y(vector[0], vector[1], vector[2]))
        xy = lambda vector: (x_2D(scaling(vector))*self.width/2+self.width/2, -1*y_2D(scaling(vector))*self.height/2+self.height/2)
        # y multiplies with -1, so that positive angles are up and negative angles down.

        # debug calculus
        p0 = (500, 1000, 0)
        p = scaling(p0)
        print("original point: "+str(p0))
        print("scaled point:   "+str(p))
        print("Px:             " + str( Px(p[0], p[1], p[2]) ))
        print("Py:             " + str( Py(p[0], p[1], p[2]) ))
        print("Cx:             " + str( self.x ) )
        print("CO:             " + str( CO(p[0]) ))
        print("|CO|:           " + str( vec_length(CO(p[0]))) )
        print("theta_x:        " + str( theta_x(p[0],p[1],p[2]) ) )
        print("theta_y:        " + str( theta_y(p[0],p[1],p[2]) ) )
        print("FOV:            " + str( self.fov ) )
        print("x_2D:           " + str( x_2D(p) ) )
        print("y_2D:           " + str( y_2D(p) ) )
        (x,y) = xy( p0 )        # p0 unscaled! xy() does the scaling!
        print("x in 2D pic:    " + str(x) )
        print("y in 2D pic:    " + str(y) )

        print()
        print("point series:")
        for y in range(-1*scale[1], scale[1], int(scale[1]/10)):
            p0 = (1000, 1000, y)
            (xs,ys) = xy(p0)
            print("p=({:d},{:d},{:d}), x'={:0.2f}, y'={:0.2f}, theta_y={:0.2f}".format(p0[0], p0[1], p0[2], xs, ys, theta_y(p0[0], p0[1], p0[2])))
