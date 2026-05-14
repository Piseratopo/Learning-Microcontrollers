import serial
import wave
import time
import numpy as np
import msvcrt  # Windows-specific for detecting keypress

# --- CONFIGURATION ---
PORT = "COM7"
BAUD = 460800
FLUSH_DURATION = 2
NOISE_SAMPLE_DURATION = 2
FILE_NAME = "manual_recording_cleaned.wav"


def apply_noise_reduction(signal, noise):
    """Subtracts noise frequency profile from the signal."""
    sig_f = signal.astype(float) - 127.0
    noi_f = noise.astype(float) - 127.0

    sig_fft = np.fft.rfft(sig_f)
    # Match noise length to signal length for the subtraction mask
    noi_fft = np.fft.rfft(noi_f, n=len(sig_f))

    sig_mag = np.abs(sig_fft)
    sig_phase = np.angle(sig_fft)
    noi_mag = np.abs(noi_fft)

    # Calculate noise mask (Adjust 1.5 to 2.0 if hiss is still audible)
    noise_level = np.mean(noi_mag) * 1.5
    reduced_mag = np.maximum(sig_mag - noise_level, 0)

    cleaned_fft = reduced_mag * np.exp(1j * sig_phase)
    cleaned_signal = np.fft.irfft(cleaned_fft)

    return np.clip(cleaned_signal + 127.0, 0, 255).astype(np.uint8)


def record_audio():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.1)

        print("\n--- Manual Noise-Canceling Recorder ---")
        input(">> Press [ENTER] to begin the sequence...")

        # 1. FLUSH PHASE
        print(f"1. Flushing hardware noise ({FLUSH_DURATION}s)...")
        ser.reset_input_buffer()
        t_end = time.time() + FLUSH_DURATION
        while time.time() < t_end:
            ser.read(ser.in_waiting)

        # 2. NOISE SAMPLING
        print(f"2. Sampling BACKGROUND NOISE ({NOISE_SAMPLE_DURATION}s)... BE QUIET!")
        noise_buffer = bytearray()
        t_end = time.time() + NOISE_SAMPLE_DURATION
        while time.time() < t_end:
            if ser.in_waiting > 0:
                noise_buffer.extend(ser.read(ser.in_waiting))

        # 3. ACTUAL RECORDING
        print("3. RECORDING NOW... Speak now!")
        print(">> Press [ENTER] to STOP recording.")

        # Clear the stdin buffer so it doesn't immediately trigger stop
        while msvcrt.kbhit():
            msvcrt.getch()

        rec_buffer = bytearray()
        start_time = time.time()

        # Loop until Enter is pressed
        while True:
            if ser.in_waiting > 0:
                rec_buffer.extend(ser.read(ser.in_waiting))

            if msvcrt.kbhit():
                if msvcrt.getch() in [b"\r", b"\n"]:  # Enter key
                    break

        actual_duration = time.time() - start_time
        actual_count = len(rec_buffer)
        captured_sample_rate = int(actual_count / actual_duration)

        print(f"\nStopped. Captured {actual_count} samples in {actual_duration:.2f}s.")
        print(f"Effective Sample Rate: {captured_sample_rate} Hz")

        # 4. PROCESSING
        print("4. Cleaning audio...")
        noise_data = np.frombuffer(noise_buffer, dtype=np.uint8)
        signal_data = np.frombuffer(rec_buffer, dtype=np.uint8)
        cleaned_data = apply_noise_reduction(signal_data, noise_data)

        # 5. SAVE
        with wave.open(FILE_NAME, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(1)
            wav_file.setframerate(captured_sample_rate)
            wav_file.writeframes(cleaned_data.tobytes())

        print(f"Success! Saved as {FILE_NAME}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if "ser" in locals():
            ser.close()


if __name__ == "__main__":
    record_audio()
