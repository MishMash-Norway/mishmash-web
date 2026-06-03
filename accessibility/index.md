---
layout: page
title: Accessibility
permalink: /accessibility/
translation_url: /no/accessibility/
---

We want mishmash.no to be usable for as many people as possible. We work to follow recognised web standards for structure, semantics, and accessibility.

## Standards we aim for

- **[WCAG 2](https://www.w3.org/WAI/standards-guidelines/wcag/) Level AA** — contrast, keyboard use, labels, and other requirements checked automatically in our build pipeline.
- **Valid, semantic HTML** — pages are validated as HTML5 during continuous integration.
- **Practical accessibility features** — including a skip link to main content, text alternatives for images where needed, and meaningful link and heading structure.

We know that automated testing cannot catch every barrier. If you have trouble using any part of this site, please tell us at [contact@mishmash.no](mailto:contact@mishmash.no) so we can improve it.

## Automated checks on GitHub

Every change to the site is checked in GitHub Actions before it is published. The [**Web Quality Checks**](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml) workflow includes:

- **Accessibility scan (Pa11y)** — tests key pages against WCAG 2 Level AA using [Pa11y CI](https://github.com/pa11y/pa11y-ci) and our [`.pa11yci.json`](https://github.com/MishMash-Norway/mishmash-web/blob/main/.pa11yci.json) configuration.
- **HTML validation (Nu HTML Checker)** — checks generated pages for valid HTML5 markup.
- **Link checking (htmlproofer)** — verifies internal links in the built site.

You can see the latest results on the [workflow runs page](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml).
