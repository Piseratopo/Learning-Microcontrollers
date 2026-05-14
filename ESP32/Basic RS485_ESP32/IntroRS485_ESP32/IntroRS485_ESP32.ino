#define RX_PIN 17
#define TX_PIN 18
#define RE_DE_PIN 4

void setup() {
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, RX_PIN, TX_PIN);
  
  pinMode(RE_DE_PIN, OUTPUT);
  digitalWrite(RE_DE_PIN, LOW); // Start in Receive mode (safer)
  delay(500);
}

void loop() {
  // 1. Switch to Transmit mode
  digitalWrite(RE_DE_PIN, HIGH);
  delay(10); // Give the MAX3485 a tiny moment to stabilize

  // 2. Send the data
  String msg = "Hello from ESP32!";
  Serial2.println(msg); 
  
  // 3. IMPORTANT: Wait for transmission to finish
  Serial2.flush(); 

  // 5. Debug to USB
  Serial.println("Sent: " + msg);
  
  delay(2000); // Increased delay to make it easier to see
}