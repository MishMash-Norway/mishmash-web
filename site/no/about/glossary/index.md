---
layout: default
lang: nb
title: Ordliste
translation_url: /about/glossary/
adaptive: true
description: "En ordliste over KI- og kreativitetsbegreper brukt på mishmash.no, på tre lesenivåer."
---

## Ordliste

Sentrale begreper brukt på mishmash.no, hvert forklart på tre nivåer. Bruk
velgeren øverst: *Enkel* er én setning i klartekst, *Standard* er
hverdagsforklaringen, og *Avansert* legger til presisjon, definisjonen fra
forskningslitteraturen og den norske definisjonen der en slik er fastsatt.

De samme tekstene driver
{% include stretch.html term="stretchtext" %}-forklaringene i tekstene — ord
med stiplet understrek, som det der, som kan foldes ut — slik at denne listen
og forklaringene i tekstene alltid stemmer overens, uansett hvilket nivå du
leser på.

<div class="adaptive" data-for="simple standard" markdown="1">
På nivået *Avansert* viser hvert begrep også definisjonen fra
forskningslitteraturen og den norske definisjonen, med kilder.
</div>

<div class="adaptive" data-for="advanced" markdown="1">
Der et begrep har en etablert definisjon i forskningslitteraturen, står den
under, med kilde, på originalspråket. Norske definisjoner er sitert fra
[Teknologirådets ordliste for kunstig intelligens](https://teknologiradet.no/ordliste-for-kunstig-intelligens/),
som Språkrådet har gjennomgått, og fra den nasjonale KI-strategien; de norske
termene i ordlisten følger samme liste. Sitattegn betyr at ordlyden er kildens
egen; uten dem er det en nær omskrivning.
</div>

{% assign entries = site.data.glossary | sort: "key" %}
{% assign top_level = site.data.audiences.groups | last %}
<dl class="glossary">
{% for g in entries %}
  <dt id="{{ g.key }}"><strong>{{ g.term.nb | default: g.term.en }}</strong></dt>
  <dd>
  {%- for lv in site.data.audiences.groups -%}
  {%- assign variant = g[lv.key] -%}
  {%- assign text = variant.nb | default: variant.en | default: g.standard.nb | default: g.standard.en -%}
  <span class="adaptive" data-for="{{ lv.key }}">{{ text | markdownify | remove: '<p>' | remove: '</p>' | strip }}</span>
  {%- endfor -%}
  {% if g.canonical %}<span class="adaptive glossary-ref" data-for="{{ top_level.key }}"><span class="glossary-ref-label">I litteraturen:</span> {{ g.canonical | markdownify | remove: '<p>' | remove: '</p>' | strip }} <cite>{% if g.source_url %}<a href="{{ g.source_url }}">{{ g.source }}</a>{% else %}{{ g.source }}{% endif %}</cite></span>{% endif %}
  {% if g.norsk %}<span class="adaptive glossary-ref" data-for="{{ top_level.key }}"><span class="glossary-ref-label">Norsk definisjon:</span> {{ g.norsk | markdownify | remove: '<p>' | remove: '</p>' | strip }} <cite>{% if g.norsk_source_url %}<a href="{{ g.norsk_source_url }}">{{ g.norsk_source }}</a>{% else %}{{ g.norsk_source }}{% endif %}</cite></span>{% endif %}
  </dd>
{% endfor %}
</dl>

Savner du et begrep? Foreslå det via [nettsideprosjektet](/projects/the-mishmash-website/).
