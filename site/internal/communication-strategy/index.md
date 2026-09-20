---
layout: page
title: Communication strategy
permalink: /internal/communication-strategy/
translation_url: /no/internal/kommunikasjonsstrategi/
---

This communication strategy complements the [channel strategy](/internal/kanalstrategi/). The channel strategy describes *which* channels MishMash uses and how they work together; this document describes *how we communicate* in those channels: who our readers are, what they need, and what tone and complexity fits each of them. It also says what MishMash commits to beyond what its [partners' strategies](/internal/partner-communication-strategies/) already ask of their staff.

## Principles

1. **One source, many readers.** The same underlying facts are presented at different levels of complexity rather than being rewritten in parallel documents that drift apart. On mishmash.no this is implemented as [adaptive content and stretchtext](https://github.com/MishMash-Norway/mishmash-web/wiki/Web-Philosophy): readers choose a reading level, and pages unfold more detail on demand. See the [about page](/about/description/) for a working example.
2. **The reader chooses.** We do not guess or track who a reader is. Readers self-select their level, and can always switch. The plain-language version is the default.
3. **Pull, don't retype.** Facts about people, projects, institutions, and results are pulled from authoritative sources (NVA, ORCID, Wikipedia) rather than maintained by hand, so readers at every level get the same up-to-date information.
4. **Plain language first.** Following klarspråk principles and the [Language Act](https://lovdata.no/dokument/NL/lov/2021-05-21-42), the default register is plain language; jargon is something readers opt *into*, not out of.
5. **Open by default.** What we publish may be reused: text under CC BY 4.0, our own data under CC0, code under MIT, with the sources of every fact named at the bottom of the page and the terms stated for people and machines alike. See the [terms of use](/about/terms/) and the section on licences below.
6. **Usable by everyone.** The site meets the requirements of the regulation on universal design of ICT (WCAG 2.1 level AA) and says so on the [accessibility page](/accessibility/); every change is checked before it is published, and pieces that need sound, a pointer or JavaScript say so.
7. **Show the limits.** We say what a system cannot do and how a result was measured, and we publish the measurements of our own channel rather than promising them.
8. **Art is subject, object, expression and method.** In MishMash, artistic work is not a way of disseminating research done elsewhere; it is what the centre studies, what it makes, how it expresses what it finds and how it inquires. Concerts, installations, performances and the pieces in the [lab](/lab/) are therefore communication in their own right, with the same declarations of sources and AI as the text, and they are judged as research as well as as outreach.

## Reading levels

Adaptive pages offer the same content at three **complexity levels** (defined in `site/_data/audiences.yml`). The levels describe the *text*, not the reader — a professor reading outside her field may prefer Standard, and a curious teenager may pick Advanced. Reader roles are deliberately kept out of the ladder; who *typically* reads at each level is guidance for writers, nothing more:

| Level | Complexity | Typical readers | Tone and style |
| --- | --- | --- | --- |
| **Simple** | Short and simple, no jargon | Kids and teenagers, school classes | Short sentences, concrete examples, questions; unavoidable terms explained inline with stretchtext |
| **Standard** (default) | Plain language (klarspråk) | The general public, curious visitors, policymakers | Everyday examples; why it matters to society; key terms introduced with stretchtext |
| **Advanced** | Full detail, nothing simplified away | Researchers, students, artists, and field experts | Full precision: methods, challenges, work-package detail, academic references |

## Secondary audiences

Not every audience should be a reading level: most are better served by dedicated pages and channels:

- **Press and media**: need quotable facts, figures, images, and contacts quickly. Served by clear about pages and direct contact with management, not a separate reading level.
- **Policymakers and funders**: need societal relevance and impact. Served by the Standard level plus results and news.
- **Prospective academic partners**: researchers and institutions considering joining or collaborating with the network. Served by the about pages (Advanced level), work-package pages, [results](/results/), and direct contact with WP leaders and management.
- **Prospective public/private sector partners**: companies, cultural institutions, and public bodies. Served by [project pages](/projects/), news showing existing collaborations, and contact with management.
- **Prospective employees and students**: served by [vacancies](/vacancies/) and work-package pages; students who want to help build the website itself are pointed to the [website project](/projects/the-mishmash-website/) and the [developer wiki](https://github.com/MishMash-Norway/mishmash-web/wiki).
- **The MishMash network (internal)**: served by the [internal pages](/internal/), mailing lists, and work-package channels as described in the [channel strategy](/internal/kanalstrategi/).

## Mapping audiences to channels

Channels, unlike reading levels, do target audiences:

| Channel (see [channel strategy](/internal/kanalstrategi/)) | Kids & teens | General public | Academics & artists | Field experts | Internal |
| --- | --- | --- | --- | --- | --- |
| mishmash.no (adaptive pages) | ✓ | ✓ | ✓ | ✓ | |
| mishmash.no (results, directory) | | ✓ | ✓ | ✓ | ✓ |
| mishmash.no/internal | | | | | ✓ |
| ALL@ mailing list | | | | | ✓ |
| ANNOUNCEMENTS@ mailing list | | ✓ | ✓ | ✓ | ✓ |
| LinkedIn | | ✓ | ✓ | ✓ | |
| Instagram | ✓ | ✓ | | | |
| YouTube | ✓ | ✓ | ✓ | ✓ | |

## Open science, open education, open knowledge

Principle five is part of a larger commitment. MishMash sees research, education and communication as one ecosystem: research-based and research-led education draws on the same open results the public reads, and communication is the layer that connects them. Four practices follow.

- **Open science.** Results are registered in the national research archive and shown on the site with their identifiers; data and code go to open repositories with a licence and a DOI; abstracts, sources and, where possible, the material behind a claim are one click from the claim. Open access is the default for what the centre publishes.
- **Open education.** Teaching material made in the centre, from MeshUp talks to course modules and the wiki that teaches students to build the site, is published under open licences so that partners and others can teach with it. Students build the site and its experiments as part of their education, in public.
- **Open knowledge.** Facts about people, institutions and works are pulled from the open knowledge graph and given back to it: identifiers and corrections go to Wikidata, openly licensed images to Wikimedia Commons, sounds to Freesound, and the site's own data is released under CC0 so that it can be reused without asking.
- **Citizen science and participation.** The forms, the lab and the correction link in every footer are entry points for people outside the centre; projects that invite the public to contribute recordings, observations or judgements state what happens with the contribution, under which licence, and how contributors are credited.

None of the partners' communication strategies names open science, open education or open knowledge as a communication principle; UiO's one line on open access and Simula's on open source and data are the nearest. For MishMash it is the frame the other principles sit in.

## Art as method, not dissemination

Principle eight has a practical consequence that is easy to lose when planning communication. Public performances and exhibitions are integral to the centre's work, not a shop window for it. Demonstrating and testing AI-based systems in a concert hall, a gallery or a museum is part of the iterative design loop: formal and informal evaluation in a real venue feeds the next version of the system, and the documentation from those events is material for the researchers studying what AI does to performers and audiences.

Two things follow for how we communicate.

- **An artistic event is reported as research.** A concert or an installation gets the same treatment as a publication: what was made, with which tools, what was learned, what the sources were and what AI contributed. It belongs in the results list and the [gallery](/gallery/), not only in the events calendar.
- **Real-world exploration can produce findings.** Working in public, with real audiences and their consent, has produced scientific results before, as the MusicLab concert series showed. Communication plans should therefore treat an audience as participants who may be asked something, not only as people who are told something.

This is where MishMash differs from most of the partners' strategies, which treat art as a way of making research visible. Here art is the subject, the object, the expression and the method, and the communication has to be able to say so.

## The website as it now stands

mishmash.no carries the reading levels and stretchtext described above, and a set of features that follow from the principles: a [lab](/lab/) where any work package can publish a browser experiment with its data and AI declared; a [kiosk view](/kiosk/) for screens in partner lobbies; forms for news, events, MeshUp talks and corrections so that members contribute without git; objects from Norwegian heritage collections shown in place with the collection's own rights statement; a directory, results list and calendar kept in step with the national research archive; and terms, privacy and accessibility pages that say what the site does rather than what it hopes. What exists is listed on the [website project](/projects/the-mishmash-website/) page; what is planned is in the issue tracker.

## AI in the making of the website

MishMash actively uses AI in developing and maintaining mishmash.no, which is fitting for a centre that studies creative uses of AI. AI assistance is used for writing and adapting content (including drafting the reading-level variants on adaptive pages), for developing the site's code and automation, and for machine translation between English and Norwegian. Two commitments frame this use:

1. **Transparency.** We are open about where and how AI contributes: machine-translated pages are marked as such, AI-assisted development is visible in the public commit history, and this section itself declares the practice. Readers and partners should never have to guess whether AI was involved.
2. **It is an experiment.** Using AI to build the centre's own communication channel is part of MishMash's research practice — a way to *create, explore, and reflect* on our own tools. Human editors remain responsible for everything published: AI output is reviewed before it goes live, and errors are ours, not the machine's. What we learn feeds back into the centre's research and teaching.

The practice is declared publicly on the [AI colophon](/about/ai-colophon/) page, documented in more depth in the [web philosophy](https://github.com/MishMash-Norway/mishmash-web/wiki/Web-Philosophy), and evaluated alongside the other website experiments. Three rules follow from the commitments: every page that used AI says so in its footer; every lab piece states how AI was involved in one sentence; and generated images will carry the industry's provenance markers as soon as the build pipeline can write them. None of the partners' strategies states a disclosure rule for AI in the institution's own communication; this one does.

## Licences and reuse

What MishMash publishes is meant to be reused, and the terms say so in one place so that readers, partners and machines do not have to guess.

- **Text** on mishmash.no is licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): anyone may copy, adapt and redistribute it, for any purpose, with attribution to MishMash. This includes use as training material for AI systems; attribution is the condition, not a reservation.
- **Code** in the website repository is offered under the [MIT licence](https://opensource.org/license/mit), so that scripts, includes and interface themes can be reused in projects that cannot take a copyleft licence.
- **Data** that the site produces itself (events, projects, tags, the results list as compiled here) is released under [CC0](https://creativecommons.org/publicdomain/zero/1.0/), since facts are not creative works and CC0 lets them flow into Wikidata and other open databases without friction. Data pulled from NVA, ORCID and Wikipedia keeps the terms of its source, which is named on the page.
- **Images** carry their own terms, file by file: photographer, licence and consent are recorded with the image, and event photographs are CC BY where that was agreed with the photographer beforehand. Portraits, partner logos and the funder's logo are not covered by the site licence and are excluded from any permission to train AI systems.
- **Personal data** in the directory is not licensed at all; it is published on the terms in the [privacy notice](/privacy/), which say what is shown, where it comes from and how a person has it changed or removed.
- **Third-party material** shown on the site, such as embedded videos, sounds from Freesound and objects from heritage collections, keeps the terms of its source, stated where it appears.

The terms are stated in plain language on the site, in the footer's licence entry, and in machine-readable form for crawlers: the text is open, and the reservation for images, portraits and logos is expressed in the form the EU directive on copyright in the digital single market provides for.

## Pictures from partners: a point to discuss with the partners

Every card for a partner's news item or event carries a thumbnail, and that picture is fetched from the partner's own server when a reader opens our page. Two things follow. The partner's server sees the reader's address, which is the one place where this site's promise not to track anyone depends on someone else's conduct. And the picture is not ours to keep, so the card breaks whenever the partner reorganises their site.

Everywhere else the site already collects from the source and keeps a copy: portraits from the national research archive are stored here, and a cover image from the Research Catalogue is copied only when the work carries a Creative Commons licence, with the licence named on the card. Partner thumbnails are the exception, and the reason is that nobody has told us what may be done with them.

That was measured rather than assumed on 18 September 2026, with `scripts/report_partner_image_terms.py`, over the 65 partner pages behind a thumbnail across 27 hosts.

| What the page states about its pictures | Pages | Hosts |
| --- | --- | --- |
| A licence | 0 | 0 |
| A photo credit, but no licence | 22 | 11 |
| A link to terms or copyright | 2 | 2 |

Three hosts link a terms page from their front page, and all three are sales or ticket terms rather than anything about pictures. A credit line names the photographer; it does not say what a reader may do with the photograph.

So the position to take into the partner conversation is this. We would like to keep a small thumbnail of the picture that accompanies a partner's news item or event, store it on our own server, show it at the size the listings use, and link it back to the partner's page with the partner named. That removes a third-party request for every reader and keeps the card working. We will not copy a picture without a basis for it, so until a partner says otherwise, their card shows the centre's own artwork instead.

What we ask for is one line in the partner agreement, or an e-mail, granting permission to show a thumbnail that links back. What we offer in return is the same for our own material: anything the centre publishes may be reused on the terms above, and a partner is welcome to our pictures on the same footing.

## Language

English is the main language; key sections are mirrored in Norwegian under `/no/…`. Adaptive reading levels and Norwegian translation are independent dimensions: the goal is that both language versions eventually offer the same reading levels. Machine translation is marked as such on the pages concerned.

Norwegian means both written forms. The Language Act asks state bodies to use at least a quarter of each over time, and the [survey of the partners' language policies](/internal/nynorsk/) shows that nearly every university falls short of it. MishMash aims higher than the rule: a Nynorsk mirror of the whole Norwegian site, generated from the Bokmål pages with an open-source rule-based translator in moderate Nynorsk, marked as automatic until a Nynorsk-competent member has read the page, with the centre's own terms kept in a shared glossary. Pages that matter most, the front page and the about pages, get a human reading first. The share of each form is measured with the same crawler Språkrådet uses, and the figure is published with the site's other measurements.

Sami and Kven are treated differently, because the tools are different. The Language Act asks every public body to protect and promote the Sami languages and Kven, but the only machine translator into Sami carries its makers' warning about quality, the body that builds Sami language technology refuses to publish Norwegian to Sami output on principle, and no Norwegian to Kven translator exists. So the site never generates Sami or Kven pages. Instead a fixed core set of pages is translated by people, North Sami first, then Kven, then Lule and South Sami through the partners that hold the responsibility for them, with machine output, spellers and terminology as the translator's tools and the translator named on the page. Around that, the centre promotes the languages where it can without translation: names, statements on the front page, labels in the open knowledge graph, and events on Sami and Kven language technology. The [survey](/internal/sami-kven/) gives the detail; the order of work is kept in the centre's internal plans.

## Alongside the partners' strategies

A [survey of the 22 Norwegian research partners](/internal/partner-communication-strategies/) shows what MishMash shares with them and where it goes further. Eight partners publish an institution-wide communication strategy, platform or policy; the rest have a language policy, a general strategy with visibility goals, or nothing public. The shared foundation is the state communication policy, with its principles of openness, reaching everyone affected, coherence, being active and participation; communication is everyone's job, researchers are expected to disseminate their own work, and plain language is required through the Language Act. MishMash stands on the same ground: its members remain bound by their institutions' strategies, and this document does not replace them.

What none of the partners' documents do, and this strategy therefore adds, is the set of principles five to eight above: open science, open education and open knowledge as the frame, with reuse terms and sources on every piece; a disclosure rule for AI in our own communication; a commitment to show limits and to publish our own measurements; and art as subject, object, expression and method. The arts institutions among the partners treat concerts and exhibitions as activities to be advertised, and other institutions sometimes use them to disseminate science; MishMash differs in that art is what it studies and how it works, so artistic communication carries the same weight as a paper. Where a partner's strategy is stricter, for example on Nynorsk or on who may speak for an institution, the partner's rule applies to its own staff.

## Evaluation

The adaptive-content approach is an experiment run by the [website project](/projects/the-mishmash-website/). It is evaluated on: whether variants stay in sync (an editorial cost), whether readers use the switcher, and whether the simplified levels are actually simpler (readability metrics). The measurements the site makes of itself are generated on every change and are public: the accessibility scan, the HTML and link checks, the readability check of adaptive pages and the Lighthouse scores, all on the [quality checks](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml) page. The site does not measure its readers; the [privacy notice](/privacy/) says why, and the choice is revisited when a question arises that only numbers can answer. The strategy is revised alongside the channel strategy, at least once a year.
