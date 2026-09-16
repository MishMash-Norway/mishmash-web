---
layout: lab
title: Name of the experiment
permalink: /lab/short-slug/
description: "One sentence saying what the piece does, for listings and search."
# custom_css: /assets/css/short-slug.css
# search: false        # leave the piece out of the site search
lab:
  authors: [Your Name, Another Name]
  date: 2026-10-01
  status: experiment   # experiment, prototype or piece
  data: "What the piece draws on and where it comes from, for example the results list synced from NVA."
  ai: "How AI was involved, for example: the D3 code was drafted with an AI assistant and reviewed by the authors."
---

Write a short introduction that stands on its own. Then the piece itself: a `<div>` the script draws into, a `<noscript>` fallback that says what the reader is missing, and the scripts at the end.

<div id="my-piece"></div>
<noscript><p>This piece needs JavaScript.</p></noscript>

<script src="{{ '/assets/js/lib/d3.v7.min.js' | relative_url }}"></script>
<script src="{{ '/assets/js/short-slug.js' | relative_url }}"></script>
