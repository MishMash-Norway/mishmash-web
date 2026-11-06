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

Several Norwegian collections publish their objects through open interfaces: the National Library through its catalogue and IIIF manifests, and most museums, the National Museum among them, through DigitaltMuseum. This page tests how such data and media can be shown on an external website.

## A photograph at the National Library

{% include heritage.html source="nb" id="URN:NBN:no-nb_digifoto_20180307_00007_NB_NS_NM_05512" %}

## An object at a city museum, through DigitaltMuseum

{% include heritage.html source="dimu" id="51001787-efc8-4205-9c2d-bf7481864cb0" %}

## A painting at the National Museum, through DigitaltMuseum

{% include heritage.html source="dimu" id="3df10c96-b33b-45c1-92bf-d9211ce574c8" %}

## The same fiddle at Europeana, and the term at KulturNav

{% include heritage.html source="europeana" id="/502/_011023280005" %}

{% include heritage.html source="kulturnav" id="a269db7f-1082-443b-8df6-b24049d88e43" %}

## The tunes written down, at the National Library

The National Library's music manuscripts are the one part of its collection that this page can show without asking for permission. 7,678 of the 11,150 are freely viewable, and every one sampled carries CC BY-NC-ND 4.0 and a IIIF image service, the same kind of service as the photograph at the top of this page. Among them are the folk music collections gathered from the 1840s on, 2,624 manuscripts from the six collectors the library lists: Lindeman, Crøger, Sande, Elling, Sandvik and Groven.

The manuscript below is a set of tunes for the instrument the objects above stand for. It runs to 1,373 pages, so the viewer turns them and fetches only the page asked for, which keeps a manuscript of this size cheap to show.

Turning a page costs one request for the page's description and then its tiles. The collection's image server sends no caching headers (no `cache-control`, no `etag` and no `last-modified`), so a browser cannot judge freshness and asks again every time. This page therefore keeps each description once it has it, and going back to a page already seen costs no description request. The tiles are the collection's to control, and a `cache-control` header on its side would save its traffic as much as the reader's wait.

{% include heritage.html source="nb" id="URN:NBN:no-nb_digimanus_322945" %}

## A composer and performer, in the shared authority register

The National Library and Sikt keep a shared register of people and organisations, [Felles autoritetsregister](https://bibliotekutvikling.no/kunnskapsorganisering/vokabularer/felles-autoritetsregister-for-personer-og-korporasjoner/), which libraries use to say which person a book or a manuscript is by. Its open interface gives, for a person, the established form of the name and the dates, the other forms the name is written in, a short note on who the person is, and identifiers for the same person elsewhere: a persistent handle, ISNI, VIAF, and others such as Discogs. It holds no biography and no pictures.

The National Library's catalogue does not carry the register's identifier on each item. The include therefore finds the person's works by the established name and dates together, which is how the catalogue records a person, and links each one by its URN where it has one. Wikidata stores the register's identifier as P1015, so the person's Wikidata item is found the same way as for the objects above.

The example is the violinist and composer Ole Bull, with one of his manuscripts.

{% include heritage.html source="noraf" id="90092217" %}

{% include heritage.html source="nb" id="URN:NBN:no-nb_digimanus_189231" %}

## An audio file, from a Norwegian museum

Norwegian museums publish sound through DigitaltMuseum, and 1,577 records carry a recording. Of those, 592 have a Creative Commons licence. The file is served as an ordinary address, so the same include that shows a picture can show a recording. The example is a telling of how the fiddle tune Refshaugen got its name, from a record that names its reader and its licence.

{% include heritage.html source="dimu" id="7a849ad9-7194-1014-b55f-47e143b72dbd" %}

## An audio file, from a European collection

The National Library's radio programmes cannot be played from here. The library has 100,640 programmes anyone may listen to, and each carries a IIIF manifest that names the recording and the rights, but the media server answers requests from nb.no only. European collections often serve the file openly instead. The example is a Europeana record, which says what kind of object it is and offers a player to be embedded.

{% include heritage.html source="europeana" id="/937/Culturalia_8ed234bd_3790_46ca_b6be_cfefd1123520" %}

## A video file, from a Norwegian museum

Film works the same way. DigitaltMuseum holds 2,298 records with a film, 1,166 of them under a Creative Commons licence. The picture in the record becomes the poster frame, so the reader sees what the film is before deciding to fetch it.

{% include heritage.html source="dimu" id="74f48aee-c0bc-11e4-9b5b-a291a32f8a16" %}

## A video file, from a European collection

For comparison, the example below is a film from a European collection.

{% include heritage.html source="europeana" id="/2051906/data_euscreenXL_https___www_openbeelden_nl_media_97919" %}

## Privacy

The audio and video players above are marked up with `preload="none"`, so no audio or video is fetched before the reader presses play, and the collection's server learns nothing about a reader who scrolls past.

## Licensing

All four recordings carry an open licence, which is why they can be played from here. The two Norwegian ones are CC BY and CC BY-SA, the European audio is CC BY-SA, and the European video is marked as public domain. The licence is read from the record each time the page loads, so it is the collection's statement and not a copy of it.

## How it works

A page says which object it wants, by source and identifier:

```liquid
{% raw %}{% include heritage.html source="nb" id="URN:NBN:no-nb_digifoto_20180307_00007_NB_NS_NM_05512" %}
{% include heritage.html source="dimu" id="3df10c96-b33b-45c1-92bf-d9211ce574c8" %}{% endraw %}
```

The identifier is the persistent one wherever the collection has one. For the National Library that is the URN:NBN, which the library undertakes to resolve through `urn.nb.no` for as long as the object exists; the page resolves it to the catalogue's item when it loads, and links to the URN. DigitaltMuseum's object identifiers, Europeana's record identifiers and KulturNav's are already the stable ones those services cite.

The reader's browser asks the collection for the object and shows what comes back. The rights line is the collection's own statement, and the link leads to the object's page at the source. Without JavaScript the link alone is shown.

What appears depends on what kind of object the record says it is. A picture comes as an address the browser loads directly. Where the collection also runs a IIIF image service, the include asks that service for the picture instead, and the reader gets a deep-zoom viewer, [OpenSeadragon](https://openseadragon.github.io/), served from this site. Nothing is copied here: the tiles come from the collection as the reader zooms.

An audio file or a video file comes the same way, as an address, and the include puts it in an HTML `audio` or `video` element with the browser's own controls. There is no player library and no third-party embed code. The address is the one the record gives as its main file, so the bytes come from the collection's own server when the reader presses play, and the collection can count that play in its own statistics. A video record also carries a still picture, which becomes the poster.

Besides the National Library and DigitaltMuseum, the include reads Europeana, for collections across Europe, through its public demo key, and KulturNav, for the authorities (people, places and terms) that objects refer to.

## Linking data

The same object is often held in more than one place. The painting above is in the National Museum's catalogue, in DigitaltMuseum and in Wikidata; the fiddle in Bø is in its museum's catalogue and in Europeana. Each of them gives it a different number.

Wikidata keeps those numbers next to each other. An item there can carry a DigitaltMuseum identifier or a KulturNav identifier as a property, so asking Wikidata which item has this identifier gives back the item that stands for the same thing, if anyone has made the connection.

After showing an object, the include asks Wikidata whether any item carries this collection's identifier for it, and adds a link where exactly one item answers. The painting has such an item; the fiddle in Bø does not, and its line stays as the collection wrote it.

The use of such a link is that a page which mentions an object can reach everything else known about it, in any collection that has joined the same identifier, without anyone writing those connections by hand. Making more of these links, and giving some back, is the subject of [issue #50](https://github.com/MishMash-Norway/mishmash-web/issues/50).
