This is the working version of the Arduino code as of 3/28/2025.  

There are a couple of numbers that are hardcoed:
- serial communication is at 115200 baud `BAUD_RATE`
- loop rate is 4 ms (250 Hz) `dt_loop`

The basic idea is that the Arduino loop continuously sends a certain set of information, namely
- the current counter value
- the number of milliseconds to complete the loop
- the last command sent
- the current azimuth in motor microsteps (convertible but not converted to angle)
- the current elevation in motor microsteps (convertible but not converted to angle)

** The analog voltage is not reported **

Commands are 12 characters long and must be enclosed in <> as `<xxxxxxxxxxxx>`

<X> is the abort command, which stops all motion, and violates the 12 character rule.

Axis / Sense / Microstep / Clock cycles per step / Number of steps

0: 'a' azimuth or 'e' elevation
1: +/-
2: m: 1/16, e: 1/8 q: 1/4 h: 1/2 f: 1
3 - 6: the number of clock cycles 
7 - 11: number of steps.  This sets the max at one go to 99999



