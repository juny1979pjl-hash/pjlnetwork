---
name: military-explainer-video
description: Produce AI-made military and defense explainer videos in the "cinematic breakdown" style — tense present-tense narration, 3D terrain map shots with glowing flight paths, weapon spec cards, physics explained with everyday analogies, and cinematic b-roll. Makes a 16:9 long version (5–15 min, YouTube) and/or a 9:16 short (1–3 min, TikTok/Reels/Shorts), in English and/or Spanish. Use this skill whenever the user wants to make a video about a weapon system, missile, aircraft, warship, air defense, battle, military operation, or "how X beats Y" scenario — even if they just say "make one of those military videos", "do a video like the Tomahawk one", "hazme un video militar", or paste a military TikTok and want something similar.
---

# Military explainer video

Turns a topic ("Tomahawk vs Iranian air defense", "how a carrier defends itself") into a finished, narrated, captioned video. The style is reverse-engineered from a successful TikTok explainer; see `references/script-style.md` for the full breakdown with examples.

The pipeline:

```
topic → research → script (EN, then ES) → shot list → voiceover → visuals + music/SFX
      → captions → assemble with ffmpeg → 16:9 long cut + 9:16 short cut → review
```

Each stage is checkpointed in a project folder so the user can stop, review, and resume:

```
<project>/
  research.md          sources + verified numbers
  script_en.md         narration, one beat per paragraph, with [SHOT] tags
  script_es.md
  shots_16x9.json      shot list consumed by scripts/build_video.py
  shots_9x16.json
  audio/               vo_en.mp3, vo_es.mp3, music.mp3, sfx/
  visuals/             generated images / clips, cards
  captions/            vo_en.srt, vo_es.srt
  out/                 final mp4s
```

## Defaults (the user chose these)

| Version | Aspect | Length | Words of narration (~150 wpm EN) |
|---|---|---|---|
| Long | 16:9, 1920×1080 | 5–15 min | 750–2,250 |
| Short | 9:16, 1080×1920 | 1–3 min | 150–450 |

Languages: English and Spanish. Spanish runs ~15–20% longer when spoken, so the Spanish script is *adapted*, not translated word for word — trim it to land on the same timing.

Ask the user only what you can't infer: the topic, and which versions they want this time (default: both aspects, both languages). Confirm before spending large amounts of AI credits — a 15-min long version can need 100+ generated shots.

## Step 1 — Pick the framing, then research

Decide early, and tell the user, which of two kinds of video this is, because it changes what you can say:

- **Real event / real system.** Every number (speed, range, weight, warhead, cost) must come from a public source you can cite in `research.md`. Use web search. Where sources disagree, give a range or say "about".
- **Hypothetical scenario** ("what if 12 Tomahawks went for X"). Real specs, imagined events. Put a "SCENARIO" tag on the title card and say "in this scenario" once in the first 15 seconds. Viewers share these as news otherwise, which hurts the channel's credibility and can get the video labeled misleading.

Stay at the level of public defense journalism: what systems are, how fast, how far, the physics of why one beats another. Don't invent precise vulnerabilities, unit locations or tactics presented as fact.

## Step 2 — Write the script

Read `references/script-style.md` before writing. The short version:

1. **Cold open with a clock and a number.** "At 05:38 local time, twelve Tomahawk Block V cruise missiles are crossing the desert at 550 miles an hour." Present tense, specific, no intro, no "in this video".
2. **Stakes in three short sentences.** "Twelve missiles. A dozen targets. Zero margin for a miss."
3. **Alternate story beats and explainer beats.** Story: what's happening second by second. Explainer: a "What's flying up that riverbed? The BGM-109 Tomahawk." reveal, then a spec card.
4. **Every spec gets an analogy.** "Chicago to Denver at treetop height." "Like watching a car at night on a hilly road."
5. **One clear physics idea per act** (radar horizon, ground clutter, seeker handoff…) explained with a picture the viewer already has in their head.
6. **Human detail on both sides** — the truck driver who sees a flash, the radar crew being careful. Respectful, never mocking casualties.
7. **End on the consequence**, not a summary. No "like and subscribe" in the narration — that goes in the caption.

Format `script_en.md` as one paragraph per beat, each starting with a shot tag the shot list will use:

```
[MAP] At 05:38 local time, twelve Tomahawk Block V cruise missiles ...
[BROLL] Fifty feet off the ground, headed for the hills east of the city.
[SPEC: BGM-109 Tomahawk Block V] What's flying up that riverbed? ...
```

Shot tags: `MAP`, `BROLL`, `SPEC: <name>`, `DIAGRAM`, `TITLE`, `STAT: <big number>`, `CLOCK: <time>`. See `references/visuals.md`.

**The short is its own script**, not a crop of the long one: pick the single strongest arc (usually "attacker vs one defender + one physics idea"), keep the cold open and the reveal, and cut everything else. Hook in the first 2 seconds.

Show the user the script and get a thumbs-up before generating anything — it's the cheapest place to change direction.

## Step 3 — Shot list

Turn each beat into 1–3 shots of 3–6 seconds (shorts: 2–4 s; cut faster). Write `shots_16x9.json` / `shots_9x16.json` in the format documented at the top of `scripts/build_video.py`. You don't need exact durations — the build script stretches shots to fit the voiceover — but give longer beats more shots.

## Step 4 — Voiceover

Use whichever voice connector is available (ElevenLabs `creative_generate_speech` is a good default):

- Pick a deep, calm, documentary-style male or female voice from the connector's voice list; a different native voice for Spanish. Tell the user which you picked. Keep the same voices across the series so the channel sounds consistent — note them in the project folder.
- Generate per act (not the whole 15-min script in one call) so a bad take can be redone cheaply.
- Join the takes: `ffmpeg -f concat -safe 0 -i list.txt -c copy audio/vo_en.mp3`.

## Step 5 — Visuals

Read `references/visuals.md` for prompt templates per shot type. In brief:

- **SPEC / TITLE / STAT / CLOCK cards** — render locally with `scripts/make_card.py` (free, consistent, exact text). Never ask an image model to draw text or numbers; they garble it.
- **MAP and BROLL** — AI image or video generation through the connected tools (ElevenLabs, Artlist, Higgsfield…). Generate stills for most shots and let `build_video.py` animate them with slow zoom/pan; spend video-generation credits on the 10–20% of hero moments (launches, low-level flight, intercept).
- Generate at the target aspect. For "both" versions, generate hero shots twice (16:9 and 9:16) rather than cropping; for ordinary stills, `build_video.py` can fill a vertical frame with a blurred copy behind the image (`"fit": "blur"`).
- Check cost first where the tool offers a cost estimate, and tell the user the total before a big batch.
- Don't use news-agency or channel footage (Reuters, AP, other creators). It's copyrighted and the reference video's "Source: Reuters" clips are exactly what gets channels claimed. Original or licensed only.

## Step 6 — Music and sound

Search a licensed catalog (e.g., Artlist `search_music` / `search_sfx`) for dark, pulsing, cinematic instrumental — no vocals. SFX that sell the style: missile whoosh, radar ping, low rumble, alarm, impact. Music sits ~18 dB under the voice; the build script ducks it automatically.

## Step 7 — Captions

Burned-in captions matter most on the vertical cut (most people watch muted). Transcribe the final voiceover for accurate timing:

```bash
python3 scripts/make_captions.py audio/vo_en.mp3 captions/vo_en.srt --lang en --words 4
```

Use `--words 3` or `4` for 9:16 and `--words 8` for 16:9. The script explains how to get a Whisper model if the usual download hosts are blocked. Spot-check names — Whisper mangles foreign system names (it heard "Khordad 15" as "Cordad 15"); fix them in the .srt.

## Step 8 — Assemble

```bash
python3 scripts/build_video.py <project>/shots_16x9.json
python3 scripts/build_video.py <project>/shots_9x16.json
```

It normalizes every shot to the target frame, animates stills, fits the total to the voiceover length, mixes VO + ducked music + SFX, burns captions and an optional handle watermark, and writes an H.264/AAC mp4.

Then check it yourself before handing it over: pull a contact sheet (`ffmpeg -i out.mp4 -vf "fps=1/10,scale=480:-1,tile=4x4" sheet.jpg`) and look at it, and confirm duration with `ffprobe`.

## Step 9 — Deliver

Give the user the mp4s plus a ready-to-paste post for each platform: title, 2–3 line description, 5–8 hashtags, and (for scenarios) the "hypothetical scenario" note. Remind them to switch on the platform's "AI-generated content" label — TikTok, YouTube and Instagram all require it for realistic AI visuals, and unlabeled videos get suppressed or removed.
