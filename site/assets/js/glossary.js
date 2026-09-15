/* Glossary: copy a term's link. Each term has an anchor
 * (.glossary-copy, markup in _includes/glossary-copy-link.html) that
 * already works as a plain link; with JavaScript a click also copies the
 * term's URL to the clipboard, shows "Copied" on the control for a
 * moment, and announces it to screen readers. */
(function () {
  'use strict';

  var COPIED = { en: 'Copied', nb: 'Kopiert' };
  var lang = (document.documentElement.lang || 'en').slice(0, 2);
  var label = COPIED[lang] || COPIED.en;

  var live = document.createElement('span');
  live.className = 'sr-only';
  live.setAttribute('aria-live', 'polite');

  function init() {
    var links = document.querySelectorAll('.glossary-copy[data-copy-key]');
    if (!links.length) return;
    document.body.appendChild(live);
    links.forEach(function (link) {
      link.addEventListener('click', function () {
        var url = location.origin + location.pathname + '#' + link.getAttribute('data-copy-key');
        if (!navigator.clipboard || !navigator.clipboard.writeText) return;
        navigator.clipboard.writeText(url).then(function () {
          link.setAttribute('data-copied', label);
          live.textContent = label + ': ' + url;
          setTimeout(function () {
            link.removeAttribute('data-copied');
            live.textContent = '';
          }, 1500);
        }, function () { /* clipboard blocked: the anchor still navigated */ });
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
