---
layout: page
lang: nb
title: Åpne data
permalink: /no/data/
translation_url: /data/
description: "Nettstedets personer, institusjoner, prosjekter, resultater og arrangementer som JSON- og CSV-filer, med lisenser, oppdatert ved hver bygging."
---

Alt på dette nettstedet ligger som rene filer, og kan derfor publiseres som data. Filene nedenfor bygges på nytt ved hver utrulling, bærer lisensen og kildene sine i seg, og er ment for gjenbruk av partnere, forskere og programvare, KI-agenter medregnet. [Vilkårene for bruk](/no/about/terms/) gjelder: nettstedets egne data er CC0, og det som kommer fra det nasjonale forskningsarkivet, ORCID og Wikidata beholder kildens vilkår.

| Datasett | Innhold | JSON | CSV |
| --- | --- | --- | --- |
| Personer | Medlemmer av nettverket: navn, stilling, institusjoner, arbeidspakker, roller, identifikatorer. Bare faglige opplysninger, slik [personvernerklæringen](/no/privacy/) lister dem; ingen portretter eller kontaktopplysninger. | [people.json](/data/people.json) | [people.csv](/data/people.csv) |
| Institusjoner | Partnerinstitusjoner med kortnavn, identifikatorer (Wikidata, Wikipedia, ROR) og koordinater. | [institutions.json](/data/institutions.json) | [institutions.csv](/data/institutions.csv) |
| Prosjekter | Prosjekter med personer, institusjoner, arbeidspakker og emneord. | [projects.json](/data/projects.json) | [projects.csv](/data/projects.csv) |
| Resultater | Forskningsresultater registrert for senteret i NVA: tittel, år, type, DOI, bidragsytere, institusjoner. | [results.json](/data/results.json) | [results.csv](/data/results.csv) |
| Arrangementer | MishMash-arrangementer, tidligere og kommende, med tid og sted. | [events.json](/data/events.json) | [events.csv](/data/events.csv) |

Hver JSON-fil har samme form: `title`, `licence`, `sources`, `terms`, `generated_at`, `count` og `items`. CSV-filene slår sammen lister med semikolon og nøstede felt med understrek. Personer og institusjoner har også identifikatorene sine som `sameAs` i de strukturerte dataene på sine egne sider, og arrangementene finnes som [kalenderstrøm](/events/calendar.ics). En kort beskrivelse for språkmodeller ligger på [/llms.txt](/llms.txt).

For å endre eller fjerne en oppføring om deg selv, se [personvernerklæringen](/no/privacy/). For å melde et problem med en fil, bruk «Foreslå en endring» i bunnteksten.
