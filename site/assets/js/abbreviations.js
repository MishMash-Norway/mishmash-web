/* Inline abbreviations: the first occurrence of each abbreviation in the
   main text becomes a stretchtext toggle that unfolds its expansion in place
   (WCAG 3.1.4, technique G97: the expanded form at the first occurrence).

   The list comes from the page itself: _includes/page-about.html writes the
   abbreviations found on the page, with their expansion in the page's
   language, into a JSON block, so this script never guesses. The panel in
   the footer keeps the complete list and is what a reader without scripts
   gets.

   Only the first occurrence is touched, and only in running text: headings,
   links, buttons, code, existing stretchtext, the breadcrumb trail and the
   panel are left alone. A match is a whole word, so "AI" never matches
   inside another word. */
(function () {
  'use strict';

  var SKIP = 'h1, h2, h3, h4, h5, h6, a, button, code, pre, kbd, abbr, .stretch, .mm-breadcrumbs, .page-about, script, style, textarea, select, option, [aria-hidden="true"]';

  function readList() {
    var el = document.getElementById('mm-abbreviations');
    if (!el) return null;
    try { return JSON.parse(el.textContent); } catch (e) { return null; }
  }

  function escapeRegExp(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function textNodes(root) {
    var out = [];
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (node) {
        if (!node.nodeValue || !/\S/.test(node.nodeValue)) return NodeFilter.FILTER_REJECT;
        var parent = node.parentElement;
        if (!parent || parent.closest(SKIP)) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    var n;
    while ((n = walker.nextNode())) out.push(n);
    return out;
  }

  function makeToggle(term, expansion) {
    var wrap = document.createElement('span');
    wrap.className = 'stretch stretch-abbr';
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'stretch-toggle';
    btn.setAttribute('aria-expanded', 'false');
    var abbr = document.createElement('abbr');
    abbr.textContent = term;
    btn.appendChild(abbr);
    var more = document.createElement('span');
    more.className = 'stretch-more stretch-abbr-more';
    more.hidden = true;
    more.textContent = expansion;
    btn.addEventListener('click', function () {
      var expanded = btn.getAttribute('aria-expanded') === 'true';
      btn.setAttribute('aria-expanded', expanded ? 'false' : 'true');
      more.hidden = expanded;
    });
    wrap.appendChild(btn);
    wrap.appendChild(more);
    return wrap;
  }

  function init() {
    var list = readList();
    var main = document.querySelector('.main-content');
    if (!list || !main) return;
    // Longest first, so "CC BY" is found before a shorter term could split it.
    var terms = Object.keys(list).sort(function (a, b) { return b.length - a.length; });
    var pending = {};
    terms.forEach(function (t) { pending[t] = true; });
    var nodes = textNodes(main);
    for (var i = 0; i < nodes.length && Object.keys(pending).length; i += 1) {
      var node = nodes[i];
      var text = node.nodeValue;
      var best = null;
      Object.keys(pending).forEach(function (term) {
        var re = new RegExp('(^|[^\\w-])(' + escapeRegExp(term) + ')(?![\\w-])');
        var m = re.exec(text);
        if (m && (best === null || m.index + m[1].length < best.index)) {
          best = { term: term, index: m.index + m[1].length };
        }
      });
      if (!best) continue;
      // Split the text node around the match and put the toggle in between.
      var after = node.splitText(best.index);
      after.nodeValue = after.nodeValue.slice(best.term.length);
      var toggle = makeToggle(best.term, list[best.term]);
      after.parentNode.insertBefore(toggle, after);
      delete pending[best.term];
      // The remainder of this text node may hold another first occurrence.
      nodes.splice(i + 1, 0, after);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
