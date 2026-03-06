import requests
from bs4 import BeautifulSoup
import json
import os
import hashlib
import time
import re

# =============================
# CONFIGURACIÓN
# =============================

BOT_TOKEN = "7525964751:AAFYim0qexbzSmwTAt5CWH27-kGZ6mVg8s4"
CHANNEL_ID = "-1002499768751"

MAX_POSTS = 5
MAX_PAGES = 50

forums = {
    "videos": "https://cultogore.net/forums/videos-gore.3/",
    "imagenes": "https://cultogore.net/forums/imagenes-gore.20/"
}

DB_FILE = "published_topics.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# =============================
# TELEGRAM
# =============================

def send_telegram(text):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "disable_web_page_preview": False
    }

    try:
        requests.post(url, data=data, timeout=10)
    except:
        pass


# =============================
# BASE DE DATOS
# =============================

def load_db():

    if os.path.exists(DB_FILE):

        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except:
            return set()

    return set()


def save_db(data):

    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(list(data), f, indent=2)


# =============================
# HASH
# =============================

def create_hash(title, link):

    return hashlib.md5((title + link).encode()).hexdigest()


# =============================
# OBTENER TEMAS
# =============================

def get_topics(url):

    topics = []

    for page in range(1, MAX_PAGES + 1):

        if page == 1:
            page_url = url
        else:
            page_url = f"{url}page-{page}"

        try:

            r = requests.get(page_url, headers=HEADERS, timeout=10)

            soup = BeautifulSoup(r.text, "html.parser")

            items = soup.find_all("div", class_="structItem")

            if not items:
                break

            for i in items:

                link = i.select_one(".structItem-title a")

                if not link:
                    continue

                title = link.text.strip()

                href = link["href"]

                if not href.startswith("http"):
                    href = "https://cultogore.net" + href

                author_tag = i.select_one(".username")

                author = author_tag.text.strip() if author_tag else "Autor"

                topics.append({
                    "title": title,
                    "link": href,
                    "author": author,
                    "hash": create_hash(title, href)
                })

        except:
            continue

        time.sleep(1)

    return topics


# =============================
# PROGRAMA PRINCIPAL
# =============================

def main():

    print("Iniciando bot...")

    published = load_db()

    new_topics = []

    for name, forum in forums.items():

        print("Escaneando foro:", name)

        topics = get_topics(forum)

        for t in topics:

            if t["hash"] not in published:

                new_topics.append(t)

    print("Temas pendientes:", len(new_topics))

    count = 0

    for t in new_topics[:MAX_POSTS]:

        message = f"""📹 {t['title']}

🔗 {t['link']}

👤 Autor: {t['author']}"""

        send_telegram(message)

        published.add(t["hash"])

        count += 1

        print("Publicado:", t["title"])

        time.sleep(2)

    save_db(published)

    print("Publicados en esta ejecución:", count)


# =============================

if __name__ == "__main__":
    main()
