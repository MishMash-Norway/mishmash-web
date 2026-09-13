"""Build the site's social and contact icons in the 2026 identity style.

Each icon is a square green tile with an ink border and an ink outline glyph:
the glyphs come from Tabler Icons (MIT, https://tabler.io/icons), fetched at a
pinned version, except ORCID, Wikidata and NVA, which are drawn here. Output:
site/assets/images/icons/catalogue/*.svg (used on person pages and the front
page) and the four icons in site/assets/images/icons/. Re-run only to add an
icon or change the style; needs network access for the Tabler glyphs.
"""
import pathlib, re, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
ICONS = ROOT / "site/assets/images/icons"
TABLER = "https://cdn.jsdelivr.net/npm/@tabler/icons@3.46.0/icons/outline/{}.svg"
GREEN, INK = "#b3e297", "#231f20"

CATALOGUE = {   # file name -> (label, tabler icon name or None for a drawn glyph)
    "bluesky": ("Bluesky", "brand-bluesky"),
    "calendar": ("Calendar", "calendar"),
    "discord": ("Discord", "brand-discord"),
    "email": ("E-mail", "mail"),
    "facebook": ("Facebook", "brand-facebook"),
    "github": ("GitHub", "brand-github"),
    "instagram": ("Instagram", "brand-instagram"),
    "linkedin": ("LinkedIn", "brand-linkedin"),
    "mastodon": ("Mastodon", "brand-mastodon"),
    "matrix-element": ("Matrix", "brand-matrix"),
    "newsletter": ("Newsletter", "news"),
    "nva": ("NVA", None),
    "orcid": ("ORCID", None),
    "podcast-feed": ("Podcast", "microphone"),
    "rss": ("RSS", "rss"),
    "slack": ("Slack", "brand-slack"),
    "telegram": ("Telegram", "brand-telegram"),
    "tiktok": ("TikTok", "brand-tiktok"),
    "vimeo": ("Vimeo", "brand-vimeo"),
    "web-page": ("Website", "world"),
    "wikidata": ("Wikidata", None),
    "x-twitter": ("X", "brand-x"),
    "youtube": ("YouTube", "brand-youtube"),
}
TOP = {"contact_email": ("E-mail", "mail"), "instagram": ("Instagram", "brand-instagram"),
       "linkedin": ("LinkedIn", "brand-linkedin"), "mailing_list": ("Mailing list", "mailbox")}

DRAWN = {
    # ORCID: the "iD" mark in a ring.
    "orcid": '<circle cx="12" cy="12" r="9.5"/><circle cx="8.4" cy="7.4" r="0.6" fill="{ink}"/>'
             '<path d="M8.4 10.2v6.6"/><path d="M11.6 7.6h2.6a4.6 4.6 0 0 1 0 9.2h-2.6z"/>',
    # Wikidata: the barcode-like mark.
    "wikidata": '<path d="M3.5 5v14"/><path d="M6.5 5v14"/><path d="M10.5 5v14" stroke-width="3"/>'
                '<path d="M14.5 5v14"/><path d="M18 5v14" stroke-width="3"/><path d="M21 5v14"/>',
    # NVA (the Norwegian research archive): a document with lines.
    "nva": '<path d="M14 3v4a1 1 0 0 0 1 1h4"/><path d="M17 21h-10a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2h7l5 5v11a2 2 0 0 1 -2 2z"/>'
           '<path d="M9 13h6"/><path d="M9 17h6"/>',
}

def glyph(name):
    if name is None:
        return None
    svg = urllib.request.urlopen(TABLER.format(name), timeout=30).read().decode()
    inner = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
    inner = re.sub(r'<path stroke="none" d="M0 0h24v24H0z" fill="none"\s*/>', "", inner)
    return " ".join(inner.split())

def icon(label, inner):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" role="img" aria-label="{label}">'
            f'<rect x="1" y="1" width="22" height="22" fill="{GREEN}" stroke="{INK}" stroke-width="1.25"/>'
            f'<g transform="translate(4.5 4.5) scale(0.625)" fill="none" stroke="{INK}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round">{inner}</g></svg>\n')

def build(folder, table):
    for fname, (label, tabler) in table.items():
        inner = DRAWN[fname].format(ink=INK) if tabler is None else glyph(tabler)
        (folder / f"{fname}.svg").write_text(icon(label, inner))
        print(folder.relative_to(ROOT) / f"{fname}.svg")

if __name__ == "__main__":
    build(ICONS / "catalogue", CATALOGUE)
    build(ICONS, TOP)
