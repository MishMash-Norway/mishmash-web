---
layout: page
title: Communication strategy
permalink: /internal/communication-strategy/
translation_url: /no/internal/kommunikasjonsstrategi/
---

This communication strategy complements the [channel strategy](/internal/kanalstrategi/). The channel strategy describes *which* channels MishMash uses and how they work together; this document describes *how we communicate* in those channels: who our readers are, what they need, and what tone and complexity fits each of them.

## Principles

1. **One source, many readers.** The same underlying facts are presented at different levels of complexity rather than being rewritten in parallel documents that drift apart. On mishmash.no this is implemented as [adaptive content and stretchtext](https://github.com/MishMash-Norway/mishmash-web/wiki/Web-Philosophy): readers choose a reading level, and pages unfold more detail on demand. See the [about page](/about/description/) for a working example.
2. **The reader chooses.** We do not guess or track who a reader is. Readers self-select their level, and can always switch. The plain-language version is the default.
3. **Pull, don't retype.** Facts about people, projects, institutions, and results are pulled from authoritative sources (NVA, ORCID, Wikipedia) rather than maintained by hand, so readers at every level get the same up-to-date information.
4. **Plain language first.** Following klarspråk principles and the [Language Act](https://lovdata.no/dokument/NL/lov/2021-05-21-42), the default register is plain language; jargon is something readers opt *into*, not out of.

## Reading levels

Adaptive pages offer the same content at three **complexity levels** (defined in `site/_data/audiences.yml`). The levels describe the *text*, not the reader — a professor reading outside her field may prefer Standard, and a curious teenager may pick Advanced. Reader roles are deliberately kept out of the ladder; who *typically* reads at each level is guidance for writers, nothing more:

| Level | Complexity | Typical readers | Tone and style |
| --- | --- | --- | --- |
| **Simple** | Short and simple, no jargon | Kids and teenagers, school classes | Short sentences, concrete examples, questions; unavoidable terms explained inline with stretchtext |
| **Standard** (default) | Plain language (klarspråk) | The general public, curious visitors, policymakers | Everyday examples; why it matters to society; key terms introduced with stretchtext |
| **Advanced** | Full detail, nothing simplified away | Researchers, students, artists, and field experts | Full precision: methods, challenges, work-package detail, academic references |

## Secondary audiences

Not every audience should be a reading level — most are better served by dedicated pages and channels:

- **Press and media** — need quotable facts, figures, images, and contacts quickly. Served by clear about pages and direct contact with management, not a separate reading level.
- **Policymakers and funders** — need societal relevance and impact. Served by the Standard level plus results and news.
- **Prospective academic partners** — researchers and institutions considering joining or collaborating with the network. Served by the about pages (Advanced level), work-package pages, [results](/results/), and direct contact with WP leaders and management.
- **Prospective public/private sector partners** — companies, cultural institutions, and public bodies. Served by [project pages](/projects/), news showing existing collaborations, and contact with management.
- **Prospective employees and students** — served by [vacancies](/vacancies/) and work-package pages; students who want to help build the website itself are pointed to the [website project](/projects/the-mishmash-website/) and the [developer wiki](https://github.com/MishMash-Norway/mishmash-web/wiki).
- **The MishMash network (internal)** — served by the [internal pages](/internal/), mailing lists, and work-package channels as described in the [channel strategy](/internal/kanalstrategi/).

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

## AI in the making of the website

MishMash actively uses AI in developing and maintaining mishmash.no — fitting for a centre that studies creative uses of AI. AI assistance is used for writing and adapting content (including drafting the reading-level variants on adaptive pages), for developing the site's code and automation, and for machine translation between English and Norwegian. Two commitments frame this use:

1. **Transparency.** We are open about where and how AI contributes: machine-translated pages are marked as such, AI-assisted development is visible in the public commit history, and this section itself declares the practice. Readers and partners should never have to guess whether AI was involved.
2. **It is an experiment.** Using AI to build the centre's own communication channel is part of MishMash's research practice — a way to *create, explore, and reflect* on our own tools. Human editors remain responsible for everything published: AI output is reviewed before it goes live, and errors are ours, not the machine's. What we learn feeds back into the centre's research and teaching.

The approach is documented in more depth in the [web philosophy](https://github.com/MishMash-Norway/mishmash-web/wiki/Web-Philosophy) and evaluated alongside the other website experiments.

## Language

English is the main language; key sections are mirrored in Norwegian under `/no/…`. Adaptive reading levels and Norwegian translation are independent dimensions: the goal is that both language versions eventually offer the same reading levels. Machine translation is marked as such on the pages concerned.

## Evaluation

The adaptive-content approach is an experiment run by the [website project](/projects/the-mishmash-website/). It is evaluated on: whether variants stay in sync (an editorial cost), whether readers use the switcher, and whether the simplified levels are actually simpler (readability metrics). The strategy is revised alongside the channel strategy.
