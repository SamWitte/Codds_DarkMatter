"""
Copyright (c) 2015 Andreea Georgescu

Created on Sun Mar  1 21:28:44 2015

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from globalfnc import VMin
import numpy as np

def Vmin_range(exper_name, mx, delta, mPhi=1000., quenching=None, EHI_METHOD=False):
    """ Range and number of steps for vmin.
    Input:
        exper_name: string
            Name of experiment.
        mx: float
            DM mass.
        delta: float
            DM mass split.
        mPhi: float, optional
            Mass of mediator.
        quenching: float, optional
            quenching factor, needed for experiments that can have multiple options.
        EHI_Method: ndarray of bools, optional
            Whether each step of the EHI Method is to be performed.
    Returns:
        (mx_min, mx_max, num_steps): tuple (float, float, int)
            DM mass range and number or steps.
    """
    vmin_range_options = {}
    if exper_name == "CDMSSi2012" and EHI_METHOD:
        vmin_step = vmin_min = 1
        vmin_max = 1000
    elif exper_name == '3BinXe' and EHI_METHOD:
        vmin_step = vmin_min = 1
        vmin_max = 1000
    elif exper_name == 'DAMA_2Bin' and EHI_METHOD:
        vmin_step = vmin_min = 1
        vmin_max = 1000
    elif "LUX2013" in exper_name:
        vmin_step = vmin_min = 1
        vmin_max = 1000
        vmin_range_options = {(9., 0, 1000.): (450, vmin_max, vmin_step),
                              (3.5, -50, 1000.): (10, vmin_max, vmin_step),
                              (1.3, -200, 1000.): (10, vmin_max, vmin_step),
                              (1.2, -225, 1000.): (10, vmin_max, vmin_step)
                              }
    elif "LUX2016" in exper_name:
        vmin_step = vmin_min = 1
        vmin_max = 1000
        vmin_range_options = {(9., 0, 1000.): (10, vmin_max, vmin_step),
                              (3.5, -50, 1000.): (10, vmin_max, vmin_step),
                              (1.3, -200, 1000.): (10, vmin_max, vmin_step),
                              (1.2, -225, 1000.): (10, vmin_max, vmin_step)
                              }
    elif "PandaX" in exper_name:
        vmin_step = vmin_min = 1
        vmin_max = 1000
        vmin_range_options = {(9., 0, 1000.): (10, vmin_max, vmin_step),
                              (3.5, -50, 1000.): (10, vmin_max, vmin_step),
                              (1.3, -200, 1000.): (10, vmin_max, vmin_step),
                              (1.2, -225, 1000.): (10, vmin_max, vmin_step)
                              }
    elif "DAMA" in exper_name:
        vmin_step = vmin_min = 1
        if "Na" in exper_name:
            mT = 21.4148
            qT = 0.3
        else:
            mT = 118.211
            qT = 0.06
        Emax = 20
        vmin_max = round(VMin(Emax/qT, mT, mx, delta)) + 200
        if delta == 0:
            Ethreshold = 2.
            qT = 0.09
            vmin_step = VMin(Ethreshold/qT, mT, mx, delta)
        vmin_range_options = {(30.14, 0, 1000.): (vmin_step, vmin_max, 1000),
                              (47.35, 0, 1000.): (vmin_step, vmin_max, 600)
                              }
    elif "KIMS" in exper_name:
        vmin_min = vmin_step = 1
        vmin_max = 1000
    else:
        vmin_step = vmin_min = 1
        vmin_max = 1000
    default = (vmin_min, vmin_max, vmin_step)
    return vmin_range_options.get((mx, delta, mPhi), default)


def Log_sigma_p(mx, delta, fn):
    """ Log base 10 of the total reference cross-section to a single proton.
    Only for halo-independent SHM lines.
    Input:
        mx: float
            DM mass.
        delta: float
            DM mass split.
        fn: float
            Coupling to neutron.
    Returns:
        log_sigma_p: float
    """
    sigma_p_options = {(9., 0, 1.): -41,
                       (9., 0, -0.7): -40,
                       (9., 0, -0.8): -39,
                       (3.5, -50, -0.8): -40,
                       (1.3, -200, -0.8): -41,
                       (1.2, -225, -0.7): np.log10(3.*10**-43.),
                       (1.25, -220, -0.7): -41,
                       }
    default = -40
    return sigma_p_options.get((mx, delta, fn), default)


def Steepness(exper_name, mx, delta, mPhi=1000.):
    """ Steepness parameters used for nonlinear sampling in vminStar and logetaStar,
    for the EHI method. The higher the steepnesses the more points are taken close to
    the steps in the piecewise constant best-fit logeta(vmin) function.
    Input:
        exper_name: string
            Name of experiment.
        mx: float
            DM mass.
        delta: float
            DM mass split.
        mPhi: float, optional
            Mass of mediator.
    Returns:
        steepness: tuple, optional
            (steepness_vmin, steepness_vmin_center, steepness_logeta)
    """
    if exper_name == "CDMSSi2012":

        steepness_options = {(9., 0, 1000.): (1., 2.5, 1),
                             (3.5, -50, 1000.): (0.2, 1, 1),
                             (1.3, -200, 1000.): (0.1, 0.6, 1),
                             (1.2, -225, 1000.): (0.1, 0.6, 1),
                             (1.25, -220, 1000.): (0.1, 0.6, 1),
                             (4., -100, 1000.): (0.1, 0.6, 1),
                             (5., -100, 1000.): (0.1, 0.6, 1),
                             (2.2, -150, 1000.): (0.1, 0.6, 1),
                             }
        default = (1.5, 2.5, 1)
        return steepness_options.get((mx, delta, mPhi), default)
    elif "3BinXe" in exper_name:
        steepness_options = {(9., 0, 1000.): (0.1, 0.05, 1),
                             (3.5, -50, 1000.): (0.2, 1, 1),
                             (1.3, -200, 1000.): (0.1, 0.6, 1),
                             (1.2, -225, 1000.): (0.1, 0.6, 1),
                             (1.25, -220, 1000.): (0.1, 0.6, 1),
                             (4., -100, 1000.): (0.1, 0.6, 1),
                             (5., -100, 1000.): (0.1, 0.6, 1),
                             (2.2, -150, 1000.): (0.1, 0.6, 1),
                             }
        default = (1.5, 2.5, 1)
        return steepness_options.get((mx, delta, mPhi), default)

def Logeta_guess(exper_name, mx, delta, mPhi=1000.):
    """ Guessing value of logeta for the best-fit piecewise-constant logeta(vmin)
    function, for the EHI method.
    Input:
        exper_name: string
            Name of experiment.
        mx: float
            DM mass.
        delta: float
            DM mass split.
        mPhi: float, optional
            Mass of mediator.
    Returns:
        logeta_guess: float
    """
    if exper_name == "CDMSSi2012":

        logeta_options = {(9., 0, 1000.): -26.,
                          (3.5, -50, 1000.): -24,
                          (1.3, -200, 1000.): -22,
                          (1.2, -225, 1000.): -22,
                          (38, 50, 1000.): -20,

                          (2.2, -100, 1000.): -24,
                          (3., -100, 1000.): -24,
                          (4., -100, 1000.): -24,
                          (5., -100, 1000.): -24,

                          (1.5, -150, 1000.): -24,
                          (1.8, -150, 1000.): -24,
                          (2.2, -150, 1000.): -24,

                          (4, -80, 1000.): -24,
                          (5, -80, 1000.): -24,
                          (6, -80, 1000.): -24,

                          }
    elif '3BinXe' in exper_name:
        logeta_options = {(9., 0, 1000.): -29.}

    elif exper_name == 'DAMA_2Bin':
        logeta_options = {(15., 0, 1000.): -23.,
                          (9., 0, 1000.): -23.}


    return logeta_options[(mx, delta, mPhi)]


def Vmin_EHIBand_range(exper_name, mx, delta, mPhi=1000.):
    """ VminStar range and number of steps, used for calculating the EHI confidence band.
    Input:
        exper_name: string
            Name of experiment.
        mx: float
            DM mass.
        delta: float
            DM mass split.
        mPhi: float, optional
            Mass of mediator.
    Returns:
        (vmin_Band_min, vmin_Band_max, vmin_Band_numsteps): tuple (float, float, int)
    """

    if exper_name == "CDMSSi2012":

        options = {(9., 0, 1000.): (0, 1000, 100),
                   (3.5, -50, 1000.): (0, 1000, 80),
                   (1.3, -200, 1000.): (0, 1000, 80),
                   (1.2, -225, 1000.): (0, 1000, 70),
                   (38, 50, 1000.): (0, 1000, 80),

                   (2.2, -100, 1000.): (0, 800, 20),
                   (3., -100, 1000.): (0, 800, 20),
                   (4., -100, 1000.): (0, 800, 20),
                   (5., -100, 1000.): (0, 800, 20),

                   (1.5, -150, 1000.): (0, 800, 20),
                   (1.8, -150, 1000.): (0, 800, 20),
                   (2.2, -150, 1000.): (0, 800, 20),

                   (4, -80, 1000.): (0, 800, 20),
                   (5, -80, 1000.): (0, 800, 20),
                   (6, -80, 1000.): (0, 800, 20),
                   }
        return options[(mx, delta, mPhi)]
    elif exper_name == "3BinXe":
        options = {(9., 0, 1000.): (100., 700., 50)}
        return options[(mx, delta, mPhi)]

    elif exper_name == "3BinXe2":
        options = {(9., 0, 1000.): (200., 700., 50)}
        return options[(mx, delta, mPhi)]

    elif exper_name == "DAMA_2Bin":
        options = {(9., 0, 1000.): (50., 700., 30),
                   (15., 0, 1000.): (50., 700., 30),
                              }
        return options[(mx, delta, mPhi)]

""" List of input values of the form (mx, fn, delta, mPhi).
"""
input_list = [(9., 1, 0., 1000.), (9., -0.8, 0., 1000.), (9., -0.7, 0., 1000.),  # 0 - 2
              (3.5, 1, -50, 1000.), (3.5, -0.8, -50, 1000.), (3.5, -0.7, -50, 1000.),  # 3 - 5
              (1.3, 1, -200, 1000), (1.3, -0.8, -200, 1000), (1.3, -0.7, -200, 1000),  # 6 - 8
              (9., 0, 0., 1000.), (33., 0, 0, 1000), (47., 0, 0, 1000),  # 9 - 11
              (7, 0, 0, 1000), (30.14, 0, 0, 1000), (47.35, 0, 0, 1000),  # 12 - 14, SDPS
              (38, 0, 50, 1000.), (45, 0, 100, 1000),  # 15 - 16, SDPS
              (40, 0, 50, 1000), (52, 0, 100, 1000), (80, 0, 100, 0), # 17 - 19, SDAV
              
              (2.2, -0.7, -100, 1000), (3., -0.7, -100, 1000), (4., -0.7, -100, 1000), # 20-22
              (5., -0.7, -100, 1000), (1.5, -0.7, -150, 1000), (1.8, -0.7, -150, 1000), # 23-25
              (4, -0.7, -80, 1000), (5, -0.7, -80, 1000), (6, -0.7, -80, 1000), # 26-28
              (15., 1., 0., 1000)] # 29


logeta_EHIBand_percent_range = (0.4, 0.4, 15)
# logeta_EHIBand_percent_range = (0.15, 0.15, 20)
