---
layout: page
lang: nb
title: KI-kolofon
translation_url: /about/ai-colophon/
---

MishMash forsker på kreativ bruk av KI, og bruker KI helt åpent i arbeidet med dette nettstedet.

## Hvor KI bidrar

- **Innhold.** KI-assistanse brukes til å skrive utkast og tilpasse tekster, blant annet lesenivåvariantene på [adaptive sider](/no/about/description/) og oppslag i [ordlisten](/no/about/glossary/). Menneskelige redaktører gjennomgår og bearbeider, ofte i flere runder med maskinelle endringer.
- **Kode og automatisering.** Mye av nettstedets verktøy utvikles med KI-assistanse: synkroniseringsskriptene som henter data fra NVA, ORCID, Wikipedia, Wikimedia og Wikidata, temavelgeren, maskineriet for adaptivt innhold og kvalitetssjekkene. Det er godt synlig i [commit-historikken](https://github.com/MishMash-Norway/mishmash-web/commits/main) gjennom `Co-Authored-By`-merking.
- **Oversettelse.** Maskinoversettelse brukes mellom engelsk og norsk (både *bokmål* og *nynorsk*), og merkes på de aktuelle sidene.
- **Kunstverk.** Boblevariasjonen nedenfor tegnes på nytt hver natt av et [lite skript](https://github.com/MishMash-Norway/mishmash-web/blob/main/scripts/generate_daily_bubbles.py): en deterministisk skisse med dato og dagens aktivitet på nettstedet som frø (hver liten boble er et kommende arrangement). Det er generativt i algoritmisk forstand, og ingen KI-modell er involvert. Genererte bilder på dette nettstedet bærer IPTCs digitale kildetype i metadataene (algorithmicMedia for bilder tegnet av et skript, trainedAlgorithmicMedia for alt en KI-modell lager), sammen med opphavsperson, lisens og lenke til vilkårene, og byggingen sjekker at merket er der.

<div class="colophon-bubbles">
  <img src="/assets/images/bubbles/daily/mishmash_bubbles_daily.svg"
       alt="Dagens genererte variasjon av MishMash-bobleemblemet"
       width="340">
  <p>Dagens bobler, generert hver natt fra aktiviteten på nettstedet</p>
</div>

## Våre forpliktelser

1. **Mennesker er ansvarlige.** KI-produsert innhold gjennomgås som regel før det publiseres. Unntaket er de nattlige byggene, som henter nye data fra NVA og ORCID. Uansett er feil våre, ikke maskinenes.
2. **Ingenting skjules.** KI-bruk erklæres, merkes på oversatte sider og kan spores i den åpne [commit-historikken](https://github.com/MishMash-Norway/mishmash-web/commits/main).
3. **Bruken vår av KI er en del av forskningen.** Å bygge våre egne kommunikasjonskanaler med KI-basert assistanse er en del av MishMash sin forskningspraksis. Det er en måte å *skape, utforske og reflektere* over verktøyene vi forsker på. Det vi lærer, føres tilbake til senterets forskning og undervisning.

## Nettstedets vekt

Bærekraft er en viktig sak for MishMash. Ved å bygge nettstedet selv har vi full kontroll over hvordan det tegnes opp og serveres. Ved hver utrulling veier byggingen et utvalg sider i en nettleser uten hurtiglager og anslår karbonutslippet per besøk etter Sustainable Web Design-modellen slik den er implementert i CO2.js. Hele rapporten ligger på [/data/page-weight.json](/data/page-weight.json){: data-proofer-ignore="true"}.

En måte å spare båndbredde på er å komprimere bilder og sende dem progressivt ved behov. En annen er å skjære skriftfilene ned til tegnene nettstedet faktisk bruker. Hele nettstedet er skrevet med omtrent 300 ulike tegn, mens en vanlig latinsk skriftfil bærer flere tusen tegnformer, så filene blir omtrent halvparten så store, og et første besøk på forsiden laster 85 kB skrift i stedet for 198 kB.

<div id="page-weight" class="page-weight" data-src="/data/page-weight.json" data-lang="nb"><noscript>Tabellen trenger JavaScript; tallene finnes i JSON-filen over.</noscript></div>
<script defer src="/assets/js/page-weight.js"></script>

## Nynorsk-eksperimentet

Nynorskutgaven av nettstedet (sidene under `/nn/`) lages automatisk: hver bokmålsside oversettes ved bygging med det regelbaserte, åpne oversettelsesverktøyet [Apertium](https://github.com/apertium/apertium-nno-nob) (nob–nno, moderat norm), samme motor som NPK og NRK bruker for nynorsk. Hver generert side merkes med en boks øverst og lenker til bokmålsoriginalen. En håndkorrigert side under `site/nn/` i kildekoden vinner alltid over den genererte.

Vi publiserer utgaven vel vitende om at den inneholder feil, men også som en måte å gjøre oppmerksom på begrensningene i dagens modeller og bidra til å forbedre dem. MishMash vil teste ting i det åpne, avdekke problemer og rette dem, både i våre egne og i underliggende systemer. Finner du en feil, bruk «Foreslå en endring» i bunnteksten, så retter vi verktøyene eller siden.

{% include ai-colophon-commits.html lang="nb" %}

Mer om tankene bak nettstedet: [nettfilosofien](https://github.com/MishMash-Norway/mishmash-web/wiki/Web-Philosophy) i prosjektwikien og senterets [kommunikasjonsstrategi](/no/internal/kommunikasjonsstrategi/). Spørsmål eller innspill: [contact@mishmash.no](mailto:contact@mishmash.no).
