---
layout: page
lang: nb
title: Språk
permalink: /no/about/languages/
translation_url: /about/languages/
description: "Nettstedets tre språkversjoner, hvordan nynorsksidene lages, og hvor stor del av teksten som er på hvert språk."
---

mishmash.no skrives på engelsk, og hovedsidene speiles på norsk. Norsk betyr begge målformer: bokmålssidene skrives for hånd, og nynorsksidene lages fra dem. Språkvelgeren øverst på hver side går mellom de tre versjonene av siden, eller til språkets forside der det ikke finnes noen versjon.

## Hvordan nynorsksidene lages

Hver bokmålsside oversettes når nettstedet bygges, med et regelbasert oversettelsesverktøy med åpen kildekode (Apertiums bokmål-til-nynorsk-par, i moderat nynorsk med «vi»). Navn, kode og lenker går uendret gjennom, og senterets egne begreper holdes i en felles ordliste. En side laget slik sier det nederst, med lenke til bokmålssiden den kommer fra, til et medlem som skriver nynorsk har lest og rettet den; en rettet side beholder merknaden om hvem som har lest den og skrives ikke over. Funnet en feil på en nynorskside? Bruk «Foreslå en endring» nederst på siden.

## Hvor mye tekst som er på hvert språk

{% assign ls = site.data.language_share %}
{% if ls %}
Målt på kildene til sidene {{ ls.generated_at | date: "%-d. %B %Y" }}, ved å telle ordene i hvert avsnitt på fem ord eller mer og klassifisere hvert avsnitt med en språkgjenkjenner som skiller bokmål fra nynorsk. Interne sider og grensesnittemaene er holdt utenfor, slik søkemotorene holder dem utenfor.

| Språk | Ord | Andel av all tekst | Andel av den norske teksten |
| --- | ---: | ---: | ---: |
| Engelsk | {{ ls.words.en }} | {{ ls.share_percent.en }} % | |
| Bokmål | {{ ls.words.nb }} | {{ ls.share_percent.nb }} % | {{ ls.norwegian_share_percent.nb }} % |
| Nynorsk | {{ ls.words.nn }} | {{ ls.share_percent.nn }} % | {{ ls.norwegian_share_percent.nn }} % |

Språkloven ber statsorganer bruke minst en fjerdedel av hver målform over tid. Språkrådet måler statlige nettsteder med innhøsteren Målfrid, som teller ord i de publiserte sidene på mye samme måte; tallene ovenfor er nettstedets egen telling og oppdateres ved hver bygging.
{% else %}
Tellingen gjøres når nettstedet bygges og er ikke tilgjengelig i denne byggingen.
{% endif %}

## Samisk og kvensk

De samiske språkene og kvensk maskinoversettes ikke på dette nettstedet: det finnes ikke noe oversettelsesverktøy av publiserbar kvalitet for dem, og de som bygger samisk språkteknologi fraråder å publisere uredigert maskinoversettelse. Et sett kjernesider på nordsamisk og på kvensk, oversatt av mennesker, planlegges sammen med partnerinstitusjonene som har ansvaret for disse språkene.
