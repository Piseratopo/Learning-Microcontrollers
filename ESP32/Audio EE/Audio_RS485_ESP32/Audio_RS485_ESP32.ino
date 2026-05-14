#include <Arduino.h>

#define MIC_PIN 7      // Safe ADC1 pin for ESP32-S3
#define RE_DE_PIN 4    
#define RX_PIN 17
#define TX_PIN 18

const uint32_t INTERVAL = 125; // 8000Hz
uint32_t lastMicros = 0;

void setup() {
  // Use a very high baud rate. 115200 is too slow for 8kHz 
  // when you factor in the overhead of the Serial driver.
  Serial2.begin(460800, SERIAL_8N1, RX_PIN, TX_PIN);
  
  pinMode(RE_DE_PIN, OUTPUT);
  digitalWrite(RE_DE_PIN, HIGH); // Enable RS485 Transmit

  analogReadResolution(12);
  // S3 specific: ensures we are using the full 0-3.1V range
  analogSetAttenuation(ADC_11db); 
  
  delay(1000);
  lastMicros = micros();
}

void loop() {
  uint32_t now = micros();
  
  if (now - lastMicros >= INTERVAL) {
    // Incrementing by INTERVAL (instead of setting to now) 
    // prevents timing drift over time.
    lastMicros += INTERVAL; 

    int val = analogRead(MIC_PIN);
    
    // Convert 12-bit to 8-bit
    uint8_t sample = (uint8_t)(val >> 4); 

    Serial2.write(sample);
  }
}