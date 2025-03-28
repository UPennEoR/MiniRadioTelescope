This is the working version of the Arduino code as of 3/28/2025.  

I'm not sure how one would figure this out with knowing it in advance, but currently the serial communication is at 115200 baud.

The basic idea is that the Arduino loop continuously sends a certain set of information.

Commands are 12 characters long and must be enclosed in <> as <xxxxxxxxxxxx>

<X> is the abort command, which stops all motion

Axis / Sense / Microstep / Clock cycles per step / Number of steps

0: 'a' azimuth or 'e' elevation
1: +/-
2: m: 1/16, e: 1/8 q: 1/4 h: 1/2 f: 1




