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

The pipeline listens rather than reads, and now it also looks. It tags sound events, separates music from speech, finds where the room applauds, clusters the voices, transcribes what is said, and reads the slides on the projection with optical character recognition. It knew the programme from the event page, and matched what it found against it.

It found ten parts for ten acts, and nine of the ten begin within a second or two of the title card the hall put up for that act. It marked 36 stretches of sound and heard 14 distinct voices across 132 turns.

## What the slides changed

The first version of this page reported seven parts against ten acts, with three acts not found. The applause rule was to blame: it cuts where talk follows the applause, which is right at a concert, where the audience applauds between pieces, and wrong here, where a contribution is applauded and a performance follows. Knowing the programme had ten acts, the detector can now go back and split its longest parts at the applause inside them, which found the three missing boundaries.

Then came the better signal. This hall projects a card when an act begins, with the work and the people in it. That card is written rather than spoken, so it survives a bilingual event and a host who says nothing, and it changes exactly when the act changes. Reading the projection took three minutes, and the boundaries moved from "somewhere near the applause" to the second the card came up. While a card is up the act is still running, so a panellist who held the floor for ten minutes no longer looks like a new act.

The marks under the part bands above are those cards.

## What the programme got wrong

The programme on the event page is not the order the evening ran in. It lists both panels at the end, while the first panel came fourth, straight after the opening contributions, and a percussion piece closed the evening. The pipeline now takes the act that was named at each boundary, by the card and by what was said, rather than by the printed order. That gets six of the ten right and three wrong, and one part says plainly that it does not know, where the printed order got four right and six wrong.

## What is still wrong

One act, the percussion piece that closed the evening, has no card in the reading: the projection was dark at that moment, and the last part therefore holds both the closing panel and the piece. Two names are swapped, the rector and the first performance, because the cards for them come up while the previous act is still finishing.

The voices are clusters, not people. The colours in the speaker row mean "this sounds like the same person", not "this is the rector". Naming them is a human act, and on this page nobody has done it.

## Why this is on the website

Three reasons. The centre works on AI and creativity, and an honest example of what machine listening and machine reading do to a real recording is worth more than a claim about it. The analysis is small, open data, while the recording stays where it was published. And the failures are as instructive as the successes: this recording is the reason [avsegmenter](https://github.com/fourMs/avsegmenter) now uses the running order to decide how many parts to look for, and reads the projection to decide where they begin.

The recording is the centre's own. Nothing about it is copied here, and nothing reaches YouTube until you press play.
