---
layout: page
lang: nb
title: Tilgjengelighet
permalink: /no/accessibility/
translation_url: /accessibility/
---

Vi ønsker at mishmash.no skal være brukbar for så mange som mulig, og vi arbeider for å følge anerkjente webstandarder for struktur, semantikk og tilgjengelighet.

## Standarder vi følger

- [WCAG 2](https://www.w3.org/WAI/standards-guidelines/wcag/) nivå AA — kontrast, tastaturbruk, etiketter og andre krav sjekkes automatisk i byggeløpet vårt.
- Gyldig, semantisk HTML — sidene valideres som HTML5 under kontinuerlig integrasjon.
- Praktiske tilgjengelighetsfunksjoner — blant annet hopp-til-innhold-lenke, tekstalternativer for bilder der det trengs, og meningsfull lenke- og overskriftsstruktur.

Vi vet at automatiserte tester ikke fanger opp alle barrierer. Hvis du har problemer med å bruke noe av dette nettstedet, kan du gi oss beskjed på [contact@mishmash.no](mailto:contact@mishmash.no) slik at vi kan forbedre det.

## Automatiserte sjekker på GitHub

Hver endring på nettstedet sjekkes i GitHub Actions før den publiseres. Arbeidsflyten [Web Quality Checks](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml) inkluderer:

- Tilgjengelighetsskanning (Pa11y) — tester viktige sider mot WCAG 2 nivå AA med [Pa11y CI](https://github.com/pa11y/pa11y-ci) og konfigurasjonen vår [`.pa11yci.json`](https://github.com/MishMash-Norway/mishmash-web/blob/main/.pa11yci.json).
- HTML-validering (Nu HTML Checker) — sjekker genererte sider for gyldig HTML5-markup.
- Lenkesjekk (htmlproofer) — verifiserer interne lenker i det bygde nettstedet.

Du kan se de nyeste resultatene på [siden for arbeidsflytkjøringer](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml).
