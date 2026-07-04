---
layout: default
title: Glossary
translation_url: /no/about/glossary/
---

## Glossary

Key terms used across mishmash.no. The same definitions power the inline
[stretchtext](https://github.com/MishMash-Norway/mishmash-web/wiki/Adaptive-Content)
explanations — dotted-underlined terms you can click to unfold — so this list
and the in-text explanations always match.

{% assign entries = site.data.glossary | sort: "key" %}
<dl class="glossary">
{% for g in entries %}
  <dt id="{{ g.key }}"><strong>{{ g.term.en }}</strong></dt>
  <dd>{{ g.definition.en | markdownify | remove: '<p>' | remove: '</p>' | strip }}</dd>
{% endfor %}
</dl>

Missing a term? Suggest one via [the website project](/projects/the-mishmash-website/).
