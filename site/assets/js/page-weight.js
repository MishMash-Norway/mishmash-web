/* Fill the page-weight table on the AI colophon from /data/page-weight.json,
   which scripts/measure_page_weight.mjs writes after every build. */
(function () {
  var box = document.getElementById('page-weight');
  if (!box) return;
  var nb = box.dataset.lang === 'nb';
  var L = nb ? { page: 'Side', kb: 'KB per besøk', req: 'Forespørsler', co2: 'g CO₂ per besøk', when: 'Målt' }
             : { page: 'Page', kb: 'KB per visit', req: 'Requests', co2: 'g CO₂ per visit', when: 'Measured' };
  fetch(box.dataset.src).then(function (r) { return r.json(); }).then(function (d) {
    var t = document.createElement('table');
    t.innerHTML = '<thead><tr><th>' + L.page + '</th><th>' + L.kb + '</th><th>' + L.req + '</th><th>' + L.co2 + '</th></tr></thead>';
    var tb = document.createElement('tbody');
    d.pages.forEach(function (p) {
      var tr = document.createElement('tr');
      [p.page, Math.round(p.bytes / 1024).toLocaleString(), p.requests, p.g_co2_first_visit.toFixed(2)].forEach(function (v, i) {
        var td = document.createElement('td'); td.textContent = v; if (i) td.style.textAlign = 'right'; tr.appendChild(td);
      });
      tb.appendChild(tr);
    });
    t.appendChild(tb); box.appendChild(t);
    var p = document.createElement('p'); p.className = 'small muted';
    p.textContent = L.when + ' ' + d.generated_at.slice(0, 10) + '. ' + d.model;
    box.appendChild(p);
  }).catch(function () {});
})();
