#!/usr/bin/python3

# 2021-03-08 ph Created

"""
    linsys.py

    2021-03-08 ph Created by Philipp Hasenfratz

    Not in use. tried to find my own algorithm to solve linear equation systems.

    some tests to solve linear equation systems.
"""

# a recursive algorithm to solve linear equation systems.
# innovated this algorithm myself.

def linsys_solve_two(x1,y1,x2,y2):
    print("solve linear:")
    print(x1,y1)
    print(x2,y2)
    a = (y2-y1)/(x2-x1)
    b = y1 - a*x1
    print("resolved to: ", a, b)
    return (a,b)

def linsys_solve_three(solve):
    xn=solve[2][0]
    yn=solve[2][1]
    zn=solve[2][2]
    xn1=solve[1][0]-solve[0][0]
    yn1=solve[1][1]
    zn1=solve[1][2]
    (a,b) = linsys_solve_two(xn,zn,xn1,zn1)
    print("result in between: ", a, b)
    c=solve[0][2] - a*solve[0][0] -b*solve[0][1]
    print(a,b,c)
    return (a,b,c)

def linsys_solve( solve ):
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

# the following are snipped from https://github.com/ThomIves/SystemOfEquations/blob/master/SystemOfEquationsStepByStep.ipynb
def print_matrix(Title, M):
    print(Title)
    for row in M:
        print([round(x,3)+0 for x in row])

def print_matrices(Action, Title1, M1, Title2, M2):
    print(Action)
    print(Title1, '\t'*int(len(M1)/2)+"\t"*len(M1), Title2)
    for i in range(len(M1)):
        row1 = ['{0:+7.3f}'.format(x) for x in M1[i]]
        row2 = ['{0:+7.3f}'.format(x) for x in M2[i]]
        print(row1,'\t', row2)

def zeros_matrix(rows, cols):
    A = []
    for i in range(rows):
        A.append([])
        for j in range(cols):
            A[-1].append(0.0)

    return A

def copy_matrix(M):
    rows = len(M)
    cols = len(M[0])

    MC = zeros_matrix(rows, cols)

    for i in range(rows):
        for j in range(cols):
            MC[i][j] = M[i][j]

    return MC

def matrix_multiply(A,B):
    rowsA = len(A)
    colsA = len(A[0])

    rowsB = len(B)
    colsB = len(B[0])

    if colsA != rowsB:
        print('Number of A columns must equal number of B rows.')
        sys.exit()

    C = zeros_matrix(rowsA, colsB)

    for i in range(rowsA):
        for j in range(colsB):
            total = 0
            for ii in range(colsA):
                total += A[i][ii] * B[ii][j]
            C[i][j] = total

    return C

def main():
    # stolen
    A = [[5.,3.,1.],[3.,9.,4.],[1.,3.,5.]]
    B = [[9.0],[16.0],[9.0]]

    AM = copy_matrix(A)
    n = len(A)
    BM = copy_matrix(B)

    print_matrices('Starting Matrices are:', 'AM Matrix', AM,
                   'IM Matrix', BM)
    print()

    indices = list(range(n)) # allow flexible row referencing ***
    for fd in range(n): # fd stands for focus diagonal
        fdScaler = 1.0 / AM[fd][fd]
        # FIRST: scale fd row with fd inverse.
        for j in range(n): # Use j to indicate column looping.
            AM[fd][j] *= fdScaler
        BM[fd][0] *= fdScaler

        # Section to print out current actions:
        string1  = '\nUsing the matrices above, '
        string1 += 'Scale row-{} of AM and BM by '
        string2  = 'diagonal element {} of AM, '
        string2 += 'which is 1/{:+.3f}.\n'
        stringsum = string1 + string2
        val1 = fd+1; val2 = fd+1
        Action = stringsum.format(val1,val2,round(1./fdScaler,3))
        print_matrices(Action, 'AM Matrix', AM, 'BM Matrix', BM)
        print()

        # SECOND: operate on all rows except fd row.
        for i in indices[0:fd] + indices[fd+1:]: # *** skip fd row.
            crScaler = AM[i][fd] # cr stands for "current row".
            for j in range(n): # cr - crScaler*fdRow.
                AM[i][j] = AM[i][j] - crScaler * AM[fd][j]
            BM[i][0] = BM[i][0] - crScaler * BM[fd][0]

            # Section to print out current actions:
            string1  = 'Using matrices above, subtract {:+.3f} *'
            string1 += 'row-{} of AM from row-{} of AM, and '
            string2 = 'subtract {:+.3f} * row-{} of BM '
            string2 += 'from row-{} of BM\n'
            val1 = i+1; val2 = fd+1
            stringsum = string1 + string2
            Action = stringsum.format(crScaler, val2, val1,
                                      crScaler, val2, val1)
            print_matrices(Action, 'AM Matrix', AM,
                                   'BM Matrix', BM)
            print()

    print("Now we multiply the original A matrix times our solution for X, which is BM.")
    print_matrix('If we get our starting X, our solution is proved.\n', matrix_multiply(A,BM))

    # 2nd order
    solve = [
        [2, 3],
        [1, 2]
    ]
    (a,b) = linsys_solve_two( solve[0][0], solve[0][1], solve[1][0], solve[1][1] )
    # a=1
    # b=1
    # check:
    assert a*solve[0][0]+b==solve[0][1]
    assert a*solve[1][0]+b==solve[1][1]
    print("result:", a, b)

    # 3rd order
    solve = [
        [2, 3, 4],
        [1, 2, 3],
        [6, 8, 10],
    ]

    print("debugging")
    (a,b) = linsys_solve_two(-1, -1, 4, 6)
    print("result:", a, b)
    assert a*-1+b==-1
    assert a*4+b==6

    print("linsys_solve_three:")

    (a,b,c) = linsys_solve_three( solve )
    #a=-1
    #b=2
    #c=0
    #assert a*solve[0][0]+b*solve[0][1]+c==solve[0][2]
    #assert a*solve[1][0]+b*solve[1][1]+c==solve[1][2]
    #assert a*solve[2][0]+b*solve[2][1]+c==solve[2][2]

    print("linsys_solve:")
    print("final result", linsys_solve(solve))

    return 0

exit(main())
