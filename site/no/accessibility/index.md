---
layout: page
lang: nb
title: Tilgjengelighet
permalink: /no/accessibility/
translation_url: /accessibility/
---

Vi ønsker at mishmash.no skal være brukbar for flest mulig. Vi arbeider for å følge anerkjente webstandarder for struktur, semantikk og tilgjengelighet.

## Standarder vi sikter mot

- **[WCAG 2](https://www.w3.org/WAI/standards-guidelines/wcag/) nivå AA** — kontrast, tastaturbruk, etiketter og andre krav sjekkes automatisk i byggeløpet vårt.
- **Gyldig, semantisk HTML** — sidene valideres som HTML5 under kontinuerlig integrasjon.
- **Praktiske tilgjengelighetsfunksjoner** — blant annet hopp-til-innhold-lenke, tekstalternativer for bilder der det trengs, og meningsfull lenke- og overskriftsstruktur.

Automatiske tester fanger ikke alle barrierer. Opplever du problemer med å bruke nettsiden, send oss gjerne en melding på [contact@mishmash.no](mailto:contact@mishmash.no), så kan vi forbedre den.

## Automatiske sjekker på GitHub

Hver endring på nettsiden sjekkes i GitHub Actions før den publiseres. Arbeidsflyten [**Web Quality Checks**](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml) inkluderer:

- **Tilgjengelighetsskanning (Pa11y)** — tester viktige sider mot WCAG 2 nivå AA med [Pa11y CI](https://github.com/pa11y/pa11y-ci) og konfigurasjonen vår [`.pa11yci.json`](https://github.com/MishMash-Norway/mishmash-web/blob/main/.pa11yci.json).
- **HTML-validering (Nu HTML Checker)** — sjekker at genererte sider har gyldig HTML5-markup.
- **Lenkesjekk (htmlproofer)** — verifiserer interne lenker i det ferdigbygde nettstedet.

Du finner de siste resultatene på [siden for arbeidsflytkjøringer](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml).
