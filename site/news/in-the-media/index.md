---
layout: page
title: MishMash in the media
permalink: /news/in-the-media/
translation_url: /no/news/in-the-media/
description: "Media contributions by MishMash researchers, from the national research archive, with links to the programme or article."
---

Interviews, articles and broadcasts where MishMash researchers speak about AI and creativity, as registered in the national research archive [NVA](https://nva.sikt.no/projects/2744839) and refreshed nightly. Register your own media contributions in NVA with MishMash as funder and they appear here.

{% assign media = site.data.mishmash_results.results | where_exp: "r", "r.group_type contains 'Media'" | sort: "year" | reverse %}
{% if media.size > 0 %}
<ul class="media-list">
{% for r in media %}
  <li>{% if r.year %}{{ r.year }} · {% endif %}{% if r.url %}<a href="{{ r.url }}">{{ r.title }}</a>{% else %}{{ r.title }}{% endif %}{% if r.citation.container and r.citation.container != '' %} · {{ r.citation.container | remove: '.' }}{% endif %}{% if r.contributors.size > 0 %} · {% for c in r.contributors limit: 3 %}{% if c.url %}<a href="{{ c.url | relative_url }}">{{ c.name }}</a>{% else %}{{ c.name }}{% endif %}{% unless forloop.last %}, {% endunless %}{% endfor %}{% endif %}</li>
{% endfor %}
</ul>
{% else %}
<p>No media contributions registered yet.</p>
{% endif %}
