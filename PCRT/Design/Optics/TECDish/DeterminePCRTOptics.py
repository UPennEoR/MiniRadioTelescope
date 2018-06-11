# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19 23:05:35 2016

@author: jaguirre
"""
import numpy as np
import pylab as plt
from astropy import units as u
from matplotlib.patches import Ellipse

def rot2d(x,y,ang):
    xr = x*np.cos(ang)+y*np.sin(ang)
    yr = -x*np.sin(ang)+y*np.cos(ang)
    return (xr,yr)

def dist2d(x1,x2,y1,y2):
    dx2 = np.power(x1-x2,2)
    dy2 = np.power(y1-y2,2)
    d = np.sqrt(dx2 + dy2)
    return d

# A bunch of values picked off the image
# THE KEY MEASUREMENT
# Edges of the primary
xtop = 630.
ytop = 18.
xbot = 3063.
ybot = 1568.
# Primary diameter, in pixels
D_pri_pix = dist2d(xtop,xbot,ytop,ybot)
# Separate measurement establishes the size of the primary
D_pri_m = 10.
# Meters per pixel
mperpix = D_pri_m/D_pri_pix
# The tilt (relative to the image borders) should be deducible from the above
tilt_pri = np.degrees(np.arctan(np.abs(ytop-ybot)/np.abs(xtop-xbot)))
tilt = np.radians(tilt_pri)#33.)

#Define the focal length
f_primary = 2.85
f_primary_pix = f_primary/mperpix

# Apparent vertex of the primary parabola from the image
xvert_app = 1507
yvert_app = 1303

# The equation of the primary parabola
# Given the endpoints of the parabola and the focal length, all else follows.
a_parabola = 1./(4.*f_primary_pix) #2.8e-4

# Parabola in standard form
x_pri = np.linspace(-D_pri_pix/2.,D_pri_pix/2.,num=1000)
y_pri = a_parabola * np.power(x_pri,2) 
# Rotate it
xr,yr = rot2d(x_pri,y_pri,tilt)
# For some reason, invert y
yr = -yr

# The desired shift is the offset between the known endpoint
xvert = xtop - xr[0]
yvert = ytop - yr[0]

# Shift into position 
xp = xr + xvert
#yp = yr - (ymax-yvert)
yp = yr + yvert

# Focal ocation of focus
fpx,fpy = (0,f_primary_pix)
fpx,fpy= rot2d(fpx,fpy,tilt)
fpx += xvert
fpy = -fpy + yvert

#Edges of the secondary
x_sec_top = 1806
y_sec_top = 566
x_sec_bot = 2088
y_sec_bot = 749
D_sec_pix = dist2d(x_sec_top,x_sec_bot,y_sec_top,y_sec_bot)

plt.plot([x_sec_top,x_sec_bot],[y_sec_top,y_sec_bot],'r')

# Secondary diameter
D_sec_m = D_sec_pix * mperpix
# vertex of the secondary support legs
xtri = 2090
ytri = 431

# The equation of the secondary ellipse.  
a = 400.;
b = 240.;
# Eccentricity
e = np.sqrt(1-np.power(b/a,2))
# The focus positions
f1x,f1y = (a*e,0)
f2x,f2y = (-a*e,0)
# Now transform the focus position
etilt = np.radians(90.-tilt_pri) #56.5)
f1x,f1y = rot2d(f1x,f1y,etilt) 
f2x,f2y = rot2d(f2x,f2y,etilt) 
# Want to force secondary focus to line up with
# the primary's
xe0 = fpx-f1x
ye0 = fpy-f1y


# The equation of the ellipse, transformed
xe = np.linspace(-a,a,num=1000) #-a:0.25:a;
yep = b*np.sqrt(1-np.power(xe/a,2));
yen = -yep #b.*sqrt(1-(xe.^2)./a^2);
xe = np.concatenate((xe,xe))
ye = np.concatenate((yep,yen))

xe,ye = rot2d(xe,ye,etilt)
#slide = 500.
#xe0 = xvert + slide*np.cos(etilt)
#ye0 = yvert - slide*np.sin(etilt)
xe = xe + xe0
ye = ye + ye0

f1x += xe0
f1y += ye0
f2x += xe0
f2y += ye0

# ----- 
# Plotting
# ------
im = plt.imread('PCRT_Image_for_Optics_Determination.jpg')
ymax,xmax,_ = im.shape

fig = plt.figure(1)
plt.clf()
ax = fig.add_subplot(111)
plt.imshow(im,interpolation='None')

# Diameter
plt.plot([xtop,xbot],[ytop,ybot],'r')

# Primary parabola
plt.plot(xp,yp,'r')
# Primary focus
plt.plot(fpx,fpy,'ro')
# Primary vertex
plt.plot(xvert,yvert,'ro')
plt.plot(np.array([xvert,fpx]),np.array([yvert,fpy]),'r')

# Extreme rays
s = np.linspace(0,1000,num=1000)
ang = (ytop - fpy)/(xtop-fpx)

plt.plot([xtop,fpx],[ytop,fpy],'g--')
plt.plot([xbot,fpx],[ybot,fpy],'g--')

# Figure out how tipped my viewing angle is
skew_ang = np.radians(1.4)
view_skew_ell = Ellipse(xy=(xtop+D_pri_pix*np.cos(tilt)/2,ytop+D_pri_pix*np.sin(tilt)/2), 
                        width=D_pri_pix, height=D_pri_pix*np.sin(skew_ang), 
angle=tilt_pri)
view_skew_ell.fill=False
ax.add_artist(view_skew_ell)



plt.plot(xe,ye,'c')
plt.plot(f1x,f1y,'co')
plt.plot(f2x,f2y,'co')

if True:
    plt.xlim([0,xmax])
    plt.ylim([ymax,0])
else:
    plt.xlim([1200,2200])
    plt.ylim([1500,500])

plt.show()
