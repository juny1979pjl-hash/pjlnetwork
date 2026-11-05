#!/usr/bin/env python3
"""Assemble a finished explainer video from a shot list with ffmpeg.

  build_video.py project/shots_16x9.json

Shot list format (paths are relative to the JSON file):

{
  "aspect": "16:9",                  # or "9:16"
  "fps": 30,
  "voiceover": "audio/vo_en.mp3",    # required; sets the video length
  "music": "audio/music.mp3",        # optional; looped, ducked under the voice
  "music_db": -18,                   # optional; music level before ducking
  "captions": "captions/vo_en.srt",  # optional; burned in
  "handle": "@yourchannel",          # optional; small watermark
  "transition": "flash",             # optional default for every cut: flash, glitch, cut
  "cut_sfx": "audio/sfx/whoosh.mp3", # optional sound on every cut; cut_sfx_db (default -10)
  "output": "out/long_en.mp4",
  "shots": [
    {"file": "visuals/clock.png", "duration": 3, "motion": "none"},
    {"file": "visuals/map01.png", "motion": "zoom_in"},
    {"file": "visuals/launch.mp4", "duration": 5, "fit": "crop",
     "sfx": "audio/sfx/whoosh.mp3", "sfx_db": -4}
  ]
}

Per shot:
  file      image (.png/.jpg/.webp) or video (.mp4/.mov/.webm; a short clip holds its last frame)
  duration  relative length in seconds (default 4). All durations are scaled together so
            the video ends 0.6 s after the voiceover — you don't need exact timings.
  motion    stills only: zoom_in (default), zoom_out, pan_left, pan_right, none
  fit       crop (default: fill the frame, cut edges) or blur (whole image over a blurred
            copy — use for 16:9 material in a 9:16 video)
  sfx       optional sound effect starting at this shot; sfx_db sets its level (default -6)
  transition  how this shot comes in: flash (white flash), glitch (RGB split + noise), cut
  shake     true for handheld/impact camera shake (launches, explosions, fast flybys)

Captions: an .ass file from make_captions.py gives the pop-word style; .srt gives plain subs.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

SIZES = {"16:9": (1920, 1080), "9:16": (1080, 1920)}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"ffmpeg failed:\n{' '.join(cmd)}\n{r.stderr[-3000:]}")


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def fit_filter(fit, w, h):
    """Filter chain taking [0:v] to a w x h frame, labelled [fit]."""
    if fit == "blur":
        return (f"[0:v]split[a][b];"
                f"[a]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=30:3,eq=brightness=-0.12[bg];"
                f"[b]scale={w}:{h}:force_original_aspect_ratio=decrease[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[fit]")
    return f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1[fit]"


def motion_filter(motion, frames, w, h, fps):
    n = max(frames - 1, 1)
    z = {"zoom_in": f"1+0.12*on/{n}", "zoom_out": f"1.12-0.12*on/{n}",
         "pan_left": "1.12", "pan_right": "1.12", "none": "1"}[motion]
    x = {"pan_left": f"(iw-iw/zoom)*(1-on/{n})", "pan_right": f"(iw-iw/zoom)*on/{n}"}.get(
        motion, "iw/2-(iw/zoom/2)")
    y = "ih/2-(ih/zoom/2)"
    # upscale first so the slow zoom doesn't jitter
    return (f"[fit]scale={w * 2}:{h * 2},zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={w}x{h}:fps={fps},"
            f"setsar=1[pre]")


def render_shot(shot, dur, w, h, fps, out):
    src, ext = shot["file"], os.path.splitext(shot["file"])[1].lower()
    fit = shot.get("fit", "crop")
    frames = max(int(round(dur * fps)), 1)
    if ext in IMAGE_EXT:
        graph = fit_filter(fit, w, h) + ";" + motion_filter(shot.get("motion", "zoom_in"), frames, w, h, fps)
        cmd = ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(fps), "-t", f"{dur:.3f}", "-i", src]
    else:
        # if the clip is shorter than its slot, hold the last frame (loops look wrong on cards)
        graph = fit_filter(fit, w, h) + f";[fit]fps={fps},tpad=stop_mode=clone:stop_duration={dur:.3f}[pre]"
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", src]
    graph += ";[pre]" + effects(shot, w, h) + "[v]"
    cmd += ["-filter_complex", graph, "-map", "[v]", "-frames:v", str(frames), "-an",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out]
    run(cmd)


def effects(shot, w, h):
    fx = []
    if shot.get("shake"):
        m = 24  # crop a margin and wobble inside it, then scale back up
        fx.append(f"crop={w - 2 * m}:{h - 2 * m}:x='{m}+{m * 0.8}*sin(t*31)*sin(t*7)':"
                  f"y='{m}+{m * 0.8}*cos(t*27)*sin(t*5)',scale={w}:{h}")
    tr = shot.get("transition", "cut")
    if tr == "flash":
        fx.append("fade=t=in:st=0:d=0.22:color=white")
    elif tr == "glitch":
        fx.append("rgbashift=rh=-18:bh=18:gv=6:enable='lt(t,0.2)'")
        fx.append("noise=alls=60:allf=t:enable='lt(t,0.2)'")
    fx.append("setsar=1")
    return ",".join(fx)


def font_file():
    for fam in ("Inter:style=Bold", "DejaVu Sans:style=Bold"):
        r = subprocess.run(["fc-match", "-f", "%{file}", fam], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    return None


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    spec_path = os.path.abspath(sys.argv[1])
    base = os.path.dirname(spec_path)
    spec = json.load(open(spec_path))
    rel = lambda p: p if os.path.isabs(p) else os.path.join(base, p)

    w, h = SIZES[spec.get("aspect", "16:9")]
    fps = int(spec.get("fps", 30))
    vo = rel(spec["voiceover"])
    total = duration(vo) + 0.6
    shots = spec["shots"]
    for i, s in enumerate(shots):
        if i and "transition" not in s and spec.get("transition"):
            s["transition"] = spec["transition"]
        s["file"] = rel(s["file"])
        if not os.path.exists(s["file"]):
            sys.exit(f"missing shot file: {s['file']}")
    weights = [float(s.get("duration", 4)) for s in shots]
    scale = total / sum(weights)
    durs = [wt * scale for wt in weights]
    print(f"{len(shots)} shots, voiceover {total - 0.6:.1f}s, scaling durations x{scale:.2f}")

    tmp = tempfile.mkdtemp(prefix="build_video_")
    try:
        seg_list = os.path.join(tmp, "segments.txt")
        with open(seg_list, "w") as f:
            for i, (s, d) in enumerate(zip(shots, durs)):
                seg = os.path.join(tmp, f"seg{i:04d}.mp4")
                render_shot(s, d, w, h, fps, seg)
                f.write(f"file '{seg}'\n")
                print(f"  shot {i + 1}/{len(shots)} {os.path.basename(s['file'])} {d:.1f}s")
        video = os.path.join(tmp, "video.mp4")
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", seg_list, "-c", "copy", video])

        # ---- audio: voice + ducked music + sfx
        inputs = ["-i", video, "-i", vo]
        filters, mix = ["[1:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[vo][key]"], ["[vo]"]
        idx = 2
        if spec.get("music"):
            inputs += ["-stream_loop", "-1", "-i", rel(spec["music"])]
            filters.append(f"[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
                           f"volume={spec.get('music_db', -18)}dB[mus];"
                           f"[mus][key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[duck]")
            mix.append("[duck]")
            idx += 1
        else:
            filters.append("[key]anullsink")
        t = 0.0
        for k, (s, d) in enumerate(zip(shots, durs)):
            if k and spec.get("cut_sfx") and not s.get("sfx"):
                ms = max(int(t * 1000) - 120, 0)  # whoosh leads the cut slightly
                inputs += ["-i", rel(spec["cut_sfx"])]
                filters.append(f"[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
                               f"volume={spec.get('cut_sfx_db', -10)}dB,adelay={ms}|{ms}[sfx{idx}]")
                mix.append(f"[sfx{idx}]")
                idx += 1
            if s.get("sfx"):
                ms = int(t * 1000)
                inputs += ["-i", rel(s["sfx"])]
                filters.append(f"[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
                               f"volume={s.get('sfx_db', -6)}dB,adelay={ms}|{ms}[sfx{idx}]")
                mix.append(f"[sfx{idx}]")
                idx += 1
            t += d
        filters.append(f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0:duration=first,"
                       f"apad,atrim=0:{total:.3f},alimiter=limit=0.95[aout]")

        # ---- video overlays: captions + handle
        vchain = "[0:v]"
        vf = []
        if spec.get("captions"):
            cap = rel(spec["captions"])
            is_ass = cap.lower().endswith(".ass")
            srt = os.path.join(tmp, "captions.ass" if is_ass else "captions.srt")
            shutil.copy(cap, srt)
            vertical = h > w
            style = ("FontName=Inter,Bold=1,Outline=3,Shadow=0,BorderStyle=1,PrimaryColour=&H00FFFFFF,"
                     "OutlineColour=&H00000000,Alignment=2,"
                     + ("FontSize=16,MarginV=62" if vertical else "FontSize=20,MarginV=40"))
            vf.append(f"ass={srt}" if is_ass else f"subtitles={srt}:force_style='{style}'")
        if spec.get("handle"):
            ff = font_file()
            handle = spec["handle"].replace(":", r"\:").replace("'", "")
            size = int(min(w, h) * 0.03)
            vf.append(f"drawtext=text='{handle}':{'fontfile=' + ff + ':' if ff else ''}fontsize={size}:"
                      f"fontcolor=white@0.7:x=w-tw-{size}:y=h-th-{size}")
        filters.append(f"{vchain}{','.join(vf) if vf else 'null'}[vout]")

        out = rel(spec.get("output", "out/video.mp4"))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(filters),
             "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
             "-t", f"{total:.3f}", out])
        print(f"done: {out} ({duration(out):.1f}s, {w}x{h})")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
