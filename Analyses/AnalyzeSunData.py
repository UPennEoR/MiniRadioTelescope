#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  7 14:43:21 2017

@author: jaguirre
"""

import numpy as np
import matplotlib.pyplot as plt
from glob import glob
import ephem
import os

def readMRT(filename):
    dat = np.load(filename)
    d = {}
    for item in dat.items():
        d[item[0]] = item[1]
#   Determine active axis
    if (np.median(np.diff(d['az']))==0):
        d['aa'] = 'el'
    else:
        d['aa'] = 'az'
    return d

dat = {}
#filenames = glob('Fri_Jun_30_*.npz')
# These are the useful ones
#[s + mystring for s in mylist]
filenames = ['45:26','46:08','47:56','48:18','54:16','55:12','56:08','56:44','58:49']
filenames = ['ExampleData/Fri_Jun_30_15:'+s for s in filenames]
filenames = [s+'_2017.npz' for s in filenames]

#%%

for i,filename in enumerate(filenames):
    dat[filename] = readMRT(filename)
    d = dat[filename]
    plt.figure(i+1)
    plt.clf()
    plt.plot(d[d['aa']],d['pwr']*300./17.)
    tit = ((filename.split('/')[1]).split('.')[0]).split('_')
    plt.title(tit[0]+' '+tit[2] +' ' + tit[1]+' '+tit[4]+' '+tit[3])
    if d['aa'] == 'el':
        Direction = 'Elevation'
    else:
        Direction = 'Azimuth'
    plt.xlabel(Direction+' (deg)')
    plt.ylabel(r'Antenna Temperature (K)')#Power ($\mu$W)')
    
    
# Calibration seems to be roughly 300 K = 17 microW
# El_true = El_measured + 4. (for the 15:56:03 data)