---
title: "Inside out: how mishmash.no is built"
date: 2026-11-10
author: "Alexander Refsum Jensenius"
layout: page
published: false
categories: [Announcement]
description: "The MishMash website is generated from the data the network already keeps, checked for accessibility on every change, and open about how it is made, including its use of AI."
image: /assets/images/news/how-we-build-the-website/footer.webp
---

When a MishMash researcher registers a lecture in NVA and names the centre as funder, the lecture appears on mishmash.no the next morning. Nobody at the centre types it in. This is one example of how the website is built, which we have described in several talks this autumn and summarise here.

## Built from the inside

Most websites are designed from the front page and filled in by hand. We work the other way round. The site starts from the information the network already maintains elsewhere and is generated outwards from it. Every night, a script fetches people, publications and affiliations from [NVA](https://nva.sikt.no/) and [ORCID](https://orcid.org/), and institutions are linked to [Wikidata](https://www.wikidata.org/) and Wikipedia. A fact is kept in one place and pulled into the pages, so a new job title or a new article does not have to be updated on the website by hand.

![The results page on mishmash.no, with filter buttons for each type of result and the first book chapters in the list](/assets/images/news/how-we-build-the-website/results.webp)

*The [results page](/results/) is generated from NVA every night.*

The pages are plain text files in a [public repository on GitHub](https://github.com/MishMash-Norway/mishmash-web), and anyone can rebuild the whole site from them. The same files are published as [open data](/data/), so the people, projects, events and results can be reused by others.

## Turned inside out

The site is also inside out in the sense of a jacket with the seams showing. Every page has a panel at the bottom, "About the page", that says when it was last edited and by whom, under which licence it is published and where its data come from. Pages made with AI support say so in the same panel. A link leads to the source file, and another to a form for suggesting a change.

![The "About the page" panel at the bottom of a page, listing last edited, reading time, source code, licence, privacy, abbreviations, accessibility and data sources](/assets/images/news/how-we-build-the-website/footer.webp)

*The panel at the bottom of every page.*

The site is developed with AI coding assistants, and people review the changes before they are published. Each change is recorded in the public history, and the [AI colophon](/about/ai-colophon/) collects the AI-assisted changes for the whole site. The colophon also shows how much data a visit to some of the pages transfers, and an estimate of the carbon this causes, measured each time the site is published.

![A table of pages on mishmash.no with the kilobytes, the number of requests and the grams of CO₂ per visit for each](/assets/images/news/how-we-build-the-website/page-weight.webp)

*The weight of a set of pages, measured at each deployment.*

The Nynorsk edition is the most visible experiment. It is translated from the Bokmål pages by the open-source machine translator Apertium every time the site is built, and it is published without proofreading. A note at the top of each page says so. We do this to show what the tools manage on their own, and the [languages page](/about/languages/) explains how it is done.

![A Nynorsk page on mishmash.no with a note at the top saying that the page is translated automatically from the Bokmål edition and may contain errors](/assets/images/news/how-we-build-the-website/nynorsk.webp)

*The note at the top of every machine-translated Nynorsk page.*

## Accessibility as a test

Norwegian law asks public websites to meet level AA of the Web Content Accessibility Guidelines. We test the contrast of text against the stricter level AAA. An automated scan runs on pages in all three languages whenever the site changes, and a single error fails the check. The [accessibility page](/accessibility/) lists what is checked and what is not yet in place, such as captions on all videos.

## A lab in the browser

The [lab](/lab/) collects small experiments built on the site's own data. One plays the publication list as sound, another runs a search model on the reader's own device, and a third draws the footprint of the site beside the same page built the usual way. Each page explains how the experiment works and where it fails. Students have also made alternative interfaces for the whole site, which are published as live previews under [/ui/](/ui/).

![The lab page on mishmash.no, with cards for experiments such as the term atlas, the footprint of the website and convolving sounds from Freesound](/assets/images/news/how-we-build-the-website/lab.webp)

*The [lab](/lab/) collects experiments on the site's own data.*

## How to take part

Everyone in the network can suggest a change through the link at the bottom of every page. Those who want to edit the site directly can start with the [project wiki](https://github.com/MishMash-Norway/mishmash-web/wiki), which assumes no prior knowledge, and the [web philosophy](https://github.com/MishMash-Norway/mishmash-web/wiki/Web-Philosophy) sets out the ideas behind it. Questions can be sent to [contact@mishmash.no](mailto:contact@mishmash.no).
