import requests
import subprocess
import asyncio
import os
import hashlib
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, ListView, ListItem, Label


VERSION = "1.3"
SUBREDDIT = "thinkpad"
USER_AGENT = "thinkpad-terminal-app"
CACHE_DIR = "/tmp/tpr_cache"
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp")


ASCII_HEADER = r"""
████████╗██╗  ██╗██╗███╗   ██╗██╗  ██╗██████╗  █████╗ ██████╗ 
╚══██╔══╝██║  ██║██║████╗  ██║██║ ██╔╝██╔══██╗██╔══██╗██╔══██╗
   ██║   ███████║██║██╔██╗ ██║█████╔╝ ██████╔╝███████║██║  ██║
   ██║   ██╔══██║██║██║╚██╗██║██╔═██╗ ██╔═══╝ ██╔══██║██║  ██║
   ██║   ██║  ██║██║██║ ╚████║██║  ██╗██║     ██║  ██║██████╔╝
   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝╚═════╝
"""


def ensure_cache():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


def cache_image(url):
    ensure_cache()
    filename = hashlib.md5(url.encode()).hexdigest() + ".img"
    path = os.path.join(CACHE_DIR, filename)

    if os.path.exists(path):
        return path

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(path, "wb") as f:
                f.write(response.content)
            return path
    except:
        return None

    return None


def render_image(path, width):
    try:
        width = max(20, width)
        height = int(width * 0.5)
        output = subprocess.check_output(
            ["chafa", f"--size={width}x{height}", path],
            text=True
        )
        return output
    except:
        return "[Failed to render image]"


def fetch_comments(permalink):
    try:
        url = f"https://reddit.com{permalink}.json"
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        comments = []
        for comment in data[1]["data"]["children"][:5]:
            if comment["kind"] == "t1":
                body = comment["data"]["body"]
                comments.append(body[:300])

        return "\n\n---\n\n".join(comments) if comments else "No comments."
    except:
        return "Failed to load comments."


def fetch_posts():
    url = f"https://www.reddit.com/r/{SUBREDDIT}/hot.json?limit=25"
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        posts = data["data"]["children"]

        results = []
        for post in posts:
            p = post["data"]

            post_url = p.get("url", "")
            preview_url = None
            is_image = post_url.lower().endswith(IMAGE_EXTENSIONS)

            if not is_image and "preview" in p:
                try:
                    preview_url = p["preview"]["images"][0]["source"]["url"]
                    preview_url = preview_url.replace("&amp;", "&")
                    is_image = True
                except:
                    pass

            results.append({
                "title": p["title"],
                "author": p["author"],
                "score": p["score"],
                "comments": p["num_comments"],
                "url": "https://reddit.com" + p["permalink"],
                "permalink": p["permalink"],
                "external_url": preview_url or post_url,
                "selftext": p.get("selftext", ""),
                "is_image": is_image
            })

        return results
    except:
        return []


class RedditTUI(App):

    image_mode = True
    comment_mode = False

    CSS = """
    Screen {
        background: #111111;
        color: #cccccc;
    }

    #header {
        color: #5aa9ff;
        text-align: center;
        padding: 1 0;
    }

    #subtitle {
        color: #5aa9ff;
        text-align: center;
        padding-bottom: 1;
        border-bottom: heavy #333333;
    }

    #main {
        height: 1fr;
    }

    #left {
        width: 50%;
        height: 1fr;
        border: round #333333;
        padding: 1;
    }

    #right {
        width: 50%;
        height: 1fr;
        border: round #333333;
        padding: 1;
    }

    ListView {
        height: 1fr;
    }

    ListView > ListItem.--highlight {
        background: #333333;
        color: white;
    }

    #footer {
        border-top: heavy #333333;
        padding: 1;
        text-align: center;
        color: #777777;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(ASCII_HEADER, id="header")
        yield Static(f"REDDIT — r/{SUBREDDIT}", id="subtitle")

        with Horizontal(id="main"):
            with Vertical(id="left"):
                self.list_view = ListView()
                yield self.list_view

            with Vertical(id="right"):
                self.preview = Static("Loading...", expand=True, markup=False)
                yield self.preview

        yield Static(
            f"tpr v{VERSION} | ENTER Open | r Refresh | i Images | c Comments | q Quit",
            id="footer"
        )

    async def on_mount(self):
        await asyncio.sleep(0.5)
        self.load_posts()

    def load_posts(self):
        self.list_view.clear()
        self.posts = fetch_posts()

        for post in self.posts:
            prefix = "[IMG] " if post["is_image"] else ""
            item = ListItem(Label(prefix + post["title"]))
            item.post_data = post
            self.list_view.append(item)

        self.preview.update("Select a post")

    def render_preview(self, post):
        preview_text = (
            f"{post['title']}\n\n"
            f"Author: {post['author']}\n"
            f"Score: {post['score']}\n"
            f"Comments: {post['comments']}\n\n"
        )

        if self.comment_mode:
            preview_text += fetch_comments(post["permalink"])
        elif post["is_image"] and self.image_mode:
            image_path = cache_image(post["external_url"])
            if image_path:
                pane_width = max(self.preview.size.width - 4, 20)
                preview_text += render_image(image_path, pane_width)
        elif post["selftext"]:
            preview_text += post["selftext"][:800]

        return preview_text

    def on_list_view_highlighted(self, event):
        post = getattr(event.item, "post_data", None)
        if post:
            self.preview.update(self.render_preview(post))

    def on_resize(self, event):
        if self.list_view.highlighted_child:
            post = getattr(self.list_view.highlighted_child, "post_data", None)
            if post:
                self.preview.update(self.render_preview(post))

    def key_i(self):
        self.image_mode = not self.image_mode
        self.preview.update("Image mode toggled.")

    def key_c(self):
        self.comment_mode = not self.comment_mode
        self.preview.update("Comment mode toggled.")

    def key_r(self):
        self.load_posts()

    def key_q(self):
        self.exit()

    def on_list_view_selected(self, event):
        post = getattr(event.item, "post_data", None)
        if post:
            subprocess.Popen(["xdg-open", post["url"]])


if __name__ == "__main__":
    RedditTUI().run()
