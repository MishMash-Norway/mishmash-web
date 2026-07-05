---
layout: internal
title: "Researchers"
---

<p>
  <button class="button" onclick="toggleForm()">📝 Register my profile</button>
</p>

<div id="register-section" hidden>
  <h2>Register your profile</h2>
  <p>Fill in the form below. Your profile will appear on this page within a few minutes after submission.</p>

  <p style="font-size:.9rem;color:#555;margin-top:0;">Fields marked <span class="mm-required">*</span> are required. Your name, institution, position, role, and email will be visible on this page and in the public GitHub repository.</p>

  <form id="profile-form" style="max-width:560px;">

    <div class="mm-field">
      <label for="f-name" class="mm-label">Full name <span class="mm-required">*</span></label>
      <input id="f-name" type="text" required class="mm-text-input">
    </div>

    <div class="mm-field">
      <label for="f-email" class="mm-label">Email <span class="mm-required">*</span></label>
      <input id="f-email" type="email" required class="mm-text-input">
      <p style="font-size:.8rem;color:#c0392b;margin:.3rem 0 0;">⚠️ Your email will be published on this page and stored in a public repository. Only submit an email address you are comfortable making public.</p>
    </div>

    <div class="mm-field">
      <label for="f-institution" class="mm-label">Institution / Organisation <span class="mm-required">*</span></label>
      <input id="f-institution" type="text" required class="mm-text-input">
    </div>

    <div class="mm-field">
      <label for="f-position" class="mm-label">Position / Title <span class="mm-required">*</span></label>
      <input id="f-position" type="text" required class="mm-text-input">
    </div>

    <div class="mm-field">
      <label for="f-role" class="mm-label">Role in WP4 <span class="mm-required">*</span></label>
      <select id="f-role" required style="width:100%;padding:.5rem .7rem;border:1px solid #bbb;border-radius:6px;font-size:1rem;box-sizing:border-box;background:#fff;">
        <option value="">— select —</option>
        <option value="leader">Leader</option>
        <option value="researcher">Researcher</option>
        <option value="non-academic">Non-academic partner</option>
      </select>
    </div>

    <div class="mm-field">
      <label for="f-bio" class="mm-label">Short bio <span style="color:#888;font-weight:400">(optional)</span></label>
      <textarea id="f-bio" rows="4" style="width:100%;padding:.5rem .7rem;border:1px solid #bbb;border-radius:6px;font-size:1rem;box-sizing:border-box;resize:vertical;"></textarea>
    </div>

    <div class="mm-field">
      <label for="f-website" class="mm-label">Website / profile URL <span style="color:#888;font-weight:400">(optional)</span></label>
      <input id="f-website" type="url" placeholder="https://" class="mm-text-input">
    </div>

    <div style="margin-bottom:1.5rem;">
      <label for="f-keywords" class="mm-label">Research keywords <span style="color:#888;font-weight:400">(optional, comma-separated)</span></label>
      <input id="f-keywords" type="text" placeholder="e.g. AI, music education, machine learning" class="mm-text-input">
    </div>

    <div style="margin-bottom:1.5rem;padding:.8rem;background:#fff8e1;border:1px solid #f0c040;border-radius:6px;font-size:.85rem;">
      <label style="display:flex;align-items:flex-start;gap:.6rem;cursor:pointer;">
        <input id="f-consent" type="checkbox" required style="margin-top:.2rem;flex-shrink:0;">
        <span>I understand that my name, institution, position, role, and email address will be published on this page and stored in a publicly accessible GitHub repository. I consent to this.</span>
      </label>
    </div>

    <button type="submit" class="button" id="submit-btn">Submit profile</button>
    <button type="button" class="button" onclick="toggleForm()" style="margin-left:.5rem;background:#eee;color:#333;">Cancel</button>

  </form>

  <div id="form-success" hidden style="margin-top:1rem;padding:1rem;background:#e8f8e8;border:1px solid #7bc87b;border-radius:6px;color:#1a5c1a;">
    ✅ <strong>Profile submitted!</strong> It is now awaiting review. Once approved by the WP4 team it will appear on this page automatically.
  </div>
  <div id="form-error" hidden style="margin-top:1rem;padding:1rem;background:#fdecea;border:1px solid #e88;border-radius:6px;color:#7a1a1a;">
    ❌ <strong>Something went wrong.</strong> <span id="error-detail"></span> Please try again or contact the WP4 team.
  </div>
</div>

<hr style="margin:2rem 0;">

{% assign all_researchers = site.data.wp4_researchers %}

{% assign leaders = all_researchers | where: "role", "leader" %}
{% assign researchers = all_researchers | where: "role", "researcher" %}
{% assign non_academic = all_researchers | where: "role", "non-academic" %}

{% if leaders.size > 0 %}
## Leaders

<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1rem;margin-bottom:2rem;">
{% for person in leaders %}
<div style="border:1px solid #ddd;border-radius:8px;padding:1rem;background:#fafafe;">
  <strong style="font-size:1.05rem;">{{ person.name }}</strong><br>
  <span style="color:#555;font-size:.9rem;">{{ person.position }}</span><br>
  <span style="color:#777;font-size:.85rem;">{{ person.institution }}</span>
  {% if person.bio %}<p style="font-size:.9rem;margin:.6rem 0 0;">{{ person.bio }}</p>{% endif %}
  {% if person.keywords %}<p style="font-size:.8rem;color:#888;margin:.4rem 0 0;">🏷 {{ person.keywords }}</p>{% endif %}
  {% if person.email %}<p class="mm-help"><a href="mailto:{{ person.email }}">✉️ {{ person.email }}</a></p>{% endif %}
  {% if person.website %}<p class="mm-help"><a href="{{ person.website }}" target="_blank" rel="noopener">🔗 Profile</a></p>{% endif %}
</div>
{% endfor %}
</div>
{% endif %}

{% if researchers.size > 0 %}
## Researchers

<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1rem;margin-bottom:2rem;">
{% for person in researchers %}
<div style="border:1px solid #ddd;border-radius:8px;padding:1rem;background:#fafafe;">
  <strong style="font-size:1.05rem;">{{ person.name }}</strong><br>
  <span style="color:#555;font-size:.9rem;">{{ person.position }}</span><br>
  <span style="color:#777;font-size:.85rem;">{{ person.institution }}</span>
  {% if person.bio %}<p style="font-size:.9rem;margin:.6rem 0 0;">{{ person.bio }}</p>{% endif %}
  {% if person.keywords %}<p style="font-size:.8rem;color:#888;margin:.4rem 0 0;">🏷 {{ person.keywords }}</p>{% endif %}
  {% if person.email %}<p class="mm-help"><a href="mailto:{{ person.email }}">✉️ {{ person.email }}</a></p>{% endif %}
  {% if person.website %}<p class="mm-help"><a href="{{ person.website }}" target="_blank" rel="noopener">🔗 Profile</a></p>{% endif %}
</div>
{% endfor %}
</div>
{% endif %}

{% if non_academic.size > 0 %}
## Non-academic partners

<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1rem;margin-bottom:2rem;">
{% for person in non_academic %}
<div style="border:1px solid #ddd;border-radius:8px;padding:1rem;background:#fafafe;">
  <strong style="font-size:1.05rem;">{{ person.name }}</strong><br>
  <span style="color:#555;font-size:.9rem;">{{ person.position }}</span><br>
  <span style="color:#777;font-size:.85rem;">{{ person.institution }}</span>
  {% if person.bio %}<p style="font-size:.9rem;margin:.6rem 0 0;">{{ person.bio }}</p>{% endif %}
  {% if person.keywords %}<p style="font-size:.8rem;color:#888;margin:.4rem 0 0;">🏷 {{ person.keywords }}</p>{% endif %}
  {% if person.email %}<p class="mm-help"><a href="mailto:{{ person.email }}">✉️ {{ person.email }}</a></p>{% endif %}
  {% if person.website %}<p class="mm-help"><a href="{{ person.website }}" target="_blank" rel="noopener">🔗 Profile</a></p>{% endif %}
</div>
{% endfor %}
</div>
{% endif %}

{% if all_researchers.size == 0 %}
<p style="color:#888;font-style:italic;">No profiles registered yet. Be the first!</p>
{% endif %}

[← Back to WP4 page](/internal/wp4/)

<script>
(function () {
  // Replace this with your GitHub fine-grained PAT (issues:write on this repo only)
  var GITHUB_TOKEN = "REPLACE_WITH_YOUR_PAT";
  var REPO = "MishMash-Norway/mishmash-web";
  var LABEL = "wp4-researcher";

  function toggleForm() {
    var section = document.getElementById('register-section');
    if (section.hidden) {
      section.hidden = false;
      section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
      section.hidden = true;
    }
  }
  window.toggleForm = toggleForm;

  document.getElementById('profile-form').addEventListener('submit', function (e) {
    e.preventDefault();

    var btn = document.getElementById('submit-btn');
    btn.disabled = true;
    btn.textContent = 'Submitting…';

    document.getElementById('form-success').hidden = true;
    document.getElementById('form-error').hidden = true;

    var data = {
      name:        document.getElementById('f-name').value.trim(),
      email:       document.getElementById('f-email').value.trim(),
      institution: document.getElementById('f-institution').value.trim(),
      position:    document.getElementById('f-position').value.trim(),
      role:        document.getElementById('f-role').value,
      bio:         document.getElementById('f-bio').value.trim(),
      website:     document.getElementById('f-website').value.trim(),
      keywords:    document.getElementById('f-keywords').value.trim(),
      submitted:   new Date().toISOString().slice(0, 10)
    };

    var issueBody = "WP4 researcher profile registration.\n\n```json\n" +
      JSON.stringify(data, null, 2) + "\n```";

    fetch('https://api.github.com/repos/' + REPO + '/issues', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + GITHUB_TOKEN,
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.github+json'
      },
      body: JSON.stringify({
        title: 'WP4 researcher registration: ' + data.name,
        body:  issueBody,
        labels: [LABEL]
      })
    })
    .then(function (res) {
      if (res.ok) {
        document.getElementById('profile-form').reset();
        document.getElementById('form-success').hidden = false;
        document.getElementById('register-section').hidden = true;
      } else {
        return res.json().then(function (json) {
          throw new Error(json.message || ('HTTP ' + res.status));
        });
      }
    })
    .catch(function (err) {
      document.getElementById('error-detail').textContent = err.message;
      document.getElementById('form-error').hidden = false;
    })
    .finally(function () {
      btn.disabled = false;
      btn.textContent = 'Submit profile';
    });
  });
})();
</script>
