// Version 10 August 2016

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
//Declare pin functions on Arduino

#define ELSTP 2  // 2  ST
#define ELDIR 3  // 3  DR
#define ELMS1 4  // 4  M1
#define ELMS2 5  // 5  M2
#define ELMS3 6  // 6  M3
#define ELEN  7  // 7  EN

#define AZSTP 9  // 2   ST
#define AZDIR 8  // 3   DR
#define AZMS1 11 // 4  M1
#define AZMS2 12 // 5  M2
#define AZMS3 13 // 6  M3
#define AZEN  10 // 7  EN

#define GEAR_RATIO 8
#define DEGREES_PER_STEP 1.8
#define MICRO_STEPS 16

#define BTX "AAA"
#define EOT "ZZZ"
#define BDTX "BDTX"
#define EDTX "EDTX"

int STP; 
int DIR; 
int MS1; 
int MS2; 
int MS3; 
int EN;  

//Declare variables for functions
char user_input;
int x;
int y;
// int state;

// Ugh.  Don't actually HAVE the current state of either axis

// Current position of elevation axis
float elCurrDeg;
int elCurrSteps;
int elCurrMicroSteps;
// Current position of azimuth axis
float azCurrDeg;
int azCurrSteps;
int azCurrMicroSteps;

char stepping_mode; 
float degrees_to_turn; 
int rot_sense;
char current_axis;

int analogPin = 0;
int val;
float voltage;

float NormAdd, MicroAdd;

void setup(){
  
  pinMode(AZSTP, OUTPUT);
  pinMode(AZDIR, OUTPUT);
  pinMode(AZMS1, OUTPUT);
  pinMode(AZMS2, OUTPUT);
  pinMode(AZMS3, OUTPUT);
  pinMode(AZEN, OUTPUT);
  pinMode(ELSTP, OUTPUT);
  pinMode(ELDIR, OUTPUT);
  pinMode(ELMS1, OUTPUT);
  pinMode(ELMS2, OUTPUT);
  pinMode(ELMS3, OUTPUT);
  pinMode(ELEN, OUTPUT);
  SetAxis('A');
  resetBEDPins(); //Set step, direction, microstep and enable pins to default states
  Serial.begin(115200); //Open Serial connection for debugging
  Serial.println("Begin motor control");
  Serial.println();
  PrintMenu();
  elCurrSteps = 0;
  elCurrDeg = 0;
  elCurrMicroSteps = 0;
  azCurrSteps = 0;
  azCurrDeg = 0;
  azCurrMicroSteps = 0;
  stepping_mode = 'N';
  rot_sense = 1;
}

//Main loop
void loop() {
  while(Serial.available()){
      user_input = Serial.read(); //Read user input and trigger appropriate function
      if((user_input == 'E') || (user_input == 'D'))
      {
        SetEnable(user_input);
      } else if ((user_input == 'F') || (user_input == 'R'))
      {
        SetDirection(user_input);
      }
      else if ((user_input == 'A') || (user_input == 'L'))
      {
        SetAxis(user_input);
      }
      else if((user_input == 'N') || (user_input == 'M'))
      {
        SetStepMode(user_input);
      }
      else if(user_input == 'S')
      {
        while (Serial.available()==0){ }
        degrees_to_turn = Serial.parseFloat();
        RotateDegrees(degrees_to_turn);
      }
      else if(user_input == 'Z'){
        elCurrSteps = 0;
        elCurrDeg = 0;
        elCurrMicroSteps = 0;
      }
      else
      {
        Serial.println("Invalid option entered.");
      }
      //resetBEDPins();
      PrintState();
      PrintMenu();
  }
}

void PrintMenu()
{
  //Print function list for user selection
  Serial.println("Enter motor control option:");
  Serial.println("E for Enable; D for Disable");
  Serial.println("F for Forward; R for Reverse");
  Serial.println("A for azimuth; L for elevation");
  Serial.println("N for normal steps; M for microsteps");
  Serial.println("S turn a number of decimal degrees");
  Serial.println("Z to zero the angle counter");
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
  Serial.println("Current position");
  Serial.print("AZ: ");
  Serial.print(azCurrDeg);
  Serial.print("  EL: ");
  Serial.println(elCurrDeg);
  Serial.println();
}

//Reset Big Easy Driver pins to default states
void resetBEDPins()
{
  digitalWrite(STP, LOW);
  digitalWrite(DIR, LOW);
  digitalWrite(MS1, LOW);
  digitalWrite(MS2, LOW);
  digitalWrite(MS3, LOW);
  digitalWrite(EN, HIGH); // Motor is off at power-on
}

void SetEnable(char enable)
{
  if (enable == 'E')
  {
    digitalWrite(EN, LOW); 
    Serial.println("Motor enabled.");
  }
  else if (enable == 'D')
  {
    digitalWrite(EN, HIGH); 
    Serial.println("Motor disabled.");
  }
}

void SetDirection(char direction)
{
  if (direction == 'F')
  {
    digitalWrite(DIR, LOW); //Pull direction pin low to move "forward"
    rot_sense = 1;
    Serial.println("Direction set to forward.");
  }
  else if (direction == 'R')
  {
    digitalWrite(DIR, HIGH); //Pull direction pin low to move "backward"
    rot_sense = -1;
    Serial.println("Direction set to backward."); 
  }
}

void SetAxis(char axis)
{
  if (axis == 'A'){
    STP = AZSTP;
    DIR = AZDIR;
    MS1 = AZMS1;
    MS2 = AZMS2;
    MS3 = AZMS3;
    EN = AZEN;
    current_axis = 'A';
  } else if (axis == 'L'){
    STP = ELSTP;
    DIR = ELDIR;
    MS1 = ELMS1;
    MS2 = ELMS2;
    MS3 = ELMS3;
    EN = ELEN;
    current_axis = 'L';
  }
  Serial.print("Set axis to ");
  if (current_axis=='A'){
    Serial.println("AZ");
  } else{
    Serial.println("EL");
  }
  
}

void SetStepMode(char mode)
{
  if (mode == 'N') // Default
  {
    digitalWrite(MS1, LOW);
    digitalWrite(MS2, LOW); 
    digitalWrite(MS3, LOW);
    Serial.println("Default step set.");
  } else if (mode == 'M')
  {
    digitalWrite(MS1, HIGH); //Pull MS1,MS2, and MS3 high to set logic to 1/16th microstep resolution
    digitalWrite(MS2, HIGH);
    digitalWrite(MS3, HIGH); 
    Serial.println("Micro (1/16) step set.");   
  }
  stepping_mode = mode;
}

void TakeSteps(int steps)
{
  //Serial.println(STP);
  for(x= 1; x<steps; x++)  
  {
    digitalWrite(STP,HIGH); //Trigger one step forward
    delay(2);
    digitalWrite(STP,LOW); //Pull step pin low so it can be triggered again
    delay(2);

    if (stepping_mode == 'M'){
      NormAdd = 1./16.;
      MicroAdd = 1;
    } 
    else {
      NormAdd = 1;
      MicroAdd = 16; 
    }
    if (current_axis == 'L'){
      elCurrSteps += rot_sense * NormAdd;
      elCurrMicroSteps += rot_sense * MicroAdd;
      elCurrDeg += rot_sense * Steps2Degrees(1,stepping_mode);
    } else{
      azCurrSteps += rot_sense * NormAdd;
      azCurrMicroSteps += rot_sense * MicroAdd;
      azCurrDeg += rot_sense * Steps2Degrees(1,stepping_mode);
    }

    // Read the ADC for the radiometer
    val = analogRead(analogPin);
    voltage = 5.0*val/1024.;
    Serial.print(azCurrDeg,5);
    Serial.print("  ");
    Serial.print(elCurrDeg,5);
    Serial.print("  ");
    Serial.println(voltage,5);
  }
}

int Degrees2Steps(float deg, char mode){
  int nSteps;
  nSteps = int(deg / DEGREES_PER_STEP * GEAR_RATIO);
  if (mode == 'M'){
    nSteps *= MICRO_STEPS;
  }
  return nSteps;
}

float Steps2Degrees(int steps, char mode){
  float deg;
  deg = float(steps)*DEGREES_PER_STEP/float(GEAR_RATIO);
  if (mode == 'M'){
    deg /= float(MICRO_STEPS);
  }
  return deg;
}

void RotateDegrees(float deg)
{
  int nSteps, nMicroSteps;
  //float actual_degrees;
  
  //Serial.print("Turning ");
  //Serial.print(deg);
  //Serial.println(" degrees.");
  
  // Calculate both steps and microsteps
  nSteps = Degrees2Steps(deg, 'N');
  nMicroSteps = Degrees2Steps(deg, 'M');

  //Serial.println(BTX);
  /* Which thing is commanded and how actual degrees are calculated depends on 
  the mode */
  if (stepping_mode == 'N')
  {
    Serial.println(BDTX);
    TakeSteps(nSteps);
    Serial.println(EDTX);
    //actual_degrees = Steps2Degrees(nSteps,'N');
  } else
  {
    Serial.println(BDTX);
    TakeSteps(nMicroSteps);
    Serial.println(EDTX);
    //actual_degrees = Steps2Degrees(nMicroSteps,'M');
  }
}

