/* Click-to-play for videos on YouTube (see _includes/youtube.html).
   The page holds a poster and a button; nothing is asked of Google until the
   reader presses it. The player then replaces the poster, on the no-cookie
   domain, and starts. */
(function () {
  document.querySelectorAll('.mm-video-poster[data-youtube]').forEach(function (button) {
    button.addEventListener('click', function () {
      var id = button.dataset.youtube;
      var frame = document.createElement('iframe');
      frame.width = 560;
      frame.height = 315;
      frame.src = 'https://www.youtube-nocookie.com/embed/' + encodeURIComponent(id) + '?autoplay=1&rel=0';
      frame.title = button.dataset.title || 'Video';
      frame.style.border = '0';
      frame.style.maxWidth = '100%';
      frame.setAttribute('allow', 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share');
      frame.setAttribute('referrerpolicy', 'no-referrer');
      frame.setAttribute('allowfullscreen', '');
      button.replaceWith(frame);
      frame.focus();
    });
  });
})();
