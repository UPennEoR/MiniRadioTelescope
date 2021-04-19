/*
 It's not clear this code does the "right" thing when only part of the command is read on a given loop 
 Need to do more to reject ill-formed commands and clear the command buffer
 I think for this application, the writing out rate and the loop rate need to be the same, so that we get a new update on the state
 of the axis every time the step changes
 */

//Declare pin functions on Arduino DIO
#define datapin 2
#define clockpin 3
#define latchpin 4
#define ELSTP 6  // 5  ST
#define AZSTP 5  // 6  ST
#define ELEN 8 // 7 EN
#define AZEN 7 // 8 EN
#define ELIMIT 12 // lower limit switch

// Pins on the shift register
#define ELDIR 0  // 0 index of shift register
#define ELMS1 1  // 1 index of shift register
#define ELMS2 2  // 2 index of shift register
#define ELMS3 3  // 3 index of shift register
#define AZDIR 4  // 4 index of shift register
#define AZMS1 5  // 5 index of shift register
#define AZMS2 6  // 6 index of shift register
#define AZMS3 7  // 7 index of shift register
//need this one for shift register
byte data = 0;

//Variables that change which pin they they refer to depending on which axis is selected
int STP;
int DIR;
int MS1;
int MS2;
int MS3;
int EN;

/*
 Commands will have the form:

  Axis / Sense / Microstep / Clock cycles per step / Number of steps

  E/A  
 
 */

#define CMDLENGTH 12;
 
char axis = 'x', sense='x', step_mode='x';
const byte Ncps_char = 5;
const byte Nstep_char = 6;
char N_cch_char[Ncps_char] = "xxxx"; 
char number_of_steps_char[Nstep_char] = "xxxxx";
int N_cch; // Number of clock cycles (loops) per half of a step
int number_of_steps;
int i;
int NreceivedChars = 0;


const byte numChars = 32;
char receivedChars[numChars] = "xxxxxxxxxxxx";
char last_command[numChars];

boolean newData = false;

unsigned long t1, t2, dt;
unsigned long dt_loop = 4000; // microseconds; this should be fast
unsigned long counter = 0;

signed long az_steps = 0;
signed long el_steps = 0;
signed long steps[2] = {0,0};

/* 
need to have a protocol for what to do if we receive a new command while executing an existing one.
for now, let's have it be blocking ...
*/
boolean executingCmd = false; 

boolean first_half = true, transition = true;
int n_steps_remaining = 0;
int n_half = 0; 
char stepstate = 'n';
int sign = 0;
int axindx = 0;
int step_size = 0;

void setup() {
  // put your setup code here, to run once:

  // Setup of DIO pins
  pinMode(AZEN, OUTPUT);
  pinMode(ELEN, OUTPUT);
  pinMode(AZSTP, OUTPUT);
  pinMode(ELSTP, OUTPUT);
  pinMode(datapin, OUTPUT);
  pinMode(clockpin, OUTPUT);
  pinMode(latchpin, OUTPUT);
  pinMode(ELIMIT, INPUT);

  // Disable the motors by default
  digitalWrite(AZEN, HIGH);
  digitalWrite(ELEN, HIGH);

  // Finally, open serial connection
  Serial.begin(115200); //Open Serial connection for debugging
  //Serial.println("ARDUINO MRT Mk3");

}

void loop() {
  // put your main code here, to run repeatedly:

  // Get the current timestamp
  t1 = micros();

  // Look for any new commands sent
  recvWithStartEndMarkers();

  // If a new command has been sent, and we're not currently executing a command, then set various toggles to start doing stuff
  // This should be collected up into a singla ParseCommand function
  // Parse the command.  Basic error checking would make sure that right number of characters was sent
  if (newData == true){
    
    // Check to see if you've been told to abort
    if (receivedChars[0] == 'X'){

      Serial.println("Received abort");
      n_steps_remaining = 0;
      
    }  else if (executingCmd == false && NreceivedChars == 12) {

      // Serial.println("Received valid command");
      
      executingCmd = true;
      
      axis = receivedChars[0];
      // Set pins based on the axis selected
      // This should be a SetAxis command
      // Enable the axis that's about to move
      switch(axis){
        case 'a': 
          axindx = 0;
          STP = AZSTP;
          DIR = AZDIR;
          MS1 = AZMS1;
          MS2 = AZMS2;
          MS3 = AZMS3;
          EN = AZEN;
          break;
        case 'e': 
          axindx = 1;
          STP = ELSTP;
          DIR = ELDIR;
          MS1 = ELMS1;
          MS2 = ELMS2;
          MS3 = ELMS3;
          EN = ELEN;
          break;
      }
      digitalWrite(EN, LOW); // enable the axis
  
      sense = receivedChars[1];
      switch(sense){
        case '+':
          shiftWrite(DIR, LOW);
          sign = 1;
          break;
        case '-':
          shiftWrite(DIR, HIGH);
          sign = -1;
          break;
      }
     
      step_mode = receivedChars[2];
      switch(step_mode){
        
        case 'm':
          shiftWrite(MS1, HIGH); // Pulling all three high to get 1/16 step
          shiftWrite(MS2, HIGH);
          shiftWrite(MS3, HIGH);
          step_size = 1;
          break;
          
        case 'e':
          shiftWrite(MS1, HIGH); // Configuration for eighth step
          shiftWrite(MS2, HIGH);
          shiftWrite(MS3, LOW);
          step_size = 2;
          break;
  
        case 'q':
          shiftWrite(MS1, LOW); // Configuration for quarter step
          shiftWrite(MS2, HIGH);
          shiftWrite(MS3, LOW);
          step_size = 4;
          break;
          
        case 'h':
          shiftWrite(MS1, HIGH); // Configuration for half step
          shiftWrite(MS2, LOW);
          shiftWrite(MS3, LOW);
          step_size = 8;
          break;
  
        case 'f':
          shiftWrite(MS1, LOW); // Pulling all three low to full step
          shiftWrite(MS2, LOW);
          shiftWrite(MS3, LOW);
          step_size = 16;
          break; 
          
      }
      
      // This seems very silly
      for (i=0; i < Ncps_char-1; i++){
        N_cch_char[i] = receivedChars[i+3];
      }
      N_cch_char[Ncps_char-1] = '\0';
      for (i=0; i < Nstep_char-1; i++){
        number_of_steps_char[i] = receivedChars[i+7];
      }
      number_of_steps_char[Nstep_char-1] = '\0';
      
      N_cch = atoi(N_cch_char);
      number_of_steps = atoi(number_of_steps_char);
  
      n_half = N_cch;
      n_steps_remaining = number_of_steps;
      
      
    }
  }
  newData = false;

  if (n_steps_remaining > 0){
  
    // Axis was already enabled when the command was received; no need to do it at every step
    //executingCmd = true;

    if (n_half < N_cch){
        transition = false;
    }
    
    if (transition){
        if(first_half){
          /* 
           *  This is where we increment the step counter: once the transition up happens, the motion has happened.
          */
            stepstate = 'u';
            digitalWrite(STP,HIGH); //Trigger one step forward
            steps[axindx] += sign * step_size;
            
        }
        if (!first_half){
            stepstate = 'd';
            digitalWrite(STP,LOW); //Pull step pin low so it can be triggered again
        }
    } else{
        stepstate='s';
    }
    
    n_half--;
    
    if(n_half == 0 && first_half){
        // We've finished the first half
        n_half = N_cch;
        first_half = false;
        transition = true;
    }
        
    if (n_half == 0 && !first_half){
        // We've finished the second half
        n_half = N_cch;
        first_half = true;
        transition = true;
        n_steps_remaining--;
    }
     
  } else {

    digitalWrite(EN, HIGH); // disable the axis when not moving.  could be a problem ...
    executingCmd = false;
    
  }

  // Write out the data for this loop
  ReportState();
  
  // Increment the counter
  counter++;

  // Now that everything is done, check the time again
  waitRemainingTime();
  
}

void recvWithStartEndMarkers() {
  
    static boolean recvInProgress = false;
    static byte ndx = 0;
    char startMarker = '<';
    char endMarker = '>';
    char rc;
 
    while (Serial.available() > 0 && newData == false) {
        rc = Serial.read();

        if (recvInProgress == true) {
            if (rc != endMarker) {
                receivedChars[ndx] = rc;
                ndx++;
                if (ndx >= numChars) {
                    ndx = numChars - 1;
                }
            }
            else {
                receivedChars[ndx] = '\0'; // terminate the string
                recvInProgress = false;
                NreceivedChars = ndx;
                ndx = 0;
                newData = true;
            }
        }

        else if (rc == startMarker) {
            recvInProgress = true;
        }
    }
}


void waitRemainingTime(){
  t2 = micros();
  dt = t2 - t1;

  while(dt < dt_loop){
    t2 = micros();
    dt = t2 - t1;
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
    // Write out the data for this loop
  Serial.print(counter);
  Serial.print(" ");
  Serial.print(dt/1000.); // Prints the actual dt to complete the loop
  Serial.print(" ");
  //Serial.print(axis); 
  //Serial.print(" ");
  //Serial.print(sense); 
  //Serial.print(" ");
  //Serial.print(step_mode); 
  //Serial.print(" ");
  //Serial.print(N_cch); 
  //Serial.print(" ");
  //Serial.print(number_of_steps); 
  //Serial.print(" ");
  //Serial.print(NreceivedChars);
  //Serial.print(" ");
  Serial.print(receivedChars);
  //Serial.print(" NSR ");
  //Serial.print(n_steps_remaining);
  //Serial.print(" FH ");
  //Serial.print(first_half);
  //Serial.print(" T ");
  //Serial.print(transition);
  //Serial.print(" S ");
  //Serial.print(stepstate);
  Serial.print(" AZ ");
  Serial.print(steps[0]);
  Serial.print(" EL ");
  Serial.println(steps[1]);

}
