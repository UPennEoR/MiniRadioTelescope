#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 18 14:49:43 2017

@author: jaguirre
"""

import numpy as np
import matplotlib.pyplot as plt

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

def plotScan(scan):
    x = scan[scan['aa']]
    pwr = scan['pwr']
    plt.plot(x,pwr)
    N = 10
    plt.plot(x,np.convolve(pwr, np.ones((N,))/N, mode='same'),'r')
    return

scan_far = readMRT('Tue_Jul_18_14:58:21_2017.npz')
plotScan(scan_far)