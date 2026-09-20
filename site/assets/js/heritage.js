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

  function node(tag, attrs, kids) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === 'class') e.className = attrs[k];
      else if (k === 'text') e.textContent = attrs[k];
      else if (attrs[k] != null) e.setAttribute(k, attrs[k]);
    });
    (kids || []).forEach(function (k) { if (k) e.appendChild(k); });
    return e;
  }

  function showImage(media, url, alt) {
    var img = document.createElement('img');
    img.src = url; img.alt = alt || ''; img.loading = 'lazy';
    media.appendChild(img);
  }

  /* Sound and moving images play where they are, from the collection's own
     server. Nothing is fetched until the reader presses play: preload="none"
     means the element is markup and no more, so a page full of recordings
     costs a visit nothing and tells the collection nothing about who opened
     the page. */
  function showMedia(media, kind, url, alt, poster) {
    var el = document.createElement(kind === 'sound' ? 'audio' : 'video');
    el.src = url;
    el.controls = true;
    el.preload = 'none';
    el.setAttribute('aria-label', alt || (kind === 'sound' ? 'Recording' : 'Film'));
    if (kind !== 'sound') {
      el.playsInline = true;
      if (poster) el.poster = poster;
    }
    el.className = 'mm-heritage-player';
    media.appendChild(el);
  }

  /* A manuscript is not one picture. Mus.ms. 4213 is 1,373 of them, and a viewer
     that shows only the first page is a viewer that hides the work. `pages` is
     every image service in the manifest, in order; with one of them nothing
     changes, and with more the reader gets a way through them. */
  function showZoom(media, pages, alt) {
    var urls = [].concat(pages);
    var at = 0;
    if (!window.OpenSeadragon) {
      showImage(media, urls[0].replace(/\/info\.json$/, '') + '/full/1200,/0/default.jpg', alt);
      if (urls.length > 1) media.appendChild(node('p', { class: 'mm-heritage-pages small muted',
        text: 'Page 1 of ' + urls.length + '. Turning the pages needs JavaScript.' }));
      return;
    }
    var id = 'osd-' + Math.random().toString(36).slice(2);
    var box = document.createElement('div');
    box.id = id; box.className = 'mm-heritage-zoom';
    box.setAttribute('role', 'img');
    box.setAttribute('aria-label', alt || 'Zoomable image');
    media.appendChild(box);
    var viewer = OpenSeadragon({ id: id, prefixUrl: OSD_PREFIX, tileSources: urls[0],
                                 showNavigationControl: true, gestureSettingsMouse: { scrollToZoom: false },
                                 crossOriginPolicy: 'Anonymous' });
    if (urls.length < 2) return;

    var field = node('input', { type: 'number', min: 1, max: urls.length, value: 1,
                              class: 'mm-heritage-page-field', 'aria-label': 'Page number' });
    var status = node('span', { class: 'mm-heritage-page-of', text: 'of ' + urls.length });
    var back = node('button', { type: 'button', class: 'mm-heritage-page-btn', text: 'Previous page' });
    var on = node('button', { type: 'button', class: 'mm-heritage-page-btn', text: 'Next page' });
    var live = node('span', { class: 'sr-only', 'aria-live': 'polite' });

    /* The collection's image server sends no caching headers, so the browser
       re-fetches info.json every time a page is opened, including a page the
       reader has just come back from. The tiles it does reuse. Holding the
       parsed description here removes that one request per page turn. */
    var described = {};
    function describe(url) {
      if (described[url]) return Promise.resolve(described[url]);
      return fetch(url).then(function (r) { return r.json(); }).then(function (info) {
        described[url] = info;
        return info;
      }).catch(function () { return url; });   // fall back to letting the viewer fetch it
    }

    function go(n) {
      at = Math.max(0, Math.min(urls.length - 1, n));
      describe(urls[at]).then(function (source) {
        if (at === Math.max(0, Math.min(urls.length - 1, n))) viewer.open(source);
      });
      field.value = at + 1;
      back.disabled = at === 0;
      on.disabled = at === urls.length - 1;
      box.setAttribute('aria-label', (alt || 'Page') + ', page ' + (at + 1) + ' of ' + urls.length);
      live.textContent = 'Page ' + (at + 1) + ' of ' + urls.length;
    }
    back.addEventListener('click', function () { go(at - 1); });
    on.addEventListener('click', function () { go(at + 1); });
    field.addEventListener('change', function () { go((parseInt(field.value, 10) || 1) - 1); });

    media.appendChild(node('p', { class: 'mm-heritage-pages' }, [back, field, status, on, live]));
    go(0);
  }

  /* DigitaltMuseum names its museums by code (BOB, NMK-B). The list of 285
     codes is fetched once per session and kept, so an object says which
     museum holds it rather than showing a code. */
  var ownersPromise = null;
  function ownerName(code) {
    if (!code) return Promise.resolve('');
    if (!ownersPromise) {
      var cached = null;
      try { cached = sessionStorage.getItem('mm-dimu-owners'); } catch (e) {}
      ownersPromise = cached
        ? Promise.resolve(JSON.parse(cached))
        : fetch('https://api.dimu.org/api/owners?api.key=' + DIMU_KEY)
            .then(function (r) { return r.text(); })
            .then(function (xml) {
              var map = {};
              var doc = new DOMParser().parseFromString(xml, 'application/xml');
              Array.prototype.forEach.call(doc.getElementsByTagName('owner'), function (o) {
                var id = o.getElementsByTagName('identifier')[0], nm = o.getElementsByTagName('name')[0];
                if (id && nm) map[id.textContent] = nm.textContent;
              });
              try { sessionStorage.setItem('mm-dimu-owners', JSON.stringify(map)); } catch (e) {}
              return map;
            })
            .catch(function () { return {}; });
    }
    return ownersPromise.then(function (map) { return map[code] || code; });
  }

  /* Wikidata knows some of these objects and authorities by their collection
     identifier: P1248 for KulturNav, P7847 for DigitaltMuseum. One query
     resolves the identifier to an item, and the link is added only when
     exactly one item matches. A failed or empty query changes nothing. */
  var WD_PROPERTY = { kulturnav: 'P1248', dimu: 'P7847' };
  function wikidataFor(source, value) {
    var prop = WD_PROPERTY[source];
    if (!prop || !value) return Promise.resolve(null);
    var q = 'SELECT ?item WHERE { ?item wdt:' + prop + ' "' + String(value).replace(/["\\]/g, '') + '" } LIMIT 2';
    return fetch('https://query.wikidata.org/sparql?format=json&query=' + encodeURIComponent(q), { headers: { Accept: 'application/sparql-results+json' } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        var rows = d && d.results && d.results.bindings;
        return rows && rows.length === 1 ? rows[0].item.value : null;
      })
      .catch(function () { return null; });
  }

  function addWikidata(rights, source, value) {
    return wikidataFor(source, value).then(function (url) {
      if (!url) return;
      rights.appendChild(document.createTextNode(' · '));
      rights.appendChild(link(url, 'Wikidata'));
    });
  }

  function link(href, label) { var a = document.createElement('a'); a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer'; a.textContent = label; return a; }

  /* A licence address is not a licence line. "CC BY-NC-ND 4.0" is. */
  function ccLabel(url) {
    var m = String(url || '').match(/creativecommons\.org\/(licenses|publicdomain)\/([a-z0-9-]+)\/([\d.]+)/);
    if (!m) return null;
    if (m[1] === 'publicdomain') return m[2] === 'zero' ? 'CC0 ' + m[3] : 'Public domain mark ' + m[3];
    return 'CC ' + m[2].toUpperCase() + ' ' + m[3];
  }

  function loadNb(fig, id) {
    var media = fig.querySelector('.mm-heritage-media');
    var title = fig.querySelector('.mm-heritage-title');
    var rights = fig.querySelector('.mm-heritage-rights');
    /* Version 3 of the manifest, because version 2 gives the terms as the
       library's own licence page and version 3 gives the Creative Commons
       address the label is built from. The image service is the same. */
    return fetch('https://api.nb.no/catalog/v3/iiif/' + id + '/manifest').then(function (r) { return r.json(); }).then(function (m) {
      var label = stripHtml(firstValue(m.label));
      if (!fig.dataset.caption) text(title, label);
      var services = [];
      try {
        if (m.sequences) {
          m.sequences[0].canvases.forEach(function (c) {
            var svc = c.images[0].resource.service;
            if (svc) services.push((svc['@id'] || svc.id) + '/info.json');
          });
        } else if (m.items) {
          m.items.forEach(function (c) {
            var svc = c.items[0].items[0].body.service;
            if (svc && svc[0]) services.push((svc[0].id || svc[0]['@id']) + '/info.json');
          });
        }
      } catch (e) {}
      if (services.length) showZoom(media, services, label);
      /* The manifest states the terms as a paragraph of Norwegian and as an
         address. The address is the licence; the paragraph is what it means,
         and it belongs behind the link rather than in the line. */
      var lic = m.license || (m.rights || '');
      rights.textContent = '';
      if (lic) {
        rights.appendChild(link(lic, ccLabel(lic) || 'Rights'));
        rights.appendChild(document.createTextNode(' · '));
      }
      rights.appendChild(link('https://www.nb.no/items/' + id, 'Nasjonalbiblioteket'));
    });
  }

  /* The platform gives a media file an identifier rather than an address, and
     serves it from one place under a name built from that identifier. */
  function dimuMediaFile(a) {
    var files = (a.media && a.media.mediaFiles) || [];
    for (var i = 0; i < files.length; i++) {
      var f = files[i];
      if (f.fileType !== 'audio' && f.fileType !== 'video') continue;
      var sound = f.fileType === 'audio';
      return {
        kind: sound ? 'sound' : 'video',
        url: f.url || 'https://ems.dimu.org/multimedia/' + f.identifier + (sound ? '.mp3' : '.mp4') + '?mmid=' + f.identifier
      };
    }
    return null;
  }

  /* {code: 'by-sa', system: 'CC'} is a licence, but only once it is spelled
     out and points at the terms it stands for. */
  function ccDeed(lic) {
    if (!lic) return null;
    /* The platform writes the same licence two ways: {system: 'CC', code: 'by'}
       on a record, and {system: null, code: 'CC BY'} on a picture. */
    var code = String(lic.code || '').toLowerCase().replace(/^cc[\s-]+/, '').replace(/\s+/g, '-');
    if (String(lic.system).toUpperCase() !== 'CC' && !/^cc[\s-]/i.test(String(lic.code || ''))) return null;
    if (code === 'pdm') return { label: 'Public domain mark 1.0', url: 'https://creativecommons.org/publicdomain/mark/1.0/' };
    if (code === 'zero' || code === '0') return { label: 'CC0 1.0', url: 'https://creativecommons.org/publicdomain/zero/1.0/' };
    if (!/^by(-(nc|nd|sa)){0,2}$/.test(code)) return null;
    return { label: 'CC ' + code.toUpperCase() + ' 4.0', url: 'https://creativecommons.org/licenses/' + code + '/4.0/' };
  }

  function loadDimu(fig, uuid) {
    var media = fig.querySelector('.mm-heritage-media');
    var title = fig.querySelector('.mm-heritage-title');
    var rights = fig.querySelector('.mm-heritage-rights');
    return fetch('https://api.dimu.org/artifact/uuid/' + uuid + '?api.key=' + DIMU_KEY).then(function (r) { return r.json(); }).then(function (a) {
      var t = (a.titles && a.titles[0] && a.titles[0].title) || (a.names && a.names[0] && a.names[0].name) || a.uniqueId;
      if (!fig.dataset.caption) text(title, t);
      var pic = a.media && a.media.pictures && a.media.pictures[0];
      var poster = pic ? 'https://dms-cf-01.dimu.org/image/' + pic.identifier + '?dimension=1200x1200' : null;
      /* A record can hold a recording as well as pictures. The recording is
         the object here, so it wins, and a picture becomes the poster. */
      var file = dimuMediaFile(a);
      if (file) {
        showMedia(media, file.kind, file.url, t, poster);
      } else if (pic) {
        var iiif = pic.sourceUrl && /\/iiif\//.test(pic.sourceUrl) ? pic.sourceUrl.replace(/\/full\/.*$/, '/info.json') : null;
        if (iiif) showZoom(media, iiif, t);
        else showImage(media, poster, t);
      }
      var lic = (pic && !file && pic.licenses && pic.licenses[0]) || (a.licenses && a.licenses[0]) || null;
      var code = (a.identifier && a.identifier.owner) || '';
      return ownerName(code).then(function (owner) {
        var parts = [];
        if (pic && !file && pic.photographer) parts.push('Photo: ' + pic.photographer);
        if (owner) parts.push(owner);
        rights.textContent = parts.filter(Boolean).join(' · ') + (parts.length ? ' · ' : '');
        var deed = ccDeed(lic);
        if (deed) { rights.appendChild(link(deed.url, deed.label)); rights.appendChild(document.createTextNode(' · ')); }
        else if (lic) { rights.appendChild(document.createTextNode((lic.description || lic.code) + ' · ')); }
        rights.appendChild(link('https://digitaltmuseum.org/' + (a.dimuCode || a.uniqueId), 'DigitaltMuseum'));
        return addWikidata(rights, 'dimu', a.dimuCode || a.uniqueId);
      });
    });
  }

  function firstLang(obj) {                    // {"no": [..], "def": [..]} or {"no": "..", "*": ".."}
    if (!obj) return '';
    /* A collection often holds the same label in several languages. Take the page's
       own first, so an English page says "Extended Outline (Norway)" where the
       Norwegian mirror says "Utvidet Outline". */
    var page = (document.documentElement.lang || 'en').slice(0, 2).toLowerCase();
    var keys = page === 'no' || page === 'nb' || page === 'nn'
      ? ['no', 'nb', 'nn', 'en', 'def', '*']
      : ['en', 'no', 'nb', 'nn', 'def', '*'];
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
      var shown = agg.edmIsShownBy || (o.europeanaAggregation || {}).edmPreview;
      var preview = (o.europeanaAggregation || {}).edmPreview;
      var kind = (o.type || '').toUpperCase();
      if (shown && kind === 'SOUND') showMedia(media, 'sound', shown, t);
      else if (shown && kind === 'VIDEO') showMedia(media, 'video', shown, t, preview);
      else if (shown) showImage(media, shown, t);
      var provider = (o.organizations || []).map(function (org) { return firstLang(org.prefLabel); }).filter(Boolean)[0] || '';
      var lic = firstLang(agg.edmRights);
      rights.textContent = [provider, lic ? '' : ''].filter(Boolean).join('') + (provider ? ' · ' : '');
      if (lic) {
        /* A public domain mark says a work is already out of copyright; CC0 is a
           waiver by someone who held the rights. They are not the same claim. */
        var label = ccLabel(lic) || lic.replace(/^https?:\/\//, '');
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
      var kind = firstLang(e.entityTypeName) || e.entityType || '';
      var dataset = p['entity.dataset'] && p['entity.dataset'][0] ? firstLang(p['entity.dataset'][0].displayValue) : '';
      var block = document.createElement('p'); block.className = 'mm-heritage-text';
      /* Most authority records carry no prose. What they do carry is a place in a
         classification, which is the thing worth showing: the code, and the term
         one step up. A bare entity type on its own says nothing. */
      var code = p['entity.code'] && p['entity.code'][0] ? p['entity.code'][0].value : '';
      var broader = p['concept.broader'] && p['concept.broader'][0] ? p['concept.broader'][0] : null;
      if (desc) {
        block.textContent = (kind ? kind + '. ' : '') + desc;
      } else {
        block.appendChild(document.createTextNode(kind + (code ? ' ' + code : '')));
        if (broader) {
          block.appendChild(document.createTextNode(', under '));
          block.appendChild(link('https://kulturnav.org/' + broader.value, firstLang(broader.displayValue)));
        }
        block.appendChild(document.createTextNode('.'));
      }
      media.appendChild(block);
      rights.textContent = (dataset ? dataset + ' · ' : '');
      rights.appendChild(link('https://kulturnav.org/' + uuid, 'KulturNav'));
      return addWikidata(rights, 'kulturnav', uuid);
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
      p.catch(function (err) {
        /* Say so in the console as well. A swallowed error here once left a
           manuscript showing its first page and nothing else, and the page
           looked fine. */
        if (window.console) console.warn('heritage: ' + src + ' ' + fig.dataset.id + ' failed', err);
        text(fig.querySelector('.mm-heritage-title'), 'This object could not be loaded from the collection.');
      }).then(function () { media.removeAttribute('aria-busy'); });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
