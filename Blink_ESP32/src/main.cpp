#include <Arduino.h>

// GPIO pin for LED (ESP32-S3 DevKit uses GPIO 8 for general purpose, or GPIO 48 for built-in addressable LED)
#define LED_PIN 8

void setup() {
   // Initialize serial communication
   Serial.begin(115200);
   delay(1000);
   Serial.println("\nESP32-S3 LED Blink starting...");

   // Set LED pin as output
   pinMode(LED_PIN, OUTPUT);
}

void loop() {
   // Turn LED on
   digitalWrite(LED_PIN, HIGH);
   Serial.println("LED ON");
   delay(1000);

   // Turn LED off
   digitalWrite(LED_PIN, LOW);
   Serial.println("LED OFF");
   delay(1000);
}