import serial
import wave
import time

# --- MUST MATCH ARDUINO ---
PORT = "COM7"  # Your RS485 Adapter Port
BAUD = 115200  # Must match Serial2.begin
SAMPLE_RATE = 8000  # 8kHz
DURATION = 10  # Seconds to record


def record_audio():
    try:
        # Set timeout to slightly more than the duration
        ser = serial.Serial(PORT, BAUD, timeout=DURATION + 2)
        ser.reset_input_buffer()

        print(f"Recording {DURATION} seconds of audio...")
        print("Talk into the mic now!")

        total_samples = SAMPLE_RATE * DURATION

        # Read exactly 80,000 bytes. This will take exactly 10 seconds.
        start_time = time.time()
        audio_buffer = ser.read(total_samples)
        actual_duration = time.time() - start_time

        print(f"Captured {len(audio_buffer)} samples in {actual_duration:.2f} seconds.")

        # Save to WAV
        with wave.open("output.wav", "wb") as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(1)  # 8-bit (1 byte per sample)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_buffer)

        print("Successfully saved to 'output.wav'. Play it now!")

    except Exception as e:
        print(f"Connection Error: {e}")
    finally:
        if "ser" in locals():
            ser.close()


if __name__ == "__main__":
    record_audio()
