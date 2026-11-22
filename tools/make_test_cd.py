#!/usr/bin/env python3
"""Generate a channel-test Audio CD image (BIN/CUE) plus per-track WAVs.

Tracks (3 min each, -6 dBFS, 44.1 kHz / 16-bit stereo):
  1  L 400 Hz,  R silent
  2  L silent,  R 400 Hz
  3  L 400 Hz,  R 400 Hz
  4  L 400 Hz,  R 1 kHz
  5  L 1 kHz,   R silent
  6  L silent,  R 1 kHz
  7  silence (noise floor)

400 Hz is used because cheap multimeters are only accurate in AC mode
up to a few hundred Hz.

Usage:  python3 make_test_cd.py   (needs numpy)
Burn RM1_test.cue with ImgBurn / cdrdao as an Audio CD on a CD-R.
"""
import wave
import numpy as np

SR = 44100
AMP = 10 ** (-6 / 20) * 32767
DUR = 180 * SR


def tone(f):
    x = np.sin(2 * np.pi * f * np.arange(DUR) / SR)
    k = int(SR * 0.02)
    x[:k] *= np.linspace(0, 1, k)
    x[-k:] *= np.linspace(1, 0, k)
    return x


Z = np.zeros(DUR)
TRACKS = [
    ("01_L_400Hz", tone(400), Z),
    ("02_R_400Hz", Z, tone(400)),
    ("03_LR_400Hz", tone(400), tone(400)),
    ("04_L400_R1000", tone(400), tone(1000)),
    ("05_L_1kHz", tone(1000), Z),
    ("06_R_1kHz", Z, tone(1000)),
    ("07_silence", Z, Z),
]

cue = ['FILE "RM1_test.bin" BINARY']
with open("RM1_test.bin", "wb") as b:
    for i, (name, l, r) in enumerate(TRACKS, 1):
        pcm = np.empty(2 * DUR, dtype="<i2")
        pcm[0::2] = (l * AMP).astype("<i2")
        pcm[1::2] = (r * AMP).astype("<i2")
        data = pcm.tobytes()
        data += b"\0" * ((-len(data)) % 2352)
        f = b.tell() // 2352
        cue += [f"  TRACK {i:02d} AUDIO", f'    TITLE "{name}"']
        if i > 1:
            cue.append("    PREGAP 00:02:00")
        cue.append(f"    INDEX 01 {f // 4500:02d}:{f // 75 % 60:02d}:{f % 75:02d}")
        b.write(data)
        with wave.open(name + ".wav", "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(pcm.tobytes())

with open("RM1_test.cue", "w") as c:
    c.write("\n".join(cue) + "\n")
print("Written RM1_test.bin / RM1_test.cue and per-track WAVs")
