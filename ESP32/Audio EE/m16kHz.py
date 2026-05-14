import serial
import wave
import time
import numpy as np

# --- CONFIGURATION ---
PORT = "COM7"
BAUD = 460800
DURATION = 10
FLUSH_DURATION = 2
FILE_NAME = "recording_16kHz.wav"


def record_and_save():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.1)

        print(f"--- 10-Second Smart Recording ---")

        # 1. FLUSH PHASE
        print(f"Discarding initial {FLUSH_DURATION}s noise...")
        ser.reset_input_buffer()
        flush_start = time.time()
        while (time.time() - flush_start) < FLUSH_DURATION:
            if ser.in_waiting > 0:
                ser.read(ser.in_waiting)

        # 2. RECORD PHASE
        raw_buffer = bytearray()
        print(f"RECORDING NOW...")
        start_time = time.time()

        while (time.time() - start_time) < DURATION:
            if ser.in_waiting > 0:
                raw_buffer.extend(ser.read(ser.in_waiting))

        end_time = time.time()
        actual_duration = end_time - start_time
        actual_count = len(raw_buffer)

        # 3. CALCULATE ACTUAL SAMPLE RATE
        # Instead of squishing data, we find out how fast the Arduino actually sent it
        captured_sample_rate = int(actual_count / actual_duration)

        print(f"Finished.")
        print(f"Captured {actual_count} samples in {actual_duration:.2f} seconds.")
        print(f"Effective Sample Rate: {captured_sample_rate} Hz")

        # 4. SAVE TO WAV
        with wave.open(FILE_NAME, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(1)
            wav_file.setframerate(captured_sample_rate)  # Use the real rate
            wav_file.writeframes(raw_buffer)

        print(f"Success! Saved as {FILE_NAME}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if "ser" in locals():
            ser.close()


if __name__ == "__main__":
    record_and_save()
