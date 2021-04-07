# 2021-03-14 ph Created
# 2021-03-21 ph line_plane_intersection had a bug. distance is C-P and not C-P_prime
# 2021-03-24 ph line() -> vec_line(), so that line() is Miniverses line()
# 2021-03-26 ph cross_product was wrong, resulting in wrong normalvector computation
# 2021-03-27 ph plane -> plane_normalvec
# 2021-03-28 ph point behind camera reports negative distance.
# 2021-03-29 ph tuple -> list returns, so that items can be accessed/modified directly.

"""
    Singulersum.VectorMath()

    2021-03-14 ph Created by Philipp Hasenfratz

    Singulersum.Camera class highly depend on vector geometry/calculus, linear equation systems (linear algebra), matrix calculations etc. This calculus is partly taken out of the Camera class to make it more readable and is placed in this class (Camera inherits from this class).
"""

from Singulersum.Debug import Debug
from math import *

class VectorMath(Debug):

    def __init__(self):
        self.vec_sub = lambda v1,v2: [v1[0]-v2[0], v1[1]-v2[1], v1[2]-v2[2]]
        self.vec_add = lambda v1,v2: [v1[0]+v2[0], v1[1]+v2[1], v1[2]+v2[2]]
        self.vec_len = lambda vector: sqrt(vector[0]**2+vector[1]**2+vector[2]**2)
        self.vec_mul_scalar = lambda vector, factor: [vector[0]*factor, vector[1]*factor,vector[2]*factor]
        self.dot_product = lambda v1,v2: v1[0]*v2[0]+v1[1]*v2[1]+v1[2]*v2[2]
        self.cross_product = lambda v, t: [ v[1]*t[2]-v[2]*t[1], v[2]*t[0]-v[0]*t[2], v[0]*t[1]-v[1]*t[0] ]
        self.matrix_vector_product_2 = lambda M, v: [M[0][0]*v[0]+M[0][1]*v[1], M[1][0]*v[0]+M[1][1]*v[1]]
        self.matrix_vector_product_3 = lambda M, v: [ M[0][0]*v[0]+M[0][1]*v[1]+M[0][2]*v[2], M[1][0]*v[0]+M[1][1]*v[1]+M[1][2]*v[2], M[2][0]*v[0]+M[2][1]*v[1]+M[2][2]*v[2] ]
        # line(point_vector(list:x,y,z)), direction_vector(list:x,y,z))):
        # DocRef.8
        self.vec_line = lambda point_vec, vector: [point_vec[0], point_vec[1], point_vec[2], vector[0], vector[1], vector[2]]
        self.line_calc = lambda line, lambd: [ line[0]+lambd*line[3], line[1]+lambd[4], line[2]+lambd[5] ]
        # DocRef.13
        self.project_p = lambda point_vec: self.line_plane_intersection(self.vec_line(self.C_prime, self.vec_sub(point_vec, self.C_prime)), self.e)

    def vec_show(self, v):
        str = "["
        for i in range(len(v)):
            str += "{:0.4f}, ".format(v[i])
        str = str[0:-2]+"]"
        return str

    def plane_show(self, plane):
        str = "[{:0.4f}x + {:0.4f}y + {:0.4f}z + {:0.4f} = 0] (ref vector: [{:0.4f}, {:0.4f}, {:0.4f}])".format(*plane)
        return str

    def line_show(self, line):
        str = self.vec_show( (line[0], line[1], line[2]) )
        str += " + lambda * "
        str += self.vec_show( (line[3], line[4], line[5]) )
        return str

    # returns (x',y',z', dist)
    # DocRef.9
    def line_plane_intersection(self, line, plane):
        const = plane[0]*line[0]
        const += plane[1]*line[1]
        const += plane[2]*line[2]
        const += plane[3]   # normally 0
        const *= -1     # at the end we have cnt*lambda+const=0, but lambda=-const we want
        lambd = 0
        lambd += plane[0]*line[3]        # the x component of line (as variable)
        lambd += plane[1]*line[4]
        lambd += plane[2]*line[5]
        lambd = const/lambd
        # distance is vec_len(lambd*line_direction_vec)
        # NOPE, I don't think so! We want to know the distance CP_prime!
        #dist  = sqrt((lambd*line[3])**2 + (lambd*line[4])**2 + (lambd*line[5])**2)
        # this is the correct distance, the direction vector is C_prime->P and hence the
        # length! 2021-03-21 ph finally found that bug.
        dist = sqrt(line[3]**2+line[4]**2+line[5]**2)
        if lambd<0.0:
            # point is BEHIND the camera! Assign negative dist
            dist = -1*dist
        return [ line[0]+lambd*line[3], line[1]+lambd*line[4], line[2]+lambd*line[5], dist ]

    # DocRef.7
    def plane_normalvec(self, normal_vector, point_vector):
        # plane_normalvec(normal_vector(list:(x,y,z)), point_on_plane(list:(x,y,z))):
        # return list:(a,b,c,d,Ox,Oy,Oz) so that: ax+by+cz=d, and O as primary vector
        # (Stützvektor)
        x = normal_vector[0]
        y = normal_vector[1]
        z = normal_vector[2]
        const = normal_vector[0]*-1*point_vector[0]
        const += normal_vector[1]*-1*point_vector[1]
        const += normal_vector[2]*-1*point_vector[2]
        return [ x,y,z,const, point_vector[0], point_vector[1], point_vector[2] ]

    def poly_normalvector(self, p0, p1, p2):
        # calculate the normalvector to this polygon
        v  = self.vec_sub(p1,p0)    # p0->p1 (p01)
        t  = self.vec_sub(p2,p0)    # p0->p2 (p02)
        # normalvector is the crossproduct of these two
        normalvector = self.cross_product(v,t)
        normallength = self.vec_len(normalvector)
        if normallength>0.0:
            normalvector = self.vec_mul_scalar(normalvector, 1/normallength)
        else:
            # collinearity fix
            self.debug("poly_normalvector(): points", p0, p1, p2)
            self.debug("poly_normalvector(): normalvector:", normalvector)
            self.debug("poly_normalvector(): normalvector 0!")
            self.debug("poly_normalvector(): points might be collinear, faking normal vector")
            p1 = [ p1[0]+1e-05, p1[1]+1e-05, p1[2]+1e-05]
            p2 = [ p2[0]+1e-05, p1[2]+1e-05, p1[2]+1e-05]
            return self.poly_normalvector(p0, p1, p2)
        return normalvector

    # rotate a 3D vector p by azimuth (0-360°), altitude (-90 to +90°), roll (-180° to +180°)
    # DocRef.5
    def rotate(self, p, azimuth=0.0, altitude=0.0, roll=0.0):
        P_prime = p
        if azimuth is None:
            azimuth = 0.0
        if altitude is None:
            altitude = 0.0
        if roll is None:
            roll = 0.0
        azimuth = azimuth/180*pi
        altitude = altitude/180*pi
        roll = roll/180*pi
        M = (
            (
            cos(azimuth)*cos(altitude),
            cos(azimuth)*sin(altitude)*sin(roll)-sin(azimuth)*cos(roll), cos(azimuth)*sin(altitude)*cos(roll)+sin(azimuth)*sin(roll)
            ),
            (
            sin(azimuth)*cos(altitude), sin(azimuth)*sin(altitude)*sin(roll)+cos(azimuth)*cos(roll), sin(azimuth)*sin(altitude)*cos(roll)-cos(azimuth)*sin(roll)
            ),
            (
            -1*sin(altitude),
            cos(altitude)*sin(roll),
            cos(altitude)*cos(roll)
            )
        )
        P_prime = self.matrix_vector_product_3(M, P_prime)
        return P_prime

    # not used anymore
    def rotateold(self, p, azimuth=None, altitude=None, roll=None):
        P_prime = p
        # rotate around Z-Axis (azimuth), yaw
        if azimuth is not None:
            azimuth = azimuth/180*pi
            M = (
                (cos(azimuth), -1*sin(azimuth), 0),
                (sin(azimuth), cos(azimuth), 0),
                (0, 0, 1),
            )
            P_prime = self.matrix_vector_product_3(M, P_prime)

        if altitude is not None:
            # rotate around Y-axis (altitude), pitch
            altitude = altitude/180*pi
            M = (
                (cos(altitude), 0, -1*sin(altitude)),
                (0, 1, 0),
                (sin(altitude), 0, cos(altitude)),
            )

            P_prime = self.matrix_vector_product_3(M, P_prime)

        if roll is not None:
            # rotate around X-axis, roll
            roll /= 180*pi
            if roll is None:
                roll=0
            M = (
                (1, 0, 0),
                (0, cos(roll), -1*sin(roll)),
                (0, sin(roll), cos(roll)),
            )
            P_prime = self.matrix_vector_product_3(M, P_prime)

        return P_prime

    def stretch(self, p, factor_x, factor_y, factor_z):
        M = (
            ( factor_x, 0, 0 ),
            ( 0, factor_y, 0 ),
            ( 0, 0, factor_z ),
        )
        P_prime = p
        P_prime = self.matrix_vector_product_3(M, P_prime)
        return P_prime

    # translate a 3D point p by "translate" (also a 3D point)
    def translate(self, p, translate):
        P_prime = p
        for i in range(len(P_prime)):
            P_prime[i]+=translate[i]
        return P_prime

    def linsys_solve(self, solve):
        AM = [ [ 0 for x in range(len(solve[0])-1) ] for y in range(len(solve)) ]
        BM = [ ]
        for x in range(0, len(solve[0])-1):
            for y in range(0, len(solve)):
                AM[y][x]=solve[y][x]
        for y in range(0, len(solve)):
            BM.append( [ solve[y][-1] ] )
        n=len(AM)
        print(AM, BM)
        # stolen from https://integratedmlai.com/system-of-equations-solution/
        indices = list(range(n)) # allow flexible row referencing ***
        for fd in range(n): # fd stands for focus diagonal
            fd_scale = 1.0 / AM[fd][fd]
            # FIRST: scale fd row with fd inverse.
            for j in range(n): # Use j to indicate column looping.
                AM[fd][j] *= fd_scale
            BM[fd][0] *= fd_scale

            # SECOND: operate on all rows except fd row.
            for i in indices[0:fd] + indices[fd+1:]: # skip fd row.
                cr_scale = AM[i][fd] # cr stands for current row
                for j in range(n): # cr - crScaler * fdRow.
                    AM[i][j] = AM[i][j] - cr_scale * AM[fd][j]
                BM[i][0] = BM[i][0] - cr_scale * BM[fd][0]

    def matrix_get(self, Uxref, Uyref):
        e = Uxref[0]
        f = Uxref[1]
        g = Uyref[0]
        h = Uyref[1]
        if f==0.0:
            f=1e-07 # anti div-0 err
        if g*f-e*h==0.0:
            q=1e-07 # anti div 0 err
        else:
            q=g*f-e*h
        a=-h/q
        b=(1-a*e)/f
        c=f/q
        d=0-c*e/f
        return (a,b,c,d)

    # linsys_solve(
    # [
    #  [2, 3, 4]   # 2a+3b+c =  4
    #  [1, 2, 3]   #  a+2b+c =  3
    #  [6, 8, 10]  # 6a+8b+c = 10
    # ]
    # = (-1, 2, 0) =>  (a, b, c)
    # currently brakes for some values. Of course I do not check if a value is not
    # defined...
    def linsys_solve_mine(self, solve):
        if len(solve)==2:
            a = (solve[1][1]-solve[0][1])/(solve[1][0]-solve[0][0])
            b = solve[0][1] - a*solve[0][0]
            return (a,b)
        res = [ [0 for i in range(len(solve)-1)] for j in range(len(solve)-1) ]
        for i in range(0, len(solve)-1):
            # make the first variable equal 0 in sum
            factor_1 = 1/solve[i][0]
            factor_2 = -1/solve[i+1][0]
            assert(solve[i][0]*factor_1 + solve[i+1][0]*factor_2<1e-06)
            for x in range(0, len(res)):
                # first (solve[i][0] and solve[i+1][0]) fall out
                res[i][x] = solve[i][x+1]*factor_1 + solve[i+1][x+1]*factor_2
        res_vec = linsys_solve( res )
        a = solve[0][-1] - res_vec[-1]
        for i in range(0, len(res_vec)-1):
            a -= solve[0][i+1]*res_vec[i]
        print(a, solve[0][0])
        a /= solve[0][0]
        result = (a, *res_vec)
        for i in range(0, len(solve)):
            sum = 0
            for j in range(0, len(solve[i])):
                sum += solve[i][j]*result[j]
            assert(sum==solve[i][-1])
        return (a, *res_vec)
