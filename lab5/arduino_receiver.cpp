void setup() { 
	Serial.begin(9600);
}

void loop() { 
	if (Serial.availableMessage() != 0){
        string availMsg = Serial.readMessage();
        Serial.println("");
        Serial.println("##### Printed by receiver: " + availMsg + " #####");
        Serial.println("");
    }
    delay(2000);
}