# 2021-03-25 ph Created
# 2021-03-25 ph Camera() class was previously in Singulersum.py. I think it improves
#               readability and developing if it is in it's own file. Code is getting
#               large.
# 2021-03-26 ph reduced z-fighting. previously the z-Index of a polygone was the point
#               that's most far away. This sounds well, but isn't. Especially with a cube
#               where edge points are shared by two sides of the cube, this caused a lot
#               of z-fighting. Better (and still not correct/good) approach is to average
#               the z-Index of all polygon points. The best (but most costly) solution is
#               to calculate the exact z-Index of ALL points within the polygon,
#               resulting in a huge uplift of needed computations.
# 2021-03-27 ph sg.showBackside (was sg.showBackground)
# 2021-03-27 ph plane -> plane_normalvec
# 2021-03-28 ph rotation matrix fix
# 2021-03-28 ph point behind camera fix (2D coordinates negate)
# 2021-03-29 ph showOnlyBoundingBox added
# 2021-03-29 ph objects relatively positioned to their parent (x,y,z is place in parent),
#               first works

"""
    class Singulersum.Camera()

    2021-03-25 ph Created by Philipp Hasenfratz

    Camera implements the whole calculus for generating a 2D image from the 3D object
    space. As of 2021-03-25 the Camera() class is contained in its own file (/Singulersum/Camera.py) for readability.
"""

from math import *

from Singulersum.Singulersum import *
from Singulersum.Draw2D import Draw2D

class Camera(Miniverse):

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
        self.setupCamera()

    def project_p2d(self, p):
        # rotate the point according to the azimuth and altitude of camera
        P_prime = p

        # rotate the point, so that X-axis is directly looking into the camera
        # as of 2021-03-21 I changed the math concept so that the whole universe is
        # translated/rotated to a fix state where X-axis is directly looking into the
        # camera, Y-axis is streight to the right and Z-axis is going up.
        P_prime = self.rotate(P_prime, -180-self.view_azimuth, 0.0)
        P_prime = self.rotate(P_prime, 0.0, -1*self.view_altitude, self.roll)

        # displace so that the camera is at (0,0,0)
        P_prime = self.vec_sub(P_prime, self.C_prime)

        (x, y, z, distance) = self.project_p( P_prime )
        # NOTE: the distance is from P to P_prime! So shorter distance is CLOSER to
        #       the plane and MORE FAR away from Camera!

        # result
        x_prime = self.factor_x * y * self.width/2
        y_prime = -1* self.factor_y * z * self.height/2
        if distance<0.0:
            # point is behind camera, which is negating x and y 2D orientation
            x_prime *= -1
            y_prime *= -1
        x_prime += self.width/2
        y_prime += self.height/2
        x_prime = int(x_prime)
        y_prime = int(y_prime)

        # NOTE: in 2D y-axis is getting more positive DOWN, where in 3D z-axis getting
        #       smaller, that's why -1*self.factor_y*z ...

        # return list, so that items can be accessed and changed
        return [x_prime, y_prime, distance]

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

        # from x,y,z of camera, calculate camera azimuth/altitude
        self.azimuth = atan2(self.y, self.x)
        #if self.azimuth<0.0:
            #self.azimuth = 2*pi+self.azimuth
        self.azimuth = self.azimuth/pi*180
        self.altitude = atan2(self.z, sqrt(self.x**2+self.y**2))/pi*180
        self.radius = sqrt(self.x**2+self.y**2+self.z**2)
        self.debug("Camera azimuth:                 ", "{:4f}".format(self.azimuth))
        self.debug("Camera altitude:                ", "{:4f}".format(self.altitude))
        self.debug("Camera radius:                  ", "{:4f}".format(self.radius))

        # TODO: camera seems to go below "ground" at azimuth 120°! But should actually stay on top of x/y plane.

        self.C = (self.x,self.y,self.z)    # camera position (eg. (2.0, 1.0, 0.0) )
        self.debug("Camera position C:              ", self.vec_show(self.C))
        self.F = (self.x0,self.y0,self.z0) # camera focus (eg. center (0.0, 0.0, 0.0))
        self.debug("Camera focus F:                 ", self.vec_show(self.F))
        self.V = self.vec_sub(self.F,self.C) # view vector, C->F (eg. (-2.0, -1.0, 0.0) )
        self.debug("Camera View Vector V:           ", self.vec_show(self.V))
        self.lV = self.vec_len(self.V)     # view vector V length, sqrt(2**2+1**2+0**2)
        self.debug("View Vector length lV:          ", "{:4f}".format(self.lV))

        # from view vector, derive azimuth, altitude with regards to
        # the "fixed camera position": (cam_distance, 0, 0), where cam_distance is
        # sqrt(V_x**2+V_y**2+V_z**2)
        azimuth = atan2(self.V[1], self.V[0])
        if azimuth<0.0:
            azimuth = 2*pi+azimuth

        # self.azimuth, self.radius and self.altitude are reserved for spherical
        # coordinates of the camera! For calculus we need the azimuth, altitude and
        # radius of the view-vector alone!
        self.view_azimuth = azimuth/pi*180
        self.view_radius  = self.lV
        self.view_altitude = atan2(self.V[2], sqrt(self.V[0]**2+self.V[1]**2))/pi*180
        self.debug("View vector azimuth             ", "{:4f}".format(self.view_azimuth))
        self.debug("View vector altitude:           ", "{:4f}".format(self.view_altitude))
        self.debug("View vector 'radius'=length(V): ", "{:4f}".format(self.view_radius))

        if self.F[0]==0.0 and self.F[1]==0.0 and self.F[2]==0.0:
            corr = 180-self.view_azimuth
            # TODO: +/- 180
            assert(abs(corr+self.azimuth)<=1e-06)
            assert(self.view_altitude==-1*self.altitude)

        self.debug("after rotation:")

        # now we back transform View Vector and Camera position
        self.V_prime = self.V
        self.V_prime = self.rotate(self.V_prime, 180-self.view_azimuth, 0.0)
        self.V_prime = self.rotate(self.V_prime, 0.0, -1*self.view_altitude)
        self.debug("Camera View Vector V_prime:     ", self.vec_show(self.V_prime))
        self.debug("Camera V_prime length:          ", "{:4f}".format(self.vec_len(self.V_prime)))
        # assert V_prime to be (-lV, 0, 0)
        assert(abs(self.V_prime[0]+(self.lV))<0.1)
        assert(abs(self.V_prime[1]-0.0)<0.1)
        assert(abs(self.V_prime[2]-0.0)<0.1)

        self.C_prime = self.C
        self.C_prime = self.rotate(self.C_prime, 180-self.view_azimuth, 0.0)
        self.C_prime = self.rotate(self.C_prime, 0.0, -1*self.view_altitude, self.roll)
        self.debug("Camera position C_prime (calc): ", self.vec_show(self.C_prime))
        assert(abs(self.C_prime[0]-self.lV)<0.1)
        assert(abs(self.C_prime[1]-0.0)<0.1)
        assert(abs(self.C_prime[2]-0.0)<0.1)
        # should now be (lV, 0, 0)

        # T is the tangential point of view vector to universe sphere
        # since our universe sphere has a radius of 1 and the reference point is (0,0,0),
        # the Tangential point (T) is equal to the normalized View Vector V_prime
        T = self.vec_mul_scalar(self.V_prime, 1/self.lV)
        self.debug("Tangential point T:             ", self.vec_show(T))
        self.debug("   T=V/lV, since universe sphere has r=1.0 and (0,0,0) is center.")
        # e is the "view plane" where each point is projected on
        self.e = self.plane_normalvec(self.V_prime, T)
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
        self.e = self.plane_normalvec(self.V_prime, self.O_prime)
        self.debug("new view plane e with O_prime:  ", self.plane_show(self.e))

        self.O_prime = self.line_plane_intersection(cl, self.e)
        self.debug("new O_prime:                    ", self.vec_show(self.O_prime))

        # let's find the max visible range
        # 2021-03-21 ph NOTE that the smallest defines the FOV! So if the picture has
        #               aspect ratio of 4:3, then the Y-axis (in 2D) defines the FOV
        #               and the X-axis (2D) actually shows a broader FOV than set.
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
                    p = obj.points[i]
                    if isSpecialContext:
                        p = self.applyContext(context, p)[0]
                    poly.append( p )
                normalvector = obj.normalvector
                if isSpecialContext:
                    normalvector = self.applyContext(context, normalvector)[0]
                #self.debug("polygon normal vector before cam", normalvector)
                cameraContext = {
                    "x":          0.0,
                    "y":          0.0,
                    "z":          0.0,
                    "size":       1.0,
                    "azimuth":    180-self.view_azimuth,
                    "altitude":   -1*self.view_altitude,
                    "roll":       self.roll,
                }
                normalvector = self.applyContext(cameraContext, normalvector)[0]
                if normalvector[0]==0 and normalvector[1]==0 and normalvector[2]==0:
                    normalvector=(1e-06, 0.0, 0.0)
                #self.debug("polygon", obj.name)
                #self.debug("polygon normal vector", normalvector)
                #self.debug("V_prime", self.V_prime)
                dot_product = self.dot_product(self.V_prime, normalvector)
                #self.debug("dot product", dot_product)
                angle = acos( dot_product / (self.vec_len(self.V_prime)*self.vec_len(normalvector) ) )
                angle = angle/pi*180
                #self.debug("polygon angle between normal vector and view vector", angle)
                if angle>90:
                    colorize = abs(90-angle)/90
                else:
                    if self.parent.showBackside is True:
                        # from back, set colorize=-1, back side of polygons are specially
                        # color coded (like green, so that the user see's that something
                        # is viewed from it's back)
                        colorize = -1
                    else:
                        # show "normal" luminescense as if viewed from front
                        colorize = abs(90-angle)/90
                #self.debug("polygon colorize", colorize)
                polys.append( { "points":poly, "normalvector":normalvector, "colorize":colorize, "fill":obj.fill, "stroke":obj.stroke, "alpha":obj.alpha, "name":obj.name } )
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
                    normalvector = p["normalvector"]
                    if isSpecialContext:
                        # TODO: no stretch, no translate, just rotate
                        normalvector = self.applyContext(context, normalvector)[0]
                    colorize = p["colorize"]
                    npoints = []
                    for pt in ppoints:
                        if isSpecialContext:
                            pt = self.applyContext(context, pt)[0]
                        npoints.append(pt)
                    poly = { "points":npoints, "normalvector":normalvector, "colorize":colorize, "fill":p["fill"], "stroke":p["stroke"], "alpha":p["alpha"], "name":p["name"] }
                    polys.append( poly )
                pass
            else:
                print("object type not known!")
                exit(0)

        return (dots, lines, polys)

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

        self.debug("1st step: iterating over ALL objects (polygons, lines, dots, ...)")
        iteration_timing = self.timeit()

        (dots, lines, polys) = self.object_iterator(self.parent)
        poly_total = len(polys)

        self.debug("iteration is complete.", timeit=iteration_timing)

        # calculate projections of all dots, lines, polys
        self.debug("2nd step: calculate projected dots, lines, polys")
        step2timeit = self.timeit()
        for i in range(len(dots)):
            dots[i][0] = self.project_p2d(dots[i][0])
        for i in range(len(lines)):
            lines[i][0] = self.project_p2d(lines[i][0])
            lines[i][1] = self.project_p2d(lines[i][1])
        for poly in polys:
            npoints = []
            distance = 0.0
            all_distances_negative = True
            # 2021-03-26 ph doing a "poly.distance=max(poly_points.distance)" causes
            # a lot of z-fighting, since for example edge points of a cube are shared
            # by cube sides and therefore they sometimes have equal maximal distances
            # and this causes z-fighting. But also taking the average over all points
            # of a polygone isn't a perfect solution.
            for p in poly["points"]:
                p = self.project_p2d(p)
                distance+=p[2]
                if distance>=0.0:
                    all_distances_negative=False
                npoints.append(p)
            distance /= len(npoints)
            if all_distances_negative is True:
                poly["visibility"]=False
            else:
                poly["visibility"]=True
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
            if poly["visibility"] is False:
                continue
            # check z-Buffer of edge points, are they taken?
            # TODO: this is not enough! Can we do better?
            # this fast (and lossy) check can be deactivated by
            # sg.useFastHiddenPolyCheck=False
            if "name" in poly and poly["name"] is not None:
                self.debug("drawing polygon "+str(poly["name"])+", zIndex: "+str(poly["distance"]))
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
                fill = None
                stroke=None
                if poly["fill"] is not None:
                    fill = self.draw2d.getColor(poly["fill"])
                if poly["stroke"] is not None:
                    stroke = self.draw2d.getColor(poly["stroke"])
                alpha = poly["alpha"]
                if poly["colorize"]>0:
                    if fill is not None:
                        fill = (int(poly["colorize"]*fill[0]), int(poly["colorize"]*fill[1]), int(poly["colorize"]*fill[2]))
                else:
                    fill = (0,255,0)
                poly_drawn+=1
                if self.parent.zBuffering is False:
                    poly["distance"]=None
                if self.parent.polyGrid is True:
                    stroke = (255, 255, 255)
                if self.parent.polyOnlyGrid is True:
                    fill = None
                    stroke = (255, 255, 255)
                if self.parent.polyOnlyPoint is False:
                    if alpha>0:
                        # object is partly transparent, disregard distance!
                        poly["distance"]=None
                    self.draw2d.polygon(*poly["points"], stroke=stroke, fill=fill, alpha=alpha, zIndex=poly["distance"])
                else:
                    # only one point per polygon. Small performance upgrade and good
                    # enough in most cases.
                    self.draw2d.point(poly["points"][0][0], poly["points"][0][1], color=fill, alpha=alpha)
            else:
                poly_hidden+=1
        self.draw2d.polygon_end()
        self.debug("polygons drawing complete.", timeit=poly_timing)

        others_count=0
        for line in lines:
            others_count+=1
            self.draw2d.line( line[0][0], line[0][1], line[1][0], line[1][1], color=line[2], thickness=line[3] )

        for dot in dots:
            others_count+=1
            self.draw2d.point( dot[0][0], dot[0][1], color=dot[1] )

        self.debug("lines/dots drawing complete.")

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
