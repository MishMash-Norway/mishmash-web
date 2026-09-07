# site/assets/files/

This directory is for downloadable files (programme PDFs, handouts, installers, checksums, etc.) that should be published with the website and served from the MishMash web origin.

Guidelines

- Filenames
  - Use lowercase, hyphens, and include a date or version: e.g. `mishmash-programme-2026-09-15.pdf`.
  - Avoid spaces and non-ASCII characters.

- Metadata & integrity
  - Include a checksum file for any binary or installer: `mishmash-programme-2026-09-15.pdf.sha256` (contains the SHA256 hex).
  - For signed releases, include a `.asc` or `.sig` signature.

- Accessibility & alternatives
  - If the document is important, provide an HTML or accessible (tagged) PDF alternative and a short text summary on the page linking to the file.

- Linking from the site
  - Example link (adjust path if needed):

    <a href="/assets/files/mishmash-programme-2026-09-15.pdf" download="mishmash-programme-2026-09-15.pdf" target="_blank" rel="noopener noreferrer" aria-label="Download MishMash programme PDF, 2.3 MB">Download programme (PDF, 2.3 MB)</a>

  - For tracking downloads, fire an analytics event on click or route through a logging/redirect endpoint.

- Size & hosting policy
  - Small documents (PDFs, images, text) can be committed in this repo and served via GitHub Pages.
  - For large binaries (>50–100 MB), frequent updates, or heavy download traffic, prefer GitHub Releases, Git LFS, or cloud storage/CDN (S3/Cloudflare/etc.).

- Security
  - Scan files for malware before publishing.
  - Warn users clearly for installers/executables and provide system requirements.

- Caching & headers
  - GitHub Pages serves files over HTTPS and handles common caching headers. If you need custom Content-Disposition (force download) or other headers, consider using a server/CDN that supports header configuration.

- How to add a file
  1. Add the file into this directory (e.g. `site/assets/files/mishmash-programme-2026-09-15.pdf`).
  2. Add a checksum file (SHA256) next to it.
  3. Update the events page (e.g. `site/events/` markdown) with a descriptive link and short summary.

If you'd like, I can:
- Open a PR that creates this README.md (done). 
- Add a sample programme PDF placeholder, checksum, and a small change to the events page showing the link.
- Show a short workflow to publish larger files via GitHub Releases or S3.
