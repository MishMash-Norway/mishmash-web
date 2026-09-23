---
layout: page
title: Open data
permalink: /data/
translation_url: /no/data/
description: "The site's people, institutions, projects, results, events and terminology as JSON and CSV files, with licences, refreshed at every build."
---

Everything on this site is kept as plain files, so it can be published as data. The files below are rebuilt with every deployment, carry their licence and their sources inside, and are meant for reuse by partners, researchers and software, including AI agents. The [terms of use](/about/terms/) apply: the site's own data is CC0, and what comes from the national research archive, ORCID and Wikidata keeps its source's terms.

{% assign base = site.url %}
| Dataset | What it holds | JSON | CSV |
| --- | --- | --- | --- |
| People | Members of the network: name, position, institutions, work packages, roles, identifiers. Professional facts only, as the [privacy notice](/privacy/) lists them; no portraits or contact details. | [people.json](/data/people.json) | [people.csv](/data/people.csv) |
| Institutions | Partner institutions with short names, identifiers (Wikidata, Wikipedia, ROR) and coordinates. | [institutions.json](/data/institutions.json) | [institutions.csv](/data/institutions.csv) |
| Projects | Projects with people, institutions, work packages and tags. | [projects.json](/data/projects.json) | [projects.csv](/data/projects.csv) |
| Results | Research results registered for the centre in NVA: title, year, type, DOI, contributors, institutions. | [results.json](/data/results.json) | [results.csv](/data/results.csv) |
| Events | MishMash events, past and upcoming, with times and places. | [events.json](/data/events.json) | [events.csv](/data/events.csv) |
| Terminology | The centre's vocabulary in English, Bokmål and Nynorsk, with the plain explanation of each term and a link to its entry in the [glossary](/about/glossary/). The Nynorsk column is the reviewed form the automatic Nynorsk pages are checked against. | [terminology.json](/data/terminology.json) | [terminology.csv](/data/terminology.csv) |

Each JSON file has the same shape: `title`, `licence`, `sources`, `terms`, `generated_at`, `count` and `items`. The CSV files flatten lists with a semicolon and nested fields with an underscore. People and institutions also carry their identifiers as `sameAs` in the structured data of their own pages, and the events are available as a [calendar feed](/events/calendar.ics). A short description for language models is at [/llms.txt](/llms.txt).

To change or remove an entry about yourself, see the [privacy notice](/privacy/). To report a problem with a file, use "Suggest a change" in the footer.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "DataCatalog",
  "name": "MishMash open data",
  "url": "{{ site.url }}/data/",
  "publisher": {"@type": "Organization", "name": "MishMash Centre for AI and Creativity", "url": "{{ site.url }}/"},
  "license": "https://creativecommons.org/publicdomain/zero/1.0/",
  "dataset": [
    {"@type": "Dataset", "name": "MishMash people", "description": "Members of the MishMash network with position, institutions, work packages, roles and identifiers.", "url": "{{ site.url }}/data/", "license": "https://creativecommons.org/publicdomain/zero/1.0/", "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": "{{ site.url }}/data/people.json"}, {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": "{{ site.url }}/data/people.csv"}]},
    {"@type": "Dataset", "name": "MishMash institutions", "description": "Partner institutions with identifiers and coordinates.", "url": "{{ site.url }}/data/", "license": "https://creativecommons.org/publicdomain/zero/1.0/", "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": "{{ site.url }}/data/institutions.json"}, {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": "{{ site.url }}/data/institutions.csv"}]},
    {"@type": "Dataset", "name": "MishMash projects", "description": "Projects with people, institutions, work packages and tags.", "url": "{{ site.url }}/data/", "license": "https://creativecommons.org/publicdomain/zero/1.0/", "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": "{{ site.url }}/data/projects.json"}, {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": "{{ site.url }}/data/projects.csv"}]},
    {"@type": "Dataset", "name": "MishMash results", "description": "Research results registered for the centre in the Norwegian national research archive (NVA).", "url": "{{ site.url }}/data/", "license": "https://creativecommons.org/publicdomain/zero/1.0/", "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": "{{ site.url }}/data/results.json"}, {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": "{{ site.url }}/data/results.csv"}]},
    {"@type": "Dataset", "name": "MishMash events", "description": "MishMash events, past and upcoming.", "url": "{{ site.url }}/data/", "license": "https://creativecommons.org/publicdomain/zero/1.0/", "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": "{{ site.url }}/data/events.json"}, {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": "{{ site.url }}/data/events.csv"}, {"@type": "DataDownload", "encodingFormat": "text/calendar", "contentUrl": "{{ site.url }}/events/calendar.ics"}]},
    {"@type": "Dataset", "name": "MishMash terminology", "description": "The centre's vocabulary in English, Bokm\u00e5l and Nynorsk, with a plain explanation of each term.", "url": "{{ site.url }}/data/", "license": "https://creativecommons.org/publicdomain/zero/1.0/", "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": "{{ site.url }}/data/terminology.json"}, {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": "{{ site.url }}/data/terminology.csv"}]}
  ]
}
</script>
