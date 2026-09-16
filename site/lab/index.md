---
layout: page
title: Lab
permalink: /lab/
description: "Browser experiments from the MishMash work packages: sound, networks, generative art and other pieces built on the site's own data."
---

The lab is where MishMash tries things in the browser: sound from the publication stream, a map of who works with whom, and whatever a work package wants to show next. Each piece says who made it, what data it draws on and how AI was involved. Pieces are experiments, and may change or disappear.

Anyone in the network can add one. Copy the template in [`site/lab/_template/`](https://github.com/MishMash-Norway/mishmash-web/tree/main/site/lab/_template) and follow the [lab guide](https://github.com/MishMash-Norway/mishmash-web/wiki/Lab) on the wiki.

{% assign lab_pages = site.pages | where_exp: "p", "p.lab" | where_exp: "p", "p.lang != 'nb'" %}
{% comment %} Newest first: sort on the date inside the lab map. {% endcomment %}
{% assign lab_pages = lab_pages | sort: "lab.date" | reverse %}
<ul class="mm-lab-list">
{% for p in lab_pages %}
  <li>
    <a href="{{ p.url | relative_url }}">{{ p.title }}</a>{% if p.lab.authors %} <span class="mm-lab-byline">by {{ p.lab.authors | join: ", " }}</span>{% endif %}
    <p>{{ p.description }}</p>
  </li>
{% endfor %}
</ul>
