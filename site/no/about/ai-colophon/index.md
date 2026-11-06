---
layout: page
lang: nb
title: KI-kolofon
translation_url: /about/ai-colophon/
---

MishMash forsker på kreativ bruk av KI, og bruker KI åpent i arbeidet med dette nettstedet.

## Hvor KI bidrar

- **Innhold.** KI-assistanse brukes til å skrive utkast og tilpasse tekster, blant annet lesenivåvariantene på [adaptive sider](/no/about/description/) og oppslag i [ordlisten](/no/about/glossary/). Menneskelige redaktører gjennomgår og bearbeider tekstene, ofte i flere runder med maskinelle endringer.
- **Kode og automatisering.** Mye av nettstedets verktøy utvikles med KI-assistanse: synkroniseringsskriptene som henter data fra NVA, ORCID, Wikipedia, Wikimedia og Wikidata, temavelgeren, maskineriet for adaptivt innhold og kvalitetssjekkene. Dette er merket med `Co-Authored-By` i [commit-historikken](https://github.com/MishMash-Norway/mishmash-web/commits/main).
- **Oversettelse.** Maskinoversettelse brukes mellom engelsk og norsk (både *bokmål* og *nynorsk*), og merkes på de aktuelle sidene.
- **Kunstverk.** Boblevariasjonen nedenfor tegnes på nytt hver natt av et [lite skript](https://github.com/MishMash-Norway/mishmash-web/blob/main/scripts/generate_daily_bubbles.py): en deterministisk skisse med dato og dagens aktivitet på nettstedet som frø (hver liten boble er et kommende arrangement). Det er generativt i algoritmisk forstand, og ingen KI-modell er involvert. Genererte bilder på dette nettstedet bærer IPTCs digitale kildetype i metadataene (algorithmicMedia for bilder tegnet av et skript, trainedAlgorithmicMedia for alt en KI-modell lager), sammen med opphavsperson, lisens og lenke til vilkårene, og byggingen sjekker at merket er der.

<div class="colophon-bubbles">
  <img src="/assets/images/bubbles/daily/mishmash_bubbles_daily.svg"
       alt="Dagens genererte variasjon av MishMash-bobleemblemet"
       width="340">
  <p>Dagens bobler, generert hver natt fra aktiviteten på nettstedet</p>
</div>

## Våre forpliktelser

1. **Mennesker er ansvarlige.** KI-produsert innhold gjennomgås som regel før det publiseres. Unntaket er de nattlige byggene, som henter nye data fra NVA og ORCID. Feil er våre, ikke maskinenes.
2. **Ingenting skjules.** KI-bruk erklæres, merkes på oversatte sider og kan spores i den åpne [commit-historikken](https://github.com/MishMash-Norway/mishmash-web/commits/main).
3. **Bruken vår av KI er en del av forskningen.** Å bygge våre egne kommunikasjonskanaler med KI-basert assistanse er en måte å *skape, utforske og reflektere* over verktøyene vi forsker på, og det vi lærer, føres tilbake til senterets forskning og undervisning.

## Nettstedets vekt

Bærekraft er en viktig sak for MishMash, og når vi bygger nettstedet selv, har vi full kontroll over hvordan det tegnes opp og serveres. Ved hver utrulling veier byggingen et utvalg sider i en nettleser uten hurtiglager og anslår karbonutslippet per besøk etter Sustainable Web Design-modellen slik den er implementert i CO2.js. Hele rapporten ligger på [/data/page-weight.json](/data/page-weight.json){: data-proofer-ignore="true"}, og labsiden [Fotavtrykket til dette nettstedet](/no/lab/footprint/) tegner og spiller den ved siden av den samme siden bygget på vanlig måte.

Nettstedet sparer båndbredde ved å komprimere bilder og sende dem progressivt ved behov, og ved å skjære skriftfilene ned til tegnene nettstedet bruker. Hele nettstedet er skrevet med omtrent 300 ulike tegn, mens en vanlig latinsk skriftfil bærer flere tusen tegnformer, så filene blir omtrent halvparten så store, og et første besøk på forsiden laster 85 kB skrift i stedet for 198 kB.

<div id="page-weight" class="page-weight" data-src="/data/page-weight.json" data-lang="nb"><noscript>Tabellen trenger JavaScript; tallene finnes i JSON-filen over.</noscript></div>
<script defer src="/assets/js/page-weight.js"></script>

## Nynorsk-eksperimentet

Nynorskutgaven av nettstedet (sidene under `/nn/`) lages automatisk: hver bokmålsside oversettes ved bygging med det regelbaserte, åpne oversettelsesverktøyet [Apertium](https://github.com/apertium/apertium-nno-nob) (nob–nno, moderat norm). Apertium er også motoren i Nynorskroboten, som NTB og NRK bruker for nynorsk, og der blir teksten korrekturlest før den publiseres. Hver generert side merkes med en boks øverst og lenker til bokmålsoriginalen. En håndkorrigert side under `site/nn/` i kildekoden vinner alltid over den genererte.

Språkrådets evaluering av seks verktøy for oversettelse fra bokmål til nynorsk, [*Frå bokmål til nynorsk*](https://sprakradet.no/wp-content/uploads/Fra-bokmal-til-nynorsk-evaluering-av-maskinomsetjingsverktoy-hausten-2025.pdf) (høsten 2025), fant feil i omtrent fire av ti maskinoversatte setninger, med liten forskjell mellom regelbaserte verktøy og KI-baserte samtaleroboter. Rapporten råder statsorganer til å lage utkast med et Apertium-basert verktøy og la noen som skriver god nynorsk, gå gjennom hele teksten. Nynorskutgaven av mishmash.no følger det første rådet, men ikke det andre: den er et eksperiment med hva verktøyene får til på egen hånd, ikke senterets offisielle nynorsk. For at den ikke skal bli treningsmateriale for fremtidige språkmodeller, er de genererte sidene reservert mot tekst- og datautvinning (se [vilkårene](/no/about/terms/)), stengt for søkerobotene som samler treningsdata, og merket maskinlesbart som oversatt fra bokmål med Apertium.

Vi publiserer utgaven vel vitende om at den inneholder feil, for å vise begrensningene i dagens modeller og bidra til å forbedre dem. MishMash tester ting i det åpne, avdekker problemer og retter dem, både i våre egne og i underliggende systemer. Finner du en feil, bruk «Foreslå en endring» i bunnteksten, så retter vi verktøyene eller siden.

{% include ai-colophon-commits.html lang="nb" %}

Tankene bak nettstedet står i [nettfilosofien](https://github.com/MishMash-Norway/mishmash-web/wiki/Web-Philosophy) i prosjektwikien og senterets [kommunikasjonsstrategi](/no/internal/kommunikasjonsstrategi/). Spørsmål eller innspill kan sendes til [contact@mishmash.no](mailto:contact@mishmash.no).
