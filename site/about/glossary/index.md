---
layout: default
title: Glossary
translation_url: /no/about/glossary/
adaptive: true
description: "A glossary of AI and creativity terms used across the MishMash centre, at three reading levels."
---

## Glossary

Key terms used across mishmash.no, each explained at three levels. Use the
switcher above to choose: *Simple* is one plain sentence, *Standard* is the
everyday explanation, and *Advanced* adds precision, the definition from the
research literature, and the Norwegian definition where one has been settled.

The same texts power the inline
{% include stretch.html term="stretchtext" %} explanations — dotted-underlined
terms like that one, which you can click to unfold — so this list and the
in-text explanations always match, at whichever level you read.

<div class="adaptive" data-for="simple standard" markdown="1">
At the *Advanced* level, each term also shows its definition from the research
literature and the Norwegian definition, with sources.
</div>

<div class="adaptive" data-for="advanced" markdown="1">
Where a term has a settled definition in the research literature, that is given
underneath, with its source. Norwegian definitions are quoted from
[Teknologirådet's glossary of artificial intelligence](https://teknologiradet.no/ordliste-for-kunstig-intelligens/),
which Språkrådet has reviewed, and from the national AI strategy; the Norwegian
terms in this glossary follow the same list. Quotation marks mean the wording
is the source's own; without them it is a close paraphrase.
</div>

{% assign entries = site.data.glossary | sort: "key" %}
{% assign top_level = site.data.audiences.groups | last %}
<dl class="glossary">
{% for g in entries %}
  <dt id="{{ g.key }}"><strong>{{ g.term.en }}</strong>{% include glossary-copy-link.html key=g.key term=g.term.en %}</dt>
  <dd>
  {%- for lv in site.data.audiences.groups -%}
  {%- assign variant = g[lv.key] -%}
  {%- assign text = variant.en | default: g.standard.en -%}
  <span class="adaptive" data-for="{{ lv.key }}">{{ text | markdownify | remove: '<p>' | remove: '</p>' | strip }}</span>
  {%- endfor -%}
  {% if g.canonical %}<span class="adaptive glossary-ref" data-for="{{ top_level.key }}"><span class="glossary-ref-label">In the literature:</span> {{ g.canonical | markdownify | remove: '<p>' | remove: '</p>' | strip }} <cite>{% if g.source_url %}<a href="{{ g.source_url }}">{{ g.source }}</a>{% else %}{{ g.source }}{% endif %}</cite></span>{% endif %}
  {% if g.norsk %}<span class="adaptive glossary-ref" data-for="{{ top_level.key }}"><span class="glossary-ref-label">Norwegian definition:</span> {{ g.norsk | markdownify | remove: '<p>' | remove: '</p>' | strip }} <cite>{% if g.norsk_source_url %}<a href="{{ g.norsk_source_url }}">{{ g.norsk_source }}</a>{% else %}{{ g.norsk_source }}{% endif %}</cite></span>{% endif %}
  </dd>
{% endfor %}
</dl>
<script defer src="/assets/js/glossary.js"></script>

Missing a term? Suggest one via [the website project](/projects/the-mishmash-website/).
