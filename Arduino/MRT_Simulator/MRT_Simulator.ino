// Current elevation position
float elCurrDeg = 3;
int elCurrSteps;
int elCurrMicroSteps;
// Current azimuth position
float azCurrDeg = -1;
int azCurrSteps;
int azCurrMicroSteps;
// Mode
char current_axis='A';
char step_mode='M';
int el_enable = false, az_enable = false;
float voltage;
char angleMode = 'A';

String input;

#define MAX_BUF 64

char buffer[MAX_BUF];
long sofar = 0;

struct coord {
  long A;
  long E;
  long F;
};

struct index {
  long ca;
  long ce;
  long cf;
};

void setup() {
  Serial.begin(115200);
  Serial.println("Arduino MRT");
  ReportPosition();
}

void loop() {
  while(Serial.available()) {
    char c = Serial.read();
//    Serial.print(c);
    if(sofar < MAX_BUF) {
      buffer[sofar++] = c;
    } else {
      Serial.print(F("Buffer Overflow"));
      serialReady();
      break;
    }

    if(c == ';') {
      Serial.print(F("\r\n"));
      buffer[sofar-1] = 0;
      String cmd = String(buffer);
      processCommand(cmd);
      serialReady();
    }
  }
//  while(Serial.available()) {
//    input = Serial.readString();
//    input.trim();
//    if (input.startsWith("G0")) {
//      Serial.println("Command Received: G0 Rapid Movement");
//      
//    } else if (input.startsWith("G1")) {
//      Serial.println("Command Received: G1 Programmed Movement");
//    } else if (input.startsWith("G28")) {
//      Serial.println("Command Received: G28 Home");
//    } else if (input.startsWith("G30")) {
//      Serial.println("Command Received: G30 Starting Position");
//    } else if (input.startsWith("G90")) {
//      Serial.println("Command Received: G90 Absolute Angles");
//      angleMode = 'A';
//    } else if (input.startsWith("G91")) {
//      Serial.println("Command Received: G91 Relative Angles");
//      angleMode = 'R';
//    } else if (input.startsWith("G92")) {
//      Serial.println("Command Received: G92 Set Current Position");
//    } else if (input.startsWith("M17")) {
//      Serial.println("Command Received: M17 Enable Motors");
//    } else if (input.startsWith("M18")) {
//      Serial.println("Command Received: M18 Disable Motors");
//    } else if (input.startsWith("M84")) {
//      Serial.println("Command Received: M84 Disable after inactivity");
//    } else if (input.startsWith("M105")) {
//      Serial.println("Command Received: M105 Report Current Readings");
//      ReportReadings();
//    } else if (input.startsWith("M114")) {
//      Serial.println("Command Received: M114 Report Current Position");
//      ReportPosition();
//    } else if (input.startsWith("M350")) {
//      Serial.println("Command Received: M350 Microstepping Mode");
//    } else if (input == "") {
//      Serial.println("Blank");
//    } else {
//      Serial.println("Invalid Command: " + input);
//    }
//  }
}

void serialReady() {
  sofar = 0;
  Serial.println(F("> "));
}

void processCommand(String str) {
  if(str.charAt(0) == 'G' || str.charAt(0) == 'g') {
    long c1 = str.substring(1,3).toInt();

    switch(c1) {
      case 00: 
        Serial.println("Command Received: G0 Rapid Movement");
        break;
      case 01:
        Serial.println("Command Received: G1 Programmed Movement");
        break;
      case 28:
        Serial.println("Command Received: G28 Home");
        break;
      case 30:
        Serial.println("Command Received: G30 Starting Position");
        break;
      case 90:
        Serial.println("Command Received: G90 Absolute Angles");
        break;
      case 91:
        Serial.println("Command Received: G92 Set Current Position");
        break;
      case 92:
        Serial.println("Command Received: G92 Set Current Position");
        break;
    }
  }

  if(str.charAt(0) == 'M' || str.charAt(0) == 'm') {
    long c1 = str.substring(1,4).toInt();

    switch(c1) {
      case 17:
        Serial.println("Command Received: M17 Enable Motors");
        break;
      case 18:
        Serial.println("Command Received: M18 Disable Motors");
        break;
      case 84:
        Serial.println("Command Received: M84 Disable after inactivity");
        break;
      case 105:
        Serial.println("Command Received: M105 Report Current Readings");
        ReportReadings();
        break;
      case 114:
        Serial.println("Command Received: M114 Report Current Position");
        ReportPosition();
        break;
      case 350:
        Serial.println("Command Received: M350 Microstepping Mode");
        break;        
    }
  } 
}

void ReportPosition() {
  Serial.print(elCurrDeg,4);
  Serial.print(" ");
  Serial.print(elCurrMicroSteps);
  Serial.print(" ");
  Serial.print(azCurrDeg,4);
  Serial.print(" ");
  Serial.print(azCurrMicroSteps);
  Serial.print(" ");
  Serial.print(current_axis);
  Serial.print(" ");
  Serial.print(step_mode);
  Serial.print(" ");
  Serial.print(el_enable);
  Serial.print(" ");
  Serial.print(az_enable);
  Serial.println();
}

void ReportReadings() {
  voltage = 50 * (pow(2.,(-pow(azCurrDeg,2.)/1000.)) + pow(2.,(-pow(elCurrDeg,2.)/1000.)));
  Serial.print(elCurrDeg,4);
  Serial.print(" ");
  Serial.print(azCurrDeg,4);
  Serial.print(" ");
  Serial.print(voltage,4);
  Serial.println();
}
