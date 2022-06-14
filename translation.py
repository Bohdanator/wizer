import tracer.logger as lg
from sympy.geometry import Segment, Polygon, Point
from wizer import visualize

def point_repr(x): return ('point', (float(x.x), float(x.y)))

def segment_repr(x): return ('segment', (point_repr(x.p1)[1], point_repr(x.p2)[1]))

def polygon_repr(p): return ('polygon', list(map(lambda x: point_repr(x)[1], p.vertices)))

PointV = lg.create_logger_from(Point, repr_fn=point_repr, enter_on_init=True)
SegmentV = lg.create_logger_from(Segment, repr_fn=segment_repr, enter_on_init=True)
PolygonV = lg.create_logger_from(Polygon, repr_fn=polygon_repr, enter_on_init=True)

n = int(input())
coords = [tuple(map(float, input().split())) for _ in range(n)]

@lg.logged_function
def left_most(points):
    p = points[0]
    ind = 0
    for i, x in enumerate(points):
        if x.x < p.x:
            p = x
            ind = i
        elif x.x == p.x and x.y < p.y:
            p = x 
            ind = i
    return p

@lg.logged_function
def is_inside(point, polygon):
    if polygon.encloses_point(point):
        return point
    return False

@lg.logged_function
def divide_by_line(polygon, a, b):
    l1, l2 = [], []
    points = polygon.vertices
    i = min(a, b)
    j = max(a, b)
    return (PolygonV(*(points[:(i+1)] + points[j:])), PolygonV(*points[i:(j+1)]))

def triangulate(polygon):
    points = polygon.vertices
    if len(points) < 4:
        return []
    # find left-most vertex
    b = left_most(points)
    lind = points.index(b)
    a, c = points[lind-1], points[lind+1]
    l = SegmentV(a, c)
    t =  PolygonV(a, b, c)
    candidate = None
    distance = 0
    rind = 0
    for i, x in enumerate(points):
        if is_inside(x, t) and (candidate is None or l.distance(x) > distance):
            candidate = x
            distance = l.distance(x)
            rind = i
    lg.log_exit(t)
    if candidate is None:
        inner = PolygonV(*filter(lambda x: x != b, points))
        tr = triangulate(inner)
        lg.log_exit(inner)
        return [l] + tr
    else:
        p1, p2 = divide_by_line(polygon, lind, rind)
        t1, t2 = triangulate(p1), triangulate(p2)
        lg.log_exit(p1, p2, l)
        return [SegmentV(b, candidate)] + t1 + t2

ps = list(map(lambda c: PointV(*c), coords))
poly = PolygonV(*ps)
tr = triangulate(poly)
for seg in tr:
    print(*list(map(float, [seg.p1.x, seg.p1.y, seg.p2.x, seg.p2.y])))

for x in lg.log: print('\n', x)
visualize(lg.log)
    