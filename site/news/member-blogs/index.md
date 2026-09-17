---
layout: page
title: Member blogs
permalink: /news/member-blogs/
translation_url: /no/news/member-blogs/
description: "The latest posts from the blogs and project sites of MishMash members who have chosen to be listed here."
---

Members of the network write in their own places. This page gathers the latest posts from those who have chosen to be listed, with a title, a date and a line or two; the reading happens at the source. Nothing is copied here, and no post is listed without the writer having opted in.

To be listed, write to [contact@mishmash.no](mailto:contact@mishmash.no) with the address of your feed, or use "Suggest a change" in the footer of your own [directory page](/search/?type=person). A feed is the machine-readable version of a blog, usually at an address ending in `feed.xml`, `atom.xml` or `/feed/`; most blogging tools publish one without being asked.

{% assign planet = site.data.member_posts %}
{% if planet and planet.posts.size > 0 %}
<ul class="planet-list">
{% for p in planet.posts %}
  <li>
    <a href="{{ p.url }}">{{ p.title }}</a>
    <span class="planet-meta">{% if p.date %}{{ p.date }} · {% endif %}{% if p.author %}<a href="{{ p.author_url | relative_url }}">{{ p.author }}</a>{% endif %}</span>
    {% if p.summary %}<p class="planet-summary">{{ p.summary }}</p>{% endif %}
  </li>
{% endfor %}
</ul>
<p class="small muted">Collected {{ planet.synced_at | date: "%-d %B %Y" }} from {{ planet.sources }} feed{% if planet.sources != 1 %}s{% endif %}.</p>
{% else %}
<p>No feeds are listed yet. Yours can be the first.</p>
{% endif %}
