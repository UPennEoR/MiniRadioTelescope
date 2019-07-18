# -*- coding: utf-8 -*-
"""
Created on Wed Jul 20 22:54:01 2016

@author: jaguirre
"""

import numpy as np
import pylab as plt
import MRTtools as mrt
reload(mrt)

az,el,v = np.loadtxt('DATA',unpack=True)
p = mrt.zx47_60(v)
N= 50
smp = np.convolve(p, np.ones((N,))/N,mode='same')
smp -= 16.
smp /= smp.max()

plt.figure(1)
plt.clf()
#plt.plot(az,p)
plt.plot(az,smp)
plt.plot([az.min(),az.max()],[0,0])
plt.plot([az.min(),az.max()],[0.5,0.5])
plt.plot([21.5,21.5],[0,1],'c')
plt.plot([34,34],[0,1],'c')
