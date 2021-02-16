/*****************************************************************
LSM9DS1_Basic_I2C.ino
SFE_LSM9DS1 Library Simple Example Code - I2C Interface
Jim Lindblom @ SparkFun Electronics
Original Creation Date: April 30, 2015
https://github.com/sparkfun/LSM9DS1_Breakout

The LSM9DS1 is a versatile 9DOF sensor. It has a built-in
accelerometer, gyroscope, and magnetometer. Very cool! Plus it
functions over either SPI or I2C.

This Arduino sketch is a demo of the simple side of the
SFE_LSM9DS1 library. It'll demo the following:
* How to create a LSM9DS1 object, using a constructor (global
  variables section).
* How to use the begin() function of the LSM9DS1 class.
* How to read the gyroscope, accelerometer, and magnetometer
  using the readGryo(), readAccel(), readMag() functions and 
  the gx, gy, gz, ax, ay, az, mx, my, and mz variables.
* How to calculate actual acceleration, rotation speed, 
  magnetic field strength using the calcAccel(), calcGyro() 
  and calcMag() functions.
* How to use the data from the LSM9DS1 to calculate 
  orientation and heading.

Hardware setup: This library supports communicating with the
LSM9DS1 over either I2C or SPI. This example demonstrates how
to use I2C. The pin-out is as follows:
  LSM9DS1 --------- Arduino
   SCL ---------- SCL (A5 on older 'Duinos')
   SDA ---------- SDA (A4 on older 'Duinos')
   VDD ------------- 3.3V
   GND ------------- GND
(CSG, CSXM, SDOG, and SDOXM should all be pulled high. 
Jumpers on the breakout board will do this for you.)

The LSM9DS1 has a maximum voltage of 3.6V. Make sure you power it
off the 3.3V rail! I2C pins are open-drain, so you'll be 
(mostly) safe connecting the LSM9DS1's SCL and SDA pins 
directly to the Arduino.

Development environment specifics:
  IDE: Arduino 1.6.3
  Hardware Platform: SparkFun Redboard
  LSM9DS1 Breakout Version: 1.0

This code is beerware. If you see me (or any other SparkFun 
employee) at the local, and you've found our code helpful, 
please buy us a round!

Distributed as-is; no warranty is given.
*****************************************************************/
// The SFE_LSM9DS1 library requires both Wire and SPI be
// included BEFORE including the 9DS1 library.
#include <Wire.h>
#include <SPI.h>
#include <SparkFunLSM9DS1.h>

//////////////////////////
// LSM9DS1 Library Init //
//////////////////////////
// Use the LSM9DS1 class to create an object. [imu] can be
// named anything, we'll refer to that throught the sketch.
LSM9DS1 imu;

///////////////////////
// Example I2C Setup //
///////////////////////
// SDO_XM and SDO_G are both pulled high, so our addresses are:
#define LSM9DS1_M  0x1E // Would be 0x1C if SDO_M is LOW
#define LSM9DS1_AG  0x6B // Would be 0x6A if SDO_AG is LOW

////////////////////////////
// Sketch Output Settings //
////////////////////////////
#define PRINT_CALCULATED
//#define PRINT_RAW

// Earth's magnetic field varies by location. Add or subtract 
// a declination to get a more accurate heading. Calculate 
// your's here:
// http://www.ngdc.noaa.gov/geomag-web/#declination
#define DECLINATION -8.58 // Declination (degrees) in Boulder, CO.
/****************************************************************************** 
SparkFun Big Easy Driver Basic Demo
Toni Klopfenstein @ SparkFun Electronics
February 2015
https://github.com/sparkfun/Big_Easy_Driver

Simple demo sketch to demonstrate how 5 digital pins can drive a bipolar stepper motor,
using the Big Easy Driver (https://www.sparkfun.com/products/12859). Also shows the ability to change
microstep size, and direction of motor movement.

Development environment specifics:
Written in Arduino 1.6.0

This code is beerware; if you see me (or any other SparkFun employee) at the local, and you've found our code helpful, please buy us a round!
Distributed as-is; no warranty is given.

Example based off of demos by Brian Schmalz (designer of the Big Easy Driver).
http://www.schmalzhaus.com/EasyDriver/Examples/EasyDriverExamples.html
******************************************************************************/

//Define gear ratios and step sizes

#define AZ_GEAR_RATIO 8
#define EL_GEAR_RATIO 20
#define DEGREES_PER_STEP 1.8
#define HALF_STEPS 2
#define QUARTER_STEPS 4
#define EIGHTH_STEPS 8
#define MICRO_STEPS 16

//Variables to signal start and stop of transmition from arduino
//#define BTX "AAA"
#define EOT "ZZZ"
#define BDTX "BDTX"
#define EDTX "EDTX"

#define BLCKAVG 16

//Declare pin functions on Arduino and shift register
#define datapin 2
#define clockpin 3
#define latchpin 4
#define ELSTP 6  // 5  ST
#define AZSTP 5  // 6  ST
#define ELEN 8 // 7 EN
#define AZEN 7 // 8 EN
#define ELDIR 0  // 0 index of shift register
#define ELMS1 1  // 1 index of shift register
#define ELMS2 2  // 2 index of shift register
#define ELMS3 3  // 3 index of shift register
#define AZDIR 4  // 4 index of shift register
#define AZMS1 5  // 5 index of shift register
#define AZMS2 6  // 6 index of shift register
#define AZMS3 7  // 7 index of shift register
#define ELIMIT 12 // lower limit switch

//Variables that toggle between azimuth and elevation depending on which axis is selected
int STP;
int DIR;
int MS1;
int MS2;
int MS3;
int EN;
int GEAR_RATIO;

int analogPin = 0;
/*
 * will need more of these for limit switch and photogate
 */

// Define the telescope state variables, reported after every command
// Current position of elevation axis
float elCurrDeg;
int elCurrSteps;
int elCurrHalfSteps;
int elCurrQuarterSteps;
int elCurrEighthSteps;
int elCurrMicroSteps;
// Current position of azimuth axis
float azCurrDeg;
int azCurrSteps;
int azCurrHalfSteps;
int azCurrQuarterSteps;
int azCurrEighthSteps;
int azCurrMicroSteps;
// Mode
char current_axis;
char step_mode;
int rot_sense;
int el_enable;
int az_enable;
char last_command_valid;
int el_limit;

//Declare other variables
char user_input;
float degrees_to_turn; 
int val;
float voltage;
float NormAdd, HalfAdd, QuarterAdd, EighthAdd, MicroAdd;

//need this one for shift register
byte data = 0;

void setup()
{
  pinMode(AZEN, OUTPUT);
  pinMode(ELEN, OUTPUT);
  pinMode(AZSTP, OUTPUT);
  pinMode(ELSTP, OUTPUT);
  pinMode(datapin, OUTPUT);
  pinMode(clockpin, OUTPUT);
  pinMode(latchpin, OUTPUT);
  pinMode(ELIMIT, INPUT);
  /*
   * Add stuff here to setup the pins for limit switch and photo gate
   */

  SetAxis('L');
  resetBEDPins();
  delay(1);
  SetAxis('A');
  resetBEDPins();
  
  // Initialize stepping variables
  elCurrSteps = 0;
  elCurrHalfSteps = 0;
  elCurrQuarterSteps = 0;
  elCurrEighthSteps = 0;
  elCurrMicroSteps = 0;
  elCurrDeg = 0;
  
  azCurrSteps = 0;
  azCurrHalfSteps = 0;
  azCurrQuarterSteps = 0;
  azCurrEighthSteps = 0;
  azCurrMicroSteps = 0;
  azCurrDeg = 0;

  // Convention: 1 = CCW, Inc; 0 = CW, Dec
  rot_sense = 1;

  InitializeLSM9DS1();
  
  // Finally, open serial connection
  Serial.begin(115200); //Open Serial connection for debugging
  Serial.println("ARDUINO MRT");
  ReportState();
}

void loop()
{
  while(Serial.available())
  {
    user_input = Serial.read(); // Reads the user's input to trigger function
    if((user_input == 'E') || (user_input == 'D'))
    {
      last_command_valid = 'Y';
      SetEnable(user_input);
    }
    else if ((user_input == 'A') || (user_input == 'L'))
    {
      last_command_valid = 'Y';
      SetAxis(user_input);
    }
    else if ((user_input == 'F') || (user_input == 'R'))
    {
      last_command_valid = 'Y';
      SetDirection(user_input);
    }
    else if (user_input == 'S')
    {
      last_command_valid = 'Y';
      while (Serial.available()==0){ }
      degrees_to_turn = Serial.parseFloat();
      RotateDegrees(degrees_to_turn);
    }
    else if ((user_input == 'm') || (user_input == 'e') || (user_input == 'q') || (user_input == 'h') || (user_input == 'f'))
    {
      last_command_valid == 'Y';
      SetStepMode(user_input);
    }
    else
    {
      last_command_valid = 'N';
    }
    if(digitalRead(ELIMIT) == HIGH)
    {
      el_limit = 1;
    }
    else
    {
      el_limit = 0;
    }
    ReportState();
  }
}

void shiftWrite(int desiredPin, boolean desiredState)
{

// This function lets you make the shift register outputs
// HIGH or LOW in exactly the same way that you use digitalWrite().

  bitWrite(data,desiredPin,desiredState); //Change desired bit to 0 or 1 in "data"

  // Now we'll actually send that data to the shift register.
  // The shiftOut() function does all the hard work of
  // manipulating the data and clock pins to move the data
  // into the shift register:

  shiftOut(datapin, clockpin, MSBFIRST, data); //Send "data" to the shift register

  //Toggle the latchPin to make "data" appear at the outputs
  digitalWrite(latchpin, HIGH); 
  digitalWrite(latchpin, LOW); 
}


void ReportState()
{
  Serial.print(last_command_valid);
  Serial.print(" ");
  Serial.print(elCurrDeg,4);
  Serial.print(" ");
  //Serial.print(elCurrSteps);
  //Serial.print(" ");
  Serial.print(elCurrMicroSteps);
  Serial.print(" ");
  Serial.print(azCurrDeg,4);
  Serial.print(" ");
  //Serial.print(elCurrSteps);
  //Serial.print(" ");
  Serial.print(azCurrMicroSteps);
  Serial.print(" ");
  Serial.print(current_axis);
  Serial.print(" ");
  Serial.print(step_mode);
  Serial.print(" ");
  Serial.print(rot_sense);
  Serial.print(" ");
  Serial.print(el_enable);
  Serial.print(" ");
  Serial.print(az_enable);
  Serial.print(" ");
  Serial.print(voltage,4);
  Serial.print(" ");
  Serial.print(el_limit);
  Serial.print(" ");
  printAccel(); // Print "A: ax, ay, az
  printMag();   // Print "M: mx, my, mz"
  // Print the heading and orientation for fun!
  // Call print attitude. The LSM9DS1's magnetometer x and y
  // axes are opposite to the accelerometer, so my and mx are
  // substituted for each other.
  printAttitude(imu.ax, imu.ay, imu.az, -imu.my, -imu.mx, imu.mz);
  Serial.println();
  Serial.println(EOT);
}

void PrintState()
{
  Serial.println();
  Serial.print("Active axis: ");
  if (current_axis=='A'){
    Serial.println("AZ");
  } else{
    Serial.println("EL");
  }
  Serial.print("Rotation sense: ");
  // Ugly.  Gotta have a better way of knowing the internal state
  if (current_axis=='A'){
    if (rot_sense==1){
      Serial.println("CCW");
    } else {
      Serial.println("CW");
    }
  } else{
    if (rot_sense ==1){
      Serial.println("Inc");
    } else {
      Serial.println("Dec");
    }
  }
  Serial.println("Current position");
  Serial.print("AZ: ");
  Serial.print(azCurrDeg);
  Serial.print("  EL: ");
  Serial.println(elCurrDeg);
  Serial.println();
}

void resetBEDPins()
{
  digitalWrite(datapin, LOW);
  digitalWrite(clockpin, LOW);
  digitalWrite(STP, LOW);
  SetEnable('E'); // Motors are on at power-on
  //SetStepMode('m'); // Motors in microstepping mode by default
  SetDirection('F'); // Motor direction is forward by default
  /*
   * Add stuff here to reset the limit switch and photogate pins
   */
}

void SetAxis(char axis)
{
  if (axis == 'A')
  {
    STP = AZSTP;
    DIR = AZDIR;
    MS1 = AZMS1;
    MS2 = AZMS2;
    MS3 = AZMS3;
    EN = AZEN;
    GEAR_RATIO = AZ_GEAR_RATIO;
    current_axis = 'A';
  }
  else if (axis == 'L')
  {
    STP = ELSTP;
    DIR = ELDIR;
    MS1 = ELMS1;
    MS2 = ELMS2;
    MS3 = ELMS3;
    EN = ELEN;
    GEAR_RATIO = EL_GEAR_RATIO;
    current_axis = 'L';
  }
  SetStepMode('m');
  SetDirection('F');
}

// Enables or Disables BOTH motors
void SetEnable(char enable)
{
  if (enable == 'E')
  {
    digitalWrite(EN, LOW);
    if (current_axis == 'L')
    {
    el_enable = 1;
    }
    else
    {
     az_enable = 1;
    }
  }
  else if (enable == 'D')
  {
    digitalWrite(EN, HIGH);
    if (current_axis == 'L')
    {
    el_enable = 0;
    }
    else
    {
     az_enable = 0;
    }
  }
}

// Sets the direction of BOTH motors
void SetDirection(char direction)
{
  if (direction == 'F')
  {
    shiftWrite(DIR, LOW);
    rot_sense = 1;
  }
  else if (direction == 'R')
  {
    shiftWrite(DIR, HIGH);
    rot_sense = -1;
  }
}

// Sets step mode of BOTH motors
void SetStepMode(char mode)
{
  if (mode == 'm') // Default
  {
    shiftWrite(MS1, HIGH); // Pulling all three high to get 1/16 step
    shiftWrite(MS2, HIGH);
    shiftWrite(MS3, HIGH);
    step_mode = 'm';
    //Serial.println("1/16 step set.");
  }
  else if (mode == 'e')
  {
    shiftWrite(MS1, HIGH); // Configuration for eighth step
    shiftWrite(MS2, HIGH);
    shiftWrite(MS3, LOW);
    step_mode = 'e';
    //Serial.println("1/8 step set.");
  }
  else if (mode == 'q')
  {
    shiftWrite(MS1, LOW); // Configuration for quarter step
    shiftWrite(MS2, HIGH);
    shiftWrite(MS3, LOW);
    step_mode = 'q';
    //Serial.println("1/4 step set.");
  }
  else if (mode == 'h')
  {
    shiftWrite(MS1, HIGH); // Configuration for half step
    shiftWrite(MS2, LOW);
    shiftWrite(MS3, LOW);
    step_mode = 'h';
    //Serial.println("1/2 step set.");
  }
  else if (mode == 'f')
  {
    shiftWrite(MS1, LOW); // Pulling all three low to full step
    shiftWrite(MS2, LOW);
    shiftWrite(MS3, LOW);
    step_mode = 'f';
    //Serial.println("Full step set.");
  }
}

float ReadRadioADC(int ndata)
{
  int cnt;
  voltage = 0.;
  for(cnt= 1; cnt<ndata; cnt++)  
  {
    // Read the ADC for the radiometer
    val = analogRead(analogPin);
    voltage += 5.0*val/1024.;
  }
  voltage /= ndata;
  return voltage;
}

void TakeSteps(int steps)
{
  long x;
  float voltaccum[BLCKAVG];
  int avg, cnt = 0;
  
  for(x= 1; x<steps; x++)  
  {
    digitalWrite(STP,HIGH); //Trigger one step forward
    delay(1);
    digitalWrite(STP,LOW); //Pull step pin low so it can be triggered again
    delay(1);

    if (step_mode == 'm')
    {
      NormAdd = 1./16.;
      MicroAdd = 1;
    } 
    else if (step_mode == 'e')
    {
      NormAdd = 1./8.;
      MicroAdd = 2; 
    }
    else if (step_mode == 'q')
    {
      NormAdd = 1./4.;
      MicroAdd = 4; 
    }
    else if (step_mode == 'h')
    {
      NormAdd = 1./2.;
      MicroAdd = 8; 
    }
    else
    {
      NormAdd = 1;
      MicroAdd = 16; 
    }
    if (current_axis == 'L'){
      elCurrSteps += rot_sense * NormAdd;
      elCurrMicroSteps += rot_sense * MicroAdd;
      elCurrDeg += rot_sense * Steps2Degrees(1,step_mode);
    } else{
      azCurrSteps += rot_sense * NormAdd;
      azCurrMicroSteps += rot_sense * MicroAdd;
      azCurrDeg += rot_sense * Steps2Degrees(1,step_mode);
    }

    // Read the ADC for the radiometer
    voltage = ReadRadioADC(10);
    voltaccum[cnt] = voltage;
    cnt++;
    if (x%BLCKAVG == 0){
      voltage = 0.;
      cnt = 0;
      for(avg=1; avg<BLCKAVG; avg++){
        voltage += voltaccum[avg];
      }
      voltage /= float(BLCKAVG);
      ReportState();
    }
  }
}

int Degrees2Steps(float deg, char mode)
{
  int nSteps;
  nSteps = int(deg / DEGREES_PER_STEP * GEAR_RATIO);
  if (mode == 'm')
  {
    nSteps *= MICRO_STEPS;
  }
  else if (mode == 'e')
  {
    nSteps *= EIGHTH_STEPS;
  }
  else if (mode == 'q')
  {
    nSteps *= QUARTER_STEPS;
  }
  else if (mode == 'h')
  {
    nSteps *= HALF_STEPS;
  }
  return nSteps;
}

float Steps2Degrees(int steps, char mode)
{
  float deg;
  deg = float(steps)*DEGREES_PER_STEP/float(GEAR_RATIO);
  if (mode == 'm')
  {
    deg /= float(MICRO_STEPS);
  }
  else if (mode == 'e')
  {
    deg /= float(EIGHTH_STEPS);
  }
  else if (mode == 'q')
  {
    deg /= float(QUARTER_STEPS);
  }
  else if (mode == 'h')
  {
    deg /= float(HALF_STEPS);
  }
  return deg;
}

void RotateDegrees(float deg)
{
  int nSteps, nHalfSteps, nQuarterSteps, nEighthSteps, nMicroSteps;
  
  // Calculate all step sizes
  nSteps = Degrees2Steps(deg, 'f');
  nHalfSteps = Degrees2Steps(deg, 'h');
  nQuarterSteps = Degrees2Steps(deg, 'q');
  nEighthSteps = Degrees2Steps(deg, 'e');
  nMicroSteps = Degrees2Steps(deg, 'm');

  /* Which thing is commanded and how actual degrees are calculated depends on 
  the mode */
  if (step_mode == 'f')
  {
    Serial.println(BDTX);
    Serial.println(EOT);
    TakeSteps(nSteps);
    Serial.println(EDTX);
    Serial.println(EOT);
  } 
  else if (step_mode == 'h')
  {
    Serial.println(BDTX);
    Serial.println(EOT);
    TakeSteps(nHalfSteps);
    Serial.println(EDTX);
    Serial.println(EOT);
  }
  else if (step_mode == 'q')
  {
    Serial.println(BDTX);
    Serial.println(EOT);
    TakeSteps(nQuarterSteps);
    Serial.println(EDTX);
    Serial.println(EOT);
  }
  else if (step_mode == 'e')
  {
    Serial.println(BDTX);
    Serial.println(EOT);
    TakeSteps(nEighthSteps);
    Serial.println(EDTX);
    Serial.println(EOT);
  }
  else
  {
    Serial.println(BDTX);
    Serial.println(EOT);
    TakeSteps(nMicroSteps);
    Serial.println(EDTX);
    Serial.println(EOT);
  }
}

/*********************/
/* LSM9DS1 Functions */
/*********************/

void InitializeLSM9DS1(){
  // Before initializing the IMU, there are a few settings
  // we may need to adjust. Use the settings struct to set
  // the device's communication mode and addresses:
  imu.settings.device.commInterface = IMU_MODE_I2C;
  imu.settings.device.mAddress = LSM9DS1_M;
  imu.settings.device.agAddress = LSM9DS1_AG;
  // The above lines will only take effect AFTER calling
  // imu.begin(), which verifies communication with the IMU
  // and turns it on.
  if (!imu.begin())
  {
    Serial.println("Failed to communicate with LSM9DS1.");
    Serial.println("Double-check wiring.");
    Serial.println("Default settings in this sketch will " \
                  "work for an out of the box LSM9DS1 " \
                  "Breakout, but may need to be modified " \
                  "if the board jumpers are.");
    //while (1)
    //  ;
  }
}

void printGyro()
{
  // To read from the gyroscope, you must first call the
  // readGyro() function. When this exits, it'll update the
  // gx, gy, and gz variables with the most current data.
  imu.readGyro();
  
  // Now we can use the gx, gy, and gz variables as we please.
  // Either print them as raw ADC values, or calculated in DPS.
  // Serial.print("G: ");
#ifdef PRINT_CALCULATED
  // If you want to print calculated values, you can use the
  // calcGyro helper function to convert a raw ADC value to
  // DPS. Give the function the value that you want to convert.
  Serial.print(imu.calcGyro(imu.gx), 4);
  Serial.print(", ");
  Serial.print(imu.calcGyro(imu.gy), 4);
  Serial.print(", ");
  Serial.print(imu.calcGyro(imu.gz), 4);
  // Serial.println(" deg/s");
#elif defined PRINT_RAW
  Serial.print(imu.gx);
  Serial.print(", ");
  Serial.print(imu.gy);
  Serial.print(", ");
  Serial.println(imu.gz);
#endif
}

void printAccel()
{
  // To read from the accelerometer, you must first call the
  // readAccel() function. When this exits, it'll update the
  // ax, ay, and az variables with the most current data.
  imu.readAccel();
  
  // Now we can use the ax, ay, and az variables as we please.
  // Either print them as raw ADC values, or calculated in g's.
  // Serial.print("A: ");
#ifdef PRINT_CALCULATED
  // If you want to print calculated values, you can use the
  // calcAccel helper function to convert a raw ADC value to
  // g's. Give the function the value that you want to convert.
  Serial.print(imu.calcAccel(imu.ax), 4);
  Serial.print(" ");
  Serial.print(imu.calcAccel(imu.ay), 4);
  Serial.print(" ");
  Serial.print(imu.calcAccel(imu.az), 4);
  Serial.print(" ");
  //Serial.println(" g");
#elif defined PRINT_RAW 
  Serial.print(imu.ax);
  Serial.print(", ");
  Serial.print(imu.ay);
  Serial.print(", ");
  Serial.println(imu.az);
#endif

}

void printMag()
{
  // To read from the magnetometer, you must first call the
  // readMag() function. When this exits, it'll update the
  // mx, my, and mz variables with the most current data.
  imu.readMag();
  
  // Now we can use the mx, my, and mz variables as we please.
  // Either print them as raw ADC values, or calculated in Gauss.
  // Serial.print("M: ");
#ifdef PRINT_CALCULATED
  // If you want to print calculated values, you can use the
  // calcMag helper function to convert a raw ADC value to
  // Gauss. Give the function the value that you want to convert.
  Serial.print(imu.calcMag(imu.mx), 4);
  Serial.print(" ");
  Serial.print(imu.calcMag(imu.my), 4);
  Serial.print(" ");
  Serial.print(imu.calcMag(imu.mz), 4);
  Serial.print(" ");
  //Serial.println(" gauss");
#elif defined PRINT_RAW
  Serial.print(imu.mx);
  Serial.print(", ");
  Serial.print(imu.my);
  Serial.print(", ");
  Serial.println(imu.mz);
#endif
}

// Calculate pitch, roll, and heading.
// Pitch/roll calculations take from this app note:
// http://cache.freescale.com/files/sensors/doc/app_note/AN3461.pdf?fpsp=1
// Heading calculations taken from this app note:
// http://www51.honeywell.com/aero/common/documents/myaerospacecatalog-documents/Defense_Brochures-documents/Magnetic__Literature_Application_notes-documents/AN203_Compass_Heading_Using_Magnetometers.pdf
void printAttitude(
float ax, float ay, float az, float mx, float my, float mz)
{
  float roll = atan2(ay, az);
  float pitch = atan2(-ax, sqrt(ay * ay + az * az));
  
  float heading;
  if (my == 0)
    heading = (mx < 0) ? 180.0 : 0;
  else
    heading = atan2(mx, my);
    
  heading -= DECLINATION * PI / 180;
  
  if (heading > PI) heading -= (2 * PI);
  else if (heading < -PI) heading += (2 * PI);
  else if (heading < 0) heading += 2 * PI;
  
  // Convert everything from radians to degrees:
  heading *= 180.0 / PI;
  pitch *= 180.0 / PI;
  roll  *= 180.0 / PI;
  
  //Serial.print("Pitch, Roll: ");
  Serial.print(pitch, 2);
  Serial.print(" ");
  Serial.print(roll, 2);
  Serial.print(" ");
  //Serial.print("Heading: "); 
  Serial.print(heading, 2);
}
