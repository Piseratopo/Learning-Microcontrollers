import serial
import time

PORT = "COM5"
BAUD_RATE = 9600

try:
    ser = serial.Serial(PORT, BAUD_RATE, timeout=1)

    # Clear any garbage data currently in the USB adapter's buffer
    ser.reset_input_buffer()
    print(f"Connected to {PORT}. Waiting for clean data...")

    while True:
        if ser.in_waiting > 0:
            try:
                # Read until a newline character is found
                line = ser.readline().decode("utf-8").strip()
                if line:
                    print(f"Received: {line}")
            except UnicodeDecodeError:
                # This handles cases where a partial byte is read
                print("Received incomplete data, skipping...")

        time.sleep(0.01)

except serial.SerialException as e:
    print(f"Error: {e}")
except KeyboardInterrupt:
    print("\nStopping...")
finally:
    if "ser" in locals() and ser.is_open:
        ser.close()
