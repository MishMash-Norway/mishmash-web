---
layout: page
title: Projects
permalink: /projects/
---

Projects in the MishMash directory, with related people, institutions, tags, and work package (WP) mappings.

{% assign all_projects = site.directory | where: "type", "project" | where_exp: "project", "project.slug" | sort: "title" %}

## PhD Projects

<ul>
{% for project in all_projects %}{% if project.tags contains "PhD Project" %}
  <li><a href="{{ project.url | relative_url }}">{{ project.title | default: project.name }}</a>{% if project.wps and project.wps.size > 0 %} — {{ project.wps | join: ", " }}{% endif %}</li>
{% endif %}{% endfor %}
</ul>

## Seed Funding Projects

<ul>
{% for project in all_projects %}{% unless project.tags contains "PhD Project" %}
  <li><a href="{{ project.url | relative_url }}">{{ project.title | default: project.name }}</a>{% if project.wps and project.wps.size > 0 %} — {{ project.wps | join: ", " }}{% endif %}</li>
{% endunless %}{% endfor %}
</ul>
