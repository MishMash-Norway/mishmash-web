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
  {%- assign term_nb = g.term.nb | default: g.term.en -%}
  <dt id="{{ g.key }}"><strong>{{ term_nb }}</strong>{% include glossary-copy-link.html key=g.key term=term_nb %}</dt>
  <dd>
  {%- for lv in site.data.audiences.groups -%}
  {%- assign variant = g[lv.key] -%}
  {%- assign text = variant.nb | default: variant.en | default: g.standard.nb | default: g.standard.en -%}
  <span class="adaptive" data-for="{{ lv.key }}">{{ text | markdownify | remove: '<p>' | remove: '</p>' | strip }}</span>
  {%- endfor -%}
  {%- for r in g.references -%}
  {%- case r.kind -%}
  {%- when 'literature' -%}{%- assign ref_label = 'I litteraturen' -%}
  {%- when 'standard' -%}{%- assign ref_label = 'I standarder' -%}
  {%- when 'policy' -%}{%- assign ref_label = 'I regelverk' -%}
  {%- else -%}{%- assign ref_label = 'Norsk definisjon' -%}
  {%- endcase %}
  <span class="adaptive glossary-ref" data-for="{{ top_level.key }}"><span class="glossary-ref-label">{{ ref_label }}:</span> {{ r.quote | markdownify | remove: '<p>' | remove: '</p>' | strip }} <cite>{% if r.url %}<a href="{{ r.url }}">{{ r.source }}</a>{% else %}{{ r.source }}{% endif %}</cite></span>
  {%- endfor %}
  </dd>
{% endfor %}
</dl>
<script defer src="/assets/js/glossary.js"></script>

Savner du et begrep? Foreslå det via [nettsideprosjektet](/projects/the-mishmash-website/).
