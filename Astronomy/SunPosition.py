import numpy as np
#import matplotlib.pyplot as plt
#from astropy import units as u
#from astropy import constants as c
from astropy.time import Time
from astropy.coordinates import EarthLocation, get_sun, AltAz
#solar_system_ephemeris, EarthLocation
#from astropy.coordinates import get_body_barycentric, get_body, get_moon, get_sun, SkyCoord, AltAz
import time

Philadelphia = EarthLocation(lat='+39d57m35s',lon='-75d11m49s')
current_time = Time(time.time(), format='unix')

Sun = get_sun(current_time)
Sun_altaz = Sun.transform_to(AltAz(obstime=current_time, location=Philadelphia))

print(current_time.iso)
print('Sun Alt/Az')
print('%.2f %.2f' % (Sun_altaz.alt.deg, Sun_altaz.az.deg))

