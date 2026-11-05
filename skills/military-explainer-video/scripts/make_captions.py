#!/usr/bin/env python3
"""Transcribe a voiceover into a short-chunk .srt for burned-in captions.

  make_captions.py audio/vo_en.mp3 captions/vo_en.srt --lang en --words 4 [--model PATH_OR_NAME]

Needs `pip install faster-whisper` and ffmpeg. The model ("small" by default) normally
downloads from huggingface.co. If that host is blocked (some sandboxes), the same model
is published on npm, which is often allowed:

  for p in 0 1 2 3; do npm pack "@skillninja/shortmovie-telop-model-p$p@1.0.0"; done
  # untar each, copy config.json, preprocessor_config.json, tokenizer.json, vocabulary.json
  # from part 0 into a folder, and `cat model.bin.part0..3 > folder/model.bin`;
  # verify against part 0's model.sha256, then pass --model folder

Audio is decoded with ffmpeg into a numpy array, which sidesteps PyAV version clashes.
"""
import argparse
import subprocess

import numpy as np


def ts(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("audio")
    p.add_argument("out")
    p.add_argument("--lang", default="en")
    p.add_argument("--words", type=int, default=4, help="max words per caption (3-4 vertical, ~8 horizontal)")
    p.add_argument("--model", default="small")
    a = p.parse_args()

    from faster_whisper import WhisperModel

    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", a.audio, "-ac", "1", "-ar", "16000",
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    model = WhisperModel(a.model, device="cpu", compute_type="int8")
    segs, _ = model.transcribe(audio, language=a.lang, word_timestamps=True, vad_filter=True)

    cues, chunk = [], []
    for seg in segs:
        for w in seg.words:
            chunk.append(w)
            ends_sentence = w.word.strip().endswith((".", "?", "!", ","))
            if len(chunk) >= a.words or ends_sentence:
                cues.append(chunk)
                chunk = []
        if chunk:
            cues.append(chunk)
            chunk = []

    with open(a.out, "w", encoding="utf-8") as f:
        for i, c in enumerate(cues, 1):
            text = "".join(w.word for w in c).strip()
            f.write(f"{i}\n{ts(c[0].start)} --> {ts(c[-1].end)}\n{text}\n\n")
    print(f"{a.out}: {len(cues)} captions")


if __name__ == "__main__":
    main()
