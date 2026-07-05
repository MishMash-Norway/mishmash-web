/* Session password gate for internal pages. The expected SHA-256 hash is
   provided by the layout via a data-hash attribute on this script tag.
   Note: this is a courtesy gate, not security — the page content is in
   the HTML and files under /internal/ are directly reachable. */
(function () {
  var SESSION_KEY = 'mm_internal_auth';
  var HASH = document.currentScript.dataset.hash;

  function buf2hex(buf) {
    return Array.from(new Uint8Array(buf)).map(function (b) {
      return b.toString(16).padStart(2, '0');
    }).join('');
  }

  function sha256(text) {
    var enc = new TextEncoder();
    return crypto.subtle.digest('SHA-256', enc.encode(text)).then(buf2hex);
  }

  function unlock() {
    document.getElementById('pw-gate').style.display = 'none';
    document.getElementById('pw-content').removeAttribute('hidden');
  }

  if (sessionStorage.getItem(SESSION_KEY) === HASH) {
    unlock();
    return;
  }

  document.getElementById('pw-form').addEventListener('submit', function (e) {
    e.preventDefault();
    var val = document.getElementById('pw-input').value;
    sha256(val).then(function (h) {
      if (h === HASH) {
        sessionStorage.setItem(SESSION_KEY, HASH);
        unlock();
      } else {
        document.getElementById('pw-error').style.display = 'block';
      }
    });
  });
})();
