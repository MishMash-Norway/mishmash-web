---
layout: lab
title: Today's bubbles
permalink: /lab/daily-bubbles/
description: "A variation of the MishMash emblem, drawn again every night from the day's activity on the site."
lab:
  authors: [mishmash.no]
  date: 2026-07-04
  status: piece
  data: "The date, the number of results in the national research archive and the events coming up on this site. Each small bubble is one upcoming event."
  ai: "None. The drawing is a deterministic script, generative in the algorithmic sense; the script itself was written with an AI assistant."
---

Every night a script redraws the centre's emblem from that day's numbers: how many results are registered, how many events are coming, and the date as the seed. The same day always gives the same picture, and no two days give the same one. No model is involved, and the file says so itself: it carries the IPTC marker for an image drawn by an algorithm.

<div class="colophon-bubbles">
  <img src="/assets/images/bubbles/daily/mishmash_bubbles_daily.svg"
       alt="Today's generated variation of the MishMash bubble emblem"
       width="420">
</div>

The [AI colophon](/about/ai-colophon/) explains where this sits among the site's other uses of automation, and the [script](https://github.com/MishMash-Norway/mishmash-web/blob/main/scripts/generate_daily_bubbles.py) is a page of Python. If you want the emblem to play with rather than to look at, the [bubbles](/lab/bubbles/) are next door.
