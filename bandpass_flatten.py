#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 28 22:08:58 2017

@author: jaguirre
"""

import matplotlib.pyplot as plt
import numpy as np
from numpy.polynomial.legendre import Legendre

f_min = 64e6
f_max = 500e6
rate_best = 2.4e6
df = rate_best

#%%
# configure device

freqs = np.arange(f_min + df/2.,f_max,df)

dat = np.load('spectrum.npz')
f = dat['f_all']
flag = dat['flags_all']
p = dat['psd_all']
pdb = 10.*np.log10(p/flag)


#%%
def bandpass(spec,fold=1024,flags=None):
    if flags is None:
        flags = np.ones_like(spec)
    wf = np.reshape(spec,[len(spec)/fold,fold])
    fl = np.reshape(flags,[len(spec)/fold,fold])
    fl = fl.prod(axis=0)
    bp = np.median(wf,axis=0)
    bp /= np.median(bp)
    return bp, fl

#%%
def bp_flatten(spec,fold=1024):
    bp = bandpass(spec,fold=1024)
    wf = np.reshape(spec,[len(spec)/fold,fold])
    spec_norm = np.reshape(wf/np.outer(np.ones(len(spec)/fold),bp),len(spec))
    return spec_norm

def specdb(spec,flags=None):
    if flags is None:
        flags = np.ones_like(spec)
    return 10.*np.log10(spec/flags)
    
#%%
fold = 1024
wf = np.reshape(p,[len(p)/fold,fold])
bp, fl = bandpass(p,flags=flag)  
x = np.linspace(-1,1,num=fold,endpoint=True)

#%% Fit the spectrum
L = Legendre([1,1,1,1])
bpfit = L.fit(x[fl != 0],bp[fl != 0],10,domain=[-1,1])
x_fit,y_fit = bpfit.linspace(n=fold)
#%%
plt.figure(1)
plt.clf()
plt.plot(bp/fl)
plt.subplot(211)
plt.imshow(np.log10(wf),aspect='auto')
plt.xlim([0,1023])
plt.subplot(212)
plt.plot(bp/fl)
plt.plot(y_fit)
plt.plot(bp/fl-y_fit)
plt.hlines(0,0,1023,linestyles='--',colors='red')
plt.xlim([0,1023])
plt.ylim([-0.5,1.5])
#plt.plot(f,pdb)
#plt.plot(f,specdb(bp_flatten(p),flags=flag))
 
    