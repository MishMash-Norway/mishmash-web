---
layout: lab
title: Semantic search on your device
permalink: /lab/semantic-search/
description: "Search the site by meaning rather than by exact words, with a small language model that runs in your browser and sends nothing anywhere."
search: false
lab:
  authors: [mishmash.no]
  date: 2026-09-18
  status: experiment
  data: "The site's own search index: every page, person, institution, project and event with its title and description, embedded at build time with a small multilingual sentence model (paraphrase-multilingual-MiniLM-L12-v2). The embeddings are a file on this site."
  ai: "A sentence-embedding model of about 30 MB runs in your browser to turn your query into numbers; the model is fetched from a public content network on first use, and your query never leaves your device. The page was drafted with an AI assistant and reviewed by the site maintainers."
---

The site's [search](/search/) matches the words you type. This experiment matches meaning: type "instruments that listen" and it can find a project about machine listening even if neither word appears. It works by turning every item on the site into a list of numbers at build time, doing the same to your query in your browser, and comparing the two. Nothing you type is sent anywhere; the only download is the model, about 30 MB, fetched once on first use and kept by your browser.

<div id="semantic-search" class="semantic-search" data-index="/data/embeddings.json" data-vectors="/data/embeddings.bin">
  <form id="semantic-form" role="search" aria-label="Semantic search">
    <label for="semantic-query">Search by meaning</label>
    <div class="search-input-row">
      <input type="search" id="semantic-query" class="search-input" autocomplete="off" placeholder="for example: music that plays with you">
      <button type="submit" class="search-submit">Search</button>
    </div>
  </form>
  <p id="semantic-status" class="small muted" aria-live="polite">The model loads when you search for the first time.</p>
  <ol id="semantic-results" class="semantic-results" aria-label="Results by meaning"></ol>
  <noscript><p>This experiment needs JavaScript. The <a href="/search/">keyword search</a> works without it.</p></noscript>
</div>

## What to compare

Try the same query in the [keyword search](/search/). The keyword search is exact and fast and needs no model; the semantic search finds paraphrases and related ideas, including across English and Norwegian, and ranks by similarity, so the last results are weak matches rather than no matches. Both use the same index, built from the site's pages at every deployment.

## Where this leads

The same on-device retrieval can feed a question-answering assistant that cites the pages it draws on, without a server and without logging, which is the direction discussed for the chat page. What is measured here first is whether the download and the computation are acceptable on an ordinary laptop and phone.

<script type="module" src="/assets/js/semantic-search.js"></script>
