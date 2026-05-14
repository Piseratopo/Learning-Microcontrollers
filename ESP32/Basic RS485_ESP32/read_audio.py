import serial
import time
import sys

# --- CONFIGURATION ---
PORT = "COM7"  # Change this to your RS485 Adapter port
BAUD = 115200  # Must match Serial2.begin in Arduino
SILENCE_LEVEL = 128  # The middle point of an 8-bit sample (0-255)


def run_visualizer():

    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.1)
        # Clear the buffer to start fresh
        ser.reset_input_buffer()

        print(f"--- Connected to {PORT} ---")
        print("Displaying Real-time Mic Level (Press Ctrl+C to stop)")

        # Throttling logic: We only update the screen every X samples
        # to prevent the terminal from lagging.
        samples_to_skip = 200
        counter = 0

        while True:
            # Read one byte from the RS485 stream
            raw_byte = ser.read(1)

            if raw_byte:
                counter += 1

                # Only update the visual bar every 200 samples
                if counter >= samples_to_skip:
                    counter = 0

                    # Convert byte to integer (0-255)
                    sample_value = int.from_bytes(raw_byte, byteorder="big")

                    # Calculate volume (distance from the center/silence)
                    amplitude = abs(sample_value - SILENCE_LEVEL)

                    # Scale the bar (Max amplitude is 128)
                    bar_length = int(amplitude / 2)
                    bar = "█" * bar_length

                    # Use \r (carriage return) to keep the bar on a single line
                    sys.stdout.write(f"\rVal: {sample_value:3} | {bar:<64}")
                    sys.stdout.flush()

    except serial.SerialException as e:
        print(f"\nError: {e}")
    except KeyboardInterrupt:
        print("\nStopping Visualizer...")
    finally:
        if "ser" in locals() and ser.is_open:
            ser.close()


if __name__ == "__main__":
    run_visualizer()
