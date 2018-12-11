#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@file   common.py

@author Lars Pastewka <lars.pastewka@imtek.uni-freiburg.de>

@date   11 Dec 2018

@brief  Bin for small common helper function and classes for uniform
        topographies.

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


def _get_size(surface_xy, size=None):
    """
    Get the physical size of the topography map. Defaults to the shape of
    the array if no other information is present.
    """
    if size is None:
        if isinstance(surface_xy, np.ndarray):
            size = surface_xy.shape
        else:
            try:
                size = surface_xy.size
            except:
                pass
    if size is None:
        size = surface_xy.shape
    return size


def _derivative(profile, size, n, periodic):
    """
    Compute derivative of uniform topography.

    Parameters
    ----------
    profile : array
        Array containing height information.
    size : tuple of floats
        Size of the topography.
    n : int
        Order of derivative.
    periodic : bool
        Determines if topography is periodic.

    Returns
    -------
    derivative : array
        Array with derivative values. If dimension of the topography is
        unity (line scan), then an array of the same shape as the
        topography is returned. Otherwise, the first array index contains
        the direction of the derivative. If the topgography is nonperiodic,
        then all returning array with have shape one less than the input
        arrays.
    """
    grid_spacing = np.array(size)/np.array(profile.shape)
    if periodic:
        if n != 1:
            raise ValueError('Only first derivatives are presently supported for periodic topographies.')
        d = np.array([(np.roll(profile, axis=d) - profile) / grid_spacing[d] ** n
                      for d in range(len(profile.shape))])
    else:
        d = np.array([np.diff(profile, n=n, axis=d) / grid_spacing[d] ** n
                      for d in range(len(profile.shape))])
    if d.shape[0] == 1:
        return d[0]
    else:
        return d