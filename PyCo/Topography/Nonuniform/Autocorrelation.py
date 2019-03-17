#
# Copyright 2019 Lars Pastewka
# 
# ### MIT license
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

"""
Height-difference autocorrelation functions for nonuniform line scans
"""


import numpy as np

from ..NonuniformLineScan import NonuniformLineScan


def height_height_autocorrelation_1D(line_scan, distances=None):
    r"""
    Compute the one-dimensional height-height autocorrelation function
    (ACF).

    This function treats the nonuniform line scan as a piece-wise function of
    straight lines between the data points. The ACF is computed exactly for
    this piece-wise linear interpolation of the data.

    Parameters
    ----------
    line_scan : :obj:`NonuniformLineScan`
        Container storing the nonuniform line scan.
    r : array_like
        Array containing distances for which to compute the ACF. If no array
        is given, the function will automatically construct an array with
        equally spaced distances. (Default: None)

    Returns
    -------
    distances : array
        Distances. (Units: length)
    A : array
        Autocorrelation function. (Units: length**2)
    """
    size, = line_scan.size
    if distances is None:
        # FIXME!!! We need a better heuristics to decide on the distances
        res, = line_scan.resolution
        distances = np.linspace(0, size, res)
    else:
        distances = np.asarray(distances, dtype=float)
    A = np.zeros_like(distances)

    x, h = line_scan.positions_and_heights()
    s = line_scan.derivative(1)
    # FIXME!!! This is slow
    for i in range(len(x)-1):
        for j in range(len(x)-1):
            # Determine lower and upper distance between segment i, i+1 and
            # segment j, j+1
            x1 = x[i]
            x2 = x[j]
            h1 = h[i]
            h2 = h[j]
            s1 = s[i]
            s2 = s[j]
            b1 = np.maximum(x1, x2 - distances)
            b2 = np.minimum(x[i + 1], x[j + 1] - distances)
            b = (b1 + b2) / 2
            db = (b2 - b1) / 2
            m = db > 0
            if m.sum() > 0:
                b = b[m]
                db = db[m]
                # f1[x_] := (h1 + s1*(x - x1))
                # f2[x_] := (h2 + s2*(x - x2))
                # FullSimplify[Integrate[f1[x]*f2[x + d], {x, b - db, b + db}]]
                #   = 2 * f1[b] * f2[b + d] * db + 2 * s1 * s2 * db ** 3 / 3
                A[m] += 2 * (h1 + s1 * (b - x1)) * (h2 + s2 * (b + distances[m] - x2)) * db + 2 * (
                            s1 * s2 * db ** 3) / 3
    return distances, A

def height_difference_autocorrelation_1D(line_scan, distances=None):
    r"""
    Compute the one-dimensional height-difference autocorrelation function
    (ACF).

    This function treats the nonuniform line scan as a piece-wise function of
    straight lines between the data points. The ACF is computed exactly for
    this piece-wise linear interpolation of the data.

    Parameters
    ----------
    line_scan : :obj:`NonuniformLineScan`
        Container storing the nonuniform line scan.
    r : array_like
        Array containing distances for which to compute the ACF. If no array
        is given, the function will automatically construct an array with
        equally spaced distances. (Default: None)

    Returns
    -------
    distances : array
        Distances. (Units: length)
    A : array
        Autocorrelation function. (Units: length**2)
    """
    size, = line_scan.size
    if distances is None:
        # FIXME!!! We need a better heuristics to decide on the distances
        res, = line_scan.resolution
        distances = np.linspace(0, size, res)
    else:
        distances = np.asarray(distances, dtype=float)
    A = np.zeros_like(distances)

    x, h = line_scan.positions_and_heights()
    s = line_scan.derivative(1)
    # FIXME!!! This is slow
    for i in range(len(x)-1):
        for j in range(len(x)-1):
            # Determine lower and upper distance between segment i, i+1 and
            # segment j, j+1
            x1 = x[i]
            x2 = x[j]
            h1 = h[i]
            h2 = h[j]
            s1 = s[i]
            s2 = s[j]
            b1 = np.maximum(x1, x2 - distances)
            b2 = np.minimum(x[i + 1], x[j + 1] - distances)
            b = (b1 + b2) / 2
            db = (b2 - b1) / 2
            m = db > 0
            if m.sum() > 0:
                b = b[m]
                db = db[m]
                # f1[x_] := (h1 + s1*(x - x1))
                # f2[x_] := (h2 + s2*(x - x2))
                # FullSimplify[Integrate[f1[x]*f2[x + d], {x, b - db, b + db}]]
                #   = 2 * f1[b] * f2[b + d] * db + 2 * s1 * s2 * db ** 3 / 3
                A[m] += (db * (3 * (h2 - s2 * x2 + (b + distances[m]) * s2 - h1 + s1 * x1 - b * s1) ** 2 + (
                            s1 - s2) ** 2 * db ** 2)) / 3
    return distances, A / (size - distances)

### Register analysis functions from this module

NonuniformLineScan.register_function('autocorrelation_1D', height_difference_autocorrelation_1D)
