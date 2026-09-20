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

Several Norwegian collections publish their objects through open interfaces: the National Library through its catalogue and IIIF manifests, and most museums, the National Museum among them, through DigitaltMuseum. This page explores how it is possible to integrate such data and media on an external website. 

## A photograph at the National Library

{% include heritage.html source="nb" id="3ab035574c80dd3baa18330fc9b3bc66" %}

## An object at a city museum, through DigitaltMuseum

{% include heritage.html source="dimu" id="51001787-efc8-4205-9c2d-bf7481864cb0" %}

## A painting at the National Museum, through DigitaltMuseum

{% include heritage.html source="dimu" id="3df10c96-b33b-45c1-92bf-d9211ce574c8" %}

## The same fiddle at Europeana, and the term at KulturNav

{% include heritage.html source="europeana" id="/502/_011023280005" %}

{% include heritage.html source="kulturnav" id="a269db7f-1082-443b-8df6-b24049d88e43" %}

## An audio file, from a European collection

Currently, no Norwegian collection allows for embedding audio similar to images. However, some European collections do. Here is an example from an Europeana record, which says what kind of object it is, and offers a player to be embedded. 

{% include heritage.html source="europeana" id="/937/Culturalia_8ed234bd_3790_46ca_b6be_cfefd1123520" %}

## A video file, from a European collection

Norwegian institutions do not currently offer video files either. But here is an example of how it could work.

{% include heritage.html source="europeana" id="/2051906/data_euscreenXL_https___www_openbeelden_nl_media_97919" %}

## Privacy

The audio and video players above are marked up with `preload="none"`, so no audio or video is fetched before a user presses play. This also means that the collection's server learns nothing about a reader who scrolls past, which preserves privacy for the user. 

## Licensing

Both audio and video examples carry an open licence, which is why they can be played from here. The audio recording is CC BY-SA and the video file is marked as public domain.

## How it works

A page says which object it wants, by source and identifier:

```liquid
{% raw %}{% include heritage.html source="nb" id="3ab035574c80dd3baa18330fc9b3bc66" %}
{% include heritage.html source="dimu" id="3df10c96-b33b-45c1-92bf-d9211ce574c8" %}{% endraw %}
```

The reader's browser asks the collection for the object and shows what comes back. The rights line is the collection's own statement, and the link leads to the object's page at the source. Without JavaScript the link alone is shown.

What appears depends on what the record says the object is.

A picture comes as an address the browser loads directly. Where the collection also runs a IIIF image service, the include asks that service for the picture instead, and the reader gets a deep-zoom viewer, [OpenSeadragon](https://openseadragon.github.io/), served from this site. Nothing is copied here: the tiles come from the collection as the reader zooms.

An audio file or a video file comes the same way, as an address, and the include puts it in an HTML `audio` or `video` element with the browser's own controls. There is no player library and no third-party embed code. The address is the one the record gives as its main file, so the bytes come from the collection's own server when the reader presses play, and the collection can count that play in its own statistics. A video record also carries a still picture, which becomes the poster.

The same rule decides all three: the record says what kind of object this is, the include shows it accordingly, and the rights line under it is whatever the collection states.

Europeana and KulturNav are now in too: Europeana for collections across Europe, through its public demo key, and KulturNav for the authorities, people, places and terms, that objects refer to. 

## Linking data

The same object is often held in more than one place. The painting above is in the National Museum's catalogue, in DigitaltMuseum, and in Wikidata; the fiddle in Bø is in its museum's catalogue and in Europeana. Each of them gives it a different number.

Wikidata keeps those numbers next to each other. An item there can carry a DigitaltMuseum identifier or a KulturNav identifier as a property, so asking Wikidata "who has this identifier" gives back the item that stands for the same thing, if anyone has made the connection.

That is what the include does after it has shown an object. It asks Wikidata whether any item carries this collection's identifier for it, and adds a link where exactly one item answers. The painting has such an item; the fiddle in Bø does not, and the line stays as the collection wrote it.

The value is not the extra link. It is that a page which mentions an object can reach everything else known about it, in any collection that has joined the same identifier, without anyone writing those connections by hand. Making more of them, and giving some back, is the subject of [issue #50](https://github.com/MishMash-Norway/mishmash-web/issues/50).
