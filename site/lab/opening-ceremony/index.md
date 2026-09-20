---
layout: lab
title: The opening ceremony, as a machine heard it
permalink: /lab/opening-ceremony/
custom_css: /assets/css/opening-segments.css
description: "An hour and 42 minutes of the centre's opening, segmented automatically into parts, sound kinds and speaker turns, with what the pipeline got right and what it missed."
lab:
  authors: [mishmash.no]
  date: 2026-09-19
  status: experiment
  data: "The recording of the opening ceremony, published on the centre's YouTube channel, analysed locally with avsegmenter. What this page loads is the analysis, 14 kB of JSON; the recording itself stays on YouTube and is fetched only when a reader presses play."
  ai: "The segmentation is machine listening: sound-event tagging, a music and speech classifier, speaker clustering and a whole-file transcript from Whisper. The page and the reading of the results were drafted with an AI assistant and reviewed by the site maintainers."
---

What can a machine tell about an event from its recording alone? The centre's opening in the University Aula on 8 April 2026 ran for an hour and 42 minutes, with two introductions, six artistic and scholarly contributions and two panels. Here it is as [avsegmenter](https://github.com/fourMs/avsegmenter) heard it, with nothing corrected by hand.

<div id="opening-segments">
  <p>Loading the analysis…</p>
</div>
<noscript>
  <p>This piece needs JavaScript to draw the timeline. The recording is on <a href="https://www.youtube.com/watch?v=rq8UnZlzYk4">YouTube</a>, the programme is on the <a href="/events/aulaen2026/">event page</a>, and the analysis itself is a <a href="/assets/data/opening-ceremony-segments.json">JSON file</a>.</p>
</noscript>

<script defer src="{{ '/assets/js/opening-segments.js' | relative_url }}"></script>

## What it found

The pipeline listens, reads and looks. It tags sound events, separates music from speech, finds where the room applauds, clusters the voices, transcribes what is said, and reads the slides on the projection. It knew the programme from the event page, and matched what it found against it.

It found eleven parts for the ten acts on the programme, and named every one of them. The eleventh is the centre's own short presentation of an Artistic Readiness Level, which was never on the printed programme and which the page therefore leaves without an act.

## Three ways of knowing the same evening

The interesting part is not that the analysis worked. It is that each way of sensing the room failed somewhere the others did not.

**Sound** marks the shape of an event: applause ends something, a silence is a break, a new voice may be a new speaker. It found seven of the ten acts. Its weakness is that applause tells you that something ended, not when the next thing began, and not what it was. The hall was also bilingual, which caught the transcriber out: asked to pick a language from the opening half minute, it scored 0.50 for Norwegian against 0.48 for English, and a whole-file pass in one language would have turned an English talk into Norwegian words. The transcript here is made with the language decided per passage instead.

**Sight** turned out to be the better witness to structure. This hall projects a card when an act begins, with the work and the people in it. A card is written rather than spoken, so a bilingual evening does not trouble it, and it changes at the moment the act changes rather than a little after. Reading the projection every ten seconds took three minutes and moved nine of the ten boundaries from "somewhere near the applause" to the second the card came up. It also names the act, which sound can only do if somebody says the name out loud.

**Words** then rescued what sight lost. The hall dims the screen for a performance, and the percussion piece that closed the evening therefore has no card at all. It has an announcement: "vi skal nå høre og se Koka Nikoladse spille". Where the running order has an act that no part carries, the pipeline now looks for that sentence and cuts the recording where it falls. That recovered the last act, and nothing on the programme is left unaccounted for.

None of the three is the reliable one. Sound is there always but says least about what; sight says most but only while the screen is lit; words say who but only when somebody bothers to announce it. Reading them together is not a trick for getting a better number. It is the same thing a person in the room does without noticing.

| What was read | Parts found | Act names right |
| --- | --- | --- |
| sound alone | 7 of 10 | 4 |
| sound and the running order | 10 | 6 |
| sound, projection and transcript | 11, all named | 8 |

One caveat is worth keeping. This worked because the hall labels its acts on screen. A room without that habit gives the reading nothing, and the applause, the running order and whatever the host says are all that remain.

## What the programme got wrong

The programme on the event page was not the order the evening ran in. It listed both panels at the end, while the first panel came fourth, straight after the opening contributions, and a percussion piece closed. The pipeline takes the act named at each boundary, on the card and in the transcript, rather than the printed order. The [event page](/events/aulaen2026/) now gives the order as it happened.

## What else was measured

The timeline above is a selection. The advanced view under it holds the rest: three strips that squeeze the whole evening into a picture, and ten curves running the same axis, one point per ten seconds. They are the pipeline's raw material, and they are there to be looked at rather than read off, since none of them carries a scale.

The curves say things the bands do not. Spectral flatness separates the kinds of sound cleanly: 0.043 through the applause, 0.024 through the talk, 0.011 through the music, which is the measure doing exactly what it is for. Quantity of motion is near zero through both panels, 0.028 and 0.040, and highest in the fiddle piece at 0.459 and the closing percussion at 0.332. Most of the other parts sit near the panels, between 0.020 and 0.060, so the curve separates two acts from the rest of the evening rather than performance from talk.

Reading a curve back to a named act is where this gets delicate, since the two swapped names above belong to parts these numbers are attached to. The numbers are the parts; the names are a claim about the parts.

Those figures come from `scripts/build_opening_analysis.py --report`, which prints them per part and per kind of sound.

Two of them are not drawn. The codec motion vectors came back empty for this recording: the reader takes them from P-frames, and the file is AV1, which it cannot read. The frame-based quantity of motion measures the same thing a different way and is plotted instead.

## What is still wrong

Two names are swapped, the rector and the first performance, because their cards come up while the previous act is still finishing. The voices are clusters, not people: the colours in the speaker row mean "this sounds like the same person", not "this is the rector". Naming them is a human act, and on this page nobody has done it.

## Why this is on the website

Three reasons. The centre works on AI and creativity, and an honest example of what machine listening, reading and looking do to a real recording is worth more than a claim about it. The analysis is small, open data, while the recording stays where it was published. And the failures are as instructive as the successes: this recording is the reason [avsegmenter](https://github.com/fourMs/avsegmenter) now uses the running order to decide how many parts to look for, reads the projection to decide where they begin, and asks the transcript for the act that the projection missed.

The recording is the centre's own. Nothing about it is copied here, and nothing reaches YouTube until you press play.
