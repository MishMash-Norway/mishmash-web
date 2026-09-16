/* Rotating photo gallery (see _includes/photo-carousel.html).
   One slide is visible at a time. The gallery advances every six seconds
   unless the reader prefers reduced motion, hovers or focuses it, or
   presses Pause. Arrow keys move between photos. */
(function () {
  var INTERVAL = 6000;
  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  document.querySelectorAll('[data-carousel]').forEach(function (root) {
    if (root.dataset.carouselReady) return;
    root.dataset.carouselReady = 'true';

    var slides = root.querySelectorAll('.mm-carousel-slide');
    if (slides.length < 2) { root.classList.add('is-static'); return; }
    var status = root.querySelector('[data-carousel-status]');
    var toggle = root.querySelector('[data-carousel-toggle]');
    var index = 0, timer = null, paused = reduced, held = false;

    function show(i) {
      index = (i + slides.length) % slides.length;
      slides.forEach(function (s, k) { s.hidden = k !== index; });
      if (status) status.textContent = (index + 1) + ' / ' + slides.length;
    }
    function tick() { if (!paused && !held) show(index + 1); }
    function start() { if (!timer) timer = setInterval(tick, INTERVAL); }
    function setPaused(p) {
      paused = p;
      toggle.setAttribute('aria-pressed', p ? 'true' : 'false');
      toggle.setAttribute('aria-label', p ? 'Play the slideshow' : 'Pause the slideshow');
      toggle.textContent = p ? 'Play' : 'Pause';
      if (status) status.setAttribute('aria-live', p ? 'polite' : 'off');
    }

    root.classList.add('is-ready');
    show(0);
    setPaused(paused);
    root.querySelector('[data-carousel-prev]').addEventListener('click', function () { setPaused(true); show(index - 1); });
    root.querySelector('[data-carousel-next]').addEventListener('click', function () { setPaused(true); show(index + 1); });
    toggle.addEventListener('click', function () { setPaused(!paused); });
    root.addEventListener('mouseenter', function () { held = true; });
    root.addEventListener('mouseleave', function () { held = false; });
    root.addEventListener('focusin', function () { held = true; });
    root.addEventListener('focusout', function () { held = false; });
    root.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') { setPaused(true); show(index - 1); }
      if (e.key === 'ArrowRight') { setPaused(true); show(index + 1); }
    });
    start();
  });
})();
