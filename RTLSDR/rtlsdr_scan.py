#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 26 21:55:36 2017

@author: jaguirre
"""

import matplotlib.pyplot as plt
import rtlsdr
import numpy as np
import time

f_min = 750e6
f_max = 1700e6
rate_best = 2.4e6
df = rate_best
#%%

# Open device
sdr = rtlsdr.RtlSdr()

#%%
# configure device
sdr.sample_rate = rate_best
sdr.gain = 4

freqs = np.arange(f_min + df/2.,f_max,df)

f_all = np.zeros(len(freqs)*1024)
psd_all = np.zeros(len(freqs)*1024)
flags_all = np.zeros(len(freqs)*1024)
indx = np.arange(1024)

plt.figure(1)
plt.clf()

for freq in freqs:
    print(freq)
    sdr.center_freq = freq
    samples = sdr.read_samples(256*1024)
    fc_mhz = freq/1e6
    bw_mhz = sdr.sample_rate/1e6
    off = 0.781

    flags = np.ones(1024)
    # use matplotlib to estimate and plot the PSD
    p,f = plt.psd(samples, NFFT=1024, Fs=bw_mhz, Fc=fc_mhz)
    # Notch out zero freq plus some other spurious spike ("off")
    wh0 = np.abs(f - fc_mhz).argmin()
    flags[wh0-1:wh0+2] = 0
    #p[wh0] = np.median([p[wh0-1],p[wh0+1]])
    wh3 = np.abs(f - (fc_mhz+off)).argmin()
    flags[wh3-2:wh3+3] = 0
    #p[wh3] = np.median([p[wh3-1],p[wh3+1]])
    psd_all[indx] = p
    f_all[indx] = f
    flags_all[indx] = flags
    indx += 1024

plt.xlabel('Frequency (MHz)')
plt.ylabel('Relative power (dB)')

#%%
plt.figure(2)
plt.clf()
plt.plot(f_all,10.*np.log10(psd_all/flags_all))

plt.xlabel('Frequency (MHz)')
plt.ylabel('Relative power (dB)')
tm = time.ctime().replace(' ','_')
plt.savefig('SDRFrequencyScan_'+tm+'.png')
np.savez('SDRFrequencyScan_'+tm+'.npz',f_all=f_all,psd_all=psd_all,flags_all=flags_all,f_min=f_min,f_max=f_max,rate_best=rate_best,df=df)

sdr.close()
plt.show()

