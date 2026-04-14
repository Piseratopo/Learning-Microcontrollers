#include <Arduino.h>

int LED_PIN = PC13;
int delayTime = 1000;

void setup() {
   pinMode(LED_PIN, OUTPUT);
}

void loop() {
   digitalWrite(LED_PIN, HIGH);
   delay(delayTime);
   digitalWrite(LED_PIN, LOW);
   delay(delayTime);
}