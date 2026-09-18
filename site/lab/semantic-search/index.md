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
  ai: "A multilingual sentence-embedding model runs in your browser to turn your query into numbers. It is about 130 MB and is fetched from a public content network the first time you search, then kept by your browser; your query never leaves your device. The page was drafted with an AI assistant and reviewed by the site maintainers."
---

The site's [search](/search/) matches the words you type. This experiment matches meaning: type "instruments that listen" and it can find a project about machine listening even if neither word appears. It works by turning every item on the site into a list of numbers at build time, doing the same to your query in your browser, and comparing the two. Nothing you type is sent anywhere.

The cost is the model. It understands Norwegian as well as English, and that costs 130 MB, fetched from a public content network the first time you press Search and then kept by your browser. On a laptop the first result took 11 seconds and every query after it about 40 milliseconds; on a throttled mid-range phone, with the model already in the cache, a query took under a tenth of a second. An English-only model would be 23 MB, but would not find the Norwegian pages. Nothing downloads until you search.

<div id="semantic-search" class="semantic-search" data-index="/data/embeddings.json" data-vectors="/data/embeddings.bin">
  <form id="semantic-form" role="search" aria-label="Semantic search">
    <label for="semantic-query">Search by meaning</label>
    <div class="search-input-row">
      <input type="search" id="semantic-query" class="search-input" autocomplete="off" placeholder="for example: music that plays with you">
      <button type="submit" class="search-submit">Search</button>
    </div>
  </form>
  <p id="semantic-status" class="small muted" aria-live="polite">Pressing Search downloads a 130 MB language model the first time, then keeps it. Nothing is downloaded until you do.</p>
  <div class="semantic-compare">
    <div>
      <h2>By meaning</h2>
      <ol id="semantic-results" class="semantic-results" aria-label="Results by meaning"></ol>
    </div>
    <div>
      <h2>By words</h2>
      <ol id="keyword-results" class="semantic-results" aria-label="Results by keyword"></ol>
    </div>
  </div>
  <noscript><p>This experiment needs JavaScript. The <a href="/search/">keyword search</a> works without it.</p></noscript>
</div>

## What the two columns show

Both columns answer the same query from the same index. The right column matches the words you typed, as the site's own [search](/search/) does: exact, instant, and empty when nothing contains the word. The left column matches meaning, so it finds paraphrases and related ideas, including across English and Norwegian, and always returns its twelve closest items, which means the last of them may be a weak match rather than a good one. Neither is better in general. Try a precise name in both, then try a description of something whose name you cannot remember.

## Where this leads

The same on-device retrieval can feed a question-answering assistant that cites the pages it draws on, without a server and without logging, which is the direction discussed for the chat page. What is measured here first is whether the download and the computation are acceptable on an ordinary laptop and phone. The computation is: a query takes tens of milliseconds even on a phone. The download is the open question, and the answer may be that an assistant belongs where the reader has already chosen to wait, rather than on every page.

<script type="module" src="/assets/js/semantic-search.js"></script>
