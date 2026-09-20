/* Third-party embeds that load when a reader asks for them.

   A button carries the address and the size of the embed; pressing it puts the iframe in place.
   Until then the other site is not contacted at all, which matters more than it sounds: an
   embedded player often brings its own fonts, scripts and counters with it. */
(function () {
  document.querySelectorAll('button[data-embed-src]').forEach(function (button) {
    button.addEventListener('click', function () {
      var frame = document.createElement('iframe');
      frame.src = button.dataset.embedSrc;
      frame.title = button.dataset.embedTitle || 'Embedded player';
      frame.width = button.dataset.embedWidth || 481;
      frame.height = button.dataset.embedHeight || 86;
      frame.className = button.className.replace('mm-embed-button', 'mm-embed-frame');
      frame.setAttribute('frameborder', '0');
      frame.setAttribute('scrolling', 'no');
      frame.setAttribute('referrerpolicy', 'strict-origin');
      button.replaceWith(frame);
    });
  });
})();
