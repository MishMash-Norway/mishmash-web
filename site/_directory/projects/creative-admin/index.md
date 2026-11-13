---
layout: page
type: project
title: Creative Use of AI for Research Administration
permalink: /projects/creative-admin/
wps:
- WP7
tags:
- Artificial Intelligence
- Infrastructure
- Cross-WP
- Ethics
slug: creative-admin
name: Creative Use of AI for Research Administration
people:
- alexander-refsum-jensenius
- eskil-muan-saether
institutions:
- university-of-oslo
projects:
- the-mishmash-website
---

## Summary

This project tests how much of the administration of a research centre can be done with AI agents, and what it takes to make that work. The people in the MishMash administration use agents for their shared work: agendas, minutes, follow-up, role descriptions, routines and the website. They use more than one agent and more than one model, so the work cannot depend on a single tool. The core challenge is therefore not the agents but the context they work in: written rules, skills and routines that any agent can read, kept in one place and kept current.

## Questions

- What context, rules and skills does an agent need to do useful administrative work, and how are they kept up to date as the centre changes?
- Can the same context serve different agents and models, from the university's own models to commercial coding assistants?
- Which tasks save time, which need so much checking that they do not, and which should not be given to an agent at all?
- What do data classes, privacy and accountability require when agents draft what people later send, sign and decide?

## How it works

- A private repository at the University of Oslo holds the working documents as plain text, with one file of rules for agents, routines written as step-by-step recipes, and a log of what was done and what was learnt.
- General administrative work uses the open-source agent [OpenCode](https://opencode.ai/) with the university's models through [GPT UiO](https://www.uio.no/tjenester/it/ki/gpt-uio/), approved for yellow data.
- Work on the website uses [GitHub Copilot](https://github.com/features/copilot) through GitHub Education in [Visual Studio Code](https://code.visualstudio.com/), on the public [website repository](https://github.com/MishMash-Norway/mishmash-web), which has [its own rules for agents](https://github.com/MishMash-Norway/mishmash-web/blob/main/AGENTS.md).
- People decide, send, sign and pay. Agents draft, tidy and check, and a person reads every change in the log.

The first phase runs to the end of January 2027. The centre then decides how to continue, and what has been learnt is written up here and in the [website project](/projects/the-mishmash-website/).

## Work Package

Cross-work-package initiative, closest to [WP7](/wp7/)

## Duration

2026–ongoing

## People

- Project leader: [Alexander Refsum Jensenius](/people/alexander-refsum-jensenius/)
- Participants: [Eskil Muan Sæther](/people/eskil-muan-saether/), Eirik Slinning Karlsen

## Institutions

- [University of Oslo](/institutions/university-of-oslo/)
