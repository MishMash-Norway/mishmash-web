---
layout: lab
title: Heritage objects in place
permalink: /lab/heritage/
description: "Three objects from Norwegian collections shown on this page through their open APIs and IIIF, with the rights each collection states."
lab:
  authors: [mishmash.no]
  date: 2026-09-17
  status: prototype
  data: "Metadata and images fetched in the browser from the National Library's catalogue API and from DigitaltMuseum's API, which also serves the National Museum. Nothing is copied to this site."
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

## How it works

A page says which object it wants, by source and identifier:

```liquid
{% raw %}{% include heritage.html source="nb" id="3ab035574c80dd3baa18330fc9b3bc66" %}
{% include heritage.html source="dimu" id="3df10c96-b33b-45c1-92bf-d9211ce574c8" %}{% endraw %}
```

The reader's browser asks the collection for the object and shows what comes back. The rights line is the collection's own statement, and the link leads to the object's page at the source. Without JavaScript the link alone is shown. The deep-zoom viewer is [OpenSeadragon](https://openseadragon.github.io/), served from this site.

What a wider version would add: Europeana for collections outside Norway, KulturNav authorities for the people and places an object names, and a Wikidata link where the object has one. That is the subject of [issue #50](https://github.com/MishMash-Norway/mishmash-web/issues/50).
