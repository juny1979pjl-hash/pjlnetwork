#!/usr/bin/env python3
"""Transcribe a voiceover into burned-in captions.

  make_captions.py audio/vo_en.mp3 captions/vo_en.ass --aspect 9:16 --lang en --words 3
  make_captions.py audio/vo_en.mp3 captions/vo_en.srt --lang en --words 8   (plain subtitles)

An .ass output gives the punchy social style: big bold uppercase words, the word being
spoken lights up yellow and pops. An .srt output gives plain subtitles. Either one goes
in the shot list's "captions" field.

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


def ass_ts(t):
    cs = int(round(max(t, 0) * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def write_ass(path, cues, aspect):
    w, h = (1080, 1920) if aspect == "9:16" else (1920, 1080)
    size, margin, outline = (84, 420, 7) if aspect == "9:16" else (72, 80, 6)
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Pop,Inter,{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,1,0,1,{outline},3,2,60,60,{margin},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    clean = lambda s: s.strip().upper().replace("{", "(").replace("}", ")")
    lines = []
    for ci, c in enumerate(cues):
        words = [clean(w.word) for w in c]
        next_start = cues[ci + 1][0].start if ci + 1 < len(cues) else float("inf")
        for k, w in enumerate(c):
            start = w.start
            end = c[k + 1].start if k + 1 < len(c) else min(c[-1].end + 0.15, next_start)
            parts = []
            for j, word in enumerate(words):
                if j == k:  # the spoken word: yellow, pops from 115% to 100%
                    parts.append("{\\c&H00D6FF&\\fscx115\\fscy115\\t(0,90,\\fscx100\\fscy100)}"
                                 + word + "{\\c&HFFFFFF&\\fscx100\\fscy100}")
                else:
                    parts.append(word)
            lines.append(f"Dialogue: 0,{ass_ts(start)},{ass_ts(end)},Pop,,0,0,0,,{' '.join(parts)}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(lines) + "\n")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("audio")
    p.add_argument("out")
    p.add_argument("--lang", default="en")
    p.add_argument("--words", type=int, default=4, help="max words per caption (3-4 vertical, ~8 horizontal)")
    p.add_argument("--model", default="small")
    p.add_argument("--aspect", choices=["16:9", "9:16"], default="9:16", help="frame for .ass styling")
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

    if a.out.lower().endswith(".ass"):
        write_ass(a.out, cues, a.aspect)
        print(f"{a.out}: {len(cues)} captions (karaoke)")
        return
    with open(a.out, "w", encoding="utf-8") as f:
        for i, c in enumerate(cues, 1):
            text = "".join(w.word for w in c).strip()
            f.write(f"{i}\n{ts(c[0].start)} --> {ts(c[-1].end)}\n{text}\n\n")
    print(f"{a.out}: {len(cues)} captions")


if __name__ == "__main__":
    main()
