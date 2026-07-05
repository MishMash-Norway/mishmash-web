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

{% assign entries = site.data.glossary | sort: "key" %}
<dl class="glossary">
{% for g in entries %}
  <dt id="{{ g.key }}"><strong>{{ g.term.en }}</strong></dt>
  <dd>{{ g.definition.en | markdownify | remove: '<p>' | remove: '</p>' | strip }}</dd>
{% endfor %}
</dl>

Missing a term? Suggest one via [the website project](/projects/the-mishmash-website/).
