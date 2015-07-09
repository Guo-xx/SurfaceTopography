#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@file   WindowTest.py

@author Till Junge <till.junge@kit.edu>

@date   07 Jul 2015

@brief  Compare windowed parameter recoups to non-windowed

@section LICENCE

 Copyright (C) 2015 Till Junge

WindowTest.py is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation, either version 3, or (at
your option) any later version.

WindowTest.py is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with GNU Emacs; see the file COPYING. If not, write to the
Free Software Foundation, Inc., 59 Temple Place - Suite 330,
Boston, MA 02111-1307, USA.
"""

import numpy as np
import scipy
import os.path

import matplotlib.pyplot as plt

import PyPyContact.Tools as Tools
import PyPyContact.Surface as Surf

counter = 0
def process(surf_name, surface):
    surfs = dict()
    surfs["Hanning "] = Tools.CharacteriseSurface(surface)
    surfs["Kaiser 8.6"] = Tools.CharacteriseSurface(surface, 'kaiser', {"beta": 8.6})
    surfs["periodic"] = Tools.CharacterisePeriodicSurface(surface)
    fig = plt.figure()
    ax=fig.add_subplot(111)
    ax.set_yscale('log')
    ax.set_xscale('log')
    colors = ('r', 'b', 'g')
    q_max = 2e8
    q_min = 2e7
    lambda_min = 2*np.pi/q_max


    names = ('Hanning ', 'Kaiser 8.6', 'periodic' )
    for color, name in zip(colors, names):
        surf = surfs[name]
        q = surf.q
        C = surf.C
        fit_sl = np.logical_and(q > q_min, q < q_max)
        global counter
        counter += 1
        print('Hello {}'.format(counter))
        H, alpha, res = surf.estimate_hurst_alt(lambda_min=lambda_min, full_output=True, H_bracket=(0, 3))
        print(res)
        ax.loglog(q, C, alpha=.1, color=color)
        mean, err, q_g = surf.grouped_stats(100)

        ax.errorbar(q_g, mean, yerr=err, color=color)
        ax.set_title("{}: H={:.2f}, h_rms={:.2e}".format(surf_name, H, np.sqrt((surface.profile()**2).mean())))
        a, b = np.polyfit(np.log(q), np.log(C), 1)
        ax.plot(q[fit_sl], q[fit_sl]**(-2-2*H)*alpha, label="{}, H={:.2f}".format(name, H), color=color)
    slice_fig = plt.figure()
    slice_ax1_4 = slice_fig.add_subplot(311)
    slice_ax1_2 = slice_fig.add_subplot(312)
    slice_ax3_4 = slice_fig.add_subplot(313)
    slices = ((slice_ax1_4, .25),
              (slice_ax1_2, .50),
              (slice_ax3_4, .75))
    for sl_ax, location in slices:
        q = surfs[names[0]].q
        q_center = location*q[0] + (1-location)*q[-1]
        slice = np.logical_and(q>.95*q_center, q< 1.05*q_center)
        Cs = [np.sqrt(surfs[name].C[slice]) for name in names]
        sl_ax.hist(Cs, bins = 50, normed = True, label = names)
        sl_ax.set_xlabel("|h(q)| for {} at q = {:.2e}".format(surf_name, q_center))

    ax.legend(loc='best')
    sl_ax.legend(loc='best')
    slice_fig.subplots_adjust(hspace=.3)
    ax.grid(True)

def plot_distro(name, surf):
    fig = plt.figure()
    ax=fig.add_subplot(111)
    ax.hist(1e9*surf.ravel(), normed=True, bins = 100, edgecolor='none', alpha=.5)
    loc, scale = scipy.stats.norm.fit(1e9*surf.ravel())
    print(scale)
    x = np.linspace(surf.min(), surf.max(), 100)*1e9
    ax.plot(x, scipy.stats.norm.pdf(x, loc, scale), label=r'Fit, $\sqrt{\sigma} = ' + "{:.2f}$ nm".format(scale))
    ax.set_xlabel("height in [nm])")
    ax.set_ylabel("probability density")
    fig.suptitle(name)
    ax.legend(loc='best')

    fig2 = plt.figure()
    ax = fig2.add_subplot(111, aspect='equal')
    ax.pcolormesh(surf)
    ax.set_xlim(0, 1024)
    ax.set_ylim(0, 1024)

def main():
    siz = 2000e-9
    size = (siz, siz)
    path = os.path.join(os.path.dirname(__file__), "SurfaceExampleUnfiltered.asc")
    surface = Surf.NumpyTxtSurface(path, size=size, factor=1e-9)
    surfs = []
    surfs.append(('Topo1', surface))
    arr, x, residual = Tools.shift_and_tilt(surface.profile(), full_output=True)
    print("ň = {[0]:.15e}, d = {}, residual = {}, mean(arr) = {}".format(
        (float(x[0]), float(x[1]), float(np.sqrt(1-x[0]**2 - x[1]**2))),
        float(x[-1]), residual, arr.mean()))
    arr = Tools.shift_and_tilt_approx(surface.profile())
    surface = Surf.NumpySurface(arr, size=size)
    plot_distro('Topo1_corr', surface.profile())
    surfs.append(('Topo1_corr', surface))

    hurst = .98
    res = surface.resolution
    h_rms = 3.24e-8

    surface = Tools.RandomSurfaceExact(res, size, hurst, h_rms).get_surface()
    surfs.append(('Gauss periodic', surface))

    dsize = (2*siz, 2*siz)
    dres = (res[0], res[0])
    dsurface = Tools.RandomSurfaceGaussian(dres, dsize, hurst, h_rms).get_surface()
    surface = Surf.NumpySurface(dsurface.profile()[:res[0], :res[0]], size = size)
    surfs.append(('Gauss aperiodic', surface))

    for name, surf in surfs[:1]:
        process(name, surf)




if __name__ == "__main__":
    main()
    plt.show()