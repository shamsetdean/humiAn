#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anthropotech · Lab — Générateur automatique
=============================================
Génère en une commande :
  - articles/articles-meta.json
  - rss.xml  (avec catégories, sans images)
  - sitemap.xml
  - article/[slug]/index.html  ← pages OG statiques pour LinkedIn/réseaux

Usage :
  python3 generate.py

Placer ce script à la racine du repo (même niveau que articles/)
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

# ── CONFIG ──────────────────────────────────────────────────────────────────
SITE_URL     = "https://shamsetdean.github.io/Anthropotech"
SITE_TITLE   = "Anthropotech · Lab"
SITE_DESC    = "Explorer la manière dont les comportements et les innovations numériques façonnent notre quotidien."
AUTHOR       = "Shams & Dean"
ARTICLES_DIR = Path("articles")
OG_IMAGE_DEFAULT = "https://shamsetdean.github.io/Anthropotech/og-image.png"

CAT_LABELS = {
    "tech":   "Tech",
    "tesla":  "Tech",
    "os":     "OS",
    "apple":  "OS",
    "linux":  "OS",
    "humian": "Hum{i}An",
}
# ────────────────────────────────────────────────────────────────────────────

MONTHS_FR = {
    "janvier": 1, "février": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
}

def parse_date_fr(date_str):
    if not date_str:
        return datetime(2000, 1, 1, tzinfo=timezone.utc)
    parts = date_str.strip().lower().split()
    if len(parts) == 3:
        try:
            return datetime(int(parts[2]), MONTHS_FR.get(parts[1], 1), int(parts[0]), tzinfo=timezone.utc)
        except (ValueError, KeyError):
            pass
    return datetime(2000, 1, 1, tzinfo=timezone.utc)

def load_articles():
    articles = []
    skip = {"index.json", "articles-meta.json"}
    for filepath in sorted(ARTICLES_DIR.glob("*.json")):
        if filepath.name in skip:
            continue
        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
            data["_file"] = filepath.name
            data["_id"]   = filepath.stem
            articles.append(data)
            print(f"  ✓  {filepath.name}")
        except Exception as e:
            print(f"  ⚠️  Ignoré {filepath.name} : {e}")
    articles.sort(key=lambda a: parse_date_fr(a.get("date", "")), reverse=True)
    return articles

def generate_meta(articles):
    meta = [{
        "id":        a.get("id") or a["_id"],
        "titre":     a.get("titre", ""),
        "resume":    a.get("resume", ""),
        "categorie": a.get("categorie", ""),
        "date":      a.get("date", ""),
        "auteur":    a.get("auteur", AUTHOR),
    } for a in articles]
    out = ARTICLES_DIR / "articles-meta.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"  ✅  {out}  ({len(meta)} articles)")

def generate_rss(articles):
    """RSS amélioré : catégories lisibles, sans images, description complète."""
    now_rfc = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    items = []
    for a in articles[:20]:
        art_id   = a.get("id") or a["_id"]
        title    = escape(a.get("titre", "Sans titre"))
        desc     = escape(a.get("resume", ""))
        link     = f"{SITE_URL}/article/{art_id}"
        pub_date = parse_date_fr(a.get("date", "")).strftime("%a, %d %b %Y 08:00:00 +0000")
        cat_raw  = a.get("categorie", "")
        cat_label = escape(CAT_LABELS.get(cat_raw, cat_raw.capitalize()))
        author   = escape(a.get("auteur", AUTHOR))

        items.append(f"""    <item>
      <title>{title}</title>
      <link>{link}</link>
      <description>{desc}</description>
      <pubDate>{pub_date}</pubDate>
      <author>{author}</author>
      <category>{cat_label}</category>
      <guid isPermaLink="true">{link}</guid>
    </item>""")

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>{escape(SITE_TITLE)}</title>
    <link>{SITE_URL}/</link>
    <description>{escape(SITE_DESC)}</description>
    <language>fr-FR</language>
    <lastBuildDate>{now_rfc}</lastBuildDate>
    <atom:link href="{SITE_URL}/rss.xml" rel="self" type="application/rss+xml"/>
    <copyright>Copyright 2026 Guettaf Shams — CC BY-NC-ND 4.0</copyright>
    <managingEditor>{AUTHOR}</managingEditor>
    <category>Technologie</category>
    <category>Numérique</category>
    <ttl>1440</ttl>
{chr(10).join(items)}
  </channel>
</rss>"""

    with open("rss.xml", "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"  ✅  rss.xml  ({min(len(articles), 20)} entrées, catégories incluses)")

def generate_sitemap(articles):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls = [f"""  <url>
    <loc>{SITE_URL}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>"""]
    for a in articles:
        art_id  = a.get("id") or a["_id"]
        dt      = parse_date_fr(a.get("date", ""))
        lastmod = dt.strftime("%Y-%m-%d") if dt.year > 2000 else today
        urls.append(f"""  <url>
    <loc>{SITE_URL}/article/{art_id}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>"""
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap)
    print(f"  ✅  sitemap.xml  ({len(articles) + 1} URLs, chemins /article/ inclus)")

def generate_og_pages(articles):
    """
    Génère article/[slug]/index.html pour chaque article.
    Ces pages statiques exposent les bonnes balises OG aux scrapers
    (LinkedIn, Twitter, Facebook…) et redirigent les vrais visiteurs
    vers la SPA via meta-refresh + JS.
    """
    base_dir = Path("article")
    base_dir.mkdir(exist_ok=True)
    count = 0

    for a in articles:
        art_id  = a.get("id") or a["_id"]
        titre   = a.get("titre", "Sans titre")
        resume  = a.get("resume", SITE_DESC)
        auteur  = a.get("auteur", AUTHOR)
        date    = a.get("date", "")
        cat_raw = a.get("categorie", "")
        cat     = CAT_LABELS.get(cat_raw, cat_raw.capitalize())

        page_url   = f"{SITE_URL}/article/{art_id}/"
        spa_url    = f"{SITE_URL}/?article={art_id}"
        og_image   = OG_IMAGE_DEFAULT

        # Échapper pour HTML
        def h(s): return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")

        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <!-- Redirection immédiate vers la SPA (visiteurs humains) -->
  <meta http-equiv="refresh" content="0;url={spa_url}">

  <title>{h(titre)} — {h(SITE_TITLE)}</title>
  <meta name="description" content="{h(resume)}">
  <meta name="author" content="{h(auteur)}">
  <link rel="canonical" href="{page_url}">

  <!-- Open Graph (LinkedIn, Facebook, Slack…) -->
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="{h(SITE_TITLE)}">
  <meta property="og:title" content="{h(titre)}">
  <meta property="og:description" content="{h(resume)}">
  <meta property="og:url" content="{page_url}">
  <meta property="og:image" content="{og_image}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{h(titre)}">
  <meta property="og:locale" content="fr_FR">
  <meta property="article:author" content="{h(auteur)}">
  <meta property="article:section" content="{h(cat)}">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="@shamsetdean">
  <meta name="twitter:title" content="{h(titre)}">
  <meta name="twitter:description" content="{h(resume)}">
  <meta name="twitter:image" content="{og_image}">

  <!-- JSON-LD -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "{h(titre)}",
    "description": "{h(resume)}",
    "author": {{"@type": "Person", "name": "{h(auteur)}"}},
    "publisher": {{"@type": "Person", "name": "Guettaf Shams"}},
    "url": "{page_url}",
    "datePublished": "{date}",
    "articleSection": "{h(cat)}",
    "inLanguage": "fr-FR"
  }}
  </script>
</head>
<body>
  <p>Redirection en cours… <a href="{spa_url}">Cliquez ici si la redirection ne fonctionne pas.</a></p>
  <script>window.location.replace("{spa_url}");</script>
</body>
</html>"""

        out_dir = base_dir / art_id
        out_dir.mkdir(exist_ok=True)
        out_file = out_dir / "index.html"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(html)
        count += 1

    print(f"  ✅  article/[slug]/index.html  ({count} pages OG générées)")

def main():
    print("\n🔄  Anthropotech · Lab — Génération en cours...\n")
    print("📂  Lecture des articles :")
    if not ARTICLES_DIR.exists():
        print(f"  ❌  Dossier '{ARTICLES_DIR}' introuvable.")
        print("     Lance ce script depuis la racine du repo.")
        return
    articles = load_articles()
    if not articles:
        print("  ⚠️  Aucun article trouvé.")
        return
    print(f"\n📝  Génération ({len(articles)} articles) :")
    generate_meta(articles)
    generate_rss(articles)
    generate_sitemap(articles)
    generate_og_pages(articles)
    print(f"\n✨  Terminé !\n")

if __name__ == "__main__":
    main()
