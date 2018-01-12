#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
HST observation module.
"""

from __future__ import (division, print_function, absolute_import,
                        unicode_literals)

import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.time import Time
from blastoise import tools
from scipy.integrate import simps

__all__ = []


# HST visit
class Visit(object):
    """

    """
    def __init__(self):
        self.orbit = {}

    def append_orbit(self, spectrum):
        """

        Args:
            spectrum (``UVSpectrum``):

        Returns:

        """
        self.orbit[spectrum.dataset_name] = spectrum


# The general ultraviolet spectrum object
class UVSpectrum(object):
    """

    """
    def __init__(self, dataset_name, good_pixel_limits=None):
        self.dataset_name = dataset_name
        self.x1d = dataset_name + '_x1d.fits'
        self.corrtag = dataset_name + '_corrtag_a.fits'
        self.gpl = good_pixel_limits

        # Read data from x1d file
        with fits.open(self.x1d) as f:
            self.header = f[0].header
            self.data = f['SCI'].data

        # Read some metadata from the corrtag file
        with fits.open(self.corrtag) as f:
            self.start_JD = Time(f[3].header['EXPSTRTJ'], format='jd')
            self.end_JD = Time(f[3].header['EXPENDJ'], format='jd')

        # If ``good_pixel_limits`` is set to ``None``, then the data will be
        # retrieved from the file in its entirety. Otherwise, it will be
        # retrieved using the limits established by ``good_pixel_limits``
        if self.gpl is None:
            self.gpl = ((0, -1), (0, -1))
        else:
            pass

        # Extract the most important information from the data
        i00 = self.gpl[0][0]
        i01 = self.gpl[0][1]
        i10 = self.gpl[1][0]
        i11 = self.gpl[1][1]
        self.wavelength = np.array([self.data['WAVELENGTH'][0][i00:i01],
                                    self.data['WAVELENGTH'][1][i10:i11]])
        self.flux = np.array([self.data['FLUX'][0][i00:i01],
                              self.data['FLUX'][1][i10:i11]])
        self.error = np.array([self.data['ERROR'][0][i00:i01],
                               self.data['ERROR'][1][i10:i11]])
        self.gross_counts = np.array([self.data['GCOUNTS'][0][i00:i01],
                                      self.data['GCOUNTS'][1][i10:i11]])
        self.background = np.array([self.data['BACKGROUND'][0][i00:i01],
                                    self.data['BACKGROUND'][1][i10:i11]])
        self.net = np.array([self.data['NET'][0][i00:i01],
                             self.data['NET'][1][i10:i11]])
        self.exp_time = np.array([self.data['EXPTIME'][0],
                                  self.data['EXPTIME'][1]])


# COS spectrum class
class COSSpectrum(UVSpectrum):
    """

    """
    def __init__(self, dataset_name,
                 good_pixel_limits=((1260, 15170), (1025, 15020))):
        super(COSSpectrum, self).__init__(dataset_name, good_pixel_limits)

        # Instantiating useful global variables
        self.sensitivity = None

    # Compute the correct errors for the HST/COS observation
    def compute_proper_error(self):
        """

        """
        self.sensitivity = self.flux / self.net / self.exp_time
        self.error = (self.gross_counts + 1.0) ** 0.5 * self.sensitivity

    # Compute the integrated flux in a given wavelength range
    def integrated_flux(self, wavelength_range,
                        uncertainty_method='quadratic_sum'):
        """

        Args:
            wavelength_range:
            uncertainty_method:

        Returns:

        """
        ind = tools.pick_side(self.wavelength, wavelength_range)

        min_wl = tools.nearest_index(self.wavelength[ind], wavelength_range[0])
        max_wl = tools.nearest_index(self.wavelength[ind], wavelength_range[1])
        # The following line is hacky, but it works
        delta_wl = self.wavelength[ind][1:] - self.wavelength[ind][:-1]
        int_flux = simps(self.flux[ind][min_wl:max_wl],
                         x=self.wavelength[ind][min_wl:max_wl])

        # Compute the uncertainty of the integrated flux
        if uncertainty_method == 'quadratic_sum':
            uncertainty = np.sqrt(np.sum((delta_wl[min_wl:max_wl] *
                                          self.error[ind][min_wl:max_wl]) ** 2))
        elif uncertainty_method == 'bootstrap':
            n_samples = 10000
            # Draw a sample of spectra and compute the fluxes for each
            samples = np.random.normal(loc=self.flux[ind][min_wl:max_wl],
                                       scale=self.error[ind][min_wl:max_wl],
                                       size=[n_samples, max_wl - min_wl])
            fluxes = []
            for i in range(n_samples):
                fluxes.append(simps(samples[i],
                                    x=self.wavelength[ind][min_wl:max_wl]))
            fluxes = np.array(fluxes)
            uncertainty = np.std(fluxes)
        else:
            raise ValueError('This value of ``uncertainty_method`` is not '
                             'accepted.')

        return int_flux, uncertainty

    # Plot the spectrum
    def plot_spectrum(self, wavelength_range, plot_uncertainties=False):
        """

        Args:
            wavelength_range:
            plot_uncertainties:

        Returns:

        """
        ind = tools.pick_side(self.wavelength, wavelength_range)

        min_wl = tools.nearest_index(self.wavelength[ind], wavelength_range[0])
        max_wl = tools.nearest_index(self.wavelength[ind], wavelength_range[1])

        # Finally plot it
        if plot_uncertainties is False:
            plt.plot(self.wavelength[ind][min_wl:max_wl],
                     self.flux[ind][min_wl:max_wl],
                     label=self.start_JD.value)
        else:
            plt.errorbar(self.wavelength[ind][min_wl:max_wl],
                         self.flux[ind][min_wl:max_wl],
                         yerr=self.error[ind][min_wl:max_wl],
                         fmt='.',
                         label=self.start_JD.value)
        plt.xlabel(r'Wavelength ($\mathrm{\AA}$)')
        plt.ylabel(r'Flux (erg s$^{-1}$ cm$^{-2}$ $\mathrm{\AA}^{-1}$)')


# STIS spectrum class
class STISSpectrum(object):
    """

    """
    def __init__(self):
        pass