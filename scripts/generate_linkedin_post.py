#!/usr/bin/env python3
"""
HumiAn -> LinkedIn : selection aleatoire d'un article + envoi par email.

Logique :
1. Charge articles-meta.json depuis le repo (chemin local)
2. Charge publications-history.json (historique des publications)
3. Filtre les articles publies dans les 30 derniers jours -> exclus
4. Selectionne aleatoirement parmi les eligibles
5. Genere le texte du post LinkedIn (titre + resume + lien + hashtags)
6. Envoie le post par email via SMTP Gmail
7. Met a jour publications-history.json (commit fait par le workflow)
"""

import json
import os
import random
import smtplib
import sys
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# === CONFIG ===
SITE_BASE_URL = "https://shamsetdean.github.io/humiAn/"
ARTICLES_META_PATH = Path("articles-meta.json")
HISTORY_PATH = Path("publications-history.json")
COOLDOWN_DAYS = 30

# Mapping categorie -> hashtags
CATEGORY_HASHTAGS = {
    "tech": "#Tech #Numerique #Innovation",
    "os": "#OS #Systeme #Informatique",
    "humian": "#HumiAn #Numerique #Societe",
    "apple": "#Apple #Ecosysteme #Tech",
    "linux": "#Linux #OpenSource #Tech",
}
DEFAULT_HASHTAGS = "#Anthropotech #HumiAn"


def load_articles():
    """Charge la liste des articles depuis articles-meta.json."""
    if not ARTICLES_META_PATH.exists():
        sys.exit(f"ERREUR : {ARTICLES_META_PATH} introuvable.")
    with open(ARTICLES_META_PATH, encoding="utf-8") as f:
        data = json.load(f)
    # Si le JSON est un objet avec une cle "articles", on extrait. Sinon on suppose une liste.
    if isinstance(data, dict) and "articles" in data:
        return data["articles"]
    return data


def load_history():
    """Charge l'historique des publications."""
    if not HISTORY_PATH.exists():
        return []
    with open(HISTORY_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_history(history):
    """Sauvegarde l'historique mis a jour."""
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def get_recently_published_ids(history, cooldown_days=COOLDOWN_DAYS):
    """Retourne l'ensemble des IDs d'articles publies dans les N derniers jours."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=cooldown_days)
    recent = set()
    for entry in history:
        try:
            published_at = datetime.fromisoformat(entry["published_at"].replace("Z", "+00:00"))
            if published_at >= cutoff:
                recent.add(entry["article_id"])
        except (KeyError, ValueError):
            continue
    return recent


def pick_article(articles, excluded_ids):
    """Selectionne aleatoirement un article non exclu."""
    eligible = [a for a in articles if a.get("id") not in excluded_ids]
    if not eligible:
        return None
    return random.choice(eligible)


def build_linkedin_post(article):
    """Construit le texte du post LinkedIn."""
    title = article.get("title", "Article HumiAn")
    # Recuperer un resume : essaie "excerpt", "description", "summary", ou tronque "content"
    excerpt = (
        article.get("excerpt")
        or article.get("description")
        or article.get("summary")
        or ""
    )
    if not excerpt and article.get("content"):
        content = article["content"]
        if isinstance(content, list):
            content = " ".join(str(c) for c in content)
        # Premier paragraphe ou 200 premiers caracteres
        excerpt = str(content).split("\n")[0][:200]

    article_id = article.get("id", "")
    url = f"{SITE_BASE_URL}?article={article_id}"

    category = (article.get("category") or "").lower()
    hashtags = CATEGORY_HASHTAGS.get(category, DEFAULT_HASHTAGS)

    post = f"""{title}

{excerpt}

Lire l'article complet : {url}

{hashtags}"""
    return post


def send_email(post_text, article):
    """Envoie le post par email via Gmail SMTP."""
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    smtp_to = os.environ.get("SMTP_TO", smtp_user)

    if not smtp_user or not smtp_password:
        sys.exit("ERREUR : SMTP_USER et SMTP_PASSWORD doivent etre definis.")

    subject = f"[HumiAn -> LinkedIn] {article.get('title', 'Article')}"

    body_plain = f"""Post LinkedIn pret a copier-coller :

----- DEBUT DU POST -----
{post_text}
----- FIN DU POST -----

Article ID : {article.get('id')}
Categorie : {article.get('category', 'n/c')}
Genere le : {datetime.now(timezone.utc).isoformat()}
"""

    body_html = f"""<html><body style="font-family: Georgia, serif; max-width: 640px;">
<h2 style="color: #7a1f2e;">Post LinkedIn pret</h2>
<p><strong>Article :</strong> {article.get('title')}<br>
<strong>Categorie :</strong> {article.get('category', 'n/c')}<br>
<strong>ID :</strong> <code>{article.get('id')}</code></p>

<div style="background: #f5f3ef; border-left: 4px solid #7a1f2e; padding: 16px; white-space: pre-wrap; font-family: monospace; font-size: 14px;">{post_text}</div>

<p style="margin-top: 24px;">
<a href="https://www.linkedin.com/feed/" style="background: #7a1f2e; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Ouvrir LinkedIn</a>
</p>

<p style="color: #9aa0ae; font-size: 12px; margin-top: 32px;">
Genere automatiquement par GitHub Actions le {datetime.now(timezone.utc).strftime('%d/%m/%Y a %H:%M UTC')}.<br>
Anthropotech Lab.
</p>
</body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = smtp_to
    msg.attach(MIMEText(body_plain, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, [smtp_to], msg.as_string())

    print(f"Email envoye a {smtp_to}")


def main():
    print("=== HumiAn -> LinkedIn : selection d'article ===")

    articles = load_articles()
    print(f"Articles charges : {len(articles)}")

    history = load_history()
    print(f"Historique : {len(history)} entree(s)")

    excluded = get_recently_published_ids(history)
    print(f"Articles exclus (publies dans les {COOLDOWN_DAYS} derniers jours) : {len(excluded)}")

    article = pick_article(articles, excluded)
    if article is None:
        print("AVERTISSEMENT : aucun article eligible. On reinitialise le filtre.")
        article = pick_article(articles, set())
        if article is None:
            sys.exit("ERREUR : aucun article disponible.")

    print(f"Article selectionne : {article.get('id')} - {article.get('title')}")

    post_text = build_linkedin_post(article)
    print("\n----- POST GENERE -----")
    print(post_text)
    print("----- FIN -----\n")

    send_email(post_text, article)

    history.append({
        "article_id": article.get("id"),
        "title": article.get("title"),
        "published_at": datetime.now(timezone.utc).isoformat(),
    })
    save_history(history)
    print(f"Historique mis a jour : {len(history)} entree(s) au total.")


if __name__ == "__main__":
    main()
