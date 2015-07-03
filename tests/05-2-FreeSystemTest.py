#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@file   05-2-FreeSystemTest.py

@author Till Junge <till.junge@kit.edu>

@date   24 Feb 2015

@brief  tests that the Fast optimization for free (non-periodic) systems is
        consistent with computing the full system

@section LICENCE

 Copyright (C) 2015 Till Junge

PyPyContact is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation, either version 3, or (at
your option) any later version.

PyPyContact is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with GNU Emacs; see the file COPYING. If not, write to the
Free Software Foundation, Inc., 59 Temple Place - Suite 330,
Boston, MA 02111-1307, USA.
"""

try:
    import unittest
    import numpy as np
    from numpy.random import rand, random
    from scipy.optimize import minimize
    import time

    from PyPyContact.System.Systems import SmoothContactSystem
    from PyPyContact.System.SmoothSystemSpecialisations import FastSmoothContactSystem
    from PyPyContact.System import SystemFactory
    import PyPyContact.SolidMechanics as Solid
    import PyPyContact.ContactMechanics as Contact
    import PyPyContact.Surface as Surface
    import PyPyContact.Tools as Tools

    import matplotlib.pyplot as plt
except ImportError as err:
    import sys
    print(err)
    sys.exit(-1)


class FastSystemTest(unittest.TestCase):
    def setUp(self):
        self.size = (15, 15)#(7.5+5*rand(), 7.5+5*rand())
        self.radius = 4
        base_res = 32
        self.res = (base_res, base_res)
        self.young = 3#+2*random()

        self.substrate = Solid.FreeFFTElasticHalfSpace(
            self.res, self.young, self.size)

        self.eps = 1# +np.random.rand()
        self.sig = 2# +np.random.rand()
        self.gam = 5# +np.random.rand()
        self.rcut = 2.5*self.sig# +np.random.rand()
        self.interaction = Contact.LJ93smooth(self.eps, self.sig, self.gam)
        self.min_pot = Contact.LJ93smoothMin(self.eps, self.sig, self.gam)

        self.surface = Surface.Sphere(self.radius, self.res, self.size,
                                      standoff=float('inf'))

    def test_FastSmoothContactSystem(self):
        S = FastSmoothContactSystem(self.substrate,
                                    self.interaction,
                                    self.surface)
        fun = S.objective(.95*self.interaction.r_c)
        print(fun(np.zeros(S.babushka.substrate.computational_resolution)))

    def test_SystemFactory(self):
        S = SystemFactory(self.substrate,
                          self.interaction,
                          self.surface)
        print("Mofo is periodic ?: ", self.substrate.is_periodic())
        print("substrate: ", self.substrate)
        self.assertIsInstance(S, FastSmoothContactSystem)
        self.assertIsInstance(S, SmoothContactSystem)

    def test_babushka_translations(self):
        S = FastSmoothContactSystem(self.substrate,
                                    self.interaction,
                                    self.surface)
        fun = S.objective(.95*self.interaction.r_c)


    def test_equivalence(self):
        tol = 1e-6
        # here, i deliberately avoid using the SystemFactory, because I want to
        # explicitly test the dumb (yet safer) way of computing problems with a
        # free, non-periodic  boundary. A user who invokes a system constructor
        # directliy like this is almost certainly mistaken
        systems = (SmoothContactSystem, FastSmoothContactSystem)
        def eval(system):
            print("running for system {}".format(system.__name__))
            S = system(self.substrate,
                       self.min_pot,
                       self.surface)
            offset = .8 * S.interaction.r_c
            fun = S.objective(offset, gradient=True)

            options = dict(ftol = 1e-18, gtol = 1e-10)
            disp = S.shape_minimisation_input(
                np.zeros(self.substrate.computational_resolution))
            bla = fun(disp)
            result = minimize(fun, disp, jac=True,
                              method = 'L-BFGS-B', options=options)
            if system.is_proxy():
                dummy, force, disp = S.deproxified()

            else:
                disp = S.shape_minimisation_output(result.x)
            gap = S.compute_gap(disp, offset)
            gap[np.isinf(gap)] = self.min_pot.r_c

            print('r_min = {}'.format(self.min_pot.r_min))
            return S.interaction.force, disp, gap, S.compute_normal_force()

        def timer(fun, *args):
            start = time.perf_counter()
            res = fun(*args)
            delay = time.perf_counter()-start
            return res, delay

        (((force_slow, disp_slow, gap_slow, N_slow), slow_time),
         ((force_fast, disp_fast, gap_fast, N_fast), fast_time)) = tuple(
             (timer(eval, system) for system in systems))
        error = Tools.mean_err(disp_slow, disp_fast)

        print("Normal forces: fast: {}, slow: {}, error: {}".format(
            N_fast, N_slow, abs(N_slow- N_fast)))

        print("timings: fast: {}, slow: {}, gain: {:2f}%".format(
            fast_time, slow_time, 100*(1-fast_time/slow_time)))
        self.assertTrue(error < tol,
                        "error = {} > tol = {}".format(
                            error, tol))

    def test_minimize_proxy(self):
        tol = 1e-6
        # here, i deliberately avoid using the SystemFactory, because I want to
        # explicitly test the dumb (yet safer) way of computing problems with a
        # free, non-periodic  boundary. A user who invokes a system constructor
        # directliy like this is almost certainly mistaken
        systems = (SmoothContactSystem, FastSmoothContactSystem)
        def eval(system):
            print("running for system {}".format(system.__name__))
            S = system(self.substrate,
                       self.min_pot,
                       self.surface)
            offset = .8 * S.interaction.r_c
            options = dict(ftol = 1e-18, gtol = 1e-10)
            result = S.minimize_proxy(offset, options=options)

            gap = S.compute_gap(S.disp, offset)
            gap[np.isinf(gap)] = self.min_pot.r_c

            return S.interaction.force, S.disp, gap, S.compute_normal_force()

        def timer(fun, *args):
            start = time.perf_counter()
            res = fun(*args)
            delay = time.perf_counter()-start
            return res, delay

        (((force_slow, disp_slow, gap_slow, N_slow), slow_time),
         ((force_fast, disp_fast, gap_fast, N_fast), fast_time)) = tuple(
             (timer(eval, system) for system in systems))
        error = Tools.mean_err(disp_slow, disp_fast)

        print("Normal forces: fast: {}, slow: {}, error: {}".format(
            N_fast, N_slow, abs(N_slow- N_fast)))

        print("timings: fast: {}, slow: {}, gain: {:2f}%".format(
            fast_time, slow_time, 100*(1-fast_time/slow_time)))
        self.assertTrue(error < tol,
                        "error = {} > tol = {}".format(
                            error, tol))

    def test_unit_neutrality(self):
        tol = 1e-7
        # runs the same problem in two unit sets and checks whether results are
        # changed

        # Conversion factors
        length_c   = 1. +9# np.random.rand()
        force_c    = 2. + 1#np.random.rand()
        pressure_c = force_c/length_c**2
        energy_per_area_c   = force_c/length_c
        energy_c   = force_c*length_c

        young = (self.young, pressure_c*self.young)
        size = (self.size, tuple((length_c*s for s in self.size)))
        print("SIZES!!!!! = ", size)
        radius = (self.radius, length_c*self.radius)
        res = self.res
        eps = (self.eps, energy_per_area_c*self.eps)
        sig = (self.sig, length_c*self.sig)
        gam = (self.gam, energy_per_area_c*self.gam)

        systems = list()
        offsets = list()
        length_rc = (1., 1./length_c)
        force_rc = (1., 1./force_c)
        energy_per_area_rc = (1., 1./energy_per_area_c)
        energy_rc = (1., 1./energy_c)

        for i in range(2):
            substrate = Solid.PeriodicFFTElasticHalfSpace(
                res, young[i], size[i])
            interaction = Contact.LJ93smoothMin(
                eps[i], sig[i], gam[i])
            surface = Surface.Sphere(
                radius[i], res, size[i], standoff=float(sig[i]*1000))
            systems.append(SystemFactory(substrate, interaction, surface))
            offsets.append(.8*systems[i].interaction.r_c)

        gaps = list()
        for i in range(2):
            gap = systems[i].compute_gap(np.zeros(systems[i].resolution), offsets[i])
            gaps.append(gap*length_rc[i])

        error = Tools.mean_err(gaps[0], gaps[1])
        self.assertTrue(error < tol,
                        "error = {} ≥ tol = {}".format(error, tol))

        forces = list()
        for i in range(2):
            energy, force = systems[i].evaluate(np.zeros(res), offsets[i], forces=True)
            forces.append(force*force_rc[i])

        error = Tools.mean_err(forces[0], forces[1])
        self.assertTrue(error < tol,
                        "error = {} ≥ tol = {}".format(error, tol))

        energies, forces = list(), list()
        substrate_energies = list()
        interaction_energies = list()
        disp = np.random.random(res)
        disp -= disp.mean()
        disp = (disp, disp*length_c)
        gaps = list()

        for i in range(2):
            energy, force = systems[i].evaluate(disp[i], offsets[i], forces=True)
            gap = systems[i].compute_gap(disp[i], offsets[i])
            gaps.append(gap*length_rc[i])
            energies.append(energy*energy_rc[i])
            substrate_energies.append(systems[i].substrate.energy*energy_rc[i])
            interaction_energies.append(systems[i].interaction.energy*energy_rc[i])
            forces.append(force*force_rc[i])

        error = Tools.mean_err(gaps[0], gaps[1])
        self.assertTrue(error < tol,
                        "error = {} ≥ tol = {}".format(error, tol))

        error = Tools.mean_err(forces[0], forces[1])

        self.assertTrue(error < tol,
                        "error = {} ≥ tol = {}".format(error, tol))

        error = abs(interaction_energies[0] - interaction_energies[1])
        self.assertTrue(error < tol,
                        "error = {} ≥ tol = {}".format(error, tol))


        error = abs(substrate_energies[0] - substrate_energies[1])
        self.assertTrue(error < tol,
                        "error = {} ≥ tol = {}, (c = {})".format(error, tol, energy_c))

        error = abs(energies[0] - energies[1])
        self.assertTrue(error < tol,
                        "error = {} ≥ tol = {}".format(error, tol))

        disps = list()
        for i in range(2):
            options = dict(ftol = 1e-32, gtol = 1e-20)
            result = systems[i].minimize_proxy(offsets[i], options=options)
            disps.append(systems[i].shape_minimisation_output(result.x)*length_rc[i])

        error = Tools.mean_err(disps[0], disps[1])
        self.assertTrue(error < tol,
                        "error = {} ≥ tol = {}, (c = {})".format(error, tol, length_c))