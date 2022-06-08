import tracer.logger as lg
from sympy.geometry import Segment, Polygon, Point
from wizer import visualize, point_repr, segment_repr, polygon_repr


n = int(input())
coords = [list(map(int, input().split())) for _ in range(n)]

PointV = lg.transform_into_logger(Point, repr_fn=point_repr, enter_on_init=True)
SegmentV = lg.transform_into_logger(Segment, repr_fn=segment_repr, enter_on_init=True)
PolygonV = lg.transform_into_logger(Polygon, repr_fn=polygon_repr, enter_on_init=True)

@lg.logged_function
def left_most(points):
    p = points[0]
    for x in points:
        if x.x < p.x:
            p = x
        elif x.x == p.x and x.y < p.y:
            p = x 
    return p

def triangulate(points):
    pass
    # TODO
    