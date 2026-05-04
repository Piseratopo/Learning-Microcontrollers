#include <Adafruit_NeoPixel.h>

// On this specific board, the RGB LED is usually on Pin 48
#define RGB_PIN 48 
#define NUM_PIXELS 1

// Initialize the NeoPixel library
Adafruit_NeoPixel pixels(NUM_PIXELS, RGB_PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  pixels.begin(); // Initialize the LED
  pixels.setBrightness(50); // Set brightness (0-255) - don't set to 255 or it's blinding!
}

void loop() {
  // Red
  pixels.setPixelColor(0, pixels.Color(255, 0, 0));
  pixels.show();
  delay(1000);

  // Green
  pixels.setPixelColor(0, pixels.Color(0, 255, 0));
  pixels.show();
  delay(1000);

  // Blue
  pixels.setPixelColor(0, pixels.Color(0, 0, 255));
  pixels.show();
  delay(1000);

  // Rainbow Cycle effect
  for(long firstPixelHue = 0; firstPixelHue < 5*65536; firstPixelHue += 256) {
    pixels.setPixelColor(0, pixels.gamma32(pixels.ColorHSV(firstPixelHue)));
    pixels.show();
    delay(5);
  }
}