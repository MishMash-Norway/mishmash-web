---
layout: page
title: Accessibility
permalink: /accessibility/
translation_url: /no/accessibility/
---

This website should be usable by as many people as possible, whatever they browse with. The site is built to be accessible to the standard Norwegian law sets: the regulation on universal design of ICT, which requires public websites to satisfy the 48 success criteria of the [Web Content Accessibility Guidelines (WCAG) 2.1](https://www.w3.org/TR/WCAG21/) at levels A and AA listed by the [Norwegian Authority for Universal Design of ICT](https://www.uutilsynet.no/wcag-standarden/wcag-standarden/86).

The centre's accessibility statement, [published at uustatus.no](https://uustatus.no/nb/erklaringer/publisert/2858c960-8d5e-41ab-9fab-cf0ed3944ed3), sits in the register the Norwegian Authority for Universal Design of ICT keeps. It is the formal declaration of how far this site meets the requirements, and it is maintained by the University of Oslo as the responsible body. This page says the same thing in ordinary words, and adds how the site is checked.

## What the site does

- A skip link at the top of every page leads straight to the content.
- Menus, the language switch, search and the expandable sections work with a keyboard, and the element in focus is always visible.
- The page language is declared, and the language switch marks the other language so screen readers pronounce it correctly.
- Text and its background have a contrast of at least 4.5:1, and text can be enlarged to 200% without loss of content.
- Pages reflow to a width of 320 pixels without horizontal scrolling.
- Images have text alternatives, links describe their target, and headings follow a logical order.
- Charts on the results pulse page have a table alternative.

## How the site is checked

Every change is checked in GitHub Actions before it is published. The [Web Quality Checks](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml) workflow includes:

- Accessibility scan: [Pa11y CI](https://github.com/pa11y/pa11y-ci) runs both the axe-core and HTML CodeSniffer engines against WCAG 2.1 level AA on a set of representative pages in both languages, listed in [`.pa11yci.json`](https://github.com/MishMash-Norway/mishmash-web/blob/main/.pa11yci.json). A single error fails the check.
- HTML validation: the Nu HTML Checker validates every generated page as HTML5.
- Link checking: htmlproofer verifies internal links in the built site.

Automated tools find only part of the barriers a person can meet. The rest depends on how content is written, so contributors are asked to give images text alternatives, keep headings in order, write link text that makes sense on its own, and provide captions for video. The latest results are on the [workflow runs page](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml).

## Known limitations

- Embedded videos from YouTube do not always have captions, and none has audio description.
- The chat page depends on JavaScript and on an external language model service.
- The experimental interface themes under `/ui/` are student work and are outside the automated checks.
- The pieces in the [lab](/lab/) are experiments; each is scanned like any page but may need JavaScript, sound or a pointer, and says so.

## Tell us about a barrier

If you have trouble using any part of this site, write to [contact@mishmash.no](mailto:contact@mishmash.no) and say which page you were on and what happened. We aim to answer within a week and to fix what we can.
