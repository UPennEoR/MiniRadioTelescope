char user_input;
float flt;

#define ELEN  7  
#define AZEN  10 

#define BTX "BDTX"
#define ETX "EDTX"
#define RCVD 'R'
#define EOT "ZZZ"

int analogPin = 0;
int x, val;

//String user_input = String('initialize');

void setup() {
  // put your setup code here, to run once:
  pinMode(ELEN, OUTPUT);
  pinMode(AZEN, OUTPUT);
  digitalWrite(ELEN, HIGH); 
  digitalWrite(AZEN, HIGH); 
  Serial.begin(115200);
  //
  Serial.println("ARDUINO MRT");
  Serial.println(EOT);
  
}

void loop() {
  int i;
  unsigned long sec0, sec;
  
  // put your main code here, to run repeatedly:
  while(Serial.available()){
      user_input = Serial.read();
      if (user_input == 'n'){
          //
          //Serial.println("Enter number of data points to transmit: ");
          //Serial.println(EOT);
          while (Serial.available()==0){ }
          flt = Serial.parseFloat();
          for(x=1; x<=int(flt); x++){
            Serial.print("Sample ");
            Serial.print(x);
            Serial.print(" of ");
            Serial.println(int(flt));
            Handshake();
          }
          Serial.println(EOT);
      }  
      else {
          Serial.println("Invalid option");
          Serial.println(EOT);
      }   
  }
}

void Handshake(){
  char rcvd_val;
  boolean received;
  
  Serial.println(BTX);
  val = analogRead(analogPin);
  Serial.println(val);
  Serial.println(ETX);
  received = false;
  while(!received){
    //Serial.println("Waiting for verification");
    while (Serial.available()==0){ }
    rcvd_val = Serial.read();
    //Serial.println(rcvd_val);
    //Serial.println(received);
    if (rcvd_val == 'R'){
      //Serial.println("Transmission verified");
      received=true;
      //Serial.println(received);
    }
  }
}

