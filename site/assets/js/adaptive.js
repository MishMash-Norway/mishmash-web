/* Adaptive content: audience switching and stretchtext.
 * The chosen reader group is kept in localStorage and applied as a
 * data-audience attribute on <html> (set early by an inline script in
 * the default layout to avoid a flash of the wrong variant).
 * Visibility itself is pure CSS — see assets/css/adaptive.css. */
(function () {
  'use strict';

  var KEY = 'mishmash-audience';
  var root = document.documentElement;

  function setAudience(key) {
    root.setAttribute('data-audience', key);
    try {
      localStorage.setItem(KEY, key);
    } catch (e) {
      /* private mode etc. — switching still works for this page */
    }
    updateButtons();
  }

  function updateButtons() {
    var current = root.getAttribute('data-audience');
    document
      .querySelectorAll('.audience-switcher button[data-audience-choice]')
      .forEach(function (btn) {
        btn.setAttribute(
          'aria-pressed',
          btn.getAttribute('data-audience-choice') === current ? 'true' : 'false'
        );
      });
  }

  function init() {
    var bars = document.querySelectorAll('.audience-switcher');
    bars.forEach(function (bar) {
      bar.hidden = false;
    });

    // A stored level that no longer exists (e.g. after a rename in
    // _data/audiences.yml) would match no CSS rule — reset to default.
    var valid = Array.prototype.map.call(
      document.querySelectorAll('.audience-switcher button[data-audience-choice]'),
      function (btn) { return btn.getAttribute('data-audience-choice'); }
    );
    if (bars.length && valid.indexOf(root.getAttribute('data-audience')) === -1) {
      setAudience(bars[0].getAttribute('data-default') || valid[0]);
    }
    document
      .querySelectorAll('.audience-switcher button[data-audience-choice]')
      .forEach(function (btn) {
        btn.addEventListener('click', function () {
          setAudience(btn.getAttribute('data-audience-choice'));
        });
      });
    updateButtons();

    document.querySelectorAll('.stretch-toggle').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var more = btn.nextElementSibling;
        if (!more || !more.classList.contains('stretch-more')) return;
        var expanded = btn.getAttribute('aria-expanded') === 'true';
        btn.setAttribute('aria-expanded', expanded ? 'false' : 'true');
        more.hidden = expanded;
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
