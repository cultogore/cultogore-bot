import requests
from bs4 import BeautifulSoup
import json
import os
import hashlib
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")

CHANNEL_ID = "-1002499768751"

MAX_POSTS = 5

forums = {
    "videos": "https://cultogore.net/forums/videos-gore.3/",
    "imagenes": "https://cultogore.net/forums/imagenes-gore.20/"
}

PUBLISHED_FILE = "published_topics.json"
BLOCKED_FILE = "blocked_topics.json"
STATE_FILE = "state.json"

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

    requests.post(url, data=data)

# =============================
# JSON
# =============================

def load_json(file):

    if not os.path.exists(file):

        with open(file,"w") as f:
            json.dump([],f)

        return set()

    with open(file,"r") as f:
        return set(json.load(f))


def save_json(file,data):

    with open(file,"w") as f:
        json.dump(list(data),f,indent=2)


# =============================
# STATE
# =============================

def load_state():

    if not os.path.exists(STATE_FILE):

        state = {"page":1}

        with open(STATE_FILE,"w") as f:
            json.dump(state,f)

        return state

    with open(STATE_FILE,"r") as f:
        return json.load(f)


def save_state(state):

    with open(STATE_FILE,"w") as f:
        json.dump(state,f)


# =============================
# HASH
# =============================

def create_hash(title,link):

    return hashlib.md5((title+link).encode()).hexdigest()


# =============================
# SCRAPER
# =============================

def get_topics(url,start_page):

    topics=[]

    page=start_page

    while True:

        if page==1:
            page_url=url
        else:
            page_url=f"{url}page-{page}"

        print("Escaneando:",page_url)

        r=requests.get(page_url,headers=HEADERS,timeout=20)

        soup=BeautifulSoup(r.text,"html.parser")

        items=soup.select(".structItem")

        if not items:
            break

        for item in items:

            link_tag=item.select_one(".structItem-title a")

            if not link_tag:
                continue

            # eliminar todos los prefijos
            for label in link_tag.select(".label"):
                label.decompose()

            # obtener título limpio
            title=link_tag.get_text(strip=True)

            href=link_tag["href"]

            if not href.startswith("http"):
                href="https://cultogore.net"+href

            author_tag=item.select_one(".username")

            author=author_tag.text.strip() if author_tag else "Autor"

            topics.append({
                "title":title,
                "link":href,
                "author":author,
                "hash":create_hash(title,href)
            })

        page+=1

        time.sleep(0.5)

        if len(topics)>=100:
            break

    return topics,page


# =============================
# MAIN
# =============================

def main():

    print("Iniciando bot")

    published=load_json(PUBLISHED_FILE)

    blocked=load_json(BLOCKED_FILE)

    state=load_state()

    start_page=state["page"]

    new_topics=[]

    for name,forum in forums.items():

        topics,next_page=get_topics(forum,start_page)

        for t in topics:

            if t["hash"] in published:
                continue

            if t["hash"] in blocked:
                continue

            new_topics.append(t)

        state["page"]=next_page

    print("Temas encontrados:",len(new_topics))

    count=0

    for t in new_topics[:MAX_POSTS]:

        message=(
            f"📹 {t['title']}\n"
            f"🔗 {t['link']}\n"
            f"👤 Publicado por: {t['author']}"
        )

        send_telegram(message)

        published.add(t["hash"])

        count+=1

        print("Publicado:",t["title"])

        time.sleep(2)

    save_json(PUBLISHED_FILE,published)

    save_state(state)

    print("Publicados:",count)


if __name__=="__main__":
    main()
