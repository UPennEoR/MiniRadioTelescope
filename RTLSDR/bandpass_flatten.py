#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 28 22:08:58 2017

@author: jaguirre
"""

import matplotlib.pyplot as plt
import numpy as np
from numpy.polynomial.legendre import Legendre

#%%
def fit_bp(bp,fl):
    # Fit the spectrum
    n_bp=len(bp)
    x = np.linspace(-1,1,num=n_bp,endpoint=True)
    L = Legendre([1,1,1,1])
    bpfit = L.fit(x[fl != 0],bp[fl != 0],10,domain=[-1,1])
    x_fit,y_fit = bpfit.linspace(n=n_bp)
    #y_fit /= np.median(y_fit)
    return y_fit

#%%
def bandpass(spec,fold=1024,flags=None):
    if flags is None:
        flags = np.ones_like(spec)
    wf = np.reshape(spec,[len(spec)/fold,fold])
    fl = np.reshape(flags,[len(spec)/fold,fold])
    fl = fl.prod(axis=0)
    bp = np.median(wf,axis=0)
    bp /= np.median(bp)
    # Flag any remaining deviations from the smooth spectrum
    bp_fit = fit_bp(bp,fl)
    whbad = np.where(bp-bp_fit>0.02)[0]
    fl[whbad] = 0
    fl[whbad+1] = 0
    fl[whbad-1] = 0
    return bp, fl

#%%
def bp_flatten(spec,fold=1024,flags=None,fit=False):
    if flags is None:
        flags = np.ones_like(spec)
    bp,fl = bandpass(spec,flags = flags, fold=fold)
    wf = np.reshape(spec,[len(spec)/fold,fold])
    if fit:
        print 'Fitting bandpass'
        print bp.shape
        print fl.shape
        bp = fit_bp(bp.copy(),fl.copy())
    spec_norm = np.reshape(wf/np.outer(np.ones(len(spec)/fold),bp),len(spec))
    return spec_norm

#%%
def specdb(spec,flags=None):
    if flags is None:
        flags = np.ones_like(spec)
    return 10.*np.log10(spec/flags)

#%% Parameters for this data
f_min = 64e6
f_max = 500e6
rate_best = 2.4e6
df = rate_best

freqs = np.arange(f_min + df/2.,f_max,df)

dat = np.load('ExampleData/spectrum.npz')
f = dat['f_all']
flag = dat['flags_all']
p = dat['psd_all']
pdb = 10.*np.log10(p/flag)
    
#%%
fold = 1024
wf = np.reshape(p,[len(p)/fold,fold])
bp, fl = bandpass(p,flags=flag)  
y_fit = fit_bp(bp,fl)
# Need to fold the bandpass-fitting flags forward into the flags.  
fl2 = np.outer(np.ones(len(p)/1024),fl)
flag2 = np.reshape(flag,[len(p)/fold,fold])
flag = np.reshape(flag2*fl2,len(p))
#%%
plt.figure(1)
plt.clf()
plt.plot(bp/fl)
plt.subplot(211)
plt.imshow(np.log10(wf),aspect='auto')
plt.xlim([0,1023])
plt.ylabel('Spectral Chunk')
plt.subplot(212)
plt.plot(bp/fl)
plt.plot(y_fit)
plt.plot(bp/fl-y_fit)
plt.hlines(0,0,1023,linestyles='--',colors='red')
plt.xlim([0,1023])
plt.ylim([-0.5,1.5])
plt.xlabel('Channel Number')
plt.ylabel('Relative Bandpass')
plt.savefig('SDR_Bandpass.png')
#%%
plt.figure(2)
plt.clf()
#plt.plot(f,pdb)
#plt.plot(f,specdb(bp_flatten(p,flags=flag),flags=flag))
plt.plot(f,specdb(bp_flatten(p,flags=flag,fit=True),flags=flag))
plt.xlabel('Frequency [MHz]')
plt.ylabel('Relative Power [dB]')
plt.savefig('SDR_Spectrum.png')
plt.xlim([91.5,95.0])
plt.savefig('SDR_Spectrum_Zoom1.png')
plt.xlim([64,500])
 
    