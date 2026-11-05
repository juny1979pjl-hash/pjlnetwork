# Visuals: shot types and prompt templates

Keep one look across the whole series: desaturated desert/steel palette, teal-and-amber grade, high-contrast, slight film grain, overcast or golden-hour light. Add the same style suffix to every generation prompt so shots match:

> `cinematic documentary still, photorealistic, muted teal and amber color grade, high contrast, subtle film grain, 35mm, no text, no logos, no watermark`

For 9:16, add "vertical composition, subject centered". Always "no text" — text comes from `make_card.py`.

## MAP — 3D terrain with flight paths

The signature shot. Generate a clean terrain image with no overlays, then animate the paths, targets, radar and countdown with `scripts/make_map.py` (exact, and they move):

> `3D satellite terrain render of arid mountains and dry riverbeds seen from a high oblique angle, clear daylight, sharp detail, no lines, no markers, no text, ` + style suffix

Make 2–3 terrain images per video (approach, defended zone, target area) and reuse them with different paths so the geography feels consistent.

## BROLL — cinematic action

- Missile in flight: `a subsonic cruise missile with small stubby wings flying fifty feet above a dry gravel riverbed, motion blur, dust kicked up, low angle` + suffix
- Launch: `a vertical missile launch from a truck-mounted canister in the desert at dawn, huge dust cloud, telephoto` + suffix
- Radar crew: `inside a dim mobile radar command shelter, operators' hands on a trackball console, green radar scope glow` + suffix (hands and screens, not faces — avoids uncanny faces)
- Interceptor miss: `a surface-to-air missile streaking low over a ridgeline, then detonating harmlessly against the rock face, debris and dust` + suffix
- Target: `aerial view of a sprawling industrial complex in barren hills with large halls and a tall stack` + suffix

Don't make generated shots look like real, identifiable sites or real news footage of a real attack — keep them generic. For a hypothetical scenario that matters doubly.

## SPEC card (local, `make_card.py spec`)

Name + variant at the top, 3–6 stat rows, optional small render of the weapon (generate it on a plain light-blue background: `side view of <weapon> on a plain light blue background, product render, centered` — then pass it with `--image`).

## STAT / CLOCK / TITLE cards (local)

- STAT: one huge number + label ("93 mi → 20 mi", "~$1M per shot").
- CLOCK: "05:38 LOCAL" in a monospace-style font — opens the video.
- TITLE: video title + optional "SCENARIO" tag.

## DIAGRAM — physics ideas

Generate a clean simple illustration (no text), then add labels with a STAT card or caption:

> `simple clean side-view diagram of the curved surface of the earth, a radar truck on the left emitting a straight beam, a small missile flying low below the beam behind the curvature, flat vector infographic style, dark navy background, white and amber lines, no text`

## Hero video shots

Spend video credits on 10–20% of shots: opening map flight, low-level missile pass, launch, intercept/miss, final approach. 5-second clips are enough; the build script trims or loops to fit.
