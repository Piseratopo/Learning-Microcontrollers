#define TEST_PIN_1 17
#define TEST_PIN_2 18

void setup() {
//   pinMode(4, OUTPUT);
//   digitalWrite(4, LOW); // Force RE/DE HIGH (Disables MAX3485 Receiver)
  pinMode(TEST_PIN_1, OUTPUT);
  pinMode(TEST_PIN_2, OUTPUT);
}

void loop() {
  digitalWrite(TEST_PIN_1, HIGH);
  digitalWrite(TEST_PIN_2, HIGH);
  delay(2000);
  digitalWrite(TEST_PIN_1, LOW);
  digitalWrite(TEST_PIN_2, LOW);
  delay(2000);
}