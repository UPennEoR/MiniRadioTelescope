# -*- coding: utf-8 -*-
"""
Created on Wed Aug  3 11:14:08 2016

@author: jaguirre
"""

import numpy as np
from astropy import units as u
from astropy import constants as c
import MRTtools as mrt

#%%
def dB2g(dB):
    g = np.power(10,dB/10.)
    return g
#%%    
def g2dB(g):
    dB = 10.*np.log10(g)
    return dB

def Pthermal(T,dnu):
    return (c.k_B * T * dnu).to(u.W)

def k_per_jy(a_eff):

    return (a_eff/(2.*c.k_B)).to(u.K/u.Jy)

Wthermal1MHz = (c.k_B * 300.*u.K * 1.*u.MHz).to(u.W)

# Number 1 MHz bins in the bandwidth
BW_N1MHz = 800.

G_amp = dB2g(15.)
G_LNA = 9e4
G_tot = G_amp * G_LNA
GdB = 10.*np.log10(G_tot)

lmbda = (c.c/(12.*u.GHz)).to(u.m)
A_tel = np.pi*np.power(0.2*u.m,2)
Omega_tel = ((np.power(lmbda,2)/A_tel).to(u.dimensionless_unscaled)).value
Omega_sun = np.pi*np.power(np.radians(0.5/2.),2)
Omega_jup = np.pi*np.power(np.radians(30./3600.),2)

#Spectrometer should see
print "The spectrometer (pre-amplification) should see", mrt.W2dBm((Wthermal1MHz*G_LNA).value), "dBm"
print "The spectrometer (post-amplification) should see", mrt.W2dBm((Wthermal1MHz*G_tot).value), "dBm"
print "The power detector should see",(Wthermal1MHz*G_tot*BW_N1MHz).value*1e6, "microW"
print "The power detector should see",mrt.W2dBm((Wthermal1MHz*G_tot*BW_N1MHz).value), "dBm"

# What's the dynamic range we expect to see?
print
print "Atmosphere:", mrt.W2dBm((Pthermal(20.*u.K,800.*u.MHz)*G_tot).value),"dBm"
print "Room:", mrt.W2dBm((Pthermal(300.*u.K,800.*u.MHz)*G_tot).value),"dBm"
print "Sun:", mrt.W2dBm((Pthermal(5800.*np.power(0.5/4.5,2)*u.K,800.*u.MHz)*G_tot).value),"dBm"