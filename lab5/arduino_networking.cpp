PulseOximeter pox;
Adafruit_GPS GPS;

// Declare vars
int temperaturePin = A1;
int pulsoxPin = 2;
int ledPin = 3;
int humidityPin = 7;
int networkPin = 0;
long arduinoID = random();
string output_str;

// Setup function with pins
void setup() {
  pinMode(pulsoxPin, INPUT);
  pinMode(ledPin, OUTPUT);
  pinMode(temperaturePin, INPUT);
  pinMode(humidityPin, INPUT);
  pinMode(0, OUTPUT);
  Serial.begin(9600);
}
void loop() {
    // Read data if available
    if (Serial.available() > 0) {
        // Humidity Data
        float h = digitalRead(humidityPin);
        // Temperature Data
        float temp = analogRead(temperaturePin) / 1023.0 * 5.0 * 100.0;
        // GPS data
        string gpsResult = GPS.read();
        output_str = "|| Arduino ID: " + to_string(arduinoID) + " | Humidity: " + to_string(h) + " | Temp: " + to_string(temp) + " | GPS: " + gpsResult;
        // PulseOximiter
        if (pox.begin()) {
            string spO2_res = pox.getSpO2();
            string hb_res = pox.getHeartRate();
            output_str += " | sp02: " + spO2_res + " | Heart Rate: " + hb_res;
        } 
        digitalWrite(ledPin, HIGH);
        
    } else {
        digitalWrite(ledPin, LOW);
        //Serial.println("no_data");
    }
    // Send message to other Arduino
    Serial.sendMessage(networkPin, output_str, to_string(9600));
    // Print output
    Serial.println("");
    Serial.println("Printed by sender: " + output_str);
    Serial.println("");
    // delay
    delay(1000);

}