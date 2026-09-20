---
layout: page
title: AI colophon
translation_url: /no/about/ai-colophon/
---


MishMash studies creative uses of AI, and uses AI openly in making this website. This page declares how, so that readers and partners never have to guess whether AI was involved.

## Where AI contributes

- **Content.** AI assistance is used for drafting and adapting texts, including the reading-level variants on [adaptive pages](/about/description/) and entries in the [glossary](/about/glossary/). Editors review and revise before anything is published.
- **Code and automation.** Much of the site's tooling, including the sync scripts that pull data from NVA, ORCID and Wikipedia, the theme switcher, the adaptive-content machinery and the quality checks, is developed with AI assistance, visible in the repository's [commit history](https://github.com/MishMash-Norway/mishmash-web/commits/main) through `Co-Authored-By` trailers.
- **Translation.** Machine translation is used between English and Norwegian, and is marked as such on the pages concerned.
- **Artwork.** The bubble variation below is redrawn every night by a [small script](https://github.com/MishMash-Norway/mishmash-web/blob/main/scripts/generate_daily_bubbles.py): a deterministic sketch seeded by the date and the day's site activity (each small bubble is an upcoming event). It is generative in the algorithmic sense, with no AI model involved. The file says so itself: generated images on this site carry the IPTC digital source type in their metadata (algorithmicMedia for script-drawn images, trainedAlgorithmicMedia for anything an AI model makes), with the creator, the licence and a link to the terms, and the build checks that the marker is there.

<div class="colophon-bubbles">
  <img src="/assets/images/bubbles/daily/mishmash_bubbles_daily.svg"
       alt="Today's generated variation of the MishMash bubble emblem"
       width="340">
  <p>Today's bubbles, generated nightly from site activity</p>
</div>


## Our commitments

1. **Humans are responsible.** AI output is generally reviewed before it goes live. The exception is the nightly builds, retrieving new data from NVA and ORCID. In any case, errors are ours, not the machine's.
2. **Nothing is hidden.** AI involvement is declared here, marked on translated pages, and traceable in the open [commit history](https://github.com/MishMash-Norway/mishmash-web/commits/main).
3. **It is an experiment.** Building our own communication channel with AI-based assistance is part of MishMash's research practice. It is a way to *create, explore, and reflect* on the tools we study. What we learn feeds back into the centre's research and teaching.

## The weight of the site

A light site costs readers less time and the planet less energy. At every deployment the build weighs a set of pages in a headless browser with an empty cache: the bytes a first visit transfers, counted as the server sends them, and an estimate of the carbon per visit using the Sustainable Web Design model as implemented in CO2.js. The count covers everything a reader of the whole page is sent, and leaves out the slides a gallery keeps hidden until asked for and pictures hotlinked from other sites. The figures are an estimate for comparing builds, not a measurement of anyone's device or network. The full report is at [/data/page-weight.json](/data/page-weight.json){: data-proofer-ignore="true"}.

The build also cuts the web fonts down to the characters the site actually uses. The whole site is written with about 300 different characters, while a general Latin font file carries thousands of glyphs, so the font files shrink by roughly half and a first visit to the front page loads 85 kB of fonts instead of 198 kB. A character that no page uses falls back to a font already on the reader's device.

<div id="page-weight" class="page-weight" data-src="/data/page-weight.json" data-lang="en"><noscript>The table needs JavaScript; the figures are in the JSON file linked above.</noscript></div>
<script defer src="/assets/js/page-weight.js"></script>

## The Nynorsk experiment

The Nynorsk edition of the site (the pages under `/nn/`) is generated automatically: every Bokmål page is translated at build time with the rule-based, open-source [Apertium](https://github.com/apertium/apertium-nno-nob) engine (nob–nno, moderate norm), the same engine the Norwegian press agency NPK and NRK use for Nynorsk. Every generated page is marked with a notice at the top and links back to its Bokmål original. A hand-corrected page under `site/nn/` in the source always wins over the generated one.

We publish the edition knowing it contains errors. That is the point: MishMash wants to test things in the open, expose problems, and fix them, in our own systems and in the underlying ones. It is part of the MishMash DNA. If you spot a mistake, use "Suggest a change" in the footer and we fix the tooling or the page.

{% include ai-colophon-commits.html lang="en" %}

More about the thinking behind the site: the [web philosophy](https://github.com/MishMash-Norway/mishmash-web/wiki/Web-Philosophy) in the project wiki and the centre's [communication strategy](/internal/communication-strategy/). Questions or concerns: [contact@mishmash.no](mailto:contact@mishmash.no).
