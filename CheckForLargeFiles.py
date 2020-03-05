import numpy as np
from astropy import units as u
from astropy import constants as c
from glob import glob
import os
from os import path

large_data_path = './Data/'

def FileSize(filename):
    statinfo = os.stat(filename)
    return statinfo.st_size*u.byte

# Recursively get everything
files = [f for f in glob('**',recursive=True) if path.isfile(f)]
# But ignore what's already in LargeData
files = [f for f in files if (f.split('/')[0] != 'Data')]

large_size = 49.9*u.Mbyte

for f in files:
    fs = FileSize(f).to(u.Mbyte)
    fn = f.split('/')[-1]
    if (fs > large_size):
        print('Moving ',fn,' which is ',FileSize(f).to(u.Mbyte))
        os.rename(f,large_data_path+fn)

