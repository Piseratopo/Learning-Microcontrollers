import argparse
import math
import wave
import struct
import numpy as np


def generate_sweep(f0, f1, duration, sr, sweep_type="log"):
    n = int(sr * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    if sweep_type == "linear":
        k = (f1 - f0) / duration
        phase = 2 * math.pi * (f0 * t + 0.5 * k * t * t)
    else:  # log
        if f0 <= 0 or f1 <= 0:
            raise ValueError("f0 and f1 must be > 0 for log sweep")
        L = math.log(f1 / f0)
        phase = 2 * math.pi * f0 * duration / L * (np.exp(t * L / duration) - 1)
    y = np.sin(phase)
    # apply a mild fade in/out to avoid clicks
    fade_len = int(sr * 0.01)  # 10 ms
    if fade_len > 0:
        window = np.ones_like(y)
        window[:fade_len] = np.linspace(0, 1, fade_len)
        window[-fade_len:] = np.linspace(1, 0, fade_len)
        y = y * window
    return y


def save_wav(path, samples, sr):
    # convert float samples in [-1,1] to 16-bit PCM
    samples = np.clip(samples, -1.0, 1.0)
    ints = (samples * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(ints.tobytes())


def try_play(samples, sr):
    try:
        import simpleaudio as sa

        audio = (samples * 0.9 * 32767).astype(np.int16).tobytes()
        play_obj = sa.play_buffer(audio, 1, 2, sr)
        play_obj.wait_done()
    except Exception:
        print("Playback not available (install simpleaudio to enable).")


def main():
    p = argparse.ArgumentParser(description="Generate frequency sweep WAV file")
    p.add_argument("--f0", type=float, default=20.0, help="start frequency (Hz)")
    p.add_argument("--f1", type=float, default=10000.0, help="end frequency (Hz)")
    p.add_argument("--duration", type=float, default=10.0, help="duration in seconds")
    p.add_argument("--sr", type=int, default=44100, help="sample rate")
    p.add_argument(
        "--type", choices=["log", "linear"], default="log", help="sweep type"
    )
    p.add_argument("--outfile", default="sweep_20-10000Hz.wav", help="output WAV file")
    p.add_argument(
        "--play", action="store_true", help="play after generation if possible"
    )
    args = p.parse_args()

    samples = generate_sweep(args.f0, args.f1, args.duration, args.sr, args.type)
    save_wav(args.outfile, samples, args.sr)
    print(
        f"Saved sweep to {args.outfile} ({args.f0}Hz -> {args.f1}Hz, {args.duration}s, {args.sr}Hz, {args.type})"
    )
    if args.play:
        try_play(samples, args.sr)


if __name__ == "__main__":
    main()
