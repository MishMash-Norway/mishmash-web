---
layout: default
lang: nb
title: Ordliste
translation_url: /about/glossary/
stretchtext: true
---

## Ordliste

Sentrale begreper brukt på mishmash.no. De samme definisjonene driver
{% include stretch.html term="stretchtext" %}-forklaringene i tekstene — ord
med stiplet understrek, som det der, som kan foldes ut — slik at denne listen
og forklaringene i tekstene alltid stemmer overens.

Der et begrep har en etablert definisjon i forskningslitteraturen, står den
under, med kilde. Sitattegn betyr at ordlyden er kildens egen; uten dem er det
en nær omskrivning. Disse definisjonene står på originalspråket.

{% assign entries = site.data.glossary | sort: "key" %}
<dl class="glossary">
{% for g in entries %}
  <dt id="{{ g.key }}"><strong>{{ g.term.nb | default: g.term.en }}</strong></dt>
  <dd>{{ g.definition.nb | default: g.definition.en | markdownify | remove: '<p>' | remove: '</p>' | strip }}
  {% if g.canonical %}<span class="glossary-canonical"><span class="glossary-canonical-label">I litteraturen:</span> {{ g.canonical | markdownify | remove: '<p>' | remove: '</p>' | strip }} <cite>{% if g.source_url %}<a href="{{ g.source_url }}">{{ g.source }}</a>{% else %}{{ g.source }}{% endif %}</cite></span>{% endif %}</dd>
{% endfor %}
</dl>

Savner du et begrep? Foreslå det via [nettsideprosjektet](/projects/the-mishmash-website/).
