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

The pipeline listens rather than reads. It tags sound events, separates music from speech, finds where the room applauds, clusters the voices, and cuts the recording into parts at the cues between them. It knew the programme from the event page, and matched what it found against it.

It found seven parts and matched them, in order, to the first seven acts. It marked 36 stretches of sound: 14 of talk, 15 of applause, five of music and two of something else. It heard 14 distinct voices across 132 turns, which is close to the number of people who took the floor.

## What it missed

Three acts are listed as not detected: the last artistic contribution and both panel discussions. The pipeline says so itself rather than stretching the programme to fit, which is the useful behaviour.

Two of the seven parts are suspiciously long. Part 4 runs 28 minutes and part 7 runs 28 minutes, where no single act on the programme should. Almost certainly each holds several contributions that were never separated, and the acts that follow them are the ones reported missing. Applause is the obvious cue between short contributions, and there is plenty of it here, so the boundary rule has room to improve.

The voices are clusters, not people. The colours in the speaker row mean "this sounds like the same person", not "this is the rector". Naming them is a human act, and on this page nobody has done it.

## Why this is on the website

Three reasons. The centre works on AI and creativity, and an honest example of what machine listening does to a real recording is worth more than a claim about it. The analysis is small, open data, while the recording stays where it was published. And the failure is as instructive as the success: a tool that says which acts it did not find is one you can work with.

The recording is the centre's own. Nothing about it is copied here, and nothing reaches YouTube until you press play.
