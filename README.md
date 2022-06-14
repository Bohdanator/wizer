# Wizer

Package providing the ability to visualize algorithms on simple polygons.

Archive `thesis-appendix.zip` contains the version submitted as appendix in
the thesis. It utilizes `scikit-geometry` module for geometrical operations
on polygons, segments and points.

The latest version is built around `sympy.geometry` providing a wider scale of 
operations. Some inconsistencies were found and the tracing decorators were enhanced.

The example algorithm is a triangulation algorithm using the correct sweeping heuristic.
To run it install the `sympy` package and run `python translation.py`. The input is the
