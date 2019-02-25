#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@file   VariableBandwidth.py

@author Lars Pastewka <lars.pastewka@imtek.uni-freiburg.de>

@date   09 Jan 2019

@brief  Variable bandwidth analysis for nonuniform topographies

@section LICENCE

Copyright 2015-2018 Till Junge, Lars Pastewka

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import numpy as np

from ..NonuniformLineScan import NonuniformLineScan


def checkerboard_detrend(line_scan, subdivisions, tol=1e-6):
    """
    Perform tilt correction (and substract mean value) in each individual
    rectangle of a checkerboard decomposition of the surface. This is
    identical to subdividing the surface into individual, nonoverlapping
    rectangles and performing individual tilt corrections on them.

    The main application of this function is to carry out a variable
    bandwidth analysis of the surface.

    Parameters
    ----------
    line_scan : :obj:`NonuniformLineScan`
        Container storing the uniform topography map
    subdivisions : int
        Number of subdivisions.
    tol : float
        Tolerance for searching for existing data points at domain boundaries.
        (Default: 1e-6)

    Returns
    -------
    subdivided_line_scans : list of :obj:`NonuniformLineScan`
        List with new, subdivided and detrended line scans.
    """
    if subdivisions == 1:
        return [line_scan]

    x, z = line_scan.positions_and_heights()

    subdivided_line_scans = []
    for i in range(subdivisions):
        # Subdivide interval
        sub_xleft = x[0] + i*(x[-1] - x[0])/subdivisions
        sub_xright = x[0] + (i+1)*(x[-1] - x[0])/subdivisions

        # Search for the data point closes to sub_xleft and sub_xright
        sub_ileft = x.searchsorted(sub_xleft)
        sub_iright = x.searchsorted(sub_xright)

        sub_x = x[sub_ileft:sub_iright]
        sub_y = y[sub_ileft:sub_iright]

        # Put additional data points on the left and right boundaries, if there is none already in the data set at
        # exactly those points

        if sub_ileft != 0 and x[sub_ileft] - sub_xleft > tol:
            # Linear interpolation to boundary point
            sub_yleft = y[sub_ileft - 1] + (sub_xleft - x[sub_ileft - 1]) / (x[sub_ileft] - x[sub_ileft - 1]) * (
                        y[sub_ileft] - y[sub_ileft - 1])
            # Add additional point to data
            sub_x = np.append([sub_xleft], sub_x)
            sub_y = np.append([sub_yleft], sub_y)

        if sub_iright != len(x) and x[sub_iright] - sub_xright > tol:
            # Linear interpolation to boundary point
            sub_yright = y[sub_iright - 1] + (sub_xright - x[sub_iright - 1]) / (x[sub_iright] - x[sub_iright - 1]) * (
                        y[sub_iright] - y[sub_iright - 1])
            # Add additional point to data
            sub_x = np.append(sub_x, [sub_xright])
            sub_y = np.append(sub_y, [sub_yright])

        subdivided_line_scans += [NonuniformLineScan(x, y, info=line_scan.info).detrend()]


def variable_bandwidth(line_scan, resolution_cutoff=4):
    """
    Perform a variable bandwidth analysis by computing the mean
    root-mean-square height within increasingly finer subdivisions of the
    line scan.

    Parameters
    ----------
    line_scan : obj:`NonuniformLineScan`
        Container storing the uniform topography map
    resolution_cutoff : int
        Minimum number of data points to allow for subdivision. The analysis
        will automatically analyze subdivision down to this resolution.

    Returns
    -------
    magnifications : array
        Array containing the magnifications.
    rms_heights : array
        Array containing the rms height corresponding to the respective
        magnification.
    """
    magnification = 1
    min_resolution = line_scan.resolution
    magnifications = []
    rms_heights = []
    while min_resolution >= resolution_cutoff:
        subdivided_line_scans = line_scan.checkerboard_detrend(magnification)
        min_resolution = min([l.resolution for l in subdivided_line_scans])
        magnifications += [magnification]
        rms_heights += [np.mean(l.rms_height() for l in subdivided_line_scans)]
        magnification *= 2
    return np.array(magnifications), np.array(rms_heights)


### Register analysis functions from this module

NonuniformLineScan.register_function('checkerboard_detrend', checkerboard_detrend)
NonuniformLineScan.register_function('variable_bandwidth', variable_bandwidth)