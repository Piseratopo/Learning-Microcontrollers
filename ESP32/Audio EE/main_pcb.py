import serial
import wave
import time
import numpy as np

# --- CONFIGURATION ---
PORT = "COM7"
BAUD = 460800  # Matched to Arduino
TARGET_SAMPLE_RATE = 22050  # 22.05kHz
DURATION = 10
FLUSH_DURATION = 2
FILE_NAME = "recording_22kHz.wav"


def record_and_resample():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.1)

        print(f"--- 10-Second High-Quality Recording ({TARGET_SAMPLE_RATE}Hz) ---")

        # 1. FLUSH PHASE
        print(f"Discarding initial {FLUSH_DURATION}s of noise...")
        ser.reset_input_buffer()
        flush_start = time.time()
        while (time.time() - flush_start) < FLUSH_DURATION:
            if ser.in_waiting > 0:
                ser.read(ser.in_waiting)

        # 2. RECORD PHASE
        raw_buffer = bytearray()
        print(f"RECORDING NOW... Speak or play music!")
        start_time = time.time()

        while (time.time() - start_time) < DURATION:
            if ser.in_waiting > 0:
                raw_buffer.extend(ser.read(ser.in_waiting))

        actual_count = len(raw_buffer)
        print(f"Finished. Captured {actual_count} samples.")

        # 3. RESAMPLING LOGIC
        # This maps the actual data received to exactly 10 seconds at 22050Hz
        target_count = TARGET_SAMPLE_RATE * DURATION
        data_array = np.frombuffer(raw_buffer, dtype=np.uint8)

        indices = np.linspace(0, actual_count - 1, target_count)
        final_data = np.interp(indices, np.arange(actual_count), data_array).astype(
            np.uint8
        )

        # 4. SAVE TO WAV
        with wave.open(FILE_NAME, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(1)
            wav_file.setframerate(TARGET_SAMPLE_RATE)
            wav_file.writeframes(final_data.tobytes())

        print(f"Success! Saved as {FILE_NAME}")
        print(f"Hardware Drift: {((actual_count/target_count)-1)*100:.2f}%")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if "ser" in locals():
            ser.close()


if __name__ == "__main__":
    record_and_resample()
