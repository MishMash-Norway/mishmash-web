---
layout: page
lang: nb
title: Medlemsblogger
permalink: /no/news/member-blogs/
translation_url: /news/member-blogs/
description: "De siste innleggene fra bloggene og prosjektsidene til MishMash-medlemmer som har valgt å stå oppført her."
---

Medlemmene i nettverket skriver på egne steder. Denne siden samler de siste innleggene fra dem som har valgt å stå oppført, med tittel, dato og en linje eller to; lesingen skjer hos kilden. Ingenting kopieres hit, og ingen innlegg listes uten at skribenten har sagt ja.

For å bli oppført, skriv til [contact@mishmash.no](mailto:contact@mishmash.no) med adressen til strømmen din, eller bruk «Foreslå en endring» nederst på din egen [katalogside](/search/?type=person). En strøm er den maskinlesbare utgaven av en blogg, gjerne på en adresse som slutter på `feed.xml`, `atom.xml` eller `/feed/`; de fleste bloggverktøy publiserer en uten at man ber om det.

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
<p class="small muted">Hentet {{ planet.synced_at | date: "%-d. %B %Y" }} fra {{ planet.sources }} strøm{% if planet.sources != 1 %}mer{% endif %}.</p>
{% else %}
<p>Ingen strømmer er oppført ennå. Din kan bli den første.</p>
{% endif %}
