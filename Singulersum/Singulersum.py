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

# TODO: poly_fill: max to (0,self.width] and same for height to reduce payload
#       the drawing sometimes takes extremely long, I think this is because some polygons
#       go far out the view port and polygon_fill tries to fill all the invisible pixels,
#       too.
# TODO: zIndex of polygons. What's the zIndex of a line (currently unimplemented).
#       Problem here is that currently all polygon pixels share the very same zIndex. How
#       ever the zIndex changes within the polygon.
# TODO: zIndex problems. I still have a lot of z-fighting, mostly due to the "todo" above
#       Polygons would need a zIndex calculus for each pixel.
# TODO: Function() class should enable the use the sg.time, so that custom functions may
#       change with time.
# TODO: tiny_house.yaml: size=2.0 stuff get out of universe, but should not. Rescale into
#       parent scale context wrong I assume. Need to check where and how I did that.
# TODO: Naming convention: always use named parameters instead of something like
#       point=(x,y,z). Easier for GUI (edit objects) and YAML

# Main TODO:
# - light (camera light) is still wrong (normal vector calculus depends on point order)
#       - this is why the sine_waves.yaml example has this "chessboard" kind of look.
#         this is not happening on STL files, because there the normal vector for polygons
#         is defined within the STL file and thus is not calculated by Singulersum.
# - if normalvector of a poly is pointing in the view vector V direction, the poly must be
#   "hidden", use green to show that a poly is viewed from the back side.
# - z-Index problems, z-fighting
# - ObjectBrowser implementation
# - spheres, cubes, planes and other geometric forms
# - I guess there are still lots of bugs in the Miniverse placing (recursively place,
#   rotate, translate and resize other Miniverses (such as Function() or Sphere()) into
#   Singulersum)
# - Fast polyfill or my own approach: don't use polys at all, use a SurroundingPoly only.
# - Game and Mobile version of Singulversum
# - .yaml files to configure Singulversi
# - singulersum_video scenery.yaml -fps 30 scenery.mp4
# - singulersum_animatedgif scenery.yaml -fps 30 scenery.gif
# - singulersum_jpg scenery.yaml -time 0:20.5 -cam 1.0x0.1x0.3x0x0x0 scenery_20_5.jpg

# TODO later:
# - Debug verbousity
# - Test suite
# - colors in STL's
# - .yaml files to load a scenery/singulersum
# - texture mapping
# - 3D text
# - 3D sphere/camera illustration
# - 3D solar system Euler+ simulation
# - iPhone X 3D face STL test
# - Binocular tests, stereoview with two cameras
# - VR360° videos

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
        self.top=None
        self.startTime = time.time()
        self.time      = 0.0
        self.scale     = (1.0, 1.0, 1.0)
        self.place     = (0.0, 0.0, 0.0)        # where are we placed in the parent frame
        self.size      = 1.0
        self.azimuth   = 0.0
        self.altitude  = 0.0
        self.roll      = 0.0
        self.object_count = 0
        self.objects   = {}
        self.id        = ""
        self.name      = None
        self.visibility = True
        if "visibility" in args:
            self.visibility = args["visibility"]
        self.name = "AnonymousObject"
        auto_fill = ["name", "scale", "size", "place", "azimuth", "altitude", "roll", "fill", "stroke", "alpha"]
        for name in auto_fill:
            if name in args and hasattr(self, name):
                self.debug("auto fill "+name+" with "+str(args[name]))
                setattr(self, name, args[name])

    def top(self):
        if self.top is not None:
            return self.top
        while parent is not None and isinstance(parent, Singulersum) is False:
            parent = parent.parent
        self.top=parent

    def setPlace(self, place):
        self.place = place

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

    def point(self, *kwargs, **args):
        self.object_count += 1
        name = "point#"+str(self.object_count)
        if "name" in args:
            name = args["name"]
        obj = Point(self, *kwargs, **args)
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

    def object(self, name=None, *kwargs, **args):
        self.object_count += 1
        if name is None:
            name = "obj#"+str(self.object_count)
        obj = Object(self, *kwargs, **args)
        self.objects[name]=obj
        return obj

    def update(self):
        changed = False
        for name, obj in self.objects.items():
            if obj.update() is True:
                changed = True
        return changed

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

    # animate the Miniverse
    def animation(self, **args):
        sg = self.parent
        self.debug("next animation cycle for {:s}".format(str(self)))
        ox = self.x
        oy = self.y
        oz = self.z
        self.debug("args:", args)
        self.debug("old values:")
        self.debug("  x", ox)
        self.debug("  y", oy)
        self.debug("  z", oz)
        args["time"] = sg.time      # TODO: or camera setup time! if it inherits from Mini

        """
        type: animation
        stop: time>1.0
        start:time>0.0
        begin: [1.2, 2.0, 1.0]
        end: [1.6, 0.1, 0.5]
        camera: cam         # or miniverse: xyz
        x: begin[0] + (time*(end[0] - begin[0]))
        y: begin[1] + (time*(end[1] - begin[1]))
        z: begin[2] + (time*(end[2] - begin[2]))
        """
        if "start" in args:
            if sg.time<args["start"]:
                return False
        if "stop" in args:
            if sg.time>args["stop"]:
                self.parent.callback("animation_stop", object=self)
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

        self.debug("current/new values:")
        self.debug("  x", self.x)
        self.debug("  y", self.y)
        self.debug("  z", self.z)

        if ox==self.x and oy==self.y and oz==self.z:
            # no change, return False
            # turned out to be wrong because of mathematical precision, sometimes there's
            # no change, as the mantissa of floats does not reflect any change
            return True
        else:
            return True


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
        self.cameras   = {}
        self.lights    = {}
        self.fps       = 0
        self.timing    = "fix"  # rt=realtime or fix
        self.timingFps = 30     # for timing=fix, choose framerate
        self.zBuffering= True   # hide polygons in background

        if "callback" in args:
            self.callback = args["callback"]
        else:
            self.callback = lambda event, **args: None

        self.showCoordinateSystem   = True
        self.showCenterOfView       = True
        self.showBackside           = True       # highlight polygons if viewed from back
        self.useFastHiddenPolyCheck = False      # this is lossy!
        self.polyOnlyGrid           = False      # show only lines of polynoms
        self.polyOnlyPoint          = False      # show only point clouds
        self.polyGrid               = False
        self.parent    = None
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

    def setTime(self, t):
        self.time=t

    def timeAdvance(self):
        if self.timing=="rt":
            self.time = time.time()-self.startTime
        elif self.timing=="fix":
            self.time += 1.0/self.timingFps
        return self.time

    def update(self):
        changed = False
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
        self.timeAdvance()
        if changed is False:
            self.callback("animation_stop", object=self)
        return changed

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

    def __init__(self, parent, *kwargs, **args):
        super().__init__(parent, *kwargs, **args)

# some basic drawers

class Line(BasicObject):

    def __init__(self, parent, x1, y1, z1, x2, y2, z2, *kwargs, **args):
        super().__init__(parent)
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

class Point(BasicObject):

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

    def __init__(self, parent, x="x", y="y", z="z", rel=None, amount=20, *kwargs, **args):
        super().__init__(parent, *kwargs, **args)
        self.amount=amount
        x = self.replaceKnown(x)
        y = self.replaceKnown(y)
        z = self.replaceKnown(z)
        self.rel=rel
        if rel is None:
            # check for x in x
            if x.find("x")==-1:
                rel=0
            elif y.find("y")==-1:
                rel=1
            elif z.find("z")==-1:
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
        self.x=x
        self.y=y
        self.z=z
        self.createPolygons()

    def update(self):
        # TODO: if x,y or z depend on time, then change polys here and return True!
        return False

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
                poly = self.polygon( corps[i][j], corps[i+1][j], corps[i+1][j+1])
                poly2= self.polygon( corps[i][j], corps[i+1][j+1], corps[i][j+1])
                pass

        self.debug("polygon count for this function: ", cnt)

    def replaceKnown(self, arg):
        #arg=arg.replace("sin", "sin")
        return arg

    def eval(self, x, y, z):
        nx=eval(self.x, globals(), {"x":x, "y":y, "z":z} )
        ny=eval(self.y, globals(), {"x":x, "y":y, "z":z} )
        nz=eval(self.z, globals(), {"x":x, "y":y, "z":z} )
        return (nx,ny,nz)

class Sphere(Object):

    def __init__(self, parent, x=0.0, y=0.0, z=0.0, r=1.0, amount=20, *kwargs, **args):
        self.alpha = 0.3
        self.fill = [255, 255, 255]
        self.stroke = [255, 255, 255]
        super().__init__(parent, *kwargs, **args)
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
                # 2021-03-21 ph without +0.0001 we have collinear points and normal can't
                #               be calculated.
                theta = (the/self.amount)*2*pi+0.0001
                alpha = (alp/self.amount)*pi+0.0001
                x = self.x + self.r*cos(theta)*sin(alpha)
                y = self.y + self.r*sin(theta)*sin(alpha)
                z = self.z + self.r*cos(alpha)
                corps[the][alp] = (x,y,z)
        # make polis
        cnt=0
        # 2021-03-27 ph range begins at -1, so that sphere is closed.
        #               but there's still a hole...
        for i in range(-1,self.amount-1):
            for j in range(0, self.amount-1):
                cnt+=1
                poly = self.polygon( corps[i][j], corps[i+1][j], corps[i+1][j+1], alpha=self.alpha, fill=self.fill, stroke=self.stroke)
                poly2= self.polygon( corps[i][j], corps[i+1][j+1], corps[i][j+1], alpha=self.alpha, fill=self.fill, stroke=self.stroke)
        # need to fix normal vectors.
        self.debug("polygon count for this sphere: ", cnt)

class Cube(Object):

    def __init__(self, parent, x=0.0, y=0.0, z=0.0, r=1.0, *kwargs, **args):
        super().__init__(parent, *kwargs, **args)
        self.x = x
        self.y = y
        self.z = z
        self.r = r
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
        p0 = (x+r, y-r, z+r)
        p1 = (x+r, y+r, z+r)
        p2 = (x+r, y+r, z-r)
        p3 = (x+r, y-r, z-r)
        # back
        p4 = (x-r, y-r, z+r)
        p5 = (x-r, y+r, z+r)
        p6 = (x-r, y+r, z-r)
        p7 = (x-r, y-r, z-r)

        # front
        self.polygon( p3, p1, p0, name="front1", fill="white" )
        self.polygon( p3, p2, p1, name="front2", fill="white" )
        # top
        self.polygon( p0, p1, p5, name="top1", fill="#ff0000" )
        self.polygon( p0, p5, p4, name="top2", fill="#ff0000" )
        # left
        self.polygon( p0, p4, p7, name="left1", fill="#00f000" )
        self.polygon( p0, p7, p3, name="left2", fill="#00f000" )
        # right
        self.polygon( p1, p6, p5, name="right1", fill="#0000ff" )
        self.polygon( p1, p2, p6, name="right2", fill="#0000ff"  )
        # bottom
        self.polygon( p3, p7, p6, name="bottom1", fill="#ffff00"  )
        self.polygon( p3, p6, p2, name="bottom2", fill="#ffff00" )
        # back
        self.polygon( p4, p5, p6, name="back1", fill="#00ffff" )
        self.polygon( p4, p6, p7, name="back2", fill="#00ffff" )

class Plane(Object):

    def __init__(self, parent, xf=1.0, yf=1.0, zf=1.0, df=1.0, *kwargs, **args):
        # define plane as xf*x+yf*y+zf*z+df=0
        super().__init__(parent, *kwargs, **args)
        #self.function(x="x", y="y", z="("+str(df)+"-1*"+str(xf)+"*x-1*"+str(yf)+"*y)/"+str(zf), rel="z", amount=10)
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
                        self.parent.point( nx,ny,nz, color="red" )


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
