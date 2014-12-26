# -*- coding: utf-8 -*-
"""
Created on Thu Nov 20 22:52:11 2014

@author: Andreea
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division


INPUT_DIR = "Data/"
OUTPUT_MAIN_DIR = "Output/"

def import_file(full_path_to_module):
    import os, sys
    directory, module_name = os.path.split(full_path_to_module)
    module_name = os.path.splitext(module_name)[0]
        
    path = list(sys.path)
    sys.path.insert(0, directory)
    try:
        module = __import__(module_name)
        return module
    finally:
        sys.path[:] = path # restore 


from globalfnc import *
from haxtonFF import *
import numpy as np
from numpy import pi
from scipy import integrate
from scipy.optimize import fsolve
from scipy.special import lambertw

class Experiment:
    def __init__(self, expername, scattering_type, mPhi = mPhiRef):
        module = import_file(INPUT_DIR + expername + ".py")
        self.name = expername
        self.scattering_type = scattering_type
        self.energy_resolution_type = module.energy_resolution_type
        self.EnergyResolution = module.EnergyResolution
        self.ResolutionFunction = Gaussian if \
            self.energy_resolution_type == "Gaussian" else GPoisson  

        self.mPhi = mPhi
        self.J = module.target_nuclide_JSpSn_list[:,0]
        self.numT = module.num_target_nuclides
        if "SD" in self.scattering_type:
            self.mT = np.array([module.target_nuclide_mass_list[i] \
                for i in range(self.numT) if self.J[i] != 0 ])
            self.A = np.array([module.target_nuclide_AZC_list[i,0] \
                for i in range(self.numT) if self.J[i] != 0 ])
            self.Z = np.array([module.target_nuclide_AZC_list[i,1] \
                for i in range(self.numT) if self.J[i] != 0 ])
            self.mass_fraction = np.array([module.target_nuclide_AZC_list[i,2] \
                for i in range(self.numT) if self.J[i] != 0 ])
            self.SpScaled = np.array([module.target_nuclide_JSpSn_list[i,1] \
                for i in range(self.numT) if self.J[i] != 0 ])
            self.SnScaled = np.array([module.target_nuclide_JSpSn_list[i,2] \
                for i in range(self.numT) if self.J[i] != 0 ])
            self.J = np.array([j for j in self.J if j != 0 ])
            self.numT = np.size(self.J)
        else:
            self.mT = module.target_nuclide_mass_list
            self.A = module.target_nuclide_AZC_list[:,0]
            self.Z = module.target_nuclide_AZC_list[:,1]
            self.mass_fraction = module.target_nuclide_AZC_list[:,2]
            self.SpScaled = module.target_nuclide_JSpSn_list[:,1]
            self.SnScaled = module.target_nuclide_JSpSn_list[:,2]

        if module.modulated == False:
            self.etaMaxwellian = eta0Maxwellian
        else:
            self.etaMaxwellian = eta1Maxwellian

        FF_default = np.array([[lambda y: 0]*2]*2)
        self._FFSigmaPPJ_function_list = np.array(list(map(lambda a, z: \
            FFSigmaPPJ.get((np.trunc(a), np.trunc(z)), FF_default), \
            self.A, self.Z)))
        self._FFSigmaPJ_function_list = np.array(list(map(lambda a, z: \
            FFSigmaPJ.get((np.trunc(a), np.trunc(z)), FF_default), \
            self.A, self.Z)))

        self.FF = FF_options[self.scattering_type][module.FF[scattering_type]]
        self.ffelemQ = FFElementQ(self.Z)
        if ((self.ffelemQ == 1).all()):
            print("Haxton")
            self.CrossSectionFactors_SD44 = self.CrossSectionFactors_SD44_Haxton
            self.CrossSectionFactors_SD66 = self.CrossSectionFactors_SD66_Haxton
        else:
            print("mixed")
            self.CrossSectionFactors_SD44 = self.CrossSectionFactors_SD44_Mixed
            self.CrossSectionFactors_SD66 = self.CrossSectionFactors_SD66_Mixed

        CrossSectionFactors_options = {'SI' : self.CrossSectionFactors_SI,
           'SD66' : self.CrossSectionFactors_SD66,
           'SD44' : self.CrossSectionFactors_SD44,
        }
        self.CrossSectionFactors = CrossSectionFactors_options[self.scattering_type]
        if self.energy_resolution_type == "Dirac":
            self.IntegratedResponseSHM = self.IntegratedResponseSHM_Dirac
        else:
            self.IntegratedResponseSHM = self.IntegratedResponseSHM_Other

        self.QuenchingFactor = module.QuenchingFactor  
        self.Efficiency = module.Efficiency
        self.Efficiency_ER = module.Efficiency_ER
        self.Ethreshold = module.Ethreshold
        self.Emaximum = module.Emaximum
        self.ERmaximum = module.ERmaximum
        self.Exposure = module.Exposure
        
        self.count_diffresponse_calls = 0
        self.count_response_calls = 0

        self._bsq = 41.467/(45. * self.A**(-1./3) - 25. * self.A**(-2./3)) * fermiGeV**2
        self._y_over_ER =  2.e-6 * self.mT * self._bsq / 4.
        self._cross_sec_factors_SD66 =  (SpeedOfLight/v0bar)**4 * \
            self.mass_fraction * self.mT**2 

    def FormFactor(self, ER):
        result = (4./3. * (4. * pi)/(2 * self.J + 1.)) * self.FF(ER, self.A, self.mT)
        return result

    def CrossSectionFactors_SI(self, ER, mx, fp, fn, delta):
        mu_p = ProtonMass * mx / (ProtonMass + mx)
        return self.mass_fraction * 1./(2.*mu_p**2) * \
            mPhiRef**4 / (4. * self.mT**2 * (ER + self.mPhi**2/(2. * self.mT))**2) * \
            ((self.Z + (self.A - self.Z) * fn/fp)**2) * self.FormFactor(ER) 

    def FF66normlalized(self, ER, N1, N2):
        y = ER * self._y_over_ER
        l = np.empty(self.numT)
        for i in range(self.numT):
            l[i] = self._FFSigmaPPJ_function_list[i, N1, N2](y[i])
        return l * np.exp(-2. * y)

    def FF44normlalized(self, ER, N1, N2):
        y = ER * self._y_over_ER
        l = np.empty(self.numT)
        for i in range(self.numT):
            l[i] = 1./3 * (self._FFSigmaPPJ_function_list[i, N1, N2](y[i]) + \
                self._FFSigmaPJ_function_list[i, N1, N2](y[i]))
        return l * np.exp(-2. * y)
    
    def CrossSectionFactors_SD66_Haxton(self, ER, mx, fp, fn, delta):
        mu_p = ProtonMass * mx / (ProtonMass + mx)
        return 1.e-12 * ER**2 * 3./(8. * mu_p**6) * \
            mPhiRef**4 / (4. * self.mT**2 * (ER + self.mPhi**2/ 2 / self.mT)**2) * \
            self._cross_sec_factors_SD66 * \
            (self.FF66normlalized(ER, 0, 0) + 2 * fn/fp * self.FF66normlalized(ER, 0, 1) + \
            (fn/fp)**2 * self.FF66normlalized(ER, 1, 1))
#            (self.SpScaled + self.SnScaled * fn/fp)**2 * self.FormFactor(ER)

    def CrossSectionFactors_SD66_Mixed(self, ER, mx, fp, fn, delta):
        mu_p = ProtonMass * mx / (ProtonMass + mx)
        return 1.e-12 * ER**2 * 3./(8. * mu_p**6) * \
            mPhiRef**4 / (4. * self.mT**2 * (ER + self.mPhi**2/ 2 / self.mT)**2) * \
            self._cross_sec_factors_SD66 * \
            (self.ffelemQ * (self.FF66normlalized(ER, 0, 0) + 2 * fn/fp * self.FF66normlalized(ER, 0, 1) + \
            (fn/fp)**2 * self.FF66normlalized(ER, 1, 1)) + \
            (1-self.ffelemQ) * (self.SpScaled + self.SnScaled * fn/fp)**2 * self.FormFactor(ER))

    def CrossSectionFactors_SD44_Haxton(self, ER, mx, fp, fn, delta):
        mu_p = ProtonMass * mx / (ProtonMass + mx)
        return self.mass_fraction / (2 * mu_p**2) * \
            mPhiRef**4 / (4. * self.mT**2 * (ER + self.mPhi**2/(2 * self.mT))**2) * \
            (self.FF44normlalized(ER, 0, 0) + 2 * fn/fp * self.FF44normlalized(ER, 0, 1) + \
            (fn/fp)**2 * self.FF44normlalized(ER, 1, 1))
#            (self.SpScaled + self.SnScaled * fn/fp)**2 * self.FormFactor(ER)

    def CrossSectionFactors_SD44_Mixed(self, ER, mx, fp, fn, delta):
        mu_p = ProtonMass * mx / (ProtonMass + mx)
        return self.mass_fraction / (2 * mu_p**2) * \
            mPhiRef**4 / (4. * self.mT**2 * (ER + self.mPhi**2/(2 * self.mT))**2) * \
            (self.ffelemQ * (self.FF44normlalized(ER, 0, 0) + 2 * fn/fp * self.FF44normlalized(ER, 0, 1) + \
            (fn/fp)**2 * self.FF44normlalized(ER, 1, 1)) + \
            (1-self.ffelemQ) * (self.SpScaled + self.SnScaled * fn/fp)**2 * self.FormFactor(ER))
 
    def Resolution(self, Eee, qER):
        return self.ResolutionFunction(Eee, qER, self.EnergyResolution(qER))
        
    def DifferentialResponseSHM(self, Eee, ER, mx, fp, fn, delta): 
        self.count_diffresponse_calls += 1
        q = self.QuenchingFactor(ER)
        qER = q * ER
        vmin = VMin(ER, self.mT, mx, delta)
        r_list = 1.e-6 * kilogram * self.CrossSectionFactors(ER, mx, fp, fn, delta) * \
            self.Efficiency(Eee) * self.Efficiency_ER(ER) * \
            self.ResolutionFunction(Eee, qER, self.EnergyResolution(qER)) * \
            self.etaMaxwellian(vmin, vobs, v0bar, vesc)
        return r_list.sum()
        
    def ResponseSHM_Dirac(self, ER, Eee1, Eee2, mx, fp, fn, delta): 
        q = self.QuenchingFactor(ER)
        qER = q * ER
        vmin = VMin(ER, self.mT, mx, delta)
        integrated_delta = 1. if Eee1 <= qER < Eee2 else 0.
        r_list = 1.e-6 * kilogram * self.CrossSectionFactors(ER, mx, fp, fn, delta) * \
            self.Efficiency(Eee1, qER) * self.Efficiency_ER(qER) * \
            integrated_delta * self.etaMaxwellian(vmin, vobs, v0bar, vesc)
        self.count_response_calls += 1
        r = r_list.sum()
#        print(ER, " ", Eee1, " ", Eee2, " ", r)
#        print(vmin)
#        print(self.etaMaxwellian(vmin, vobs, v0bar, vesc))
        return r
        
    def ResponseSHM_Other(self, ER, Eee1, Eee2, mx, fp, fn, delta):
        self.count_response_calls += 1
        result = integrate.quad(self.DifferentialResponseSHM, Eee1, Eee2, \
            args=(ER, mx, fp, fn, delta), epsrel = PRECISSION, epsabs = 0)[0]
#        print(ER, " ", result)
        return result

    def IntegratedResponseSHM_Dirac(self, Eee1, Eee2, mx, fp, fn, delta):
        vmax = vesc + vobs
        muT = self.mT * mx / (self.mT + mx)
        vdelta = SpeedOfLight / 500. * np.sqrt(delta / 2. / muT) if delta > 0 \
            else np.array([0] * self.numT)
        ER_plus_list = list(map(lambda i, j: ERecoilBranch(vmax, i, mx, delta, 1) \
            if j < vmax else 0., self.mT, vdelta))
        ER_minus_list = list(map(lambda i, j: ERecoilBranch(vmax, i, mx, delta, -1) \
            if j < vmax else 1.e6, self.mT, vdelta))
#        print("ER_plus_list = ", ER_plus_list)
#        print(min(np.max(ER_plus_list), self.ERmaximum))
#        print(Eee2)
        #TODO! This is only valid for quenching factor 1!!! Extend to arbitrary q!
        ER_plus = min(min(np.max(ER_plus_list), self.ERmaximum), Eee2)
        ER_minus = max(np.min(ER_minus_list), Eee1)
#        print("ER+- = ", ER_minus, " ", ER_plus)
        if ER_minus < ER_plus:
            integr = integrate.quad(self.ResponseSHM_Dirac, ER_minus, ER_plus, \
                args=(Eee1, Eee2, mx, fp, fn, delta)) #, vec_func=False
#            print("Eee1, Eee2, integr = ", Eee1, " ", Eee2, " ", integr)
            return integr[0]
        else:
            return 0.
            
    def IntegratedResponseSHM_Other(self, Eee1, Eee2, mx, fp, fn, delta):
        vmax = vesc + vobs
        muT = self.mT * mx / (self.mT + mx)
        vdelta = SpeedOfLight / 500. * np.sqrt(delta / 2. / muT) if delta > 0 \
            else np.array([0] * self.numT)
        ER_plus_list = list(map(lambda i, j: ERecoilBranch(vmax, i, mx, delta, 1) \
            if j < vmax else 0., self.mT, vdelta))
        ER_minus_list = list(map(lambda i, j: ERecoilBranch(vmax, i, mx, delta, -1) \
            if j < vmax else 1.e6, self.mT, vdelta))
        ER_plus = min(np.max(ER_plus_list), self.ERmaximum)
        ER_minus = np.min(ER_minus_list)
#        print("ER+- = ", ER_minus, " ", ER_plus)
#        print("Eee = ", Eee1, " ", Eee2)
        midpoints = []
        if ER_minus < Eee1 < ER_plus:
            midpoints += [Eee1]
        if ER_minus < Eee2 < ER_plus:
            midpoints += [Eee2]
        if ER_minus < ER_plus:
            integr = integrate.quad(self.ResponseSHM_Other, ER_minus, ER_plus, \
                args=(Eee1, Eee2, mx, fp, fn, delta), points = midpoints, epsrel = PRECISSION, epsabs = 0)
            '''
            integr = integrate.dblquad(self.DifferentialResponseSHM, ER_minus, ER_plus, \
                lambda Eee: Eee1, lambda Eee: Eee2, \
                args=(mx, fp, fn, delta), epsrel = PRECISSION, epsabs = 0)
            '''
#            print("midpoints = ", midpoints)
#            print("Eee1, Eee2, integr = ", Eee1, " ", Eee2, " ", integr)
            return integr[0]
        else:
            return 0.

class PoissonExperiment(Experiment):
    def __init__(self, expername, scattering_type, mPhi = mPhiRef, quenching_factor = None):
        Experiment.__init__(self, expername, scattering_type, mPhi)
        module = import_file(INPUT_DIR + expername + ".py")
        self.Expected_limit = module.Expected_limit

    def PoissonUpperBoundSHM(self, mx, fp, fn, delta):
        vmax = vobs + vesc
        muT = self.mT * mx / (self.mT + mx)
        vdelta = SpeedOfLight / 500. * np.sqrt(delta / 2. / muT) if delta > 0 \
            else np.array([0] * self.numT)
        Eee_max_list = list(map(lambda i, j: ERecoilBranch(vmax, i, mx, delta, 1) \
            if j < vmax else 0., self.mT, vdelta))
        Eee_min_list = list(map(lambda i, j: ERecoilBranch(vmax, i, mx, delta, -1) \
            if j < vmax else 1.e6, self.mT, vdelta))
        Eee_max = np.max(Eee_max_list)
        Eee_min = max(self.Ethreshold, np.min(Eee_min_list))
#        print("mT = ", self.mT)
#        print("Eee_min & max = ", Eee_min, " ", Eee_max)
        int_response = self.IntegratedResponseSHM(Eee_min, Eee_max, mx, fp, fn, delta)
#        print("int_response = ", int_response)
        if int_response > 0:
            result = self.Expected_limit / self.Exposure / int_response
        else:
            result = np.inf
        print("mx = ", mx)
        print("result = ", result)
        return result

    def UpperLimit(self, fp, fn, delta, mx_min, mx_max, num_steps, output_file):
        mx_list = np.logspace(np.log10(mx_min), np.log10(mx_max), num_steps)
        upper_limit = np.array(list(map(lambda mx: \
            self.PoissonUpperBoundSHM(mx, fp, fn, delta), mx_list)))
        print("mx_list = ", mx_list)
        print("upper_limit = ", upper_limit)
        to_print = np.log10(np.transpose([mx_list, upper_limit]))
        to_print = to_print[to_print[:, 1] != np.inf]
        with open(output_file,'ab') as f_handle:
            np.savetxt(f_handle, to_print)
        return to_print

class GaussianExperiment(Experiment):
    def __init__(self, expername, scattering_type, mPhi = mPhiRef, quenching_factor = None):
        Experiment.__init__(self, expername, scattering_type, mPhi)
        module = import_file(INPUT_DIR + expername + ".py")
        self.BinEdges_left = module.BinEdges_left
        self.BinEdges_right = module.BinEdges_right
        self.BinData = module.BinData
        self.BinError = module.BinError
        self.BinSize = module.BinSize
        self.chiSquared = module.chiSquared
        
        if quenching_factor != None:
            self.QuenchingFactor = lambda e: quenching_factor

    def GaussianUpperBoundSHM(self, mx, fp, fn, delta, output_file):
        predicted = conversion_factor / mx * \
            np.array(list(map(lambda i, j: \
            self.IntegratedResponseSHM(i, j, mx, fp, fn, delta), \
            self.BinEdges_left, self.BinEdges_right)))
        sum_pred_squared = 1./self.BinSize**2 * sum((predicted/self.BinError)**2)
        sum_pred_bindata = 2./self.BinSize * \
            sum(predicted * self.BinData / self.BinError**2)
        sum_bindata_squared = sum((self.BinData/self.BinError)**2) - self.chiSquared
        result = (sum_pred_bindata + np.sqrt(sum_pred_bindata**2 - \
            4 * sum_pred_squared * sum_bindata_squared)) / (2 * sum_pred_squared)
        print("mx = ", mx)
        print("result = ", result)
        to_print = np.log10(np.array([[mx, result]]))
        with open(output_file,'ab') as f_handle:
            np.savetxt(f_handle, to_print)
        return result

    def UpperLimit(self, fp, fn, delta, mx_min, mx_max, num_steps, output_file):
        mx_list = np.logspace(np.log10(mx_min), np.log10(mx_max), num_steps)
        upper_limit = np.array(list(map(lambda mx: \
            self.GaussianUpperBoundSHM(mx, fp, fn, delta, output_file), mx_list)))
        print("mx_list = ", mx_list)
        print("upper_limit = ", upper_limit)
        result = np.transpose([mx_list, upper_limit.flatten()])
        return result[result[:, 1] != np.inf]


class MaxGapExperiment(Experiment):
    def __init__(self, expername, scattering_type, mPhi = mPhiRef):
        Experiment.__init__(self, expername, scattering_type, mPhi)
        module = import_file(INPUT_DIR + expername + ".py")
        self.ERecoilList = module.ERecoilList
        self.ElistMaxGap = np.append( np.insert( \
            np.array(list(filter(lambda x: self.Ethreshold < x < self.Emaximum, \
            self.ERecoilList))), \
            0, self.Ethreshold), self.Emaximum)

    def MaximumGapUpperBoundSHM(self, mx, fp, fn, delta, output_file):
        print("mx = ", mx)
        xtable = np.array(list(map(lambda i, j: \
            self.IntegratedResponseSHM(i, j, mx, fp, fn, delta), \
            self.ElistMaxGap[:-1], self.ElistMaxGap[1:])))
        mu_scaled = xtable.sum()
        x_scaled = np.max(xtable)
        if x_scaled == 0:
            mu_over_x = np.inf
            result = [np.inf]
        else:
            mu_over_x = mu_scaled / x_scaled
            y_guess = np.real(-lambertw(-0.1 / mu_over_x, -1))
#            print("y_guess = ", y_guess)
            y = fsolve(lambda x: MaximumGapC0scaled(x, mu_over_x) - ConfidenceLevel, y_guess)
            result =  y / x_scaled / self.Exposure
        print("mx = ", mx, "   mu_over_x = ", mu_over_x)
        print("xtable = ", xtable)
        print("result = ", result[0])
        to_print = np.log10(np.array([[mx, result[0]]]))
        with open(output_file,'ab') as f_handle:
            np.savetxt(f_handle, to_print)
        return result
        
    def UpperLimit(self, fp, fn, delta, mx_min, mx_max, num_steps, output_file):
        mx_list = np.logspace(np.log10(mx_min), np.log10(mx_max), num_steps)
        upper_limit = np.array(list(map(lambda mx: \
            self.MaximumGapUpperBoundSHM(mx, fp, fn, delta, output_file), mx_list)))
        print("mx_list = ", mx_list)
        print("upper_limit = ", upper_limit)
        result = np.log10(np.transpose([mx_list, upper_limit.flatten()]))
        return result[result[:, 1] != np.inf]



class DAMAExperiment(Experiment):
    def __init__(self, expername, scattering_type, mPhi = mPhiRef, quenching_factor = None):
        Experiment.__init__(self, expername, scattering_type, mPhi)
        module = import_file(INPUT_DIR + expername + ".py")
        self.BinEdges = module.BinEdges
        self.BinData = self.Exposure * module.BinData
        self.BinError = self.Exposure *  module.BinError
        
        if quenching_factor != None:
            self.QuenchingFactor = lambda e: quenching_factor

    def RegionSHM(self, mx, fp, fn, delta, output_file):
        predicted = self.Exposure * conversion_factor / mx * \
            np.array(list(map(lambda i, j: \
            self.IntegratedResponseSHM(i, j, mx, fp, fn, delta), \
            self.BinEdges[:-1], self.BinEdges[1:])))
        sum_pred_squared = sum((predicted/self.BinError)**2)
        sum_pred_bindata = sum(predicted * self.BinData / self.BinError**2)
        sigma_fit = max(sum_pred_bindata / sum_pred_squared, 0)
        predicted *= sigma_fit
        log_likelihood_max = -0.5 * sum(((predicted - self.BinData) / self.BinError)**2)
        print("mx = ", mx)
        print("sigma_fit = ", sigma_fit)
        print("max log likelihood = ", log_likelihood_max)
        to_print = np.hstack((mx, sigma_fit, log_likelihood_max, predicted, self.BinData, self.BinError))
        with open(output_file,'ab') as f_handle:
            np.savetxt(f_handle, to_print)
        return to_print

    def UpperLimit(self, fp, fn, delta, mx_min, mx_max, num_steps, output_file):
        mx_list = np.logspace(np.log10(mx_min), np.log10(mx_max), num_steps)
        upper_limit = np.array(list(map(lambda mx: \
            self.RegionSHM(mx, fp, fn, delta, output_file), mx_list)))
        print("mx_list = ", mx_list)
        print("upper_limit = ", upper_limit)
        return upper_limit


class DAMATotalRateExperiment(Experiment):
    def __init__(self, expername, scattering_type, mPhi = mPhiRef, quenching_factor = None):
        Experiment.__init__(self, expername, scattering_type, mPhi)
        module = import_file(INPUT_DIR + expername + ".py")
        self.BinEdges = module.BinEdges
        self.BinData = self.Exposure * module.BinData

        if quenching_factor != None:
            self.QuenchingFactor = lambda e: quenching_factor

    def RegionSHM(self, mx, fp, fn, delta, output_file):
        predicted = self.Exposure * conversion_factor / mx * \
            np.array(self.IntegratedResponseSHM(self.BinEdges[0], self.BinEdges[1], mx, fp, fn, delta))
        sigma_fit = self.BinData[0] / predicted
        print("mx = ", mx)
        print("sigma_fit = ", sigma_fit)
        to_print = np.array([[mx, sigma_fit]])
        with open(output_file,'ab') as f_handle:
            np.savetxt(f_handle, to_print)
        return to_print.flatten()

    def UpperLimit(self, fp, fn, delta, mx_min, mx_max, num_steps, output_file):
        mx_list = np.logspace(np.log10(mx_min), np.log10(mx_max), num_steps)
        upper_limit = np.array(list(map(lambda mx: \
            self.RegionSHM(mx, fp, fn, delta, output_file), mx_list)))
        print("mx_list = ", mx_list)
        print("upper_limit = ", upper_limit)
        return upper_limit