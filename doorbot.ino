/* Artifactory Doorbot - Arduino code to connect to reader
 * and relays.
 *
 * Andrew Elwell <Amdrew.Elwell@gmail.com>
 *  Nov 2016
 */


/* Hardware Config - Via IRC with Lt_Lemming
 *  "I've not done the diagram yet, been too busy building it
 *  RFID is soft serial on Pin 2
 *  button on the box is pulled high on Pin 3 via 10K resistor
 *  Relays are 8, 9, 10 & 11
 *  pins 4 and 5 now wired for door with a common 5v pulled up via 10k resistor
 *  so one should always be high, and if both go low we know something is wrong"
 *
 *  http://gerblook.org/pcb/Vx2DYUBo5HQAF4LjZUSib3
 */


const int RFID = 2;
const int Bell = 3;
const int DoorA = 4;
const int DoorB = 5;
const int Relay1 =  8; // doorstrike
const int Relay2 =  9;
const int Relay3 = 10;
const int Relay4 = 11;


#include <SoftwareSerial.h>
SoftwareSerial rfid(RFID, 13); // RX and TX - RFID is read only so use a 'spare' pin for TX

int doorbell = 1 ;
int doorA = 0;
int doorB = 0;
int i;
int incomingByte = 0;

// checkcard() variables
int  val = 0;
char code[10];
int bytesread = 0;


void setup() {
  rfid.begin(9600);    // start serial to RFID reader
  Serial.begin(9600);  // start serial to Pi

  pinMode(Bell, INPUT);
  pinMode(DoorA, INPUT);
  pinMode(DoorB, INPUT);
  pinMode(Relay1, OUTPUT);
  pinMode(Relay2, OUTPUT);
  pinMode(Relay3, OUTPUT);
  pinMode(Relay4, OUTPUT);

}

void readcard() // ideally this would return value?
{
  if ((val = rfid.read()) == 2)  {
    bytesread = 0;
    while (bytesread < 10) {
      if ( rfid.available() > 0) {
        val = rfid.read();
        if ((val == 2) || (val == 3)) { // if header or stop bytes before the 10 digit reading
          break;                        // stop reading
        }
        code[bytesread] = val;          // add the digit
        bytesread++;                    // ready to read next digit
      }
    }
    if (bytesread == 10) {              // if 10 digit read is complete
      Serial.print("RFID: ");           // who needs stinkin checksums
      Serial.println(code);               // print the TAG code
    }
    bytesread = 0;
  }
}

void loop() {
  if ( Serial.available() > 0) { // got something on serial line
    int inByte = Serial.read();
    // single quotes to get the ASCII value for the character.
    // ie; 'a' = 97, 'b' = 98, and so forth:
    // UPPERCASE: ON, lowercase OFF.
    switch (inByte) {
      case 'A':
        digitalWrite(Relay1, HIGH);
        Serial.print("Relay1: ");
        Serial.println(digitalRead(Relay1));
        break;
      case 'a':
        digitalWrite(Relay1, LOW);
        Serial.print("Relay1: ");
        Serial.println(digitalRead(Relay1));
        break;
      case 'B':
        digitalWrite(Relay2, HIGH);
        Serial.print("Relay2: ");
        Serial.println(digitalRead(Relay2));
        break;
      case 'b':
        digitalWrite(Relay2, LOW);
        Serial.print("Relay2: ");
        Serial.println(digitalRead(Relay2));
        break;
      case 'C':
        digitalWrite(Relay3, HIGH);
        Serial.print("Relay3: ");
        Serial.println(digitalRead(Relay3));
        break;
      case 'c':
        digitalWrite(Relay3, LOW);
        Serial.print("Relay3: ");
        Serial.println(digitalRead(Relay3));
        break;
      case 'D':
        digitalWrite(Relay4, HIGH);
        Serial.print("Relay4: ");
        Serial.println(digitalRead(Relay4));
        break;
      case 'd':
        digitalWrite(Relay4, LOW);
        Serial.print("Relay4: ");
        Serial.println(digitalRead(Relay4));
        break;

      default:
        // return state of all relays and inputs:
        Serial.println(PINB, BIN);
        /* prints say 101011
            maps to Rly 4321
            So, 4,2,1 are on, 3 is off
        */
        Serial.println(PIND, BIN);
    }

  }
  // grab all the digital inputs
  doorbell = digitalRead(Bell);
  doorA = digitalRead(DoorA);
  doorB = digitalRead(DoorB);


  //and process
  readcard();


}
