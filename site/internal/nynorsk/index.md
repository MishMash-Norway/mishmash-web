---
layout: page
title: Nynorsk on mishmash.no
permalink: /internal/nynorsk/
description: "What the Language Act and the partners' language policies require, how Nynorsk is produced at scale, which tools can run in the site's build, and the options for a full Nynorsk mirror."
sitemap: false
page_about:
  ai_support:
    agent: Claude Code
    model_name: Claude
    model_version: "Fable 5.1"
---

This survey supports the [communication strategy](/internal/communication-strategy/) and the proposal in [issue #39](https://github.com/MishMash-Norway/mishmash-web/issues/39) to give mishmash.no a full Nynorsk mirror beside the Bokmål one. It was made on 17 September 2026 by web search and page fetching; every claim comes from a fetched page, named after the claim, and pages that could not be fetched are listed at the end. Figures are copied from the sources.

Survey written 2026-09-17 for Alexander Refsum Jensenius. Every claim below comes from a page fetched during the survey; the URL follows the claim. Pages that could not be fetched are named as such. Figures are copied from the sources, not computed.

## Summary

1. The Language Act (2021) requires central state bodies to use at least 25 % of each of Bokmål and Nynorsk in generally accessible documents over time (§ 13); for universities only the administrative part of the activity is covered (§ 3 fourth paragraph).
2. Språkrådet supervises under § 19, harvests state websites with the Målfrid crawler (word counts) and collects self-reported social media counts each January; the yearly report names each body.
3. In the 2024 supervision, OsloMet was the only university meeting the rule in new web text; UiO sat between 10 and 20 %; NTNU, UiT, Nord, KHiO and Innlandet were under 10 %; UiA and HiØ under 5 %.
4. Språkstatus 2025 says about 90 % of state bodies break the rules on Nynorsk and Bokmål, and that this includes all the universities and colleges.
5. Every institution policy fetched names Norwegian (Bokmål and Nynorsk) as main language; HVL alone has Nynorsk as its main written form; Nord, NLA, NMH and UiO restate the 25 % rule; UiT and Nord carry Sami provisions; NTNU, HVL and OsloMet name Norwegian sign language.
6. Apertium nob-nno is the rule-based engine under NPK's Nynorskroboten, which NRK uses for Bokmål to Nynorsk with proofreading; the pair reports a median word error rate under 5 % on NTB news.
7. Språkrådet's 2025 test of chatbots found 2.3 to 3.3 errors per 100 words in Nynorsk against 1.3 to 2.2 in Bokmål; NorMistral-11b did best in Nynorsk.
8. NorMistral-7b-warm reaches BLEU 75.8 and chrF++ 87.5 on Bokmål to Nynorsk (Tatoeba, zero-shot); no Nynorsk translation figures are published for the National Library's Borealis models.
9. Apertium APy is open source, preserves HTML, runs locally or at apertium.org/apy, and is what MediaWiki Content Translation uses; Weblate and i18n-ai-translate add translation memory and glossaries and run against Git.
10. Prices for Nyno, Nynorobot and NTB Arkitekst's Nynorskroboten are not published on the pages fetched.

## 1. Policy and law

### 1.1 The Language Act (språklova, LOV-2021-05-21-42)

Source: [lovdata.no](https://lovdata.no/lov/2021-05-21-42)

- Purpose (§ 1): strengthen Norwegian as a society-bearing language and promote equality between Bokmål and Nynorsk.
- § 4: Bokmål and Nynorsk are equal written languages in public bodies.
- Definitions (§ 2): a statsorgan is a state body or an independent legal entity where the state holds over 50 % of the votes or appoints over 50 % of the members of the top body; allment tilgjengelege dokument are documents issued and distributed by a covered body that are not addressed to individual recipients; sentrale statsorgan serve the whole country, regionale statsorgan serve less than the whole country.
- § 3 fourth paragraph: for universities, state colleges and other state schools only the administrative part of the activity falls under the language use rules, not the academic activity.
- § 13 (Veksling mellom bokmål og nynorsk i allment tilgjengelege dokument): central state bodies must over time use at least 25 % of each of Bokmål and Nynorsk in generally accessible documents.
- § 14: forms and self-service solutions must be available in both written languages at the same time.
- § 15: documents to private entities are in the language the entity wrote in; documents to municipalities follow the municipality's language decision.
- § 16: state bodies must ensure adequate writing competence; employees must be able to write both forms (with exceptions).
- § 19: Språkrådet supervises compliance with § 10 second paragraph and §§ 12 to 17 and gives guidance. § 20: state bodies must report to Språkrådet on request.
- § 5: Sami languages are indigenous languages, equal to Norwegian under the Sami Act chapter 3. § 6: Kven, Romani and Romanes are national minority languages. § 7: Norwegian sign language is the national sign language, equal to Norwegian in linguistic and cultural standing.

What this means for a research centre hosted by a university: UiO is a statsorgan, and the administrative part of its activity, which Språkrådet treats as including websites, is covered by § 13. The Act does not name research centres separately. Språkrådet's 2024 report shows it is still investigating the scope of the § 3 fourth paragraph exemption: FFI argued that texts written by researchers fall under it, Språkrådet replied that only the bodies named explicitly are exempt and that it is preparing an assessment of what the exemption covers (https://sprakradet.no/wp-content/uploads/Rapport-fra-tilsynet-med-bruken-av-nynorsk-og-bokmal-i-staten-for-2024_retta-versjon-141125.pdf, p. 33). [Question for Alexander: does UiO's supervision harvest include mishmash.no, or only uio.no subdomains? The report describes filtering out subdomains the body does not itself write; recommended action is to ask UiO's web team.]

Private institutions: the Act's obligations in §§ 12 to 17 attach to statsorgan as defined in § 2; Kristiania and NLA are not state-owned and their own policies (below) speak of following "gjeldende lovverk" or of a 25 % aim without citing an obligation.

The regulation to the Act: the consultation page for the forskrift (deadline 2022-10-01) was fetched, but the regulation text itself is only in the linked PDFs, which were not fetched (https://www.regjeringen.no/no/dokumenter/hoyring-forskrift-til-spraklova/id2917929/). No claim is made here about the regulation's wording.

### 1.2 How Språkrådet supervises and reports

Source: [sprakradet.no](https://sprakradet.no/spraklova/norsk-sprak/tilsyn-med-bruken-av-bokmal-og-nynorsk-i-staten/)

- Three categories are supervised: generally accessible documents (website text, social media posts, job adverts), forms (paper and digital) and digital self-service functions.
- Reporting is yearly, in January, deadline 31 January. Two methods: the Målfrid crawler, run by Språkbanken at the National Library, harvests state websites and measures text volume in Bokmål, Nynorsk, English and Sami; a Questback survey collects what Målfrid cannot see (social media, forms, digital services).
- The supervision covers the ministries, the Prime Minister's Office and their subordinate bodies. Yearly reports exist for 2020 to 2025.

Method details from the 2024 report (https://sprakradet.no/wp-content/uploads/Rapport-fra-tilsynet-med-bruken-av-nynorsk-og-bokmal-i-staten-for-2024_retta-versjon-141125.pdf):

- The alternation requirement applies to all generally accessible documents whatever the channel; social media are counted in posts, web text in words, so the two are not merged into one percentage (p. 10).
- Målfrid downloads all text systematically without metadata; some harvested text is not a generally accessible document, and Målfrid does not always catch every document. Språkrådet filters out some subdomains the body does not write itself (p. 17).
- Målfrid distinguishes html, docx and pdf. Its source code is open on GitHub and as a Python package (p. 17).
- The supervision themes are: new text on the web, social media, forms and self-service, and the duty to report.

Findings for the Ministry of Education's subordinate bodies in 2024 (same report, pp. 47 to 48):

- Meeting the alternation requirement in new web text: Høgskulen i Volda, HVL, Foreldreutvalet for grunnopplæringa, Utdanningsdirektoratet and OsloMet. Lånekassen had 40 % but does not alternate; it runs near-complete parallel sites.
- Nearly meeting it: Forskingsrådet, UiB, HK-dir and NMH.
- Between 10 and 20 %: NOKUT, NIH, UiO and NUPI.
- Under 10 %: UiS, NHH, Nord, USN, NTNU, 22. juli-senteret, AHO, KHiO, Høgskolen i Molde, Universitetet i Innlandet and UiT.
- Under 5 %: UiA, HiØ, NMBU, Statped, Sikt, Vea and the research ethics committees.
- Social media requirement met by 14 bodies including HVL, Volda, NMH, NIH, UiS, NHH, Nord and NTNU; UiB, HK-dir, NOKUT, USN and UiT nearly.
- All forms and self-service on both languages: 6 of 30 bodies, including UiT and HiØ.
- Språkrådet writes that OsloMet is the only university that meets the alternation requirement in new web text, with a caveat that some subdomains were not harvested as planned; HVL, UiB and HK-dir nearly meet all themes.

Findings for 2023 reported by Khrono on 2024-07-08 (https://www.khrono.no/mange-universitet-og-hogskular-bryt-spraklova/886962): Volda 78 %, Lånekassen 49 % and HVL 38 % of all text on the main site met the rule; Nord 3 % new text and 2 % total; NTNU 32 % social media, 4 % new, 4 % total; UiO 20 % social media, 14 % new, 12 % total; USN 28 %, 8 %, 7 %; Innlandet 3 %, 3 %, 3 %; AHO 4 %, 4 %, 2 %.

Findings for 2025 reported by Khrono on 2026-07-29 (https://www.khrono.no/utdannar-bokmalspoliti-hogskulen-har-ein-prosent-nynorsk/1074125): Politihøgskolen 1 %, Innlandet 3 %, UiT, NTNU and HiØ 4 %, UiA 7 %.

Språkstatus 2025 (https://sprakradet.no/wp-content/uploads/Sprakstatus-2025.pdf):

- Of the central state bodies supervised for 2023, 90 % broke one or more of the requirements assessed (p. 24). Of 168 subordinate bodies, 10 met all requirements (up from 1 in 2022); 46 used at least 25 % Nynorsk in social media (36 in 2022); 14 used at least 25 % Nynorsk in total web text (8 in 2022); 26 in new web text (13 in 2022) (p. 25).
- Average Nynorsk share of all text on subordinate bodies' main sites in 2023: 10 %; in new text: 11 %; in social media posts: 19 % (p. 26). Regjeringen.no: 25 %.
- In its assessment Språkrådet writes that about 90 % of state bodies still break the provisions on Nynorsk and Bokmål, and that this applies to all the universities and colleges (p. 29).
- On language technology: Språkrådet has secured that publicly funded language models must work in both Bokmål and Nynorsk; NB-Whisper and the Mímir models at the National Library and NorwAI at NTNU are built for both (p. 12). Språkrådet has no reliable benchmark results for text tools, only a count of datasets; commercial models produce a fair number of errors in Norwegian and most in Nynorsk (p. 13).
- Of 124 bodies with digital self-service, 42 % took Nynorsk versions into account in procurement (p. 27).

### 1.3 Institution policies

Each subsection states what the fetched policy says on: main language, minimum share, who writes Nynorsk, translation practice, tools, Sami, sign language.

#### University of Oslo (UiO)

Sources: [uio.no](https://www.uio.no/for-ansatte/arbeidsstotte/profil/sprak/malbruk/) and [uio.no](https://www.uio.no/for-ansatte/arbeidsstotte/kommunikasjon/nettarbeid/veiledninger/skrive-for-nett/sprak/nynorsk/)

- UiO must follow the Act: at least 25 % of texts on the web and in print must be in Nynorsk; the rule covers letters, websites, forms, press releases and exam papers; internal texts for staff are exempt. Anyone who writes to UiO gets a reply in the same form.
- All staff must be able to use both forms; UiO as employer offers Nynorsk courses.
- Translation: UiO has a framework agreement with a translation bureau, and staff can download the Nyno program for automatic translation to Nynorsk.
- The web guidance sets targets by area: all editorial pages under om/organisasjon in Nynorsk; 25 % of IT service pages; 30 % of "vi forskar på" landing pages; all external forms; 25 % of study pages at each level; 25 % of library subject pages; Nynorsk templates for staff presentations. It records about 12.3 % Nynorsk on the web in 2015. It names no machine translation tool and no marking convention.
- No mention of Sami or sign language on the pages fetched. The UiO page for Nyno 3.32 (https://programvare.uio.no/produkt/6674.html) returned 404.

#### University of Bergen (UiB)

Source: [www4.uib.no](https://www4.uib.no/om-uib/organisasjon/sprakpolitisk-utval)

- Norwegian is the main language; Nynorsk is to have a central place, and UiB states a special responsibility for Nynorsk in Norwegian higher education. Guidelines adopted by the board 2019-10-31. The full PDF (https://ekstern.filer.uib.no/ledelse/universitetsstyret/2019/2019-10-31/S_99-19Språkpolitiske_retningslinjervedUiB.pdf) was not fetched, so nothing is stated here on share, tools, Sami or sign language.

#### NTNU

Source: [ntnu.no](https://www.ntnu.no/sprakpolitiske-retningslinjer)

- In force 2023-01-01. Main language is Norwegian, covering both Bokmål and Nynorsk, with measures to strengthen Nynorsk competence and use. Administrative staff must have sufficient competence in both forms and in English. No percentage is given in the guidelines themselves. Norwegian sign language is named as the national sign language, with interpreting and captioning at institutional events. No Sami provision on the page fetched.

#### UiT The Arctic University of Norway

Source: [uit.no](https://uit.no/utdanning/art?p_document_id=347818&dim=179017)

- Both forms are to be used to a significant extent in generally accessible circulars, announcements and information material, at minimum as the law requires; central documents in parallel versions; staff who prefer Nynorsk are supported and courses in Nynorsk are offered. UiT has national responsibility for North Sami: key documents and websites in North Sami where practical, and replies in North Sami where possible. Kven is named; generic profiling material should exist in Nynorsk, Bokmål, Sami, Kven and English. A language committee reports every 2 years to the rector. Approved by the rector under delegation (FS 42/23); page last edited 2024-02-08. No sign language provision on the page fetched.

#### University of Agder (UiA)

Source: [uia.no](https://www.uia.no/om-uia/regelverk-og-retningslinjer/sprakpolitiske-retningslinjer.html)

- Adopted 2021-09-15 (board case 112/21). Norwegian, both Nynorsk and Bokmål, is the main language; staff follow the rules on both forms; staff and students with Nynorsk are encouraged to use it. A language service develops courses, does language review and translation for research and outreach. No Sami or sign language provisions.

#### Western Norway University of Applied Sciences (HVL)

Source: [hvl.no](https://www.hvl.no/om/sentrale-dokument/reglar/sprakpolitiske-retningslinjer/)

- Nynorsk is the main language, with a stated duty to support, use and develop it; no written form under 25 %. Staff and students are expected to keep Nynorsk competence; international permanent academic staff must document B2 within 3 years. HVL will set language requirements on IT suppliers, prioritise Nynorsk in learning platforms and search, and contribute to strengthening Nynorsk in AI tool development. Writing support and courses are offered. Norwegian sign language is a priority language with interpreters on demand. No Sami provision. Revised October 2025.

#### University of Inland Norway (INN, formerly HINN)

Source: [inn.no](https://www.inn.no/om-universitetet/organisering/styringsdokumenter/Spraakpolitiske-retningslinjer-HINN) (PDF)

- Approved by the board 2019-03-12 (case 15/19). Norwegian, both Bokmål and Nynorsk with reference to the then Lov om målbruk i offentleg teneste, is the primary working and administrative language; the mållov's provisions apply in addition. Access to a language editing service is to be provided. No percentage, Sami or sign language provision.

#### Nord University

Source: [nord.no](https://www.nord.no/sites/default/files/inline-images/Spraakpolitiske-retningsliner-nynorsk.pdf)

- Adopted 2018-09-18. Motto: secure Norwegian, promote Sami, improve English. Norwegian is the primary language; Bokmål is the majority form in Nord's regions, and the aim is to meet the mållov's requirement of at least 25 % Nynorsk in generally accessible circulars, announcements and information. Staff and students are to have access to information, training and language services. National responsibility for Lule Sami and South Sami; Sami as a publishing language; main signage in Norwegian and Sami. No sign language provision.

#### OsloMet

Source attempted: [ansatt.oslomet.no](https://ansatt.oslomet.no/en/language-policy-guidelines-oslomet) and [ansatt.oslomet.no](https://ansatt.oslomet.no/sprakpolitiske-retningslinjer-oslomet), both returned HTTP 403, so the policy text is not summarised here. What the fetched 2024 supervision report says: OsloMet has worked well with Nynorsk for several years and is the only university meeting the alternation requirement in new web text for 2024, with a caveat on harvesting (https://sprakradet.no/wp-content/uploads/Rapport-fra-tilsynet-med-bruken-av-nynorsk-og-bokmal-i-staten-for-2024_retta-versjon-141125.pdf, p. 48).

#### Kristiania University College (private)

Source: [kristiania.no](https://www.kristiania.no/globalassets/strategi-og-rapporter/sprakpolitiske-retningslinjer-ved-hoyskolen-kristiania2.pdf)

- Adopted 2020-12-17. Norwegian covers both Bokmål and Nynorsk; use of written language is to comply with current law; staff and students with Nynorsk may use it; parallel language use with English as the primary foreign language. No percentage, Sami or sign language provision.

#### Norwegian Academy of Music (NMH)

Source: [ansatt.nmh.no](https://ansatt.nmh.no/organisasjon/strategier/sprakpolitiske-retningslinjer-for-norges-musikkhogskole)

- At least 25 % of each form in NMH's combined external communication; all official forms in both forms; based on Språkrådet's 2018 guide for the sector. No adoption date given; no Sami or sign language provision. The 2024 supervision report notes NMH nearly meets the requirement when social media and web are seen together.

#### Oslo National Academy of the Arts (KHiO)

Source: [khio.no](https://khio.no/intranett/nyheter/sprakpolitikk-for-khio)

- Adopted 2014-09-30. Both forms are to be clearly visible in written texts across channels in line with the Act. Sami and Norwegian are equal official languages and Sami is to be treated equally where natural. No percentage, tools or sign language provision.

#### Østfold University College (HiØ)

Source: [hiof.no](https://www.hiof.no/om/styringsdokumenter-rapporter/styringsdokumenter/sprakpolitisk-plattform.html)

- Published 2020-06-04, revised 2022-02-15 to align with the Act. Norwegian means both forms; administrative staff follow the Act's rules on the two forms; no percentage, Sami or sign language provision. HiØ was under 5 % in new web text in 2024 and at 4 % in 2025 (Khrono, above), while it had all forms and self-service in both forms in 2024.

#### NLA University College (private)

Source: [nla.no](https://www.nla.no/om-nla/vedtekter-og-planer/_/attachment/inline/33f3aebb-a541-48b7-86fb-e51b9aa3f53b:3998fdc87cd19deadeeb617570630d29dfab363c/sprakpolitiske-retningslinjer-nla.pdf)

- Norwegian (Bokmål and Nynorsk) is the main language for teaching, outreach and administration. Both forms are to be used actively on paper and web, through parallel versions or by having some documents in one form and others in the other, or chapters in each; roughly equal distribution is to be sought in forms, governing documents and web information, and at least 25 % of such texts should be in the form used least. Formal enquiries are answered in the same form. No adoption date on the document; no Sami or sign language provision.

## 2. Methods for producing Nynorsk at scale

### 2.1 Apertium nob-nno (rule-based)

Sources: [github.com](https://github.com/apertium/apertium-nno-nob), [wiki.apertium.org](https://wiki.apertium.org/wiki/Norwegian_Nynorsk_and_Norwegian_Bokm%C3%A5l), [wiki.apertium.org](https://wiki.apertium.org/wiki/Apertium-apy)

- Licence GPL-2.0. Requires lttoolbox, apertium, vislcg3 and apertium-lex-tools; built with autogen, configure, make. Command line: `echo "..." | apertium -d . nob-nno`. Variants: nno (a-mål, default, "me"), nno_e (e-mål, "vi"), nno_e_me, nno_a_vi. Latest release 1.6.0; test at beta.apertium.org.
- Quality: median word error rate under 5 % on NTB news articles (1,221 articles, median WER 3.95 to 4.37 %); a 2009 test gave 10.71 % on a linguistics article. A 2024 comparison against large language models on the wiki page reports BLEU 0.817 to 0.898, METEOR 0.932 to 0.964, BERTScore 0.984 to 0.987 for the pair.
- Users and funding: Nynorsk Wikipedia uses it for translation suggestions; NPK and the Ministry of Culture have sponsored development 2018 to 2026.
- API: apertium-apy is a Python 3 API server with /translate, /listPairs, /analyze, /generate and /translateDoc; it preserves markup through deformatter and reformatter parameters (HTML, plain text, RTF and others); a public instance runs at [apertium.org](https://apertium.org/apy) for released pairs; MediaWiki Content Translation uses it. It can be self-hosted in a build pipeline.

### 2.2 Nynorskroboten (NPK, NTB, NTB Arkitekst)

Sources: [kommunikasjon.ntb.no](https://kommunikasjon.ntb.no/pressemelding/nasjonalbiblioteket-samarbeider-med-nynorsk-pressekontor-npk-og-ntb-om-vidareutvikling-av-nynorskroboten?publisherId=17847232&releaseId=17877823) (2020-01-14), [kommunikasjon.ntb.no](https://kommunikasjon.ntb.no/pressemelding/ntb-arkitekst-tar-over-nynorskroboten?publisherId=17847221&releaseId=17926255) (2022-02-11)

- Built by NPK from 2018 on open source code and 37,000 parallel NTB/NPK texts (74,000 articles) handed to the National Library in 2019; the Library gave NOK 500,000 in 2020 for further development and hosts the parallel texts in Språkbanken.
- Since 2022 NTB Arkitekst offers it commercially; it is built on Apertium, which NPK continued developing through 2022. NTB Arkitekst's director claims the error margin is lower than for manual translation; no figures, prices or API details are given.

### 2.3 NRK and the newspapers

Source: [framtida.no](https://framtida.no/2026/03/19/mindre-nynorsk-i-nrk-i-2025-kjipt-a-sja)

- NRK's 2025 Nynorsk shares: TV 28 %, radio 23.3 %, web 23.4 %, overall 26.6 %, against a requirement of 25 % on each platform.
- NRK's language chief says NRK uses the rule-based Nynorskroboten from NTB to translate from Bokmål to Nynorsk and explicitly does not use AI for that; NRK strengthened quality control of articles in 2025 and runs a Nynorskhjelparen service for journalists before publication.

### 2.4 Nyno and Nynorobot (Nynodata AS, commercial)

Sources: [nynodata.no](https://www.nynodata.no/nyno), [nynodata.site](https://nynodata.site/info/omnynorobot/), [nynodata.no](https://nynodata.no/kjop/)

- Nyno converts Bokmål to Nynorsk sentence by sentence with suggestions; style templates for radical, moderate or conservative Nynorsk and regional tailoring; editions for Chrome, Office (Nyno 4) and CMS. Nynorobot is the automatic converter, described as built on years of development and open source components, with conservative, moderate and radical output, a web demo, Office 365 integration and CMS connections; it is marketed to public bodies for the 25 % rule.
- Licence: subscriptions of 1 to 2 years; institutional licences on quotation. No prices on the pages fetched; the single-user price page returned 404. UiO's staff page says staff can download Nyno (see 1.3).

### 2.5 Large language models

Norwegian models:

- NorMistral-7b-warm (LTG, University of Oslo), Apache-2.0, 7 billion parameters, continued pretraining on 260 billion tokens. Tatoeba Bokmål to Nynorsk: BLEU 75.8, chrF++ 87.5 zero-shot (74.0/86.9 1-shot, 75.3/87.5 5-shot); Nynorsk to Bokmål 88.1/93.6 zero-shot. Mistral-7B-v0.1 scores 32.0/62.2 on the same task (https://huggingface.co/norallm/normistral-7b-warm).
- Borealis (National Library AI lab): 270M, 1B, 4B, 12B and 27B; full models under an NB licence adapted from Apache 2.0 with use-based restrictions, open models under the Gemma licence; evaluated on NorEval, MMLU-English and nb-gpt-bench; no Bokmål to Nynorsk translation figures given; no API, only download from Hugging Face (https://ai.nb.no/borealis/).
- NorT5: named among LTG's models in search results; no page with Nynorsk translation results was fetched, so no figure is given.

Språkrådet's 2025 test of chatbots (https://sprakradet.no/wp-content/uploads/Rapport-fra-test-av-sprakroboter-2025.pdf):

- Models: ChatGPT 4.5, Microsoft Copilot, Le Chat (Mistral Pro), NorMistral-11b-warm-instruct. Six Språkrådet staff with long experience of language quality assurance marked errors in 68,635 generated words: 10 short factual texts and 10 short stories per model.
- Errors per 100 words, Bokmål: ChatGPT 1.5, Copilot 1.3, Le Chat 2.2, NorMistral 1.3. Nynorsk: ChatGPT 2.6, Copilot 2.4, Le Chat 3.3, NorMistral 2.3.
- Grammar errors (spelling and inflection) per 100 words in Nynorsk: ChatGPT 1.23, Copilot 1.21, Le Chat 1.96, NorMistral 0.81. Språkrådet's reading: in Nynorsk NorMistral is best, followed by Copilot and ChatGPT, with Le Chat well behind; all four make many errors of many kinds.
- The earlier October 2024 test of ChatGPT alone gave 2 to 3 errors per page of 320 words in Bokmål and about 8 per page in Nynorsk.
- Advice for public bodies: set aside enough resources for post-editing including language, fact and source checks, and extra resources for checking Nynorsk texts (section 6, citing the plain language provision in § 9).

Note that this test measured text generation, not Bokmål to Nynorsk translation; no Språkrådet or university evaluation of LLM translation between the two forms was found among the pages fetched.

### 2.6 Hybrid workflows with human post-editing

- NPK's Nynorskroboten output is corrected manually before publication (Språkbanken description in search results; the NPK translation memory corpora sbr-47 and sbr-80 were not fetched).
- NRK: robot translation plus strengthened proofreading and a help service (2.3).
- Lånekassen: near-complete parallel Bokmål and Nynorsk websites with a language switch, counted by Språkrådet as 40 % Nynorsk in new text though without alternation (2024 report, p. 48).
- Språkrådet's advice on chatbots (2.5) is the closest thing to an official recommendation: automatic output needs budgeted post-editing, more so in Nynorsk.

## 3. Tools for a static site

### 3.1 Build-time translation in CI

- Apertium: the pair builds from source (GPL-2.0) and apertium-apy exposes HTTP endpoints; both can be installed in a GitHub Actions job or the public [apertium.org](https://apertium.org/apy) instance can be called for released pairs. APy's HTML deformatter and reformatter keep markup intact, which matters for Jekyll output or Liquid-free Markdown (https://wiki.apertium.org/wiki/Apertium-apy, [github.com](https://github.com/apertium/apertium-nno-nob)).
- i18n-ai-translate: GPL-3.0 CLI, library and GitHub Action (`taahamahdi/i18n-ai-translate@master`) with OpenAI, Gemini, Claude or local Ollama backends; a JSON cache acts as translation memory so unchanged strings are not resent; a JSON glossary keeps terms verbatim or forces exact per-language translations. Supported formats are i18next JSON, Gettext .po, Java .properties, iOS .strings, Rails YAML and JS/TS modules; Markdown and HTML are not listed (https://github.com/taahamahdi/i18n-ai-translate). For a Jekyll site this fits UI strings in `_data`, not page bodies.
- Weblate (self-hosted or hosted): built-in translation memory with fuzzy matching, glossaries, and machine translation backends including Apertium APy, OpenAI, Anthropic Claude (from 5.16), Mistral and Ollama; 100 % translation memory matches take priority over machine translation; LLM backends receive glossary entries and failed checks as context; code-hosting and version control integration is documented separately (https://docs.weblate.org/en/latest/admin/machine.html). Weblate works on translation files (gettext and others), so page bodies would need to be split into units first.
- Measuring the share: Målfrid, Språkrådet's crawler, is open source on GitHub and as a Python package, so the Nynorsk share of mishmash.no can be measured the same way Språkrådet measures UiO (2024 report, p. 17).

### 3.2 Translation memory and glossaries

- Apertium has no translation memory; consistency comes from its dictionaries and lexical selection rules, and its variant flags (a-mål or e-mål, "me" or "vi") fix the norm across the site (https://github.com/apertium/apertium-nno-nob).
- i18n-ai-translate and Weblate both provide memory and glossaries as described above.
- The NPK/NTB parallel corpora deposited in Språkbanken are what the national systems were trained on; they were not fetched here.

### 3.3 Marking automatic translations

- NRK marks nothing on the page but proofreads before publishing; Lånekassen offers a full parallel site with a switch (2024 report). No fetched page gives a convention for labelling machine-translated pages on a public site; Språkrådet's advice is that automatic text is post-edited, not labelled and left.

### 3.4 Review workflows

- NPK and NRK: robot draft, human correction, publish (2.2, 2.3).
- MediaWiki Content Translation: Apertium among its services; automatic mechanisms enforce review of the initial machine translation before publishing, and corrections are exposed through an API and dumps to improve the services; the page does not state which service serves nb to nn (https://www.mediawiki.org/wiki/Content_translation/Machine_Translation). The Apertium wiki states that Nynorsk Wikipedia uses the pair for translation suggestions.
- The Nynorsk Wikipedia community page fetched describes interface translation and copying between nn and no, but sets no machine translation policy (https://nn.wikipedia.org/wiki/Wikipedia:Wikipedia_p%C3%A5_nynorsk).

### 3.5 Open source components that run in GitHub Actions

Apertium (pair, lttoolbox, vislcg3, apy), Weblate (self-hosted), i18n-ai-translate, Målfrid, and NorMistral or Borealis under their licences with a local runner such as Ollama. The commercial services (Nynorobot, NTB Arkitekst's Nynorskroboten) publish no API documentation on the pages fetched.


## Test on mishmash.no text

To ground the options, four Bokmål pages of this site (accessibility, privacy, terms, communication strategy; 2,310 words in all) were sent through the public Apertium service on 17 September 2026. The engine marked 43 tokens as unknown, 18.6 per 1,000 words; almost all were names and English product terms (Pa11y, JavaScript, Freesound, Wikidata, MishMash), which it passes through unchanged with an asterisk. The whole accessibility page (373 words) was then read as Nynorsk: one real error was found, a wrongly formed adjective, and everything else read as correct, natural Nynorsk. Chaining the pair with its e-infinitive variant (nno_e) turned "me" into "vi" and a-infinitives into e-infinitives, which is the moderate norm most institutions use, and the second pass marked the faulty adjective as unknown, so the two steps together also act as a check. The Ubuntu 24.04 image that GitHub's runners use packages both Apertium and the Nynorsk pair, so the same translation can run inside the site's build without an external service.

## 4. Options for MishMash

Each option assumes the English source, the Bokmål mirror under /no/ and a new /nn/ mirror.

### Option A. Apertium in the build, full coverage, marked as automatic

Run apertium nob-nno with APy's HTML mode in a GitHub Actions job that generates /nn/ from /no/ at build time, with the nno variant fixed for the whole site, a small pre- and post-substitution list for centre terms, and a banner or footer note that the page is machine translated with a link to the Bokmål page.

- For: full coverage from day one; GPL software with no per-word cost; the same engine as NPK and NRK; median WER under 5 % on news text; markup preserved.
- Against: no human check, so the roughly 1 in 20 word errors reach readers; centre vocabulary and English terms may be mishandled; Språkrådet advises post-editing; how a labelled automatic page counts in Målfrid is not stated in the sources.

### Option B. Apertium draft plus human post-editing in pull requests

Same engine, but the output is committed as source under /nn/ and reviewed page by page, with new or changed Bokmål pages producing a draft pull request for a Nynorsk reader to correct before merge; corrected pages are never regenerated.

- For: the NPK and NRK model; quality under human control; a git history of corrections that can seed a translation memory; coverage grows with review capacity.
- Against: needs a Nynorsk reader on call; unreviewed pages either stay Bokmål-only or fall back to option A; two mirrors to keep in step with the English source.

### Option C. Language model draft with glossary, post-edited

Use a local NorMistral or a commercial model through i18n-ai-translate for `_data` strings and a custom prompt for page bodies, with a JSON glossary and cache, then human review as in B.

- For: glossary and translation memory built in; can follow style instructions (conservative or radical forms, centre terms); NorMistral had the fewest Nynorsk grammar errors in Språkrådet's test.
- Against: 2.3 to 3.3 errors per 100 words in generated Nynorsk in Språkrådet's test, which is a generation task, not translation; API cost per run for commercial models; Markdown and HTML are not supported formats in i18n-ai-translate; a local 7B or 11B model needs a runner outside GitHub's standard hosted job.

### Option D. Commercial converter (Nynorobot or NTB Arkitekst's Nynorskroboten)

Buy a subscription and connect it through its CMS or Office integration or, if offered, an API, then post-edit.

- For: vendor support, style templates, used by public bodies for exactly this rule.
- Against: prices and API documentation are not public on the pages fetched; underlying engines are Apertium or undocumented, so the quality gain over option A is not established by any fetched source; a proprietary dependency in an otherwise open pipeline.

### Option E. Selective human Nynorsk without a full mirror

Write chosen pages in Nynorsk by hand (about, organisation, news and events posts in rotation), as UiO's own web guidance does, and alternate rather than mirror.

- For: what the Act's § 13 asks of a state body is alternation over time, not parallel versions; UiO's guidance already works this way; no machine output at all.
- Against: no full Nynorsk site; readers choosing Nynorsk get a mixture; the share must be tracked (Målfrid can do this) and kept above 25 % as content grows.

## Pages that could not be fetched

- OsloMet language policy (HTTP 403, two URLs).
- Forskrift til språklova text (only the consultation page was fetched).
- Nynodata price pages (404) and UiO's Nyno product page (404).
- UiB's full guidelines PDF, NorT5 model card, NPK translation memory corpora, Kristiania's second PDF, UHR's language policy page: not fetched within the budget.
