---
layout: page
title: Languages
permalink: /about/languages/
translation_url: /no/about/languages/
description: "The site's three language versions, how the Nynorsk pages are made, and how much of the text is in each language."
---

mishmash.no is written in English, with the main pages mirrored in Norwegian. Norwegian means both written forms: the Bokmål pages are written by hand, and the Nynorsk pages are made from them. The switch at the top of every page moves between the three versions of that page, or to the language's front page where no version exists.

## How the Nynorsk pages are made

Every Bokmål page is translated when the site is built, with an open-source rule-based translator (Apertium's Bokmål to Nynorsk pair, in moderate Nynorsk with "vi"). Names, code and links pass through untouched, and the centre's own terms are kept in a shared glossary. A page made this way says so at the bottom, with a link to the Bokmål page it comes from, until a member who writes Nynorsk has read and corrected it; a corrected page keeps its note about who read it and is not overwritten. Found a mistake in a Nynorsk page? Use "Suggest a change" at the bottom of the page.

## How much text is in each language

{% assign ls = site.data.language_share %}
{% if ls %}
Measured on the page sources on {{ ls.generated_at | date: "%-d %B %Y" }}, counting the words of every paragraph of five words or more and classifying each paragraph with a language detector that tells Bokmål and Nynorsk apart. Internal pages and the interface themes are left out, as search engines leave them out.

| Language | Words | Share of all text | Share of the Norwegian text |
| --- | ---: | ---: | ---: |
| English | {{ ls.words.en }} | {{ ls.share_percent.en }} % | |
| Bokmål | {{ ls.words.nb }} | {{ ls.share_percent.nb }} % | {{ ls.norwegian_share_percent.nb }} % |
| Nynorsk | {{ ls.words.nn }} | {{ ls.share_percent.nn }} % | {{ ls.norwegian_share_percent.nn }} % |

The Language Act asks state bodies to use at least a quarter of each written form over time. Språkrådet measures state websites with its Målfrid crawler, which counts words in the published pages in much the same way; the figures above are the site's own count and are refreshed with every build.
{% else %}
The count is made when the site is built and is not available in this build.
{% endif %}

## Sami and Kven

The Sami languages and Kven are not machine translated on this site: no translator of publishable quality exists for them, and the people who build Sami language technology advise against publishing unedited output. A core set of pages in North Sami and in Kven, translated by people, is planned with the partner institutions that hold the responsibility for those languages.
