---
layout: page
title: Lab
permalink: /lab/
custom_css: /assets/css/gallery.css
description: "Browser experiments from the MishMash work packages: sound, networks, generative art and other pieces built on the site's own data."
---

This is MishMash's online lab, a place where we experiment with things in the browser. This is part of our [web philosophy](https://github.com/MishMash-Norway/mishmash-web/wiki/Web-Philosophy), and links to our [general way of working](https://mishmash.no/about/description/): creating, exploring, and reflecting on AI for, in, and through creative practice. 

The pieces below are in constant change. Some may mature into the rest of the web page, others may be removed. They are also not part of our [accessibility](https://mishmash.no/accessibility/) scan.

As with everything else in MishMash, anyone in the network is free to suggest new things to include here in the lab space. Copy the template in [`site/lab/_template/`](https://github.com/MishMash-Norway/mishmash-web/tree/main/site/lab/_template) and follow the [lab guide](https://github.com/MishMash-Norway/mishmash-web/wiki/Lab) on the wiki. Whole alternative interfaces for the site are a lab of their own, browsable at [mishmash.no/ui/](/ui/). Artistic work from the network, as opposed to experiments on this site, is in the [gallery](/gallery/).

{% assign lab_pages = site.pages | where_exp: "p", "p.lab" | where_exp: "p", "p.lang != 'nb'" | where_exp: "p", "p.lang != 'nn'" %}
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
