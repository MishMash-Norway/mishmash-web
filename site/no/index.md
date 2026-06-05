---
layout: default
lang: nb
title: "MishMash Senter for KI og kreativitet"
translation_url: /
---
<div class="mishmash-bubbles" style="float:right;margin:0 0 1rem 1rem;">
    <a href="/no/about/description/">
        <img src="/assets/images/bubbles/mishmash_bubbles.svg"
             alt="MishMash utforsker møtepunktet mellom mennesker og maskiner med kunst og vitenskap"
             width="400"
             onmouseover="this.lastImage = this.lastImage ?? -1; let next; do { next = Math.floor(Math.random() * 5 + 2); } while (next === this.lastImage); this.lastImage = next; this.src='/assets/images/bubbles/mishmash_bubbles' + next + '.svg';"
             onmouseout="this.src='/assets/images/bubbles/mishmash_bubbles.svg';">
    </a>
</div>

MishMash har som mål å **skape, utforske og reflektere over KI for, gjennom og i kreative praksiser**. Mer enn 200 forskere undersøker KIs innvirkning på kreative prosesser, utvikler innovative samskapende KI-systemer og pedagogiske strategier, og tar opp de etiske, kulturelle, juridiske og samfunnsmessige implikasjonene av KI i kreative domener. [Mer om MishMash...](https://mishmash.no/no/about/)

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
