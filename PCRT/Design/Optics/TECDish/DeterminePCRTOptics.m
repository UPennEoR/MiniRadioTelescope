im = imread('PCRT_Image_for_Optics_Determination.jpg');
[ymax,xmax,~] = size(im)
%imtool(im)
% 635,27 to 3059,1566
xtop = 635;
ytop = 18;
xbot = 3059;
ybot = 1566;
x_sec_top = 1806;
y_sec_top = 566;
x_sec_bot = 2088;
y_sec_bot = 749;
D_pix = sqrt((xtop-xbot)^2 + (ytop-ybot)^2);
D_sec_pix = sqrt((x_sec_top-x_sec_bot)^2 + (y_sec_top-y_sec_bot)^2); %337.;
mperpix = 10./D_pix;
D_sec_m = D_sec_pix * mperpix;
xtri = 2090;
ytri = 431;
xvert = 1507;
yvert = 1303;
%%
x = -D_pix/2:D_pix/2;
a_parabola = 2.8e-4;
y = a_parabola * x.^2; %ymax - 7e-5 * x.^2;
tilt = 33.;
xr = x.*cosd(tilt)+y.*sind(tilt);
yr = -x.*sind(tilt)+y.*cosd(tilt);
yr = ymax - yr;
xp = xr + xvert;
yp = yr - (ymax-yvert);
%%
a = 400;
b = 220;
% Eccentricity
e = sqrt(1-b^2/a^2);
focus1 = [a*e,0]';
focus2 = -focus1;
xe = -a:0.25:a;
yep = b.*sqrt(1-(xe.^2)./a^2);
yen = -b.*sqrt(1-(xe.^2)./a^2);
xe = [xe,xe];
ye = [yep,yen];
etilt = 56.5;
Rot_e = [[cosd(etilt),sind(etilt)];[-sind(etilt),cosd(etilt)]];
xr = xe.*cosd(etilt)+ye.*sind(etilt);
yr = -xe.*sind(etilt)+ye.*cosd(etilt);
xe = xr;
ye = yr;
slide = 500.;
xe0 = 12 + xvert + slide*cosd(etilt);
ye0 = yvert - slide*sind(etilt);
xe = xe + xe0;
ye = ye + ye0;
focus1 = Rot_e * focus1 + [xe0,ye0]';
focus2 = Rot_e * focus2 + [xe0,ye0]';
% Primary focal length should be distance from vertex to focus1
f_primary_pix = sqrt((xvert-focus1(1))^2 + (yvert-focus1(2))^2);
%f_gregorian_pix =
% I'm getting that the different measures of the primary focal length are
% basicaly 3 +/- 0.1 meters
f_primary = 3.;
platescale_primary = 1./f_primary * 180./pi * 60. / 100.;
f_eff = (2*a*e/D_sec_pix*D_pix)*mperpix;
platescale_gregorian = 1./f_eff * 180./pi * 60. / 100.;
%%
%clf
imshow(im)
impixelinfo
hold on
% Approximate diameter
plot([xtop,xbot],[ytop,ybot],'r','LineWidth',2)
plot([x_sec_top,x_sec_bot],[y_sec_top,y_sec_bot],'r','LineWidth',2)
% Intersection of  tripod (2090,431) to vertex (1507,1303)
plot([xtri,xvert],[ytri,yvert],'r','LineWidth',2)
plot(xp,yp,'LineWidth',2)
plot(xe,ye,'g','LineWidth',2)
plot(focus1(1),focus1(2),'x','LineWidth',2)
plot(focus2(1),focus2(2),'x','LineWidth',2)
plot([focus2(1),x_sec_top],[focus2(2),y_sec_top])
plot(xvert,yvert,'co')
hold off
%imdistline

