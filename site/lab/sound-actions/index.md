---
layout: lab
title: Convolving sounds from Freesound
permalink: /lab/sound-actions/
custom_css: /assets/css/freesound-morph.css
description: "Fifteen everyday sound actions, published openly on Freesound, fetched and convolved with each other in the browser."
lab:
  authors: [mishmash.no]
  date: 2026-09-20
  status: experiment
  data: "Fifteen recordings from the SoundActions dataset, published on Freesound under CC BY by Alexander Refsum Jensenius. The page holds their titles, licences and addresses; the sound files themselves stay at Freesound and are fetched only when a reader presses a button."
  ai: "The page and the script were drafted with an AI assistant and reviewed by the site maintainers. The sound processing is plain Web Audio, with no machine learning involved."
---

Freesound is where a great deal of research sound already lives, openly licensed and addressable. This page takes fifteen recordings from it and asks what a browser can do with them beyond playing them back.

The recordings are from the SoundActions dataset, made by Alexander Refsum Jensenius: one sound-producing action recorded every day for a year, published on Freesound under his account there. Uncorking a wine bottle, a necklace dropped on a table, a drum machine, a box opened.

<div id="freesound-morph">
  <p>Loading the list of sounds…</p>
</div>
<noscript><p>This piece needs JavaScript. The sounds themselves are on <a href="https://freesound.org/people/alexarje/sounds/">Freesound</a>.</p></noscript>

<script type="application/json" id="freesound-data">{{ site.data.freesound | jsonify }}</script>
<script defer src="{{ '/assets/js/freesound-morph.js' | relative_url }}"></script>

## What convolution does

Convolution takes every moment of one sound and sets the other sound ringing at that moment. It is how reverberation is simulated: record a handclap in a hall, convolve dry music with that recording, and the music sounds as if it were played in the hall.

Here neither sound is a handclap and neither is a hall. Convolving the cork with the drum machine gives a drum machine that sounds struck rather than triggered. Convolving two long sounds smears them into each other. The order matters less than it seems, since convolution is commutative, but the result is levelled differently each way and the ear notices.

## Embedding a sound from Freesound

Freesound offers its own player as an iframe, which the site can include on any page:

{% include freesound.html id="863344" title="Opening Champagne bottle (SoundAction 365)" %}

That player is Freesound's own. It used to load with the page, until a measurement showed what it brings with it: the player's page loads Google Fonts, so opening this page quietly contacted Google as well. It now waits for a press, like the video players elsewhere on the site.

The piece above takes the other route entirely: the page holds only the address of the sound file, and the browser fetches that one file when a reader presses a button.

## Privacy

Nothing reaches Freesound from this page until you press a button, and that includes the embedded player. Freesound then sees the request for the sound file, as any site serving a file does. Loading their player also loads Google Fonts, which is their choice rather than ours and another reason for the press.

## Licensing

All fifteen recordings are published under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), which is why they can be played and processed here. The name of the recordist and a link to each sound are shown beside the players, which is what that licence asks for. The convolution of two CC BY recordings is a derivative of both, so anything made here and kept would carry the same terms and both credits.

## How it works

`scripts/sync_freesound.py` collects the title, author, licence, tags and preview address of each sound from Freesound's public pages, with no API key, into `site/_data/freesound.yml`. The page renders that list into the markup, and the script fetches a sound only when asked, decodes it with the Web Audio API, and renders the convolution offline before playing it, so the result can be levelled first. There is no audio library.

A Freesound API key would give this more: the sounds of a MishMash pack rather than one account, the licence straight from the source, and the analysis Freesound already holds for every sound. That is the rest of [issue #47](https://github.com/MishMash-Norway/mishmash-web/issues/47).
