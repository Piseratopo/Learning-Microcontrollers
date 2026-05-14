import serial
import wave
import time
import numpy as np
import msvcrt

# --- CONFIGURATION ---
PORT = "COM7"
BAUD = 460800
FLUSH_DURATION = 2
NOISE_SAMPLE_DURATION = 2
FILE_NAME = "manual_recording_cleaned.wav"

# --- FILTER CONFIG ---
# This removes everything above 5000Hz (where the high-pitched whine lives)
LOW_PASS_CUTOFF = 5000


def apply_advanced_cleaning(signal, noise, sample_rate):
    """Subtracts noise and filters out high-pitch whine."""

    # 1. Prepare Data
    sig_f = signal.astype(float) - 127.0
    noi_f = noise.astype(float) - 127.0

    # 2. Fourier Transform
    sig_fft = np.fft.rfft(sig_f)
    noi_fft = np.fft.rfft(noi_f, n=len(sig_f))

    sig_mag = np.abs(sig_fft)
    sig_phase = np.angle(sig_fft)
    noi_mag = np.abs(noi_fft)

    # 3. Frequency Bin Calculation
    # Determine which "bin" corresponds to our cutoff frequency
    freqs = np.fft.rfftfreq(len(sig_f), d=1.0 / sample_rate)

    # 4. Spectral Subtraction (Removes Hiss)
    # Increase 2.0 to 3.0 if you still hear background noise
    noise_mask = np.mean(noi_mag) * 2.0
    reduced_mag = np.maximum(sig_mag - noise_mask, 0)

    # 5. Low-Pass Filter (Removes High-Pitch Whine)
    # We zero out any frequency above the LOW_PASS_CUTOFF
    reduced_mag[freqs > LOW_PASS_CUTOFF] = 0

    # 6. Reconstruct
    cleaned_fft = reduced_mag * np.exp(1j * sig_phase)
    cleaned_signal = np.fft.irfft(cleaned_fft)

    return np.clip(cleaned_signal + 127.0, 0, 255).astype(np.uint8)


def record_audio():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.1)

        print("\n--- Manual Noise-Canceling Recorder (Low-Pass Filter Active) ---")
        input(">> Press [ENTER] to begin the sequence...")

        # 1. FLUSH
        print(f"1. Flushing ({FLUSH_DURATION}s)...")
        ser.reset_input_buffer()
        t_end = time.time() + FLUSH_DURATION
        while time.time() < t_end:
            ser.read(ser.in_waiting)

        # 2. NOISE SAMPLING
        print(f"2. Sampling NOISE ({NOISE_SAMPLE_DURATION}s)... STAY SILENT!")
        noise_buffer = bytearray()
        t_end = time.time() + NOISE_SAMPLE_DURATION
        while time.time() < t_end:
            if ser.in_waiting > 0:
                noise_buffer.extend(ser.read(ser.in_waiting))

        # 3. RECORDING
        print("3. RECORDING... Press [ENTER] to STOP.")
        while msvcrt.kbhit():
            msvcrt.getch()

        rec_buffer = bytearray()
        start_time = time.time()
        while True:
            if ser.in_waiting > 0:
                rec_buffer.extend(ser.read(ser.in_waiting))
            if msvcrt.kbhit():
                if msvcrt.getch() in [b"\r", b"\n"]:
                    break

        actual_duration = time.time() - start_time
        actual_rate = int(len(rec_buffer) / actual_duration)

        print(f"\nCaptured {len(rec_buffer)} samples at {actual_rate}Hz.")

        # 4. PROCESSING
        print(f"4. Cleaning & Filtering everything above {LOW_PASS_CUTOFF}Hz...")
        noise_data = np.frombuffer(noise_buffer, dtype=np.uint8)
        signal_data = np.frombuffer(rec_buffer, dtype=np.uint8)

        cleaned_data = apply_advanced_cleaning(signal_data, noise_data, actual_rate)

        # 5. SAVE
        with wave.open(FILE_NAME, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(1)
            wav_file.setframerate(actual_rate)
            wav_file.writeframes(cleaned_data.tobytes())

        print(f"Success! Saved as {FILE_NAME}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if "ser" in locals():
            ser.close()


if __name__ == "__main__":
    record_audio()
