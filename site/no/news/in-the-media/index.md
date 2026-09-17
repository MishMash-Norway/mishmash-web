---
layout: page
lang: nb
title: MishMash i mediene
permalink: /no/news/in-the-media/
translation_url: /news/in-the-media/
description: "Mediebidrag fra MishMash-forskere, fra Nasjonalt vitenarkiv, med lenker til programmet eller artikkelen."
---

Intervjuer, artikler og sendinger der MishMash-forskere snakker om KI og kreativitet, slik de er registrert i Nasjonalt vitenarkiv ([NVA](https://nva.sikt.no/projects/2744839)) og oppdatert hver natt. Registrer dine egne mediebidrag i NVA med MishMash som finansiør, så kommer de med her.

{% assign media = site.data.mishmash_results.results | where_exp: "r", "r.group_type contains 'Media'" | sort: "year" | reverse %}
{% if media.size > 0 %}
<ul class="media-list">
{% for r in media %}
  <li>{% if r.year %}{{ r.year }} · {% endif %}{% if r.url %}<a href="{{ r.url }}">{{ r.title }}</a>{% else %}{{ r.title }}{% endif %}{% if r.citation.container and r.citation.container != '' %} · {{ r.citation.container | remove: '.' }}{% endif %}{% if r.contributors.size > 0 %} · {% for c in r.contributors limit: 3 %}{% if c.url %}<a href="{{ c.url | relative_url }}">{{ c.name }}</a>{% else %}{{ c.name }}{% endif %}{% unless forloop.last %}, {% endunless %}{% endfor %}{% endif %}</li>
{% endfor %}
</ul>
{% else %}
<p>Ingen mediebidrag registrert ennå.</p>
{% endif %}
