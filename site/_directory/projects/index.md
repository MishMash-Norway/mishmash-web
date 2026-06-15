---
layout: page
title: Projects
permalink: /projects/
---

Seed-funding projects in the MishMash directory, with related people, institutions, tags, and work package (WP) mappings.

## Seed Funding Projects

{% assign seed_projects = site.directory | where: "type", "project" | where_exp: "project", "project.slug" | sort: "title" %}
<ul>
{% for project in seed_projects %}
  <li><a href="{{ project.url | relative_url }}">{{ project.title | default: project.name }}</a>{% if project.wps and project.wps.size > 0 %} — {{ project.wps | join: ", " }}{% endif %}</li>
{% endfor %}
</ul>
