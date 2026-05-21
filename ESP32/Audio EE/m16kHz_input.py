import serial
import wave
import time
import csv
import numpy as np
from datetime import datetime

try:
    import msvcrt  # Windows-specific for detecting keypress
except ImportError:
    msvcrt = None

# --- CONFIGURATION ---
PORT = "COM7"
BAUD = 460800
FLUSH_DURATION = 2
NOISE_SAMPLE_DURATION = 2
FILE_NAME = "manual_recording_cleaned.wav"
METADATA_FILE = "recording_metadata.csv"
DATA_FILE = "recording_data.csv"


def apply_noise_reduction(signal, noise):
    """Subtracts noise frequency profile from the signal."""
    if len(signal) == 0:
        return np.array([], dtype=np.uint8)

    sig_f = signal.astype(float) - 127.0
    noi_f = noise.astype(float) - 127.0 if len(noise) > 0 else np.zeros_like(sig_f)

    sig_fft = np.fft.rfft(sig_f)
    noi_fft = np.fft.rfft(noi_f, n=len(sig_f))

    sig_mag = np.abs(sig_fft)
    sig_phase = np.angle(sig_fft)
    noi_mag = np.abs(noi_fft)

    noise_level = np.mean(noi_mag) * 1.5
    reduced_mag = np.maximum(sig_mag - noise_level, 0)

    cleaned_fft = reduced_mag * np.exp(1j * sig_phase)
    cleaned_signal = np.fft.irfft(cleaned_fft)

    return np.clip(cleaned_signal + 127.0, 0, 255).astype(np.uint8)


def low_pass_filter(signal, sample_rate, cutoff_hz=9000):
    """Apply a simple FFT-based low-pass filter to remove frequencies above cutoff_hz.

    Works on 8-bit unsigned PCM (`uint8`) by centering around 0, filtering, then
    returning `uint8` data.
    """
    if len(signal) == 0:
        return np.array([], dtype=np.uint8)

    n = len(signal)
    nyquist = sample_rate / 2.0
    if cutoff_hz >= nyquist:
        return signal

    # Center to zero, FFT, mask high frequencies, inverse FFT
    sig_f = signal.astype(float) - 127.0
    sig_fft = np.fft.rfft(sig_f)
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)

    mask = freqs <= cutoff_hz
    sig_fft_filtered = sig_fft * mask

    cleaned = np.fft.irfft(sig_fft_filtered, n=n)
    return np.clip(cleaned + 127.0, 0, 255).astype(np.uint8)


def flush_serial_input(ser, duration=FLUSH_DURATION):
    ser.reset_input_buffer()
    deadline = time.time() + duration
    while time.time() < deadline:
        ser.read(ser.in_waiting or 1)


def sample_noise(ser, duration=NOISE_SAMPLE_DURATION):
    noise_buffer = bytearray()
    deadline = time.time() + duration
    while time.time() < deadline:
        if ser.in_waiting > 0:
            noise_buffer.extend(ser.read(ser.in_waiting))
    return np.frombuffer(noise_buffer, dtype=np.uint8)


def capture_audio(ser, stop_predicate):
    rec_buffer = bytearray()
    start_time = time.time()

    while True:
        if ser.in_waiting > 0:
            rec_buffer.extend(ser.read(ser.in_waiting))

        if stop_predicate and stop_predicate():
            break

    return rec_buffer, time.time() - start_time


def wait_for_enter_press():
    if msvcrt is None:
        return False

    while msvcrt.kbhit():
        if msvcrt.getch() in [b"\r", b"\n"]:
            return True
    return False


def save_wav(filename, data, sample_rate):
    with wave.open(filename, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(1)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(data.tobytes())


def save_metadata_to_csv(csv_filename, metadata):
    """Save recording metadata to a CSV file."""
    with open(csv_filename, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=metadata.keys())
        writer.writeheader()
        writer.writerow(metadata)


def save_data_to_csv(csv_filename, data, label=""):
    """Save raw audio data to a CSV file."""
    with open(csv_filename, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Index", "Sample_Value", "Label"])
        for i, sample in enumerate(data):
            writer.writerow([i, int(sample), label])


def record_audio():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.1)

        print("\n--- Manual Noise-Canceling Recorder ---")
        input(">> Press [ENTER] to begin the sequence...")

        print(f"1. Flushing hardware noise ({FLUSH_DURATION}s)...")
        flush_serial_input(ser, FLUSH_DURATION)

        print("2. RECORDING NOW... Speak now!")
        print(">> Press [ENTER] to STOP recording.")

        while msvcrt and msvcrt.kbhit():
            msvcrt.getch()

        rec_buffer, actual_duration = capture_audio(ser, wait_for_enter_press)
        actual_count = len(rec_buffer)
        captured_sample_rate = (
            int(actual_count / actual_duration) if actual_duration > 0 else BAUD
        )

        print(f"\nStopped. Captured {actual_count} samples in {actual_duration:.2f}s.")
        print(f"Effective Sample Rate: {captured_sample_rate} Hz")

        print("3. Processing audio...")
        signal_data = np.frombuffer(rec_buffer, dtype=np.uint8)

        # Apply 9 kHz low-pass filter to remove higher-frequency components
        filtered_data = low_pass_filter(
            signal_data, captured_sample_rate, cutoff_hz=9000
        )

        save_wav(FILE_NAME, filtered_data, captured_sample_rate)

        # Prepare and save metadata (based on filtered signal)
        metadata = {
            "Timestamp": datetime.now().isoformat(),
            "Sample_Rate_Hz": captured_sample_rate,
            "Duration_Seconds": round(actual_duration, 2),
            "Total_Samples": actual_count,
            "Signal_Mean": round(float(np.mean(filtered_data)), 2),
            "Signal_Std": round(float(np.std(filtered_data)), 2),
            "WAV_File": FILE_NAME,
        }
        save_metadata_to_csv(METADATA_FILE, metadata)

        # Save detailed data (filtered)
        save_data_to_csv(DATA_FILE, filtered_data, label="filtered_audio")

        print(f"Success! Saved as {FILE_NAME}")
        print(f"Metadata saved to {METADATA_FILE}")
        print(f"Data saved to {DATA_FILE}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if "ser" in locals():
            ser.close()


if __name__ == "__main__":
    record_audio()
