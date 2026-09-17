---
layout: page
type: project
title: The MishMash Website
permalink: /projects/the-mishmash-website/
wps:
- WP1
- WP2
- WP3
- WP4
- WP5
- WP6
- WP7
tags:
- Website
- GitHub
- Infrastructure
- Directory
- Cross-WP
slug: the-mishmash-website
name: The MishMash Website
people:
- aedan-soellaart
- alexander-refsum-jensenius
- carsten-griwodz
- eirik-sorbo
- eskil-muan-saether
- kyrre-glette
- sashi-komandur
- stefano-fasciani
institutions:
- nord-university
- university-of-agder
- university-of-inland-norway
- university-of-oslo
projects: []
---

## Summary

This project develops and maintains [mishmash.no](https://mishmash.no) and treats the website as a research and teaching project in its own right. The site is a static Jekyll site in a public GitHub repository, published on GitHub Pages, so anyone in the network can read the source, propose a change and see it reviewed before it goes live. The thinking behind it is set out on the [web philosophy](https://github.com/MishMash-Norway/mishmash-web/wiki/Web-Philosophy) page of the project wiki.

## What has been built

- 2025: the repository was created in June with a minimal Jekyll site for news and events, and the first alternative interface themes followed the same month.
- Early 2026: internal pages for the organisation, board and council, and partner news and events pulled from partner websites.
- Spring 2026: the directory of people, institutions and projects, refreshed nightly from [NVA](https://nva.sikt.no/) and [ORCID](https://orcid.org/); site-wide [search](/search/); the [people network](/lab/people-network/); a Norwegian mirror of the main pages; and a first [chat](/chat/) prototype running in the browser.
- Summer 2026: adaptive reading levels and stretchtext on the [about page](/about/description/) with a shared [glossary](/about/glossary/); Wikidata identifiers for people and institutions; the [research pulse](/results/pulse/), the [soundscape](/lab/soundscape/) and the [AI colophon](/about/ai-colophon/); and a provenance footer on every page.
- September 2026: the new [visual identity](/internal/brand/) replaced the launch look, which lives on as the Bubbles theme, and an accessibility audit brought the site to the machine-checkable criteria of WCAG 2.1 level AA, with the scan in the build pipeline now enforcing them.

## What runs today

- A [directory](/search/?type=person) of people, institutions and projects, and a [results list](/results/), both kept in step with NVA, ORCID and Wikipedia by nightly automation.
- [Search](/search/), the [research pulse](/results/pulse/), the [gallery](/gallery/), and the [lab](/lab/) with the people network and the soundscape.
- An [about page](/about/description/) that offers the same text at three reading levels, in English and Norwegian.
- A [chat](/chat/) prototype that answers questions from the site's own content.
- [Partner news](/news/partner-news/) and [partner events](/events/partner-events/) alongside the centre's own.
- Four alternative interfaces published at [mishmash.no/ui/](/ui/), built by students and contributors.
- Quality checks on every change: directory validation, HTML validation, link checking and an accessibility scan with two engines in both languages.

## The MishMash Mesh

Through [seed funding #2](/internal/funding/seed-funding/seed02/) (2026), the project also develops *The MishMash Mesh*, led by [Aedan Soellaart](/people/aedan-soellaart/) with UI/UX designer Mihaela Daniela Crudu (INN): an internal co-creative engine that maps members' expertise and work-package affiliations and recommends collaborations through natural-language queries, a public LLM interface grounded in MishMash documentation, and a WCAG 2.2-compliant accessibility toolbar.

## What comes next

The open work is tracked in the [issue tracker](https://github.com/MishMash-Norway/mishmash-web/issues), where ideas are labelled by direction: [web of knowledge](https://github.com/MishMash-Norway/mishmash-web/issues?q=is%3Aopen+label%3Aweb-of-knowledge), [responsible AI](https://github.com/MishMash-Norway/mishmash-web/issues?q=is%3Aopen+label%3Aresponsible-ai), [community](https://github.com/MishMash-Norway/mishmash-web/issues?q=is%3Aopen+label%3Acommunity), [creative lab](https://github.com/MishMash-Norway/mishmash-web/issues?q=is%3Aopen+label%3Acreative-lab), [privacy and copyright](https://github.com/MishMash-Norway/mishmash-web/issues?q=is%3Aopen+label%3Aprivacy-copyright) and [infrastructure](https://github.com/MishMash-Norway/mishmash-web/issues?q=is%3Aopen+label%3Ainfrastructure). The main lines are:

- Graduate the chat prototype into a grounded "Ask MishMash" assistant that cites the pages it draws on.
- Pull institution facts and images from Wikidata and Wikimedia Commons instead of maintaining them here, and contribute corrections back.
- Bring artistic results registered in the Research Catalogue into the results list.
- Publish the formal accessibility statement on uustatus.no, caption the videos, and complete a GDPR review of the site.
- Offer more languages than English and Norwegian.
- Keep the site open to students: new interface themes each year, with a vote on which look the consortium adopts, and backend projects on the sync scripts.

## Strategy

The site follows three ideas:

- **One source of truth.** Facts about people, projects, institutions and results are pulled from authoritative sources, NVA, ORCID and Wikipedia, through nightly automated syncs rather than being retyped by hand. The project is working towards Wikidata, Wikimedia Commons and other reliable open sources, both drawing from them and contributing back.
- **One text, many readers.** The site experiments with [stretchtext and adaptive content](https://github.com/MishMash-Norway/mishmash-web/wiki/Adaptive-Content): pages that offer the same content at three complexity levels (simple, standard, advanced), with the reader choosing the level. The [about page](/about/description/) is the pilot; how the levels map to typical readers is defined in the centre's communication strategy.
- **Open, student-driven development.** Students build alternative frontends (switchable UI themes) and backend automation on top of the site; see the [student development guide](https://github.com/MishMash-Norway/mishmash-web/wiki/Student-Development).

## Work Package

Cross-work-package initiative (WP1–WP7)

## Duration

2025–ongoing

## People

- Project leader: [Alexander Refsum Jensenius](/people/alexander-refsum-jensenius/)
- Participants: [Aedan Soellaart](/people/aedan-soellaart/), [Carsten Griwodz](/people/carsten-griwodz/), [Stefano Fasciani](/people/stefano-fasciani/), [Eirik Sørbø](/people/eirik-sorbo/), [Kyrre Glette](/people/kyrre-glette/), [Eskil Muan Sæther](/people/eskil-muan-saether/), [Sashidharan Komandur](/people/sashi-komandur/)

## Institutions

- [Nord University](/institutions/nord-university/)
- [University of Agder](/institutions/university-of-agder/)
- [University of Inland Norway](/institutions/university-of-inland-norway/)
- [University of Oslo](/institutions/university-of-oslo/)
