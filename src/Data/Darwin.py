"""
    Copyright (c) 2017 Sam Witte
    
    Created on Jan 19, 2017
    
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
    
    
    Results from
    """

from __future__ import absolute_import
from __future__ import division
import numpy as np
from scipy.interpolate import interp1d
pi = np.pi

name = "Darwin"
modulated = False

#energy_resolution_type = "Poisson"
#energy_resolution_type = "Dirac"
energy_resolution_type = "Gaussian"

def EnergyResolution(e):
    return np.ones_like(e) * e * 0.15

FFSD = 'GaussianFFSD'
FFSI = 'HelmFF'
FF = {'SI': FFSI,
    'SDPS': FFSD,
        'SDAV': FFSD,
        }
target_nuclide_AZC_list = \
    np.array([[124, 54, 0.0008966], [126, 54, 0.0008535], [128, 54, 0.018607],
              [129, 54, 0.25920], [130, 54, 0.040280], [131, 54, 0.21170],
              [132, 54, 0.27035], [134, 54, 0.10644], [136, 54, 0.09168]])
target_nuclide_JSpSn_list = \
    np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0],
              [1./2, 0.010 * np.sqrt(3./2 / pi), .329 * np.sqrt(3./2 / pi)], [0, 0, 0],
              [3./2, -0.009 * np.sqrt(5./2 / pi), -.272 * np.sqrt(5./2 / pi)], [0, 0, 0],
              [0, 0, 0], [0, 0, 0]])
target_nuclide_mass_list = np.array([115.418, 117.279, 119.141, 120.074, 121.004,
                                     121.937, 122.868, 124.732, 126.597])
num_target_nuclides = target_nuclide_mass_list.size

#QuenchingFactor = \
#    interp1d(np.array([0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 40, 1000]),
#             np.array([0, 0.394922, 0.714621, 0.861934, 0.944993, 1.01551, 1.08134,
#                       1.13507, 1.19417, 1.23701, 1.28068, 1.31812, 1.35872, 1.4, 1.4]))

QuenchingFactor = \
    interp1d(np.array([0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 40, 1000]),
             np.array([1., 1., 1., 1., 1., 1., 1.,
                       1., 1., 1., 1., 1., 1., 1., 1.]))


Ethreshold = 5.
Emaximum = 100.
ERmaximum = 20.5

def Efficiency_ER(er):
    try:
        len(er)
    except TypeError:
        er = [er]
    return np.ones_like(er)



Eff_ER_interp = \
    interp1d(np.loadtxt('/Users/SamWitte/Desktop/Codds_DarkMatter/src/Data/eff_Lux2016.dat')[:,0],
             np.loadtxt('/Users/SamWitte/Desktop/Codds_DarkMatter/src/Data/eff_Lux2016.dat')[:,1],
             kind='cubic', bounds_error=False, fill_value=0.)


def Efficiency(er):
    try:
        len(er)
    except TypeError:
        er = [er]
    return np.array([0.3 if ee > Ethreshold and ee < ERmaximum else 0. for ee in er])



Exposure = 200. * 1000. * 365.24
ERecoilList = np.array([])
Expected_limit = 1.

BinData = np.array([0.])
BinEdges_left = np.array([1.])
BinEdges_right = np.array([70.0])
BinBkgr=np.array([0.])
BinSize=100.
BinExposure = np.array([Exposure])


