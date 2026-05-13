#include <Arduino.h>

void setup() {
   // No need to set baud rate for Native USB, but we keep it for compatibility
   Serial.begin(115200);

   // Wait for Serial to initialize (required for native USB)
   while (!Serial) {
      delay(10);
   }

   Serial.println("ESP32-S3 Native USB Initialized!");
}

void loop() {
   Serial.println("Alive on GPIO 19/20...");
   delay(2000);
}