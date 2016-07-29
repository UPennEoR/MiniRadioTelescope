import numpy as np

def W2dBm(W):
    return 10.*np.log10(W/1e-3)

def dBm2W(dBm):
     return np.power(10,dBm/10.)*1e-3

def zx47_60(v):
    """ Calibration curve for the Mini-Circuits ZX47-60(LN)+ power detector"""
    dBm = -50/(1.8-0.6)*(v-0.6)
    W = dBm2W(dBm)
    return W*1e6
