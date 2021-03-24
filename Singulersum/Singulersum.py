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
# TODO: I still see distored objects (eg. Millenium Falcon). Something in Math still isn't
#       correct. I actually could think that it may have to do with the rotation
#       algorithm.
# TODO: tiny_house.yaml: size=2.0 stuff get out of universe, but should not. Rescale into
#       parent scale context wrong I assume. Need to check where and how I did that.

# Main TODO:
# - light (camera light) is still wrong.
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

from Singulersum.STL import STL
from Singulersum.SingulersumYaml import SingulersumYaml
from Singulersum.Debug import Debug
from Singulersum.VectorMath import VectorMath
from PIL import Image
from PIL import ImageDraw
from Singulersum.Draw2D import Draw2D
from math import *
import re
import struct
import time

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
        if "name" in args:
            self.name = args["name"]
        if "scale" in args:
            self.scale=args["scale"]
        if "size" in args:
            self.size=args["size"]
        if "place" in args:
            self.place=args["place"]
        if "azimuth" in args:
            self.azimuth=args["azimuth"]
        if "altitude" in args:
            self.altitude=args["altitude"]
        if "roll" in args:
            self.roll=args["roll"]

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
        obj = Line(self, *kwargs, **args)
        self.objects[name]=obj
        return obj

    def point(self, *kwargs, **args):
        self.object_count += 1
        name = "point#"+str(self.object_count)
        obj = Point(self, *kwargs, **args)
        self.objects[name]=obj
        return obj

    def polygon(self, *kwargs, **args):
        self.object_count += 1
        name = "poly#"+str(self.object_count)
        obj = Polygon(self, *kwargs, **args)
        self.objects[name]=obj
        return obj

    def coordinateSystem(self, *kwargs, **args):
        self.object_count += 1
        name = "cs#"+str(self.object_count)
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
            name = "line#"+str(self.object_count)
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
        anonymousObject.scale = (maxX, maxY, maxZ)
        polys = stl.getPolygons()
        norms = stl.getNormalvectors()
        for i in range(0, len(polys)):
            poly = polys[i]
            norm = norms[i]
            anonymousObject.polygon( *poly, normalvector=norm )
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

        if "r" in args:
            if type=="absolute":
                self.debug("animation() got absolute and spherical information! Only have x,y,z set OR r,azimuth,altitude!")
                exit(0)
            type="spherical"
            self.radius = eval(args["radius"], args)
        if "azimuth" in args:
            if type=="absolute":
                self.debug("animation() got absolute and spherical information! Only have x,y,z set OR r,azimuth,altitude!")
                exit(0)
            type="spherical"
            self.azimuth = eval(args["azimuth"], args)
        if "altitude" in args:
            if type=="absolute":
                self.debug("animation() got absolute and spherical information! Only have x,y,z set OR r,azimuth,altitude!")
                exit(0)
            type="spherical"
            self.altitude = eval(args["altitude"], args)

        if type=="unknown":
            self.debug("animation() got no spherical or absolute information!")
            exit(0)
            return False

        if type=="spherical":
            self.setPlaceSpherical(self.azimuth, self.altitude, self.radius)
        else:
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
        self.useFastHiddenPolyCheck = False      # this is lossy!
        self.polyOnlyGrid           = False      # show only lines of polynoms
        self.polyOnlyPoint          = False      # show only point clouds
        self.polyGrid               = False
        self.parent    = None
        pass

    def reset(self):
        self.debug("Singulersum.reset(), delete all objects")
        self.cameras={}         # delete all cameras
        self.lights={}         # delete all lights
        super().reset()

    # camera and light

    def camera(self, *kwargs, **args):
        assert("name" in args)
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

class Camera(Miniverse):

    # TODO: make x,y,z: place=(x,y,z) and name the parameter "place"
    # TODO: make x0, y0, z0: look=(x0,y0,z0)

    def __init__(self, parent, x=2.0, y=1.0, z=0.0, x0=0.0, y0=0.0, z0=0.0, fov=140.0, width=2048, height=2048, **args):
        super().__init__(parent, **args)
        assert(self.name)             # cameras need names
        self.timeit=parent.timeit     # have the same time as SG
        self.x=x
        self.y=y
        self.z=z
        self.azimuth=None
        self.altitude=None
        self.roll=None
        self.updateFunction=None
        self.r=None
        self.x0=x0
        self.y0=y0
        self.z0=z0
        self.fov=fov
        self.width=width
        self.height=height
        self.draw2d = Draw2D(width, height)
        self.lastRenderSettings = {
            "x"   : self.x,
            "y"   : self.y,
            "z"   : self.z,
            "x0"  : self.x0,
            "y0"  : self.y0,
            "z0"  : self.z0,
            "fov" : self.fov,
            "width" : self.width,
            "height": self.height,
        }
        self.debug("initialize camera:")
        self.debug("  pos/lookat", x, y, z, x0, y0, z0)
        self.debug("  fov", fov)
        self.debug("  width/height", width, height)
        if "update" in args:
            self.setUpdate(args["update"])
        self.setupCamera()

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
        (x, y, z) = self.rotate(C, azimuth, altitude)
        # TODO: z becomes negative (eg. at azimuth 120°! But should stay positive!)
        self.x = x
        self.y = y
        self.z = z
        print("placeSpherical: ", self.x, self.y, self.z)
        assert(self.x**2+self.y**2+self.z**2-r**2<1e-06)
        azimuth = atan2(self.y, self.x)
        if azimuth<0.0:
            azimuth = 2*pi+azimuth
        Aazimuth = azimuth/pi*180
        Aradius = sqrt(self.x**2+self.y**2+self.z**2)
        Aaltitude = atan2(self.z, sqrt(self.x**2+self.y**2))/pi*180
        print("azimuth:", azimuth, Aazimuth)
        print("altitude:", altitude, Aaltitude)
        print("radius:", r, Aradius)
        if x0!=x or y0!=y or z0!=z:
            return True
        else:
            return False

    def setUpdate(self, func):
        self.updateFunction = func

    def update(self):
        if self.updateFunction is not None:
            self.debug("updateFunction for "+str(self)+" not None. Calling the function.")
            return self.updateFunction(self)
        return False

    def project_p2d(self, p):
        # rotate the point according to the azimuth and altitude of camera
        P_prime = p
        # rotate the point, so that X-axis is directly looking into the camera
        # as of 2021-03-21 I changed the math concept so that the whole universe is
        # translated/rotated to a fix state where X-axis is directly looking into the
        # camera, Y-axis is streight to the right and Z-axis is going up.
        P_prime = self.rotate(P_prime, -1*self.azimuth, -1*self.altitude, self.roll)

        # displace so that the camera is at (0,0,0)
        P_prime = self.vec_add(P_prime, self.TL)

        (x, y, z, distance) = self.project_p( P_prime )
        # NOTE: the distance is from P to P_prime! So shorter distance is CLOSER to
        #       the plane and MORE FAR away from Camera!

        # result
        x_prime = int(self.factor_x * y * self.width/2 + self.width/2)
        y_prime = int( -1* self.factor_y * z * self.height/2 + self.height/2)

        return (x_prime, y_prime, distance)

    # each time the camera data is changed (shifted in space, other focal point, other
    # FOV setting etc.) setupCamera() MUST be called to update the new projection plane e.
    def setupCamera(self):
        self.debug("setupCamera() start")
        timeit = self.timeit()

        if self.lastRenderSettings["width"]!=self.width or self.lastRenderSettings["height"]!=self.height:
            print("setupCamera() detected change in width/height. Draw2D reinitialize.")
            self.draw2d = Draw2D(self.width, self.height)

        # save lastRenderSettings to detect camera changes and if camera needs a new
        # setupCamera() or even a new Draw2D init because the resolution changed.
        self.lastRenderSettings = {
            "x"   : self.x,
            "y"   : self.y,
            "z"   : self.z,
            "x0"  : self.x0,
            "y0"  : self.y0,
            "z0"  : self.z0,
            "fov" : self.fov,
            "width" : self.width,
            "height": self.height,
        }

        self.C = (self.x,self.y,self.z)    # camera position (eg. (2.0, 1.0, 0.0) )
        self.debug("Camera position C:              ", self.vec_show(self.C))
        self.F = (self.x0,self.y0,self.z0) # camera focus (eg. center (0.0, 0.0, 0.0))
        self.debug("Camera focus F:                 ", self.vec_show(self.F))
        self.V = self.vec_sub(self.F,self.C) # view vector, C->F (eg. (-2.0, -1.0, 0.0) )
        self.debug("Camera View Vector V:           ", self.vec_show(self.V))
        self.lV = self.vec_len(self.V)     # view vector V length, sqrt(2**2+1**2+0**2)
        self.debug("View Vector length lV:          ", "{:4f}".format(self.lV))

        # from camera's x,y,z coordinates, derive azimuth, altitude with regards to
        # the "fixed camera position": (cam_distance, 0, 0), where cam_distance is
        # sqrt(V_x**2+V_y**2+V_z**2)
        azimuth = atan2(-1*self.V[1], -1*self.V[0])
        if azimuth<0.0:
            azimuth = 2*pi+azimuth
        self.azimuth = azimuth/pi*180
        self.radius  = self.lV
        self.altitude = atan2(-1*self.V[2], sqrt(self.V[0]**2+self.V[1]**2))/pi*180
        self.debug("Camera azimuth                  ", "{:4f}".format(self.azimuth))
        self.debug("Camera altitude:                ", "{:4f}".format(self.altitude))
        self.debug("Camera 'radius'=length(V):      ", "{:4f}".format(self.radius))

        self.debug("after rotation:")

        # now we back transform View Vector and Camera position
        self.V_prime = self.rotate(self.V, -1*self.azimuth, -1*self.altitude, self.roll)
        self.debug("Camera View Vector V_prime:     ", self.vec_show(self.V_prime))

        self.C_prime = self.rotate(self.C, -1*self.azimuth, -1*self.altitude, self.roll)
        self.debug("Camera position C_prime:        ", self.vec_show(self.C_prime))

        # now C_prime must become (0,0,0), so we store the self.TL to be the minus of it.
        self.TL=self.vec_mul_scalar(self.C_prime, -1) # that's how we need to translate
        self.debug("Translation vector:             ", self.vec_show(self.TL))

        # T is the tangential point of view vector to universe sphere
        # since our universe sphere has a radius of 1 and the reference point is (0,0,0),
        # the Tangential point (T) is equal to the normalized View Vector V_prime
        T = self.vec_mul_scalar(self.V_prime, 1/self.lV)
        self.debug("Tangential point T:             ", self.vec_show(T))
        self.debug("   T=V/lV, since universe sphere has r=1.0 and (0,0,0) is center.")
        # e is the "view plane" where each point is projected on
        self.e = self.plane(self.V_prime, T)
        self.debug("View plane e:                   ", self.plane_show(self.e))
        # camera view line: cl   (the "camera line" cl)
        # since the mapper_3d
        cl = self.vec_line(self.C_prime, self.V_prime)
        self.debug("Camera line cl:                 ", self.line_show(cl))
        # O', where we directly look at (camera position + lambda*view_vector)->e
        self.O_prime = self.line_plane_intersection(cl, self.e)
        self.debug("line plane intersection(cl, e): ", self.vec_show(self.O_prime))
        self.debug("   NOTE: vector now has 4 dimensions, where the 4th is the distance!")
        self.debug("   this is O's projection on e, also called O_prime.")

        # now we can redo the plane e, but with O_prime as the "Stützvektor", since we
        # need this guy for later calculus of relative distances to O_prime
        self.e = self.plane(self.V_prime, self.O_prime)
        self.debug("new view plane e with O_prime:  ", self.plane_show(self.e))

        self.O_prime = self.line_plane_intersection(cl, self.e)
        self.debug("new O_prime:                    ", self.vec_show(self.O_prime))

        # let's find the max visible range
        # 2021-03-21 ph NOTE that the smallest defines the FOV! So if the picture has
        #               aspect ratio of 4:3, then the Y-axis (in 2D) defines the FOV
        #               and the X-axis (2D) actually shows a broader FOV than set.
        # TODO: still the sphere is kind of distorted!
        Uy3d = (0,1,0)
        Uy3d_prime = self.project_p(Uy3d)
        Uz3d = (0,0,1)
        Uz3d_prime = self.project_p(Uz3d)
        fov=self.fov
        Py=self.vec_add(self.O_prime, Uy3d_prime)
        OPy=self.vec_len(self.vec_sub(Py, self.O_prime))
        tan_theta=tan((fov/2)/180*pi)
        tan_theta_prime=OPy/self.vec_len(self.vec_sub(self.O_prime, self.C_prime))
        OMy = self.vec_len(self.vec_sub(self.O_prime, self.C_prime))*(tan_theta+tan_theta_prime)-self.vec_len(self.vec_sub(Py, self.O_prime))
        self.factor_x = 1/(OMy/OPy)
        # for y:
        Pz=self.vec_add(self.O_prime, Uz3d_prime)
        OPz=self.vec_len(self.vec_sub(Pz, self.O_prime))
        tan_theta=tan((fov/2)/180*pi)
        tan_theta_prime=OPz/self.vec_len(self.vec_sub(self.O_prime, self.C_prime))
        OMz = self.vec_len(self.vec_sub(self.O_prime, self.C_prime))*(tan_theta+tan_theta_prime)-self.vec_len(self.vec_sub(Pz, self.O_prime))
        self.factor_y = 1/(OMz/OPz)

        # 2021-03-21 ph NOTE that the smallest defines the FOV! So if the picture has
        #               aspect ratio of 4:3, then the Y-axis (in 2D) defines the FOV
        #               and the X-axis (2D) actually shows a broader FOV than set.
        if self.factor_x<self.factor_y:
            self.factor_y = self.factor_x
        else:
            self.factor_x = self.factor_y

        self.debug("factor_x: ", self.factor_x)
        self.debug("factor_y: ", self.factor_y)

        self.debug("setupCamera completed", timeit=timeit)

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
        if "place" in context:
            if context["place"][0]!=0.0:
                return True
            if context["place"][1]!=0.0:
                return True
            if context["place"][2]!=0.0:
                return True
        if "size" in context:
            if context["size"]!=1.0:
                return True
        return False

    def applyContext(self, context, *kwargs, **args):
        list = []
        size = context["size"]
        for p in kwargs:
            if size!=1.0:
                p = self.stretch(p, size, size, size)
            p = self.rotate(p, context["azimuth"], context["altitude"], context["roll"])
            # displace so that the camera is at (0,0,0)
            place = context["place"]
            p = self.vec_add(p, (place[0], place[1], place[2]))
            list.append(p)
        return list

    def object_iterator(self, versum):
        # we first calculate all polygons and process them later using different
        # algorithms
        # polys = [ {points=>[], distance=>1.2, normalvector=>()}, {...} ]
        # basic object lists:
        self.debug("object_iterator for "+str(versum))
        polys = []
        lines = []  # [ (p1, p2, color), ... ]
        points= []  # [ (p1, color), ...]
        context = {
            "place" :   versum.place,
            "size" :    versum.size,    # size gets added???
            "azimuth" : versum.azimuth,
            "altitude": versum.altitude,
            "roll":     versum.roll,
        }
        isSpecialContext = self.isSpecialContext(context)
        for name, obj in versum.objects.items():
            # use K-means and implement multi core processing?
            if obj.visibility is False:
                continue
            # BasicObjects
            if isinstance(obj, Line):
                p1 = (obj.x1, obj.y1, obj.z1)
                p2 = (obj.x2, obj.y2, obj.z2)
                if isSpecialContext:
                    (p1, p2) = self.applyContext(context, p1, p2)
                lines.append( [p1, p2, obj.color, obj.thickness] )
            elif isinstance(obj, Point):
                p = (obj.x, obj.y, obj.z)
                if isSpecialContext:
                    p = self.applyContext(context, p)[0]
                points.append( [p, obj.color] )
            elif isinstance(obj, Polygon):
                poly = []
                normalvector = None
                colorize = 0
                for i in range(0, len(obj.points)):
                    p = obj.points[i]
                    if isSpecialContext:
                        p = self.applyContext(context, p)[0]
                    poly.append( p )
                # TODO: normalvector must be "camera"(!) rotated as well!
                normalvector = obj.normalvector
                if isSpecialContext:
                    normalvector = self.applyContext(context, normalvector)[0]
                if normalvector[0]==0 and normalvector[1]==0 and normalvector[2]==0:
                    normalvector=(1e-06, 0.0, 0.0)
                # this is wrong. self.V should be self.V_prime?
                angle = acos( self.dot_product(self.V, normalvector) / (self.vec_len(self.V)*self.vec_len(normalvector) ) )
                if angle>90:
                    # from back
                    colorize = -1
                else:
                    colorize = abs(pi/2-angle)/(pi/2)
                polys.append( { "points":poly, "normalvector":normalvector, "colorize":colorize, "color":obj.color, "name":obj.name } )
            elif isinstance(obj, CoordinateSystem):
                # ignore it! It added Lines to the parent context
                pass
            elif issubclass(type(obj), Object):
                place = context["place"]
                nplace = (place[0]+obj.place[0], place[1]+obj.place[1], place[2]+obj.place[2])
                (npoints, nlines, npolys) = self.object_iterator(obj)
                for p in npoints:
                    (pt, color) = p
                    if isSpecialContext:
                        pt = self.applyContext(context, pt)[0]
                    points.append( [pt, color] )
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
                    normalvector = p["normalvector"]
                    if isSpecialContext:
                        normalvector = self.applyContext(context, normalvector)[0]
                    colorize = p["colorize"]
                    npoints = []
                    for pt in ppoints:
                        if isSpecialContext:
                            pt = self.applyContext(context, pt)[0]
                        npoints.append(pt)
                    poly = { "points":npoints, "normalvector":normalvector, "colorize":colorize, "color":p["color"], "name":p["name"] }
                    polys.append( poly )
                pass
            else:
                print("unknown object type", type(obj))
                exit(0)
        return (points, lines, polys)

    def image(self):
        time = self.parent.time

        self.debug("cam.image() start")
        timeit = self.timeit()

        for name in ("x", "y", "z", "x0", "y0", "z0", "fov", "width", "height"):
            if self.lastRenderSettings[name]!=getattr(self, name):
                print("image() detected change in camera settings. Call setupCamera()")
                self.setupCamera()

        self.draw2d.clear()
        scale = self.parent.scale

        poly_total  = 0
        poly_hidden = 0
        poly_drawn  = 0

        self.debug("1st step: iterating over ALL objects (polygons, lines, points, ...)")
        iteration_timing = self.timeit()

        context = {
            "place" :   self.parent.place,
            "azimuth" : self.parent.azimuth,
            "altitude": self.parent.altitude,
            "roll":     self.parent.roll,
            "size":     self.parent.size,
        }

        (points, lines, polys) = self.object_iterator(self.parent)
        poly_total = len(polys)

        self.debug("iteration is complete.", timeit=iteration_timing)

        # calculate projections of all points, lines, polys
        self.debug("2nd step: calculate projected points, lines, polys")
        step2timeit = self.timeit()
        for i in range(len(points)):
            points[i][0] = self.project_p2d(points[i][0])
        for i in range(len(lines)):
            lines[i][0] = self.project_p2d(lines[i][0])
            lines[i][1] = self.project_p2d(lines[i][1])
        for poly in polys:
            npoints = []
            distance = 0.0
            for p in poly["points"]:
                p = self.project_p2d(p)
                if p[2]>distance:
                    distance=p[2]
                npoints.append(p)
            poly["points"] = npoints
            poly["distance"] = distance
        self.debug("2nd step done", timeit=step2timeit)

        self.debug("sort polygons by distance (closest polygon first)")
        timesort = self.timeit()
        sort_distance = lambda obj: obj["distance"]
        polys.sort( key=sort_distance )
        self.debug("sorting complete.", timeit=timesort)
        # this is normally halfing the polygons that need drawing! Since half of the
        # object is on the "far" side and not visible

        self.debug("conf: polyOnlyGrid", self.parent.polyOnlyGrid)
        self.debug("conf: polyOnlyPoint", self.parent.polyOnlyPoint)
        self.debug("conf: zBuffering", self.parent.zBuffering)
        self.debug("conf: polyGrid", self.parent.polyGrid)
        self.debug("conf: useFastHiddenPolyCheck", self.parent.useFastHiddenPolyCheck)

        self.debug("3nd step - drawing")
        poly_timing = self.timeit()
        for poly in polys:
            # check z-Buffer of edge points, are they taken?
            # TODO: this is not enough! Can we do better?
            # this fast (and lossy) check can be deactivated by
            # sg.useFastHiddenPolyCheck=False
            if "name" in poly and poly["name"] is not None:
                self.debug("drawing polygon "+str(poly["name"]))
            hidden=True
            for p in poly["points"]:
                if self.draw2d.zIndex(p[0], p[1])>poly["distance"]:
                    # ok that's doing a superb job! - Reducing polys_drawn to half!
                    # how ever the check fails if all points are hidden, but part of the
                    # poly would actually be visible (just edges are hidden)
                    hidden=False
            if self.parent.useFastHiddenPolyCheck is False:
                hidden=False
            if hidden is False:
                color = self.draw2d.getColor(poly["color"])
                if poly["colorize"]>0:
                    color = (int(poly["colorize"]*color[0]), int(poly["colorize"]*color[1]), int(poly["colorize"]*color[2]))
                else:
                    color = (0,255,0)
                poly_drawn+=1
                if self.parent.zBuffering is False:
                    poly["distance"]=None
                fill = color
                stroke = color
                if self.parent.polyOnlyGrid is True:
                    fill = None
                if self.parent.polyGrid is False and self.parent.polyOnlyGrid is False:
                    stroke = None
                if self.parent.polyOnlyPoint is False:
                    self.draw2d.polygon(*poly["points"], stroke=stroke, fill=fill, zIndex=poly["distance"])
                else:
                    for p in poly["points"]:
                        self.draw2d.point(p[0], p[1], color="white")
            else:
                poly_hidden+=1
        self.debug("polygons drawing complete.", timeit=poly_timing)

        others_count=0
        for line in lines:
            others_count+=1
            self.draw2d.line( line[0][0], line[0][1], line[1][0], line[1][1], color=line[2], thickness=line[3] )

        for point in points:
            others_count+=1
            self.draw2d.point( point[0][0], point[0][1], color=point[1] )

        self.debug("lines/points drawing complete.")

        self.debug("polygons total (calculated):", poly_total)
        self.debug("polygons hidden (not drawn):", poly_hidden, " [see sg.useFastHiddenPolyCheck]")
        self.debug("polygons drawn:             ", poly_drawn)
        self.debug("lines, points drawn:        ", others_count)

        # draw the O_prime cross
        if self.parent.showCenterOfView is True:
            self.draw2d.line( self.width/2, self.height/2-25, self.width/2, self.height/2+25, color="white" )
            self.draw2d.line( self.width/2-25, self.height/2, self.width/2+25, self.height/2, color="white" )

        image = self.draw2d.image()

        self.debug("cam.image() completed.", timeit=timeit)
        diff = timeit.diff()
        self.parent.fps = 1/diff

        return image

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

# some basic shades

class Line(BasicObject):

    def __init__(self, parent, p1, p2, *kwargs, **args):
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
        self.x1=p1[0]/scale[0]
        self.y1=p1[1]/scale[1]
        self.z1=p1[2]/scale[2]
        self.x2=p2[0]/scale[0]
        self.y2=p2[1]/scale[1]
        self.z2=p2[2]/scale[2]

class Point(BasicObject):

    def __init__(self, parent, p, *kwargs, **args):
        super().__init__(parent)
        self.x = p[0]
        self.y = p[1]
        self.z = p[2]
        if "color" in args:
            self.color=args["color"]
        else:
            self.color="white"

class Polygon(BasicObject, VectorMath):

    vec = None

    def __init__(self, sg, *kwargs, normalvector=None, color=(255, 255, 255), **args):
        super().__init__(sg, **args)
        VectorMath.__init__(self)
        self.normalvector = normalvector        # normal vector from the poly
        self.color = color
        scale = sg.scale
        self.points = []
        for point in kwargs:
            self.points.append( (point[0]/scale[0], point[1]/scale[1], point[2]/scale[2] ))
        if normalvector is not None:
            return None # __init__ shall return None, but all ok.
        # calculate the normalvector to this polygon, TODO: inside/outside??
        p0 = self.points[0]
        p1 = self.points[1]
        p2 = self.points[2]
        v  = self.vec_sub(p1,p0)    # p0->p1
        t  = self.vec_sub(p2,p0)    # p0->p2
        # normalvector is the crossproduct of these two
        # TODO: check for coolinearity first! if yes: choose other points if given
        self.normalvector = self.cross_product(v,t)
        self.normallength = self.vec_len(self.normalvector)
        if self.normallength>0.0:
            self.normalvector = self.vec_mul_scalar(self.normalvector, 1/self.normallength)
        else:
            print("points:", p0, p1, p2)
            print("normalvector:", self.normalvector)
            print("normalvector 0!")
            raise ValueError

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
                    ny=(float(i)/amount*2.0-1.0)*self.scale[0]
                    nz=(float(j)/amount*2.0-1.0)*self.scale[1]
                    p = self.eval(0,ny,nz)
                elif self.rel==1:
                    nx=(float(i)/amount*2.0-1.0)*self.scale[0]
                    nz=(float(j)/amount*2.0-1.0)*self.scale[1]
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
                poly2= self.polygon( corps[i][j], corps[i][j+1], corps[i+1][j+1])
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
        for i in range(0,self.amount-1):
            for j in range(0, self.amount-1):
                cnt+=1
                poly = self.polygon( corps[i][j], corps[i+1][j], corps[i+1][j+1])
                poly2= self.polygon( corps[i][j], corps[i+1][j+1], corps[i][j+1])
        self.debug("polygon count for this function: ", cnt)

class Cube(Object):

    def __init__(self, parent, x=0.0, y=0.0, z=0.0, r=1.0, amount=20, *kwargs, **args):
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
        p0 = (x+r, y-r, z-r)
        p1 = (x+r, y+r, z-r)
        p2 = (x+r, y+r, z+r)
        p3 = (x+r, y-r, z+r)
        #back
        p4 = (x-r, y-r, z-r)
        p5 = (x-r, y+r, z-r)
        p6 = (x-r, y+r, z+r)
        p7 = (x-r, y-r, z+r)

        # TODO: color tests to identify z-Fighting problems

        # front
        poly = self.polygon( p0, p1, p2, name="front_w", color="white" )
        self.polygon( p0, p2, p3, name="front_w", color="white" )
        # top
        self.polygon( p0, p4, p5, name="top_r", color="#ff0000" )
        self.polygon( p0, p1, p5, name="top_r", color="#ff0000" )
        # left
        self.polygon( p0, p3, p4, name="left_g", color="#00ff00" )
        self.polygon( p3, p7, p4, name="left_g", color="#00ff00" )
        # right
        self.polygon( p1, p5, p6, name="right_b", color="#0000ff" )
        self.polygon( p1, p6, p2, name="right_b", color="#0000ff"  )
        # bottom
        self.polygon( p3, p6, p7, name="bottom_dark", color="#555555"  )
        self.polygon( p3, p2, p6, name="bottom_dark", color="#555555" )
        # back
        self.polygon( p4, p5, p6, name="back_dark", color="#555555" )
        self.polygon( p4, p7, p6, name="back_dark", color="#555555" )

class Plane(Object):

    def __init__(self, xf, yf, zf, df, *kwargs, **args):
        # define plane as xf*x+yf*y+zf*z+df=0
        pass

class CoordinateSystem(BasicObject):

    # coordinate system injects lines into the PARENT! It's a BasicObject (no Miniverse!)

    def __init__(self, parent, *kwargs, **args):
        super().__init__(parent, *kwargs, **args)
        scale = self.parent.scale
        self.lineX = self.parent.line( (0.0, 0.0, 0.0), (scale[0], 0, 0), color="green", tickness=5 )
        self.lineY = self.parent.line( (0.0, 0.0, 0.0), (0, scale[1], 0), color="blue", thickness=5 )
        self.lineZ = self.parent.line( (0.0, 0.0, 0.0), (0, 0, scale[2]), color="red", thickness=5 )
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
                        self.parent.point( (nx,ny,nz), color="red" )


    def update(self):
        scale = self.parent.scale
        changed = False
        if self.parent.showCoordinateSystem is True:
            # TODO: delete old lines first!
            #sg.line( (0.0, 0.0, 0.0), (scale[0], 0, 0), color="green", tickness=5 )
            #sg.line( (0.0, 0.0, 0.0), (0, scale[1], 0), color="blue", thickness=5 )
            #sg.line( (0.0, 0.0, 0.0), (0, 0, scale[2]), color="red", thickness=5 )
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
