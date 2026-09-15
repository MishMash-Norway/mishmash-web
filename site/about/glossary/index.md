---
layout: default
title: Glossary
translation_url: /no/about/glossary/
stretchtext: true
description: "A glossary of AI and creativity terms used across the MishMash centre."
---

## Glossary

Key terms used across mishmash.no. The same definitions power the inline
{% include stretch.html term="stretchtext" %} explanations — dotted-underlined
terms like that one, which you can click to unfold — so this list and the
in-text explanations always match.

Where a term has a settled definition in the research literature, that is given
underneath, with its source. Quotation marks mean the wording is the source's
own; without them it is a close paraphrase.

{% assign entries = site.data.glossary | sort: "key" %}
<dl class="glossary">
{% for g in entries %}
  <dt id="{{ g.key }}"><strong>{{ g.term.en }}</strong></dt>
  <dd>{{ g.definition.en | markdownify | remove: '<p>' | remove: '</p>' | strip }}
  {% if g.canonical %}<span class="glossary-canonical"><span class="glossary-canonical-label">In the literature:</span> {{ g.canonical | markdownify | remove: '<p>' | remove: '</p>' | strip }} <cite>{% if g.source_url %}<a href="{{ g.source_url }}">{{ g.source }}</a>{% else %}{{ g.source }}{% endif %}</cite></span>{% endif %}</dd>
{% endfor %}
</dl>

Missing a term? Suggest one via [the website project](/projects/the-mishmash-website/).
