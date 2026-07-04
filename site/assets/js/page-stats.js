/* Reading statistics for the "About the page" footer: approximate
 * reading time and LIX readability score, computed from the text the
 * reader actually sees (so adaptive pages report the chosen reading
 * level, not all variants at once). Recomputed when the reading level
 * changes. Without JavaScript the row simply stays hidden. */
(function () {
  'use strict';

  var WPM = 200;

  function visibleText() {
    var main = document.getElementById('main-content');
    if (!main) return '';
    // innerText is layout-aware: hidden adaptive variants, collapsed
    // stretchtext, and the collapsed footer list are excluded.
    var text = main.innerText || '';
    var switcher = document.querySelector('.audience-switcher');
    if (switcher) text = text.replace(switcher.innerText, ' ');
    return text;
  }

  function lix(text) {
    var words = text.match(/[A-Za-zÆØÅæøåÉéÈè0-9']+/g) || [];
    if (words.length < 20) return null;
    var sentences = (text.match(/[.!?:]+(\s|$)/g) || []).length || 1;
    var longWords = words.filter(function (w) { return w.length > 6; }).length;
    return {
      words: words.length,
      score: Math.round(words.length / sentences + (100 * longWords) / words.length),
      minutes: Math.max(1, Math.ceil(words.length / WPM)),
    };
  }

  function update() {
    var item = document.querySelector('[data-page-stats]');
    if (!item) return;
    var stats = lix(visibleText());
    if (!stats) return;
    item.querySelector('[data-page-stats-value]').textContent =
      '~' + stats.minutes + ' ' + (item.getAttribute('data-min-label') || 'min') +
      ' · ' + stats.words + ' ' + (item.getAttribute('data-words-label') || 'words') +
      ' · LIX ' + stats.score;
    item.hidden = false;
  }

  function init() {
    update();
    // Recompute after a reading-level switch.
    document.addEventListener('click', function (e) {
      if (e.target.closest && e.target.closest('[data-audience-choice]')) {
        window.requestAnimationFrame(update);
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
