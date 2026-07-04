---
layout: page
lang: nb
title: Kommunikasjonsstrategi
permalink: /no/internal/kommunikasjonsstrategi/
translation_url: /internal/communication-strategy/
translation:
  automatic: false
---

Denne kommunikasjonsstrategien utfyller [kanalstrategien](/no/internal/kanalstrategi/). Kanalstrategien beskriver *hvilke* kanaler MishMash bruker og hvordan de virker sammen; dette dokumentet beskriver *hvordan vi kommuniserer* i kanalene: hvem leserne våre er, hva de trenger, og hvilken tone og kompleksitet som passer for hver av dem.

## Prinsipper

1. **Én kilde, mange lesere.** De samme faktaene presenteres på ulike kompleksitetsnivåer i stedet for å skrives om i parallelle dokumenter som glir fra hverandre. På mishmash.no er dette implementert som [adaptivt innhold og stretchtext](https://github.com/MishMash-Norway/mishmash-web/wiki/Web-Philosophy): leseren velger lesenivå, og tekstene folder ut mer detalj ved behov. Se [om-siden](/no/about/description/) for et fungerende eksempel.
2. **Leseren velger.** Vi gjetter ikke på og sporer ikke hvem leseren er. Leserne velger nivå selv, og kan alltid bytte. Klarspråkversjonen er standard.
3. **Hent, ikke skriv av.** Fakta om personer, prosjekter, institusjoner og resultater hentes fra autoritative kilder (NVA, ORCID, Wikipedia) i stedet for å vedlikeholdes for hånd, slik at lesere på alle nivåer får den samme oppdaterte informasjonen.
4. **Klarspråk først.** I tråd med klarspråkprinsippene og [språklova](https://lovdata.no/dokument/NL/lov/2021-05-21-42) er klarspråk standardregisteret; fagspråk er noe leseren velger *til*, ikke bort.

## Lesenivåer

Adaptive sider tilbyr det samme innholdet på tre **kompleksitetsnivåer** (definert i `site/_data/audiences.yml`). Nivåene beskriver *teksten*, ikke leseren — en professor som leser utenfor sitt felt kan foretrekke Standard, og en nysgjerrig tenåring kan velge Avansert. Leserroller holdes bevisst utenfor stigen; hvem som *typisk* leser på hvert nivå er veiledning for skribenter, ikke noe mer:

| Nivå | Kompleksitet | Typiske lesere | Tone og stil |
| --- | --- | --- | --- |
| **Enkel** | Kort og enkelt, uten fagspråk | Barn og ungdom, skoleklasser | Korte setninger, konkrete eksempler, spørsmål; uunngåelige begreper forklares med stretchtext |
| **Standard** (standardvalg) | Klarspråk | Allmennheten, nysgjerrige besøkende, beslutningstakere | Hverdagslige eksempler; hvorfor det angår samfunnet; sentrale begreper introduseres med stretchtext |
| **Avansert** | Alle detaljer, ingenting forenklet | Forskere, studenter, kunstnere og fageksperter | Full presisjon: metoder, utfordringer, arbeidspakkedetaljer, akademiske referanser |

## Sekundære målgrupper

Ikke alle målgrupper bør være et lesenivå — de fleste betjenes bedre av egne sider og kanaler:

- **Presse og media** — trenger siterbare fakta, tall, bilder og kontakter raskt. Betjenes av tydelige om-sider og direkte kontakt med ledelsen, ikke av et eget lesenivå.
- **Beslutningstakere og finansiører** — trenger samfunnsrelevans og effekt. Betjenes av Standard-nivået pluss resultater og nyheter.
- **Potensielle akademiske partnere** — forskere og institusjoner som vurderer å bli med i eller samarbeide med nettverket. Betjenes av om-sidene (avansert nivå), arbeidspakkesidene, [resultater](/results/) og direkte kontakt med arbeidspakkeledere og ledelsen.
- **Potensielle partnere i offentlig og privat sektor** — bedrifter, kulturinstitusjoner og offentlige virksomheter. Betjenes av [prosjektsidene](/projects/), nyheter som viser eksisterende samarbeid, og kontakt med ledelsen.
- **Potensielle ansatte og studenter** — betjenes av [ledige stillinger](/vacancies/) og arbeidspakkesidene; studenter som vil bidra til selve nettstedet henvises til [nettsideprosjektet](/projects/the-mishmash-website/) og [utviklerwikien](https://github.com/MishMash-Norway/mishmash-web/wiki).
- **MishMash-nettverket (internt)** — betjenes av [internsidene](/internal/), e-postlister og arbeidspakkekanaler, som beskrevet i [kanalstrategien](/no/internal/kanalstrategi/).

## Målgrupper og kanaler

Kanaler retter seg, i motsetning til lesenivåer, mot målgrupper:

| Kanal (se [kanalstrategien](/no/internal/kanalstrategi/)) | Barn og unge | Allmennheten | Akademia og kunst | Fageksperter | Internt |
| --- | --- | --- | --- | --- | --- |
| mishmash.no (adaptive sider) | ✓ | ✓ | ✓ | ✓ | |
| mishmash.no (resultater, katalog) | | ✓ | ✓ | ✓ | ✓ |
| mishmash.no/internal | | | | | ✓ |
| E-postlisten ALL@ | | | | | ✓ |
| E-postlisten ANNOUNCEMENTS@ | | ✓ | ✓ | ✓ | ✓ |
| LinkedIn | | ✓ | ✓ | ✓ | |
| Instagram | ✓ | ✓ | | | |
| YouTube | ✓ | ✓ | ✓ | ✓ | |

## KI i utviklingen av nettstedet

MishMash bruker aktivt KI i utviklingen og vedlikeholdet av mishmash.no — passende for et senter som forsker på kreativ bruk av KI. KI-assistanse brukes til å skrive og tilpasse innhold (blant annet utkast til lesenivåvariantene på adaptive sider), til å utvikle nettstedets kode og automatisering, og til maskinoversettelse mellom engelsk og norsk. To forpliktelser rammer inn denne bruken:

1. **Åpenhet.** Vi er åpne om hvor og hvordan KI bidrar: maskinoversatte sider merkes, KI-assistert utvikling er synlig i den offentlige commit-historikken, og denne seksjonen erklærer selv praksisen. Lesere og partnere skal aldri måtte gjette på om KI var involvert.
2. **Det er et eksperiment.** Å bruke KI til å bygge senterets egen kommunikasjonskanal er en del av MishMash sin forskningspraksis — en måte å *skape, utforske og reflektere* over egne verktøy. Menneskelige redaktører er ansvarlige for alt som publiseres: KI-produsert innhold gjennomgås før det går ut, og feil er våre, ikke maskinens. Det vi lærer føres tilbake til senterets forskning og undervisning.

Praksisen erklæres offentlig på [KI-kolofonen](/no/about/ai-colophon/), er dokumentert nærmere i [nettfilosofien](https://github.com/MishMash-Norway/mishmash-web/wiki/Web-Philosophy) og evalueres sammen med de andre nettstedseksperimentene.

## Språk

Engelsk er hovedspråket; sentrale seksjoner speiles på norsk under `/no/…`. Adaptive lesenivåer og norsk oversettelse er uavhengige dimensjoner: målet er at begge språkversjonene etter hvert tilbyr de samme lesenivåene. Maskinoversettelse merkes på de aktuelle sidene.

## Evaluering

Tilnærmingen med adaptivt innhold er et eksperiment i regi av [nettsideprosjektet](/projects/the-mishmash-website/). Det evalueres på: om variantene holdes synkronisert (en redaksjonell kostnad), om leserne bruker velgeren, og om de forenklede nivåene faktisk er enklere (lesbarhetsmål). Strategien revideres sammen med kanalstrategien.
