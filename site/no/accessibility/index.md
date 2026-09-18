---
layout: page
lang: nb
title: Tilgjengelighet
permalink: /no/accessibility/
translation_url: /accessibility/
---

mishmash.no skal kunne brukes av så mange som mulig, uansett hva de leser det med. Nettstedet er bygget for å være tilgjengelig etter den standarden norsk lov setter: forskriften om universell utforming av IKT, som krever at offentlige nettsteder oppfyller de 48 suksesskriteriene i [Web Content Accessibility Guidelines (WCAG) 2.1](https://www.w3.org/TR/WCAG21/) på nivå A og AA som [Tilsynet for universell utforming av IKT](https://www.uutilsynet.no/wcag-standarden/wcag-standarden/86) lister opp.

## Hva nettstedet gjør

- En hopp-til-innhold-lenke øverst på hver side fører rett til innholdet.
- Menyer, språkvalg, søk og utvidbare avsnitt kan brukes med tastatur, og elementet som har fokus er alltid synlig.
- Sidens språk er oppgitt, og språkvalget merker det andre språket slik at skjermlesere uttaler det riktig.
- Tekst og bakgrunn har en kontrast på minst 4,5:1, og teksten kan forstørres til 200 % uten at innhold går tapt.
- Sidene tilpasser seg en bredde på 320 piksler uten vannrett rulling.
- Bilder har tekstalternativer, lenker beskriver målet sitt, og overskriftene følger en logisk rekkefølge.
- Diagrammene på resultatsiden har et tabellalternativ.

## Hvordan nettstedet sjekkes

Hver endring sjekkes i GitHub Actions før den publiseres. Arbeidsflyten [Web Quality Checks](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml) omfatter:

- Tilgjengelighetsskanning: [Pa11y CI](https://github.com/pa11y/pa11y-ci) kjører både axe-core og HTML CodeSniffer mot WCAG 2.1 nivå AA på et utvalg representative sider på begge språk, listet i [`.pa11yci.json`](https://github.com/MishMash-Norway/mishmash-web/blob/main/.pa11yci.json). En enkelt feil stopper sjekken.
- HTML-validering: Nu HTML Checker validerer hver genererte side som HTML5.
- Lenkesjekk: htmlproofer kontrollerer interne lenker i det bygde nettstedet.

Automatiske verktøy finner bare en del av barrierene en person kan møte. Resten avhenger av hvordan innholdet skrives, så bidragsytere bes om å gi bilder tekstalternativer, holde overskriftene i rekkefølge, skrive lenketekst som gir mening alene, og tekste video. De nyeste resultatene finnes på [siden for kjøringer av arbeidsflyten](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml).

## Kjente begrensninger

- Innebygde videoer fra YouTube har ikke alltid teksting, og ingen av dem har synstolking.
- Chat-siden er avhengig av JavaScript og av en ekstern språkmodelltjeneste.
- De eksperimentelle grensesnittene under `/ui/` er studentarbeid og ligger utenfor de automatiske sjekkene.
- Bidragene i [laben](/lab/) er eksperimenter; hvert av dem sjekkes som alle andre sider, men kan kreve JavaScript, lyd eller pekeredskap, og sier fra om det.

## Fortell oss om en barriere

Hvis du har problemer med å bruke noe på dette nettstedet, skriv til [contact@mishmash.no](mailto:contact@mishmash.no) og fortell hvilken side du var på og hva som skjedde. Vi tar sikte på å svare innen en uke og rette det vi kan.
