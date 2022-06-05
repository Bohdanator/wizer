import skgeom as sg
import logger as lg
from wizer import visualize

# Triangulation using the incorrect scaling heuristic

# a counterexample for this heuristic
counterexample = [[1,4.5], [9,2], [3,6.5], [4.6,4.1], [1.6,8]]

# acquire input
data = counterexample

# 
Point2V = lg.transform_into_logger(
    sg.Point2, 
    repr_fn=lambda p: ('point', [p.x(), p.y()]), 
    excluded=['x', 'y'],
    enter_on_init=True,
)
Segment2V = lg.transform_into_logger(
    sg.Segment2, 
    repr_fn=lambda s: ('segment', [[s.source().x(), s.source().y()], [s.target().x(), s.target().y()]]), excluded=['source', 'target'],
    enter_on_init=True,
)
def polygon_key(p): return repr(p).replace('\n', '\\n')
Polygon2V = lg.transform_into_logger(
    sg.Polygon, 
    repr_fn=lambda p: ('polygon', [[x, y] for x,y in p.coords]),
    key_fn=polygon_key,
    enter_on_init=True,
)

@lg.logged_function
def compare_lengths(l, r):
    if l.squared_length() < r.squared_length():
        return l
    return r

@lg.logged_function
def compare_points(l, r):
    if l.x() < r.x():
        return l
    elif r.x() < l.x():
        return r
    else:
        if l.y() < r.y():
            return l 
        else:
            return r

@lg.logged_function
def is_inside(point, polygon):
    if polygon.oriented_side(point) == sg.Sign.POSITIVE:
        return point
    return False

@lg.logged_function
def triangulate_polygon(vertices):
    # verices are sorted
    polygon = Polygon2V(vertices)
    if len(vertices) <= 3:
        return []
    b = 0
    pointB = vertices[0]
    for (i, v) in enumerate(vertices):
        if compare_points(v, pointB) == v:
            b = i
            pointB = v
    inside = []
    a = b-1
    c = 0 if b == len(vertices) - 1 else b+1
    triangle = Polygon2V([vertices[a], vertices[b], vertices[c]])
    for (i, v) in enumerate(vertices):
        if i in [a,b,c]:
            continue
        if is_inside(v, triangle):
            inside.append(i)
    lg.log_exit(triangle)
    if len(inside) == 0:
        # we have an ear
        diagonal = Segment2V(vertices[a], vertices[c])
        t = triangulate_polygon(([] if c == 0 else vertices[c:]) + vertices[:(a+1)])
        return t + [diagonal]
    else:
        # find vertex closest to B
        m = None
        n = 0
        for i in inside:
            diagonal = Segment2V(pointB, vertices[i])
            if m is None or compare_lengths(diagonal, m) == diagonal:
                if m is not None: lg.log_exit(m)
                m = diagonal
                n = i
            else:
                lg.log_exit(diagonal)
        x = min(b, n)
        y = max(b, n)
        t1, t2 = triangulate_polygon(vertices[x:y+1]), triangulate_polygon(vertices[y:] + vertices[:(x+1)])
        lg.log_exit(polygon)
        return t1 + t2 + [m]

vertices = list(map(lambda x: Point2V(*x), data))
triangulation = triangulate_polygon(vertices)

visualize(lg.log)
