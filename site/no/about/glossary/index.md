---
layout: default
lang: nb
title: Ordliste
translation_url: /about/glossary/
---

## Ordliste

Sentrale begreper brukt på mishmash.no. De samme definisjonene driver
[stretchtext](https://github.com/MishMash-Norway/mishmash-web/wiki/Adaptive-Content)-forklaringene
i tekstene — ord med stiplet understrek som kan foldes ut — slik at denne
listen og forklaringene i tekstene alltid stemmer overens.

{% assign entries = site.data.glossary | sort: "key" %}
<dl class="glossary">
{% for g in entries %}
  <dt id="{{ g.key }}"><strong>{{ g.term.nb | default: g.term.en }}</strong></dt>
  <dd>{{ g.definition.nb | default: g.definition.en | markdownify | remove: '<p>' | remove: '</p>' | strip }}</dd>
{% endfor %}
</dl>

Savner du et begrep? Foreslå det via [nettsideprosjektet](/projects/the-mishmash-website/).
