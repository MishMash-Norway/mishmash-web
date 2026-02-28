---
layout: default
title: "Cristin Project Results"
permalink: /results/
---

## Reported Cristin Results for MishMash Centre for AI and Creativity

<script>
  async function fetchCristinResults() {
    const url = 'https://api.cristin.no/v2/results?funding_source=NFR&project_code=357438';
    const resultsDiv = document.getElementById('results');
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error('Network response was not ok');
      const data = await response.json();
      if (!Array.isArray(data)) {
        resultsDiv.innerHTML = '<p>No results found or unexpected response.</p>';
        return;
      }
      if (data.length === 0) {
        resultsDiv.innerHTML = '<p>No results found for this project funding ID.</p>';
        return;
      }
      resultsDiv.innerHTML = '';
      data.forEach(item => {
        const title = item.title && item.title['en'] ? item.title['en'] : (item.title && item.title['no']) || 'No title';
        const div = document.createElement('div');
        div.className = 'result';
        let link = '';
        if (Array.isArray(item.links)) {
          const fulltekst = item.links.find(l => l.url_type === 'FULLTEKST' && l.url);
          if (fulltekst) link = fulltekst.url;
        }
        const contributors = item.contributors && item.contributors.preview && item.contributors.preview.length > 0
          ? item.contributors.preview.map(c => `${c.surname}, ${c.first_name}`).join('; ')
          : 'N/A';
        div.innerHTML = `
          <div class="title"><em>${link ? `<a href="${link}" target="_blank" rel="noopener">${title}</a>` : title}</em></div>
          <div class="meta">${contributors}</div>
          <div class="meta">${item.place || ''}${item.year_published ? ', ' + item.year_published : ''}</div>
          <hr>
        `;
        resultsDiv.appendChild(div);
      });
    } catch (err) {
      resultsDiv.innerHTML = '<p>Error fetching results: ' + err.message + '</p>';
    }
  }
  fetchCristinResults();
</script>

