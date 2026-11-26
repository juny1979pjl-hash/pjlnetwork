import json, soundfile as sf, numpy as np, sys
from kokoro_onnx import Kokoro
k = Kokoro("kokoro-v1.0.int8.onnx", "voices-v1.0.bin")
scenes = json.load(open("scenes.json"))
out = []
for i, s in enumerate(scenes):
    a, sr = k.create(s["say"], voice="em_alex", speed=1.12, lang="es")
    a = np.concatenate([a, np.zeros(int(sr*0.25), dtype=a.dtype)])
    sf.write(f"s{i}.wav", a, sr)
    out.append(len(a)/sr)
    print(i, round(len(a)/sr,2))
json.dump(out, open("durs.json","w"))
