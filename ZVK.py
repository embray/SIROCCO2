"""
Zariski-Van Kampen method implementation

This file contains functions to compute the fundamental group of
the complement of a curve in the complex affine plane, using 
Zariski-Van Kampen approach. It deppends on the package...

AUTHORS:

- Miguel Marco (2015-09-30): Initial version


EXAMPLES::

    sage: R.<x,y> = QQ[]
    sage: f = y^3 + x^3 -1
    sage: fundamental_group(f)
    Finitely presented group < x0 |  >
"""

#*****************************************************************************
#       Copyright (C) 2015 Miguel Marco <mmarco@unizar.es>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#                  http://www.gnu.org/licenses/
#*****************************************************************************



from sage.groups.braid import BraidGroup
from sage.groups.perm_gps.permgroup_named import SymmetricGroup
from sage.rings.rational_field import QQ
from sage.rings.qqbar import QQbar
from scipy.spatial import Voronoi
from numpy import array, vstack
from sage.rings.all import CC, CIF
from sage.rings.complex_field import ComplexField
from sage.rings.complex_interval_field import ComplexIntervalField



def braid_from_piecewise(strands):
    """
    Compute the braid corresponding to the piecewise linear curves strands.
    strands is a list whose elements are a list of pairs (x,y), where x is
    a real number between 0 and 1, and y is a complex number.
    
    INPUT: 
    
    - A list of lists of tuples (t, c), where t is a number bewteen 0 and 1,
    and c is a complex number.
    
    OUTPUT: 
    
    The braid formed by the piecewise linear strands.
    
    EXAMPLES::
    
        sage: paths = [[(0, I), (0.2, -1 - 0.5*I), (0.8, -1), (1, -I)], [(0, -1), (0.5, -I), (1, 1)], [(0, 1), (0.5, 1 + I), (1, I)]]
        sage: braid_from_piecewise(paths)
        s0*s1

    """
    L = strands
    i = min([L[k][1][0] for k in range(len(L))])
    totalpoints = [[[a[0][1].real(), a[0][1].imag()]] for a in L]
    indices = [1 for a in range(len(L))]
    while i < 1:
        for j in range(len(L)):
            if L[j][indices[j]][0] > i:
                xaux = L[j][indices[j] - 1][1]
                yaux = L[j][indices[j]][1]
                aaux = L[j][indices[j] - 1][0]
                baux = L[j][indices[j]][0]
                interpola = xaux + (yaux - xaux)*(i - aaux)/(baux - aaux)
                totalpoints[j].append([interpola.real(), interpola.imag()])
            else:
                totalpoints[j].append([L[j][indices[j]][1].real(), L[j][indices[j]][1].imag()])
                indices[j] = indices[j] + 1
        i = min([L[k][indices[k]][0] for k in range(len(L))])
    for j in range(len(L)):
         totalpoints[j].append([L[j][-1][1].real(), L[j][-1][1].imag()])
    braid = []
    G = SymmetricGroup(len(totalpoints))
    for i in range(len(totalpoints[0]) - 1):
        l1 = [totalpoints[j][i] for j in range(len(L))]
        l2 = [totalpoints[j][i+1] for j in range(len(L))]
        M = [[l1[s], l2[s]] for s in range(len(l1))]
        M.sort()
        l1 = [a[0] for a in M]
        l2 = [a[1] for a in M]
        cruces = []
        for j in range(len(l2)):
            for k in range(j):
                if l2[j] < l2[k]:
                    t = (l1[j][0] - l1[k][0])/(l2[k][0] - l1[k][0] + l1[j][0] - l2[j][0])
                    s = cmp(l1[k][1]*(1 - t) + t*l2[k][1], l1[j][1]*(1 - t) + t*l2[j][1])
                    cruces.append([t, k, j, -s])
        if len(cruces) > 0:
            cruces.sort()
            P = G(Permutation([]))
            while cruces:
                # we select the crosses in the same t
                crucesl = [c for c in cruces if c[0]==cruces[0][0]]
                crossesl = [(P(c[2]+1) - P(c[1]+1),c[1],c[2],c[3]) for c in crucesl]
                cruces = cruces[len(crucesl):]
                while crossesl:
                    crossesl.sort()
                    c = crossesl.pop(0)
                    braid.append(c[3]*min(map(P, [c[1] + 1, c[2] + 1])))
                    P = G(Permutation([(c[1] + 1, c[2] + 1)]))*P
                    crossesl = [(P(c[2]+1) - P(c[1]+1),c[1],c[2],c[3]) for c in crossesl]
    B = BraidGroup(len(L))
    return B(braid)


def discrim(f):
    """
    Return the points in the discriminant of f. f must be a polynomial in two variables with coefficients in a 
    number field with a fixed embedding in QQbar. The result is the set of values of the first variable for which
    two roots in the second variable coincide.
    
    INPUT: 
    
    - ``f`` -- a polynomial in two variables, with coefficients in a number field with a fixed embedding in QQbar.
    
    OUTPUT: 
    
    A list with the values of the discriminant in QQbar 
    
    EXAMPLES::
    
        sage: R.<x,y> = QQ[]
        sage: f = (y^3 + x^3 -1) * (x+y)
        sage: discrim(f)
        [1,
        -0.500000000000000? - 0.866025403784439?*I,
        -0.500000000000000? + 0.866025403784439?*I]

    """
    x, y = f.variables()
    F = f.base_ring()
    disc = F[x](f.discriminant(y).resultant(f, y)).roots(QQbar, multiplicities = False)
    return disc


def segments(points):
    """
    Return the bounded segments of the Voronoi diagram of the given points.
    
    INPUT: 
    
    - A list of complex points.
    
    OUTPUT: 
    
    A list of pairs (p1, p2) where p1 and p2 are the endpoints of the segments in the Voronoi diagram
    
    EXAMPLES::
    
        sage: R.<x,y> = QQ[]
        sage: f = y^3 + x^3 -1          
        sage: disc = discrim(f)
        sage: segments(disc)
        [(-2.84740787203333 - 2.84740787203333*I,
        -2.14285714285714 + 1.11022302462516e-16*I),
        (-2.84740787203333 + 2.84740787203333*I,
        -2.14285714285714 + 1.11022302462516e-16*I),
        (2.50000000000000 + 2.50000000000000*I,
        1.26513881334184 + 2.19128470333546*I),
        (2.50000000000000 + 2.50000000000000*I,
        2.50000000000000 - 2.50000000000000*I),
        (1.26513881334184 + 2.19128470333546*I, 0.000000000000000),
        (0.000000000000000, 1.26513881334184 - 2.19128470333546*I),
        (2.50000000000000 - 2.50000000000000*I,
        1.26513881334184 - 2.19128470333546*I),
        (-2.84740787203333 + 2.84740787203333*I,
        1.26513881334184 + 2.19128470333546*I),
        (-2.14285714285714 + 1.11022302462516e-16*I, 0.000000000000000),
        (-2.84740787203333 - 2.84740787203333*I,
        1.26513881334184 - 2.19128470333546*I)]

    """
    discpoints = array([(CC(a).real(), CC(a).imag()) for a in points])
    added_points = 3*abs(discpoints).max() + 1.0
    configuration = vstack([discpoints, array([[added_points, 0], [-added_points, 0], [0, added_points],[0, -added_points]])])
    V = Voronoi(configuration)
    res = []
    for rv in V.ridge_vertices:
        if not -1 in rv:
            p1 = CC(list(V.vertices[rv[0]]))
            p2 = CC(list(V.vertices[rv[1]]))
            res.append((p1, p2))
    return res

def followstrand(f, x0, x1, y0a, prec=53):
    """
    Return a piecewise linear aproximation of the homotopy continuation of the root y0a
    from x0 to x1
    
    INPUT:
    
    - ``f`` -- a polynomial in two variables
    - ``x0`` -- a complex value, where the homotopy starts
    - ``x1`` -- a complex value, where the homotopy ends
    - ``y0a`` -- an approximate solution of the polynomial $F(y)=f(x_0,y)$
    - ``prec`` -- the precission to use
        
    OUTPUT:
    
    A list of values (t, ytr, yti) such that:
        - ``t`` is a real number between zero and one
        - $f(t\cdot x_1+(1-t)\cdot x_0, y_{tr} + I\cdot y_{ti})$ is zero (or a good enough aproximation)
        - the piecewise linear path determined by the points has a tubular
          neighborhood  where the actual homotopy continuation path lies, and
          no other root intersects it.
          
    EXAMPLES::
    
        sage: R.<x,y> = QQ[]
        sage: f = x^2 + y^3
        sage: x0 = CC(1, 0)
        sage: x1 = CC(1, 0.5)
        sage: followstrand(f, x0, x1, -1.0) # optional 
        [(0.0, -1.0, 0.0),
        (0.063125, -1.0001106593601545, -0.02104011456212618),
        (0.12230468750000001, -1.0004151100003031, -0.04075695242737829),
        (0.17778564453125, -1.0008762007617709, -0.059227299979315154),
        (0.28181243896484376, -1.0021948141328698, -0.09380038023464156),
        (0.3728358840942383, -1.0038270754728402, -0.123962953123039),
        (0.4524813985824585, -1.005613540368227, -0.15026634875747985),
        (0.5221712237596512, -1.0074443351354077, -0.17320066690539515),
        (0.5831498207896948, -1.009246118007067, -0.1931978258913501),
        (0.636506093190983, -1.0109719597443307, -0.21063630045261386),
        (0.6831928315421101, -1.0125937110987449, -0.2258465242053158),
        (0.7648946236565826, -1.0156754074572174, -0.2523480191006915),
        (0.8261709677424369, -1.0181837235093538, -0.2721208327884435),
        (0.8721282258068277, -1.0201720738092597, -0.2868892148703381),
        (0.9410641129034139, -1.0233210275568283, -0.3089391941950436),
        (1.0, -1.026166099551513, -0.3276894025360433)]
        
    """
    CIF = ComplexIntervalField(prec)
    CC = ComplexField(prec)
    G = f.change_ring(QQbar).change_ring(CIF)
    (x, y) = G.variables()
    g = G.subs({x: (1-x)*CIF(x0) + x*CIF(x1)})
    coefs = []
    deg = g.total_degree()
    for d in range(deg + 1):
        for i in range(d + 1):
            c = CIF(g.coefficient({x: d-i, y: i}))
            cr = c.real()
            ci = c.imag()
            coefs += list(cr.endpoints())
            coefs += list(ci.endpoints())
    yr = CC(y0a).real()
    yi = CC(y0a).imag()
    try:
        if prec == 53:
            points = contpath(deg, coefs, yr, yi)
        else:
            points = contpath_mp(deg, coefs, yr, yi, prec)
        return points
    except:
        return followstrand(f, x0, x1, y0a, 2*prec)

@parallel
def braid_in_segment(f, x0, x1):
    """
    Return the braid formed by the y roots of f when x moves from
    x0 to x1
    
    INPUT:
    
    - ``f`` -- a polynomial in two variables
    - ``x0`` -- a complex number
    - ``x1`` -- a complex number
        
    - OUTPUT:
    
    A braid
    
    EXAMPLES::
    
        sage: R.<x,y> = QQ[]
        sage: f = x^2 + y^3
        sage: x0 = CC(1,0)
        sage: x1 = CC(1, 0.5)
        sage: braid_in_segment(f, x0, x1) # optional -
        s1

    """
    CC = ComplexField(64)
    (x, y) = f.variables()
    I = QQbar.gen()
    X0 = QQ(x0.real()) + I*QQ(x0.imag())
    X1 = QQ(x1.real()) + I*QQ(x1.imag())
    F0 = QQbar[y](f(x=X0))
    y0s = F0.roots(multiplicities=False)
    strands = [followstrand(f, x0, x1, CC(a)) for a in y0s]
    complexstrands = [[(a[0], CC(a[1], a[2])) for a in b] for b in strands]
    centralbraid =  braid_from_piecewise(complexstrands)
    initialstrands = []
    y0aps = [c[0][1] for c in complexstrands]
    used = []
    for y0ap in y0aps:
        distances = [((y0ap - y0).norm(), y0) for y0 in y0s]
        y0 = sorted(distances)[0][1]
        if y0 in used:
            raise ValueError("different roots are too close")
        used.append(y0)
        initialstrands.append([(0, CC(y0)), (1, y0ap)])
    initialbraid = braid_from_piecewise(initialstrands)
    F1 = QQbar[y](f(x=X1))
    y1s = F1.roots(multiplicities=False)
    finalstrands = []
    y1aps = [c[-1][1] for c in complexstrands]
    used = []
    for y1ap in y1aps:
        distances = [((y1ap - y1).norm(), y1) for y1 in y1s]
        y1 = sorted(distances)[0][1]
        if y1 in used:
            raise ValueError("different roots are too close")
        used.append(y1)
        finalstrands.append([(0, y1ap), (1, CC(y1))])
    finallbraid = braid_from_piecewise(finalstrands)
    return initialbraid*centralbraid*finallbraid

def fundamental_group(f, simplified=True, projective = False):
    """
    Return a presentation of the fundamental group of the complement of the algebraic
    set defined by the polynomial f.
    
    INPUT: 
    
    - ``f`` -- a polynomial in two variables, with coefficients in either the rationals
            or a number field with a fixed embedding in QQbar.
    
    - ``simplified`` -- boolean (default: True). If set to True the presentation will be
                    simplified. Otherwise, the returned presentation has as many generators
                    as degree of the polynomial times the points in the base used to create
                    the segments that surround the discriminant. In this case, the generators
                    are granted to be meridians of the curve.
                    
    -- ``projective`` -- boolean (default: False). If set to True, the fundamental group of
                    the complement of the projective completion of the curve will be computed.
                    Otherwise, the fundamental group of the complement in the affine plane will
                    be computed.
             
    OUTPUT: 
    
    A presentation of the fundamental group of the complement of the curve defined by ``f``.
    
    EXAMPLES::
    
        sage: R.<x,y> = QQ[]
        sage: f = x^2 + y^3
        sage: fundamental_group(f) # optional -
        Finitely presented group < x0, x1 | x0^-1*x1*x0*x1*x0^-1*x1^-1 >
        sage: fundamental_group(f, simplified=False) # optional
        Finitely presented group < x0, x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11 | x3*x9^-1, x4*x5*x4^-1*x10^-1, x4*x11^-1, x0*x1*x0^-1*x3^-1, x0*x4^-1, x2*x5^-1, x0*x6^-1, x2*x7^-1, x2^-1*x1*x2*x8^-1, x7*x9^-1, x7^-1*x6*x7*x10^-1, x8*x11^-1 >


    ::
    
        sage: R.<x,y> = QQ[]
        sage: f = y^3 + x^3
        sage: fundamental_group(f) # optional
        Finitely presented group < x0, x1, x2 | x1*x2*x1^-1*x0^-1*x2^-1*x0, x2*x0*x1*x0^-1*x2^-1*x1^-1 >
        
    It is also possible to have coefficients in a number field with a fixed embedding in QQbar::
    
        sage: zeta = QQbar['x']('x^2+x+1').roots(multiplicities = False)[0]
        sage: zeta
        -0.50000000000000000? - 0.866025403784439?*I
        sage: F = NumberField(zeta.minpoly(), 'zeta', embedding = zeta)                
        sage: F.inj
        F.inject_variables  F.injvar            
        sage: F.inject_variables()
        Defining zeta
        sage: R.<x,y> = F[] 
        sage: f = y^3 + x^3 +zeta *x + 1
        sage: fundamental_group(f)
        Finitely presented group < x0 |  >




    """
    (x, y) = f.variables()
    F = f.base_ring()
    g = f.factor().radical().prod()
    d = g.degree(y)
    while not g.coefficient(y**d) in F or (projective and g.total_degree() > d):
        g = g.subs({x: x + y})
        d = g.degree(y)
    disc = discrim(g)
    segs = segments(disc)
    vertices = list(set(flatten(segs)))
    Faux = FreeGroup(d)
    F = FreeGroup(d * len(vertices))
    rels = []
    if projective:
        rels.append(prod(F.gen(i) for i in range(d)))
    braidscomputed = braid_in_segment([(g, seg[0], seg[1]) for seg in segs])
    #braidscomputed = [(((g, seg[0], seg[1]), ), braid_in_segment(g,seg[0], seg[1])) for seg in segs]
    for braidcomputed in braidscomputed:
        seg = (braidcomputed[0][0][1], braidcomputed[0][0][2])
        b = braidcomputed[1]
        i = vertices.index(seg[0])
        j = vertices.index(seg[1])
        for k in range(d):
            el1 = Faux([k + 1]) * b.inverse()
            el2 = k + 1
            w1 = F([sign(a)*d*i + a for a in el1.Tietze()])
            w2 = F([d*j + el2])
            rels.append(w1/w2)
    G = F/rels
    if simplified:
        return G.simplified()
    else:
        return G
