---
layout: page
title: Communication strategy
permalink: /internal/communication-strategy/
---

This communication strategy complements the [channel strategy](/internal/kanalstrategi/). The channel strategy describes *which* channels MishMash uses and how they work together; this document describes *how we communicate* in those channels: who our readers are, what they need, and what tone and complexity fits each of them.

## Principles

1. **One source, many readers.** The same underlying facts are presented at different levels of complexity rather than being rewritten in parallel documents that drift apart. On mishmash.no this is implemented as [adaptive content and stretchtext](https://github.com/MishMash-Norway/mishmash-web/wiki/Web-Philosophy): readers choose a reading level, and pages unfold more detail on demand. See the [about page](/about/description/) for a working example.
2. **The reader chooses.** We do not guess or track who a reader is. Readers self-select their level, and can always switch. The plain-language version is the default.
3. **Pull, don't retype.** Facts about people, projects, institutions, and results are pulled from authoritative sources (NVA, ORCID, Wikipedia) rather than maintained by hand, so all reader groups get the same up-to-date information.
4. **Plain language first.** Following klarspråk principles and the [Language Act](https://lovdata.no/dokument/NL/lov/2021-05-21-42), the default register is plain language; jargon is something readers opt *into*, not out of.

## Primary reader groups

These four groups form a ladder of complexity and drive the reading levels used on adaptive pages (defined in `site/_data/audiences.yml`):

| Group | Who | What they need | Tone and style |
| --- | --- | --- | --- |
| **Young** | Kids and teenagers, school classes | What is this, why is it exciting, what does it mean for me? | Short sentences, concrete examples, questions, no jargon; unfamiliar words explained inline with stretchtext |
| **Everyone** (default) | The general public, curious visitors, families of participants | What MishMash does, why society funds it, how it affects culture, work, and school | Plain language (klarspråk); everyday examples; key terms introduced with stretchtext |
| **Academics & artists** | Researchers, students, and artists from *other* fields | The research questions, the approach, opportunities for collaboration | Standard academic/artistic register; discipline-specific jargon still explained |
| **Experts** | Peers in creative AI, music technology, HCI, and adjacent fields | Full precision: methods, challenges, work-package detail, publications | Full technical detail; nothing simplified away |

## Secondary audiences

Not every audience should be a reading level — most are better served by dedicated pages and channels:

- **Press and media** — need quotable facts, figures, images, and contacts quickly. Served by clear about pages and direct contact with management, not a separate reading level.
- **Policymakers and funders** — need societal relevance and impact. Served by the "Everyone" level plus results and news.
- **Prospective employees and students** — served by [vacancies](/vacancies/) and work-package pages; students who want to help build the website itself are pointed to the [website project](/projects/the-mishmash-website/) and the [developer wiki](https://github.com/MishMash-Norway/mishmash-web/wiki).
- **The MishMash network (internal)** — served by the [internal pages](/internal/), mailing lists, and work-package channels as described in the [channel strategy](/internal/kanalstrategi/).

## Mapping readers to channels

| Channel (see [channel strategy](/internal/kanalstrategi/)) | Young | Everyone | Academics & artists | Experts | Internal |
| --- | --- | --- | --- | --- | --- |
| mishmash.no (adaptive pages) | ✓ | ✓ | ✓ | ✓ | |
| mishmash.no (results, directory) | | ✓ | ✓ | ✓ | ✓ |
| mishmash.no/internal | | | | | ✓ |
| ALL@ mailing list | | | | | ✓ |
| ANNOUNCEMENTS@ mailing list | | ✓ | ✓ | ✓ | ✓ |
| LinkedIn | | ✓ | ✓ | ✓ | |
| Instagram | ✓ | ✓ | | | |
| YouTube | ✓ | ✓ | ✓ | ✓ | |

## Language

English is the main language; key sections are mirrored in Norwegian under `/no/…`. Adaptive reading levels and Norwegian translation are independent dimensions: the goal is that both language versions eventually offer the same reading levels. Machine translation is marked as such on the pages concerned.

## Evaluation

The adaptive-content approach is an experiment run by the [website project](/projects/the-mishmash-website/). It is evaluated on: whether variants stay in sync (an editorial cost), whether readers use the switcher, and whether the simplified levels are actually simpler (readability metrics). The strategy is revised alongside the channel strategy.
