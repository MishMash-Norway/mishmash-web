---
layout: default
title: FAQ
page_about:
  ai_support:
    agent: Cursor
    model_name: Claude
    model_version: "4.6 Sonnet"
  data_sources:
    - manual
---

# Frequently Asked Questions

<div class="faq-list">

<details class="faq-item" id="what-is-mishmash" markdown="1">
<summary><span class="faq-summary-text">What is MishMash?</span><span class="faq-expand-icon" aria-hidden="true">▸</span></summary>

MishMash is a national research centre dedicated to exploring AI in and through creative practices. It brings together researchers across disciplines and institutions to develop new knowledge, methods, and applications at the intersection of AI, creativity, and society. Read more in the [centre description](/about/description/).

</details>

<details class="faq-item" id="how-is-mishmash-organised" markdown="1">
<summary><span class="faq-summary-text">How is MishMash organised?</span><span class="faq-expand-icon" aria-hidden="true">▸</span></summary>

MishMash operates as a distributed, collaborative network rather than a single centralized organisation.

* Research activities are organised into [work packages](#what-are-work-packages), which form the core of the centre’s work
* Each work package has its own leadership and research agenda — see the [Work Package Leader Group](/about/organisation/wp-leaders/)
* A [central management team](/about/organisation/management/) and [board](/about/organisation/board/) provide coordination and strategic oversight

This structure enables broad participation across institutions while maintaining a shared direction. See [Organisation](/about/organisation/) for the full governance structure, including the [Council](/about/organisation/council/) and [Scientific Advisory Board](/about/organisation/scientific-advisory-board/).

</details>

<details class="faq-item" id="what-are-work-packages" markdown="1">
<summary><span class="faq-summary-text">What are work packages?</span><span class="faq-expand-icon" aria-hidden="true">▸</span></summary>

Work packages (WPs) are the main organisational units for research and collaboration within MishMash.

* Each WP focuses on a specific theme or research area
* Researchers and partners participate through one or more WPs
* Most activities—projects, events, and collaborations—are organised within these units

The seven work packages are:

* [WP1: AI for artistic performances](/wp1/)
* [WP2: AI in artistic processes](/wp2/)
* [WP3: Creative use of AI for health and well-being](/wp3/)
* [WP4: Creative use of AI in education](/wp4/)
* [WP5: AI in the Creative and Cultural Industries](/wp5/)
* [WP6: AI for cultural heritage](/wp6/)
* [WP7: Human-centric AI for Creative Problem-Solving](/wp7/)

</details>

<details class="faq-item" id="who-is-responsible-for-content" markdown="1">
<summary><span class="faq-summary-text">Who is responsible for content and communication?</span><span class="faq-expand-icon" aria-hidden="true">▸</span></summary>

Communication in MishMash is a shared responsibility across the network.

* Work package leaders are responsible for ensuring that relevant activities and results are communicated
* Partners contribute content such as [news](/news/), [events](/events/), and [project](/projects/) updates
* A central team coordinates overall communication and website development

In practice, MishMash operates as a collaborative effort where contributions from partners are essential.

</details>

<details class="faq-item" id="how-can-i-contribute" markdown="1">
<summary><span class="faq-summary-text">How can I contribute content to the website?</span><span class="faq-expand-icon" aria-hidden="true">▸</span></summary>

MishMash relies on active contributions from its community. You can contribute by:

* Submitting [news](/news/) or [events](/events/) to be automatically linked
* Adding content to NVA and Orcid that will be automatically synced daily
* Requesting access to contribute to the [GitHub repository](https://github.com/MishMash-Norway/mishmash-web) that the site is built from


</details>

<details class="faq-item" id="what-are-meshups" markdown="1">
<summary><span class="faq-summary-text">What are MeshUps?</span><span class="faq-expand-icon" aria-hidden="true">▸</span></summary>

MeshUps are short, weekly online events designed for sharing ongoing work and ideas. During the semesters, they run on Thursdays 12:00–12:30. They begin with a couple of minutes of information from the management team. This is followed by a 15-minute presentation and 10 minutes of Q&A. 

MeshUps provide a lightweight format for connecting across disciplines and institutions. Upcoming and past MeshUps are listed on the [events page](/events/).

</details>

<details class="faq-item" id="who-can-join-mishmash" markdown="1">
<summary><span class="faq-summary-text">Who can join MishMash?</span><span class="faq-expand-icon" aria-hidden="true">▸</span></summary>

MishMash connected institutions (partners) and people (members): 

* Partners are institutions (both research-performing and others) that have signed either the original consortium agreement or an associate partner agreement. Check the [institution list](/search/?type=institution) for an overview of connected partners. 

* Members are individuals that have signed up for one or more work packages. Many are connected through institutions, but MishMash is also open for non-affiliated researchers. 

The centre is continuously developing its network and welcomes new collaborations. It is a research consortium, but non-researchers are also welcome if they are interested in following the research activities.

</details>

<details class="faq-item" id="how-do-i-become-a-partner" markdown="1">
<summary><span class="faq-summary-text">How do I become a partner or member?</span><span class="faq-expand-icon" aria-hidden="true">▸</span></summary>

Institutions and individuals can express interest in joining MishMash by sending an e-mail to [contact@mishmash.no](mailto:contact@mishmash.no) for more information. You will then receive details about roles, expectations, and next steps. Participation typically involves contributing to work packages and collaborative activities.

</details>

<details class="faq-item" id="what-are-seed-funding-projects" markdown="1">
<summary><span class="faq-summary-text">What are seed funding projects?</span><span class="faq-expand-icon" aria-hidden="true">▸</span></summary>

MishMash supports smaller research initiatives through seed funding announced internally in the centre regularly. See the [project pages](/projects/) for examples of ongoing projects.

</details>

<details class="faq-item" id="how-does-the-website-work" markdown="1">
<summary><span class="faq-summary-text">How does the MishMash website work?</span><span class="faq-expand-icon" aria-hidden="true">▸</span></summary>

The site is a [Jekyll](https://jekyllrb.com/) static website. Source code, content, and tooling live in the open [mishmash-web](https://github.com/MishMash-Norway/mishmash-web) repository on GitHub.

* **Build and publish:** Changes merged to the `main` branch are built automatically by [GitHub Actions](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/pages.yml) and published to [mishmash.no](https://mishmash.no/) via GitHub Pages
* **Quality checks:** Pull requests are checked for broken links, directory consistency, and accessibility before merge
* **Data sync:** Person profiles and research results can be updated nightly from [NVA](https://nva.sikt.no/) and [ORCID](https://orcid.org/) where linked
* **Contributing:** Partners with repo access can propose edits via pull requests; see [CONTRIBUTING.md](https://github.com/MishMash-Norway/mishmash-web/blob/main/CONTRIBUTING.md) for what to edit locally

Each page shows metadata at the bottom (last edit, licence, data sources, and a link to its source file on GitHub).

</details>

<details class="faq-item" id="what-is-expected-from-partners" markdown="1">
<summary><span class="faq-summary-text">What is expected from partners?</span><span class="faq-expand-icon" aria-hidden="true">▸</span></summary>

Partners play an active role in shaping MishMash. Typical expectations include:

* Participating with members (people) in work package actvities
* Contributing to communication and visibility by sending information about relevant events that can be added to the [events page](/events/).
* Supporting collaboration across the network and developing applications for MishMash-related projects.

Many activities rely on shared effort across institutions, rather than central coordination alone.

</details>

<details class="faq-item" id="are-events-open-to-the-public" markdown="1">
<summary><span class="faq-summary-text">Are MishMash events open to the public?</span><span class="faq-expand-icon" aria-hidden="true">▸</span></summary>

Many MishMash activities are open, including the weekly MeshUps and conferences. See the [event page](/events/) for details. Work package events are typically reserved for partners and members. 

</details>

<details class="faq-item" id="still-have-questions" markdown="1">
<summary><span class="faq-summary-text">Still have questions?</span><span class="faq-expand-icon" aria-hidden="true">▸</span></summary>

Get in touch at [contact@mishmash.no](mailto:contact@mishmash.no), or explore [projects](/projects/), [people](/search/?type=person), [institutions](/search/?type=institution), [events](/events/), and [results](/results/) to learn more.

</details>

</div>

<script>
(function () {
  'use strict';

  var linkIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>';

  function openFaqFromHash() {
    var id = window.location.hash.slice(1);
    if (!id) return;
    var item = document.getElementById(id);
    if (item && item.classList.contains('faq-item')) {
      item.open = true;
    }
  }

  document.querySelectorAll('.faq-item[id]').forEach(function (item) {
    var summary = item.querySelector('summary');
    if (!summary || summary.querySelector('.faq-permalink')) return;

    var link = document.createElement('a');
    link.className = 'faq-permalink';
    link.href = '#' + item.id;
    link.setAttribute('aria-label', 'Link to this question');
    link.innerHTML = linkIcon;
    link.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      item.open = true;
      history.pushState(null, '', '#' + item.id);
    });

    var expandIcon = summary.querySelector('.faq-expand-icon');
    if (expandIcon) {
      summary.insertBefore(link, expandIcon);
    } else {
      summary.appendChild(link);
    }
  });

  openFaqFromHash();
  window.addEventListener('hashchange', openFaqFromHash);
})();
</script>
