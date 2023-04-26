PulseOximeter pox;
Adafruit_GPS GPS;
void setup() {
  pinMode(2, INPUT);
  pinMode(3, OUTPUT);
  pinMode(A1, INPUT);
  // Humidity Sensor Input
  pinMode(7, INPUT);
  Serial.begin(9600);
}
void loop() {
  if (Serial.available() > 0) {
      if (pox.begin()) {
          string spO2_res = pox.getSpO2();
          string hb_res = pox.getHeartRate();
          Serial.println("Oxygen percentage: " + spO2_res + "; Heart rate: " + hb_res);
      }
      digitalWrite(3, HIGH);
  } else{
      Serial.println("No data");
      digitalWrite(3, LOW);
  }
  // GPS Data
  if (Serial.available() > 0) {
      string gpsResult = GPS.read();
      Serial.println("GPS Data: " + gpsResult);
  } else {
      Serial.println("No data");
  }
  // Humidity Data
  float h = digitalRead(7);
  Serial.print("Humidity: ");
  Serial.println(h);
  // Temperature Data
  float temp = analogRead(A1) / 1023.0 * 5.0 * 100.0;
  Serial.println("temperature: " + to_string(temp));
  Serial.println("");
  delay(1000);
}