/* Heritage objects in place (see _includes/heritage.html, issue #50).
   Two sources for now:
   - nb:   the National Library's IIIF Presentation manifest (v1 or v3).
   - dimu: DigitaltMuseum's artifact API, which covers the National Museum,
           Norsk Folkemuseum and most Norwegian museums.
   Metadata and images are fetched from the collections; nothing is copied to
   this site, and the rights statement each collection gives is shown as is. */
(function () {
  var DIMU_KEY = 'demo';                       // public documentation key; ask KulturIT for a real one
  var EUROPEANA_KEY = 'api2demo';              // Europeana's public demo key; a free key is one form away
  var OSD_PREFIX = '/assets/js/lib/openseadragon/images/';

  function text(el, s) { el.textContent = s; }

  function firstValue(v) {                     // IIIF v3 language maps or plain strings
    if (!v) return '';
    if (typeof v === 'string') return v;
    if (Array.isArray(v)) return firstValue(v[0]);
    if (typeof v === 'object') { var k = Object.keys(v)[0]; return k ? firstValue(v[k]) : ''; }
    return String(v);
  }

  function stripHtml(s) { var d = document.createElement('div'); d.innerHTML = s || ''; return d.textContent || ''; }

  function showImage(media, url, alt) {
    var img = document.createElement('img');
    img.src = url; img.alt = alt || ''; img.loading = 'lazy';
    media.appendChild(img);
  }

  function showZoom(media, infoUrl, alt) {
    if (!window.OpenSeadragon) { showImage(media, infoUrl.replace(/\/info\.json$/, '') + '/full/1200,/0/default.jpg', alt); return; }
    var id = 'osd-' + Math.random().toString(36).slice(2);
    var box = document.createElement('div'); box.id = id; box.className = 'mm-heritage-zoom'; box.setAttribute('role', 'img'); box.setAttribute('aria-label', alt || 'Zoomable image');
    media.appendChild(box);
    OpenSeadragon({ id: id, prefixUrl: OSD_PREFIX, tileSources: infoUrl, showNavigationControl: true, gestureSettingsMouse: { scrollToZoom: false }, crossOriginPolicy: 'Anonymous' });
  }

  function link(href, label) { var a = document.createElement('a'); a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer'; a.textContent = label; return a; }

  function loadNb(fig, id) {
    var media = fig.querySelector('.mm-heritage-media');
    var title = fig.querySelector('.mm-heritage-title');
    var rights = fig.querySelector('.mm-heritage-rights');
    return fetch('https://api.nb.no/catalog/v1/iiif/' + id + '/manifest').then(function (r) { return r.json(); }).then(function (m) {
      var label = stripHtml(firstValue(m.label));
      if (!fig.dataset.caption) text(title, label);
      var service = null;
      try {
        if (m.sequences) service = m.sequences[0].canvases[0].images[0].resource.service['@id'];
        else if (m.items) { var s = m.items[0].items[0].items[0].body.service; service = (s[0].id || s[0]['@id']); }
      } catch (e) {}
      if (service) showZoom(media, service + '/info.json', label);
      var lic = m.license || (m.rights || '');
      rights.textContent = '';
      rights.appendChild(document.createTextNode(stripHtml(firstValue(m.attribution) || firstValue((m.requiredStatement || {}).value) || '') + ' '));
      if (lic) rights.appendChild(link(lic, 'Rights'));
      rights.appendChild(document.createTextNode(' · '));
      rights.appendChild(link('https://www.nb.no/items/' + id, 'Nasjonalbiblioteket'));
    });
  }

  function loadDimu(fig, uuid) {
    var media = fig.querySelector('.mm-heritage-media');
    var title = fig.querySelector('.mm-heritage-title');
    var rights = fig.querySelector('.mm-heritage-rights');
    return fetch('https://api.dimu.org/artifact/uuid/' + uuid + '?api.key=' + DIMU_KEY).then(function (r) { return r.json(); }).then(function (a) {
      var t = (a.titles && a.titles[0] && a.titles[0].title) || (a.names && a.names[0] && a.names[0].name) || a.uniqueId;
      if (!fig.dataset.caption) text(title, t);
      var pic = a.media && a.media.pictures && a.media.pictures[0];
      if (pic) {
        var iiif = pic.sourceUrl && /\/iiif\//.test(pic.sourceUrl) ? pic.sourceUrl.replace(/\/full\/.*$/, '/info.json') : null;
        if (iiif) showZoom(media, iiif, t);
        else showImage(media, 'https://dms-cf-01.dimu.org/image/' + pic.identifier + '?dimension=1200x1200', t);
      }
      var lic = (pic && pic.licenses && pic.licenses[0]) || (a.licenses && a.licenses[0]) || null;
      var parts = [];
      if (pic && pic.photographer) parts.push('Photo: ' + pic.photographer);
      if (lic) parts.push(lic.code || lic.description || '');
      parts.push((a.identifier && a.identifier.owner) || '');
      rights.textContent = parts.filter(Boolean).join(' · ') + ' · ';
      rights.appendChild(link('https://digitaltmuseum.org/' + (a.dimuCode || a.uniqueId), 'DigitaltMuseum'));
    });
  }

  function firstLang(obj) {                    // {"no": [..], "def": [..]} or {"no": "..", "*": ".."}
    if (!obj) return '';
    var keys = ['no', 'nb', 'nn', 'en', 'def', '*'];
    for (var i = 0; i < keys.length; i++) if (obj[keys[i]]) return Array.isArray(obj[keys[i]]) ? obj[keys[i]][0] : obj[keys[i]];
    var k = Object.keys(obj)[0]; return k ? (Array.isArray(obj[k]) ? obj[k][0] : obj[k]) : '';
  }

  function loadEuropeana(fig, id) {
    var media = fig.querySelector('.mm-heritage-media');
    var title = fig.querySelector('.mm-heritage-title');
    var rights = fig.querySelector('.mm-heritage-rights');
    var rec = id.charAt(0) === '/' ? id : '/' + id;
    return fetch('https://api.europeana.eu/record/v2' + rec + '.json?wskey=' + EUROPEANA_KEY).then(function (r) { return r.json(); }).then(function (d) {
      var o = d.object || {}; var agg = (o.aggregations || [])[0] || {};
      var t = rec;
      (o.proxies || []).forEach(function (px) { if (t === rec && px.dcTitle) t = firstLang(px.dcTitle) || rec; });
      if (!fig.dataset.caption) text(title, t);
      var img = agg.edmIsShownBy || (o.europeanaAggregation || {}).edmPreview;
      if (img) showImage(media, img, t);
      var provider = (o.organizations || []).map(function (org) { return firstLang(org.prefLabel); }).filter(Boolean)[0] || '';
      var lic = firstLang(agg.edmRights);
      rights.textContent = [provider, lic ? '' : ''].filter(Boolean).join('') + (provider ? ' · ' : '');
      if (lic) {
        var m = lic.match(/creativecommons\.org\/(licenses|publicdomain)\/([a-z-]+)\/([\d.]+)/);
        var label = m ? (m[1] === 'publicdomain' ? 'CC0 ' + m[3] : 'CC ' + m[2].toUpperCase() + ' ' + m[3]) : lic.replace(/^https?:\/\//, '');
        rights.appendChild(link(lic, label)); rights.appendChild(document.createTextNode(' · '));
      }
      rights.appendChild(link((o.europeanaAggregation || {}).edmLandingPage || 'https://www.europeana.eu/item' + rec, 'Europeana'));
      if (agg.edmIsShownAt) { rights.appendChild(document.createTextNode(' · ')); rights.appendChild(link(agg.edmIsShownAt, 'Source')); }
    });
  }

  function loadKulturnav(fig, uuid) {
    var media = fig.querySelector('.mm-heritage-media');
    var title = fig.querySelector('.mm-heritage-title');
    var rights = fig.querySelector('.mm-heritage-rights');
    return fetch('https://kulturnav.org/api/' + uuid).then(function (r) { return r.json(); }).then(function (e) {
      var p = e.properties || {};
      var name = firstLang(e.caption) || uuid;
      if (!fig.dataset.caption) text(title, name);
      var desc = p['entity.description'] && p['entity.description'][0] ? firstLang(p['entity.description'][0].value) : '';
      var kind = e.entityType || '';
      var dataset = p['entity.dataset'] && p['entity.dataset'][0] ? firstLang(p['entity.dataset'][0].displayValue) : '';
      var block = document.createElement('p'); block.className = 'mm-heritage-text';
      block.textContent = (kind ? kind + '. ' : '') + (desc || '');
      media.appendChild(block);
      rights.textContent = (dataset ? dataset + ' · ' : '');
      rights.appendChild(link('https://kulturnav.org/' + uuid, 'KulturNav'));
    });
  }

  function init() {
    document.querySelectorAll('[data-heritage]').forEach(function (fig) {
      if (fig.dataset.ready) return;
      fig.dataset.ready = 'true';
      var caption = fig.querySelector('.mm-heritage-title');
      if (caption && caption.textContent.indexOf('Loading from') !== 0) fig.dataset.caption = 'true';
      var media = fig.querySelector('.mm-heritage-media');
      var src = fig.dataset.source;
      var p = src === 'nb' ? loadNb(fig, fig.dataset.id) : src === 'europeana' ? loadEuropeana(fig, fig.dataset.id) : src === 'kulturnav' ? loadKulturnav(fig, fig.dataset.id) : loadDimu(fig, fig.dataset.id);
      p.catch(function () {
        text(fig.querySelector('.mm-heritage-title'), 'This object could not be loaded from the collection.');
      }).then(function () { media.removeAttribute('aria-busy'); });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
