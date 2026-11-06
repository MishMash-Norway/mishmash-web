---
layout: page
title: AI colophon
translation_url: /no/about/ai-colophon/
---

MishMash studies creative uses of AI, and uses AI openly in making this website.

## Where AI contributes

- **Content.** AI assistance is used for drafting and adapting texts, including the reading-level variants on [adaptive pages](/about/description/) and entries in the [glossary](/about/glossary/). Human editors review and revise them, often over several rounds with machine edits.
- **Code and automation.** Much of the site's tooling, including the sync scripts that pull data from NVA, ORCID, Wikipedia, Wikimedia and Wikidata, the theme switcher, the adaptive-content machinery and the quality checks, is developed with AI assistance, marked by `Co-Authored-By` trailers in the repository's [commit history](https://github.com/MishMash-Norway/mishmash-web/commits/main).
- **Translation.** Machine translation is used between English and Norwegian (both *bokmål* and *nynorsk*), and is marked as such on the pages concerned.
- **Artwork.** The bubble variation below is redrawn every night by a [small script](https://github.com/MishMash-Norway/mishmash-web/blob/main/scripts/generate_daily_bubbles.py): a deterministic sketch seeded by the date and the day's site activity (each small bubble is an upcoming event). It is generative in the algorithmic sense, and no AI model is involved. Generated images on this site carry the IPTC digital source type in their metadata (algorithmicMedia for script-drawn images, trainedAlgorithmicMedia for anything an AI model makes), with the creator, the licence and a link to the terms, and the build checks that the marker is there.

<div class="colophon-bubbles">
  <img src="/assets/images/bubbles/daily/mishmash_bubbles_daily.svg"
       alt="Today's generated variation of the MishMash bubble emblem"
       width="340">
  <p>Today's bubbles, generated nightly from site activity</p>
</div>


## Our commitments

1. **Humans are responsible.** AI output is generally reviewed before it goes live. The exception is the nightly builds, which retrieve new data from NVA and ORCID. Errors are ours, not the machines'.
2. **Nothing is hidden.** AI involvement is declared, marked on translated pages, and traceable in the open [commit history](https://github.com/MishMash-Norway/mishmash-web/commits/main).
3. **Our use of AI is part of our research.** Building our own communication channels with AI-based assistance is a way to *create, explore, and reflect* on the tools we study, and what we learn feeds back into the centre's research and teaching.

## The weight of the site

Sustainability is a key concern for MishMash, and building our own website gives us full control of how it is rendered and served. At each deployment, the build weighs a set of pages in a headless browser with an empty cache and estimates the carbon per visit using the Sustainable Web Design model as implemented in CO2.js. The full report is at [/data/page-weight.json](/data/page-weight.json){: data-proofer-ignore="true"}, and the lab page [The footprint of this website](/lab/footprint/) draws and plays it beside the same page built the usual way.

The site saves bandwidth by compressing images and serving them progressively when needed, and by cutting the web fonts down to the characters the site uses. The whole site is written with about 300 different characters, while a general Latin font file carries thousands of glyphs, so the font files shrink by roughly half and a first visit to the front page loads 85 kB of fonts instead of 198 kB.

<div id="page-weight" class="page-weight" data-src="/data/page-weight.json" data-lang="en"><noscript>The table needs JavaScript; the figures are in the JSON file linked above.</noscript></div>
<script defer src="/assets/js/page-weight.js"></script>

## The Nynorsk experiment

The Nynorsk edition of the site (the pages under `/nn/`) is generated automatically: every Bokmål page is translated at build time with the rule-based, open-source [Apertium](https://github.com/apertium/apertium-nno-nob) engine (nob–nno, moderate norm). Apertium is also the engine under Nynorskroboten, the tool NTB and NRK use for Nynorsk, where the output is proofread before it is published. Every generated page is marked with a notice at the top and links back to its Bokmål original. A hand-corrected page under `site/nn/` in the source always wins over the generated one.

Språkrådet's evaluation of six Bokmål to Nynorsk tools, [*Frå bokmål til nynorsk*](https://sprakradet.no/wp-content/uploads/Fra-bokmal-til-nynorsk-evaluering-av-maskinomsetjingsverktoy-hausten-2025.pdf) (autumn 2025), found errors in about four in ten machine-translated sentences, with little difference between rule-based tools and chatbots. It advises government bodies to make drafts with an Apertium-based tool and to have every text checked by someone who writes Nynorsk well. The Nynorsk edition of mishmash.no follows the first piece of advice and not the second: it is an experiment in what the tools do on their own, not the centre's official Nynorsk. So that it does not become training material for future language models, the generated pages are reserved against text and data mining (see the [terms](/about/terms/)), kept out of the crawlers that collect training data, and marked in machine-readable form as translated from Bokmål by Apertium.

We publish the edition knowing it contains errors, to show the limitations of current models and help improve them. MishMash tests things in the open, exposes problems and fixes them, in our own systems and in the underlying ones. If you spot a mistake, use "Suggest a change" in the footer and we fix the tooling or the page.

{% include ai-colophon-commits.html lang="en" %}

The thinking behind the site is set out in the [web philosophy](https://github.com/MishMash-Norway/mishmash-web/wiki/Web-Philosophy) in the project wiki and the centre's [communication strategy](/internal/communication-strategy/). Send questions or concerns to [contact@mishmash.no](mailto:contact@mishmash.no).
