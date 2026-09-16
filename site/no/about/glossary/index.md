---
layout: page
lang: nb
title: Ordliste
translation_url: /about/glossary/
adaptive: true
description: "En ordliste over KI- og kreativitetsbegreper brukt på mishmash.no, på tre lesenivåer."
---


Sentrale begreper brukt på mishmash.no, hvert forklart på tre nivåer. Bruk
velgeren øverst: *Enkel* er én setning i klartekst, *Standard* er
hverdagsforklaringen, og *Avansert* legger til presisjon og de etablerte
definisjonene fra standarder, regelverk, forskningslitteraturen og norske kilder.

De samme tekstene driver
{% include stretch.html term="stretchtext" %}-forklaringene i tekstene — ord
med stiplet understrek, som det der, som kan foldes ut — slik at denne listen
og forklaringene i tekstene alltid stemmer overens, uansett hvilket nivå du
leser på.

<div class="adaptive" data-for="simple standard" markdown="1">
Bytt til *Avansert* for å se hvor hver definisjon kommer fra. Hvert begrep
viser da også hvordan standarder, lover, forskning og norske kilder definerer det.
</div>

<div class="adaptive" data-for="advanced" markdown="1">
Der et begrep har en etablert definisjon andre steder, står den under, med
kilde og på originalspråket, i denne rekkefølgen: internasjonale standarder
(ISO/IEC 22989 og beslektede standarder, NIST), regelverk og politikk (EUs
KI-forordning, OECD, UNESCO, nasjonale strategier), forskningslitteraturen og
den norske definisjonen. Norske definisjoner er sitert fra
[Teknologirådets ordliste for kunstig intelligens](https://teknologiradet.no/ordliste-for-kunstig-intelligens/),
som Språkrådet har gjennomgått, og fra norske forskrifter og strategier; de
norske termene i ordlisten følger Teknologirådets liste. Sitattegn betyr at
ordlyden er kildens egen; uten dem er det en nær omskrivning. Utkast til
standarder er merket som utkast.
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
