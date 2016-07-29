char user_input;
float flt;

#define ELEN  7  
#define AZEN  10 

#define BTX "AAA"
#define EOT "ZZZ"

//String user_input = String('initialize');

void setup() {
  // put your setup code here, to run once:
  pinMode(ELEN, OUTPUT);
  pinMode(AZEN, OUTPUT);
  digitalWrite(ELEN, HIGH); 
  digitalWrite(AZEN, HIGH); 
  Serial.begin(9600);
  Serial.println("Testing serial back and forth");
  
  Serial.println(EOT);
}

void loop() {
  int i;
  unsigned long sec0, sec;
  
  // put your main code here, to run repeatedly:
  while(Serial.available()){
      user_input = Serial.read();
      if (user_input == 'n'){
          // This is a rather stupid way of saying: 
          // wait until you hear something before proceeding
          Serial.println("Enter float: ");
          Serial.println(EOT);
          while (Serial.available()==0){ }
          flt = Serial.parseFloat();
          Serial.print("Printing input float: ");
          Serial.println(flt);
          Serial.println(EOT);
      } else if (user_input == 'a'){
          sec0 = micros();
          for (i = 0; i < 10; i++){
            Serial.println(micros() - sec0);
          }
          Serial.println(EOT);
      } 
      else {
          Serial.println("Printing user input");
          Serial.println(user_input);
          Serial.println(EOT);
      }   
  }
}
