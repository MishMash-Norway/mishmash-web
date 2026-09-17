---
layout: page
title: Lab
permalink: /lab/
custom_css: /assets/css/gallery.css
description: "Browser experiments from the MishMash work packages: sound, networks, generative art and other pieces built on the site's own data."
---

The lab is where MishMash tries things in the browser: sound from the publication stream, a map of who works with whom, and whatever a work package wants to show next. Each piece says who made it, what data it draws on and how AI was involved. Every piece is experimental: it may change or disappear, and it is outside the promises the rest of the site makes, apart from the accessibility scan.

Anyone in the network can add one. Copy the template in [`site/lab/_template/`](https://github.com/MishMash-Norway/mishmash-web/tree/main/site/lab/_template) and follow the [lab guide](https://github.com/MishMash-Norway/mishmash-web/wiki/Lab) on the wiki.

{% assign lab_pages = site.pages | where_exp: "p", "p.lab" | where_exp: "p", "p.lang == nil or p.lang == 'en'" %}
{% comment %} Newest first: sort on the date inside the lab map. {% endcomment %}
{% assign lab_pages = lab_pages | sort: "lab.date" | reverse %}
<div class="gallery-grid">
{% for p in lab_pages %}
  <div class="gallery-card">
    <span class="gallery-kind">{{ p.lab.status | default: "experiment" }}</span>
    <h2><a href="{{ p.url | relative_url }}">{{ p.title }}</a></h2>
    <p class="gallery-byline">{% if p.lab.authors %}{{ p.lab.authors | join: ", " }}{% endif %}{% if p.lab.date %} · since {{ p.lab.date | date: "%B %Y" }}{% endif %}</p>
    <p class="gallery-desc">{{ p.description }}</p>
  </div>
{% endfor %}
</div>
