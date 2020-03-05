// Version last used: 14 December 2016

//Declare pin mappings on Arduino
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

// Serial communication bytes
#define BTX "AAA"
#define EOT "ZZZ"
#define BDTX "BDTX"
#define EDTX "EDTX"

#define RXADC 0 

//Declare variables for functions
char user_input;
int x;
int y;
// int state;

// Define radiometer input
//int analogPin = 0;
int val;
float voltage;
int NDataPts;

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

  // Turn motors off
  digitalWrite(ELEN, HIGH); 
  digitalWrite(AZEN, HIGH); 
  
  // Open serial connection
  Serial.begin(115200); //Open Serial connection for debugging
  Serial.println("ARDUINO MRT");
  //Serial.println(EOT);
  PrintMenu();
 
}

//Main loop
void loop() {
  while(Serial.available()){
      user_input = Serial.read(); //Read user input and trigger appropriate function
      if(user_input == 'X')
      {
        while (Serial.available()==0){ }
        NDataPts = Serial.parseInt();
        ReadRadADC(NDataPts);
      }
      else
      {
        Serial.println("Invalid option entered.");
        Serial.println(EOT);
      }
      PrintMenu();
  }
}

void PrintMenu()
{
  //Print function list for user selection
  Serial.println("Enter X to take receiver (RX) data");
  Serial.println();
  Serial.println(EOT);
}

void ReadRadADC(int ndata)
{
  Serial.println(BDTX);
  for(x= 1; x<ndata; x++)  
  {
    // Read the ADC for the radiometer
    val = analogRead(RXADC);
    voltage = 5.0*val/1024.;
    Serial.println(voltage,5);
  }
  Serial.println(EDTX);
}

