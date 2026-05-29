import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.fft import fft, fftfreq


def analyze_real_comparison(raw_file, cleaned_file):
    # 1. Đọc 2 file wav
    fs_raw, data_raw = wavfile.read(raw_file)
    fs_clean, data_clean = wavfile.read(cleaned_file)

    if fs_raw != fs_clean:
        print(f"Cảnh báo: Tần số lấy mẫu khác nhau! {fs_raw} vs {fs_clean}")

    # Chuyển về mono nếu là stereo
    if len(data_raw.shape) > 1:
        data_raw = data_raw[:, 0]
    if len(data_clean.shape) > 1:
        data_clean = data_clean[:, 0]

    # Khớp độ dài 2 file (cắt bỏ phần thừa nếu có)
    min_len = min(len(data_raw), len(data_clean))
    data_raw = data_raw[:min_len].astype(float)
    data_clean = data_clean[:min_len].astype(float)

    # Centering (loại bỏ offset DC)
    raw_centered = data_raw - np.mean(data_raw)
    clean_centered = data_clean - np.mean(data_clean)

    # 2. Tính toán SNR thực tế
    # Giả định phần bị loại bỏ chính là nhiễu: Noise = Raw - Cleaned
    noise = raw_centered - clean_centered
    signal_power = np.mean(clean_centered**2)
    noise_power = np.mean(noise**2)

    # Tránh chia cho 0
    snr = 10 * np.log10(signal_power / (noise_power + 1e-10))

    # 3. Tính toán FFT
    n = min_len
    freqs = fftfreq(n, 1 / fs_raw)[: n // 2]
    fft_raw = np.abs(fft(raw_centered)[: n // 2])
    fft_clean = np.abs(fft(clean_centered)[: n // 2])

    # 4. Vẽ đồ thị
    plt.figure(figsize=(12, 10))

    # Miền thời gian
    plt.subplot(2, 1, 1)
    plt.plot(data_raw, color="green", alpha=0.4, label="Tín hiệu gốc (Raw)")
    plt.plot(data_clean, color="blue", alpha=0.7, label="Tín hiệu đã xử lý (Cleaned)")
    plt.title(f"So sánh tín hiệu Miền thời gian thực tế (SNR cải thiện: {snr:.2f} dB)")
    plt.xlabel("Samples")
    plt.ylabel("Biên độ")
    plt.legend()

    # Miền tần số
    plt.subplot(2, 1, 2)
    plt.semilogy(freqs, fft_raw, color="green", alpha=0.3, label="Phổ sóng gốc")
    plt.semilogy(freqs, fft_clean, color="blue", label="Phổ sóng đã xử lý")
    plt.title("Phân tích phổ tần số thực tế (FFT)")
    plt.xlabel("Tần số (Hz)")
    plt.ylabel("Năng lượng (Log scale)")
    plt.xlim(0, fs_raw / 2)
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    plt.legend()

    plt.tight_layout()
    plt.savefig("real_comparison_analysis.png", dpi=300)
    plt.show()

    print(f"Phân tích hoàn tất.")
    print(f"SNR thực tế đo được: {snr:.2f} dB")


# Chạy phân tích
analyze_real_comparison("manual_recording_raw.wav", "manual_recording_cleaned.wav")
