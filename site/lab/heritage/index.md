---
layout: lab
title: Heritage objects in place
permalink: /lab/heritage/
description: "Objects from Norwegian and European collections, and a KulturNav authority, shown on this page through their open APIs and IIIF, with the rights each collection states."
lab:
  authors: [mishmash.no]
  date: 2026-09-17
  status: prototype
  data: "Metadata, images, sound and film fetched in the browser from the National Library's catalogue API, from DigitaltMuseum's API, which also serves the National Museum, and from Europeana. Nothing is copied to this site, and a recording is only fetched when a reader presses play."
  ai: "The include, the script and this page were drafted with an AI assistant and reviewed by the site maintainers; see the AI colophon."
---

Norwegian collections publish their objects through open interfaces: the National Library through its catalogue and IIIF manifests, and most museums, the National Museum among them, through DigitaltMuseum. This page tries one include that shows such an object where a project page mentions it, with the title, the rights statement and a link back to the collection. Images that come with a IIIF image service open in a deep-zoom viewer; the others are shown at a fixed size.

The same fiddle, three ways.

## A photograph at the National Library

{% include heritage.html source="nb" id="3ab035574c80dd3baa18330fc9b3bc66" %}

## An object at a city museum, through DigitaltMuseum

{% include heritage.html source="dimu" id="51001787-efc8-4205-9c2d-bf7481864cb0" %}

## A painting at the National Museum, through DigitaltMuseum

{% include heritage.html source="dimu" id="3df10c96-b33b-45c1-92bf-d9211ce574c8" %}

## The same fiddle at Europeana, and the term at KulturNav

{% include heritage.html source="europeana" id="/502/_011023280005" %}

{% include heritage.html source="kulturnav" id="a269db7f-1082-443b-8df6-b24049d88e43" %}

## A recording, played where it stands

Collections hold sound and moving images as well as pictures, and the same include shows them. Europeana's record says what kind of object it is, and a recording gets a player instead of a picture.

{% include heritage.html source="europeana" id="/937/Culturalia_8ed234bd_3790_46ca_b6be_cfefd1123520" %}

## A film, from a European collection

{% include heritage.html source="europeana" id="/2051906/data_euscreenXL_https___www_openbeelden_nl_media_97919" %}

Neither of these costs a visit anything until someone presses play. The player is markup with `preload="none"`, so no audio or video is fetched, and the collection's server learns nothing about a reader who scrolls past. Both examples carry an open licence, which is why they can be played from here at all: the recording is CC BY-SA and the film is marked as public domain, and the line under each says so and links to the source.

## How it works

A page says which object it wants, by source and identifier:

```liquid
{% raw %}{% include heritage.html source="nb" id="3ab035574c80dd3baa18330fc9b3bc66" %}
{% include heritage.html source="dimu" id="3df10c96-b33b-45c1-92bf-d9211ce574c8" %}{% endraw %}
```

The reader's browser asks the collection for the object and shows what comes back. The rights line is the collection's own statement, and the link leads to the object's page at the source. Without JavaScript the link alone is shown. The deep-zoom viewer is [OpenSeadragon](https://openseadragon.github.io/), served from this site.

Europeana and KulturNav are now in too: Europeana for collections across Europe, through its public demo key, and KulturNav for the authorities, people, places and terms, that objects refer to. Where Wikidata knows an object or an authority by its collection identifier, a link to the Wikidata item is added as well; the painting above has one, the fiddle in Bø does not. That is the point of identifiers: the same thing, recognised across collections. That is the subject of [issue #50](https://github.com/MishMash-Norway/mishmash-web/issues/50).
