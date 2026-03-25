#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anthropotech — Générateur automatique
======================================
Génère en une commande :
  - articles/articles-meta.json
  - rss.xml
  - sitemap.xml

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
    meta = [{"id": a.get("id") or a["_id"], "titre": a.get("titre", ""), "resume": a.get("resume", ""), "categorie": a.get("categorie", ""), "date": a.get("date", ""), "auteur": a.get("auteur", AUTHOR)} for a in articles]
    out = ARTICLES_DIR / "articles-meta.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"  ✅  {out}  ({len(meta)} articles)")

def generate_rss(articles):
    now_rfc = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    items = []
    for a in articles[:20]:
        art_id = a.get("id") or a["_id"]
        items.append(f"""    <item>
      <title>{escape(a.get('titre', ''))}</title>
      <link>{SITE_URL}/?article={art_id}</link>
      <description>{escape(a.get('resume', ''))}</description>
      <pubDate>{parse_date_fr(a.get('date','')).strftime('%a, %d %b %Y 08:00:00 +0000')}</pubDate>
      <author>{escape(a.get('auteur', AUTHOR))}</author>
      <category>{escape(a.get('categorie', ''))}</category>
      <guid isPermaLink="true">{SITE_URL}/?article={art_id}</guid>
    </item>""")
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{escape(SITE_TITLE)}</title>
    <link>{SITE_URL}/</link>
    <description>{escape(SITE_DESC)}</description>
    <language>fr-FR</language>
    <lastBuildDate>{now_rfc}</lastBuildDate>
    <atom:link href="{SITE_URL}/rss.xml" rel="self" type="application/rss+xml"/>
    <image>
      <url>{SITE_URL}/icons/icon-192.png</url>
      <title>{escape(SITE_TITLE)}</title>
      <link>{SITE_URL}/</link>
    </image>
{chr(10).join(items)}
  </channel>
</rss>"""
    with open("rss.xml", "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"  ✅  rss.xml  ({min(len(articles), 20)} entrées)")

def generate_sitemap(articles):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls = [f"""  <url>\n    <loc>{SITE_URL}/</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>1.0</priority>\n  </url>"""]
    for a in articles:
        art_id  = a.get("id") or a["_id"]
        dt      = parse_date_fr(a.get("date", ""))
        lastmod = dt.strftime("%Y-%m-%d") if dt.year > 2000 else today
        urls.append(f"""  <url>\n    <loc>{SITE_URL}/?article={art_id}</loc>\n    <lastmod>{lastmod}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.8</priority>\n  </url>""")
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{chr(10).join(urls)}\n</urlset>"""
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap)
    print(f"  ✅  sitemap.xml  ({len(articles) + 1} URLs)")

def main():
    print("\n🔄  Anthropotech · Lab — Génération en cours...\n")
    print("📂  Lecture des articles :")
    if not ARTICLES_DIR.exists():
        print(f"  ❌  Dossier '{ARTICLES_DIR}' introuvable. Lance ce script depuis la racine du repo.")
        return
    articles = load_articles()
    if not articles:
        print("  ⚠️  Aucun article trouvé.")
        return
    print(f"\n📝  Génération :")
    generate_meta(articles)
    generate_rss(articles)
    generate_sitemap(articles)
    print(f"\n✨  Terminé — {len(articles)} articles traités.\n")

if __name__ == "__main__":
    main()
