import serial
import serial.tools.list_ports
import time

TARGET_PORT = "COM7"  # Change to your RS485 Adapter port
BAUD_RATE = 9600


def run_rs485_monitor():
    try:
        # We set a longer timeout (2.1 seconds) so it waits for the ESP32
        ser = serial.Serial(TARGET_PORT, BAUD_RATE, timeout=2.1)
        print(f"--- Connected to {TARGET_PORT} ---")

        while True:
            # readline() waits until it sees a '\n' (Newline)
            line_bytes = ser.readline()

            if line_bytes:
                try:
                    # Decode and strip the \r\n characters for a clean print
                    clean_line = line_bytes.decode("utf-8").strip()
                    if clean_line:
                        print(f"[TEXT]: {clean_line}")
                except UnicodeDecodeError:
                    print(f"[RAW HEX]: {line_bytes.hex(' ')}")

    except serial.SerialException as e:
        print(f"ERROR: {e}")
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        if "ser" in locals() and ser.is_open:
            ser.close()


if __name__ == "__main__":
    run_rs485_monitor()
