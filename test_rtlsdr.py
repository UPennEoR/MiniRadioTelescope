#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 26 21:55:36 2017

@author: jaguirre
"""

import matplotlib.pyplot as plt
import rtlsdr 

sdr = rtlsdr.RtlSdr()

#%%
# configure device
sdr.sample_rate = 3.0e6
sdr.center_freq = 260.5e6
sdr.gain = 'auto'#4

samples = sdr.read_samples(256*1024)

plt.figure()
plt.clf()
# use matplotlib to estimate and plot the PSD
plt.psd(samples, NFFT=1024, Fs=sdr.sample_rate/1e6, Fc=sdr.center_freq/1e6)
plt.xlabel('Frequency (MHz)')
plt.ylabel('Relative power (dB)')

sdr.close()
plt.show()

