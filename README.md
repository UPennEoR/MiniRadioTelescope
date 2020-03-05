# Mini Radio Telescope
![MRT](https://hackaday.com/wp-content/uploads/2019/10/mrt_closeup.jpg)
A computerized telescope created using a satellite TV dish and hobbyist electronic components.<br/>
This GitHub contains Arduino and Python code for the telescope.

## Hardware
### Electronics
![Electronics](https://github.com/UPennEoR/MiniRadioTelescope/blob/master/Documentation/Electronics.jpg)
* Satellite Dish (with LNB)
* Arduino Uno
* Raspberry Pi
* [Stepper Motors](https://www.sparkfun.com/products/13656)
* [Big Easy Driver](https://www.sparkfun.com/products/12859)

### RF
* [Bias Tee](https://www.minicircuits.com/WebStore/dashboard.html?model=ZFBT-282-1.5A%2B)
* [Lumped LC High Pass Filter, 910 - 3000 MHz](https://www.minicircuits.com/WebStore/dashboard.html?model=SHP-900%2B)
* [LTCC Low Pass Filter, DC - 1200 MHz, 50Ω](https://www.minicircuits.com/WebStore/dashboard.html?model=VLF-1200%2B)
* [Power Detector](https://www.minicircuits.com/WebStore/dashboard.html?model=ZX47-60LN-S%2B)
* [Low Noise Amplifier, 40 - 2600 MHz, 50Ω](https://www.minicircuits.com/WebStore/dashboard.html?model=ZX60-P105LN%2B)
* [RTL-SDR](https://www.amazon.com/RTL-SDR-Blog-RTL2832U-Software-Defined/dp/B0129EBDS2/)

[Detailed Parts List](https://docs.google.com/spreadsheets/d/1V9u7jmuFzU5uZdgKm3iKv23dL2x4DQUVWW0j8lXsqZ8/edit?usp=sharing)

## Maps
![](https://hackaday.com/wp-content/uploads/2019/10/mrt_sats.png)
![](https://github.com/UPennEoR/MiniRadioTelescope/blob/master/Documentation/MakerFaireMap.png)
![](https://github.com/UPennEoR/MiniRadioTelescope/blob/master/Documentation/SDRScan.jpg)

As of 5 April 2020, the working Arduino sketch is: MRTArduino (previously known as MRTv2)<br/>
The python code for the Pi is MRT_PY4.py


Hackaday was kind enough to do a write-up about this project: https://hackaday.com/2019/10/22/a-miniature-radio-telescope-in-every-backyard/
