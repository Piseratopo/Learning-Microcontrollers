import serial
import wave
import time
import csv
import numpy as np
from datetime import datetime
from scipy.signal import butter, lfilter

try:
    import msvcrt
except ImportError:
    msvcrt = None

# --- CONFIGURATION ---
PORT = "COM7"
BAUD = 460800
FLUSH_DURATION = 1
NOISE_SAMPLE_DURATION = 2  # How long to listen to the room before speaking
FILE_NAME = "cleaned_audio.wav"


def butter_lowpass_filter(data, cutoff, fs, order=5):
    """Smoother filter than FFT masking to remove high-freq hiss."""
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype="low", analog=False)
    y = lfilter(b, a, data)
    return y


def spectral_subtraction(signal, noise_profile):
    """Subtracts the frequency signature of the noise from the signal."""
    # Ensure both are floats centered at 0
    sig_f = signal.astype(float) - 127.0
    # Use a chunk of the noise profile that matches signal FFT size or repeat it
    noi_f = noise_profile.astype(float) - 127.0

    # Perform FFT
    sig_fft = np.fft.rfft(sig_f)
    sig_mag = np.abs(sig_fft)
    sig_phase = np.angle(sig_fft)

    # Get average noise magnitude
    # We take the FFT of the noise sample and average the magnitude across its duration
    noi_fft = np.fft.rfft(noi_f, n=len(sig_f))
    noi_mag = np.abs(noi_fft)

    # Subtract noise magnitude (with a 'noise floor' to prevent clicking)
    # Factor 2.0 is the 'over-subtraction' factor to be more aggressive
    reduced_mag = np.maximum(sig_mag - (noi_mag * 2.0), 0.01 * sig_mag)

    # Reconstruct
    cleaned_fft = reduced_mag * np.exp(1j * sig_phase)
    cleaned_signal = np.fft.irfft(cleaned_fft, n=len(signal))

    return cleaned_signal


def capture_audio_fixed_duration(ser, duration):
    buffer = bytearray()
    end_time = time.time() + duration
    while time.time() < end_time:
        if ser.in_waiting > 0:
            buffer.extend(ser.read(ser.in_waiting))
    return np.frombuffer(buffer, dtype=np.uint8)


def record_audio():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.1)
        print("\n--- Advanced Noise-Canceling Recorder ---")

        # 1. Flush
        print("Flushing buffer...")
        time.sleep(FLUSH_DURATION)
        ser.reset_input_buffer()

        # 2. Capture Noise Profile (STAY SILENT HERE)
        print(f"STEP 1: Capture Noise. STAY SILENT for {NOISE_SAMPLE_DURATION}s...")
        noise_data = capture_audio_fixed_duration(ser, NOISE_SAMPLE_DURATION)

        # 3. Capture Voice
        print("STEP 2: RECORDING NOW... Speak now!")
        print(">> Press [ENTER] to STOP.")

        # Clear keyboard buffer
        while msvcrt and msvcrt.kbhit():
            msvcrt.getch()

        rec_buffer = bytearray()
        start_time = time.time()
        while True:
            if ser.in_waiting > 0:
                rec_buffer.extend(ser.read(ser.in_waiting))
            if msvcrt and msvcrt.kbhit():
                if msvcrt.getch() in [b"\r", b"\n"]:
                    break

        actual_duration = time.time() - start_time
        signal_data = np.frombuffer(rec_buffer, dtype=np.uint8)
        fs = int(len(signal_data) / actual_duration)
        print(f"Captured {len(signal_data)} samples at ~{fs}Hz")

        # 4. Processing
        print("Processing: Removing noise...")

        # A. Spectral Subtraction
        cleaned = spectral_subtraction(signal_data, noise_data)

        # B. Low Pass Filter (Cut off above 6kHz for better voice clarity/less hiss)
        cleaned = butter_lowpass_filter(cleaned, cutoff=6000, fs=fs)

        # C. Normalize and convert back to uint8
        cleaned = cleaned - np.min(cleaned)  # Shift to 0
        if np.max(cleaned) > 0:
            cleaned = (cleaned / np.max(cleaned)) * 255  # Scale to 0-255

        final_data = cleaned.astype(np.uint8)

        # 5. Save
        with wave.open(FILE_NAME, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(1)
            wav_file.setframerate(fs)
            wav_file.writeframes(final_data.tobytes())

        print(f"Success! Saved cleaned file to {FILE_NAME}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if "ser" in locals():
            ser.close()


if __name__ == "__main__":
    record_audio()
