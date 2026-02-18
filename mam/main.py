import os
import json
import subprocess
from pathlib import Path
from threading import Thread

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Button,
    Static,
    ListView,
    ListItem,
    Label,
    Input,
    LoadingIndicator,
)
from textual.reactive import reactive

MOVIE_EXT = {".mp4", ".mkv", ".avi", ".mov", ".webm"}
MUSIC_EXT = {".mp3", ".flac", ".wav", ".ogg"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

EXCLUDED_DIRS = {".git", "node_modules", "__pycache__"}
HOME_DIR = Path.home()
CACHE_FILE = HOME_DIR / ".mam_cache.json"

def scan_media():
    movies, music, images = [], [], []

    for root, dirs, files in os.walk(HOME_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for file in files:
            ext = Path(file).suffix.lower()
            full_path = str(Path(root) / file)

            if ext in MOVIE_EXT:
                movies.append(full_path)
            elif ext in MUSIC_EXT:
                music.append(full_path)
            elif ext in IMAGE_EXT:
                images.append(full_path)

    return {
        "Movies": sorted(movies),
        "Music": sorted(music),
        "Images": sorted(images),
    }

def format_file(path, compact=False):
    p = Path(path)
    if compact:
        return p.name
    size = p.stat().st_size / (1024 * 1024)
    return f"{p.name:<40} {size:>6.1f} MB"

class MAM(App):

    CSS = """
    Screen {
        background: #1a1a1a;
        color: #d4af37;
    }

    #header_bar {
        content-align: center middle;
        text-align: center;
        padding: 2 0;
        border-bottom: round #2a2a2a;
    }

    #divider {
        height: 1;
        background: #d4af37;
        margin: 0 25;
    }

    #sidebar {
        width: 25%;
        background: #151515;
        border-right: round #2a2a2a;
        padding: 2;
    }

    #main_panel {
        width: 75%;
        background: #101010;
        padding: 2;
    }

    Button {
        margin: 1 0;
        border: round #2a2a2a;
        content-align: center middle;
    }

    Button:hover {
        background: #2a2a2a;
        color: white;
    }

    ListView {
        border: round #2a2a2a;
    }

    ListView > ListItem {
        content-align: left middle;
    }

    ListView > ListItem.--highlight {
        background: #2a2a2a;
        color: white;
    }

    Input {
        border: round #2a2a2a;
        margin-bottom: 1;
    }

    #footer_bar {
        border-top: round #2a2a2a;
        content-align: center middle;
        color: #888888;
        padding: 1;
    }
    """

    current_category = reactive("Movies")
    search_term = reactive("")
    sort_mode = reactive("name")
    compact_mode = reactive(False)

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("/", "focus_search", "Search"),
        ("s", "toggle_sort", "Sort"),
        ("c", "toggle_compact", "Compact"),
        ("escape", "clear_search", "Clear"),
    ]

    def compose(self) -> ComposeResult:

        yield Static(
"""
███╗   ███╗ █████╗ ███╗   ███╗
████╗ ████║██╔══██╗████╗ ████║
██╔████╔██║███████║██╔████╔██║
██║╚██╔╝██║██╔══██║██║╚██╔╝██║
██║ ╚═╝ ██║██║  ██║██║ ╚═╝ ██║
╚═╝     ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝

M.A.M
Music And Movies
""",
            id="header_bar",
            expand=True
        )

        yield Static("", id="divider")

        with Horizontal():

            with Vertical(id="sidebar"):
                self.movies_btn = Button("Movies", id="movies")
                self.music_btn = Button("Music", id="music")
                self.images_btn = Button("Images", id="images")
                yield self.movies_btn
                yield self.music_btn
                yield self.images_btn
                yield Button("Refresh", id="refresh")
                yield Button("Exit", id="quit")

            with Vertical(id="main_panel"):
                self.search_input = Input(placeholder="Search...")
                yield self.search_input
                self.loader = LoadingIndicator()
                yield self.loader
                self.file_list = ListView()
                yield self.file_list

        self.footer_bar = Static("", id="footer_bar")
        yield self.footer_bar

    # ----- Logic (unchanged, stable) -----

    def on_mount(self):
        if CACHE_FILE.exists():
            self.load_cache()
            self.finish_loading()
        else:
            self.loader.display = True
            Thread(target=self.full_scan).start()

    def load_cache(self):
        with open(CACHE_FILE) as f:
            self.media_data = json.load(f)

    def save_cache(self):
        with open(CACHE_FILE, "w") as f:
            json.dump(self.media_data, f)

    def full_scan(self):
        self.media_data = scan_media()
        self.save_cache()
        self.call_from_thread(self.finish_loading)

    def finish_loading(self):
        self.loader.display = False
        self.update_counts()
        self.update_footer()
        self.update_category(self.current_category)

    def update_counts(self):
        self.movies_btn.label = f"Movies ({len(self.media_data['Movies'])})"
        self.music_btn.label = f"Music ({len(self.media_data['Music'])})"
        self.images_btn.label = f"Images ({len(self.media_data['Images'])})"

    def update_footer(self):
        self.footer_bar.update(
            f"Sort: {self.sort_mode.upper()} | "
            f"Compact: {'ON' if self.compact_mode else 'OFF'} | "
            "Press / Search | s Sort | c Compact | q Quit"
        )

    def update_category(self, category):
        self.current_category = category
        self.refresh_file_list()

    def refresh_file_list(self):
        self.file_list.clear()
        files = self.media_data.get(self.current_category, [])

        if self.sort_mode == "size":
            files = sorted(files, key=lambda x: Path(x).stat().st_size, reverse=True)
        else:
            files = sorted(files)

        for file in files:
            if self.search_term.lower() in Path(file).name.lower():
                item = ListItem(Label(format_file(file, self.compact_mode)))
                item.file_path = file
                self.file_list.append(item)

    def action_toggle_sort(self):
        self.sort_mode = "size" if self.sort_mode == "name" else "name"
        self.update_footer()
        self.refresh_file_list()

    def action_toggle_compact(self):
        self.compact_mode = not self.compact_mode
        self.update_footer()
        self.refresh_file_list()

    def action_focus_search(self):
        self.search_input.focus()

    def action_clear_search(self):
        self.search_term = ""
        self.search_input.value = ""
        self.refresh_file_list()

    def on_button_pressed(self, event):
        if event.button.id == "movies":
            self.update_category("Movies")
        elif event.button.id == "music":
            self.update_category("Music")
        elif event.button.id == "images":
            self.update_category("Images")
        elif event.button.id == "refresh":
            self.loader.display = True
            Thread(target=self.full_scan).start()
        elif event.button.id == "quit":
            self.exit()

    def on_input_changed(self, event):
        self.search_term = event.value
        self.refresh_file_list()

    def on_list_view_selected(self, event):
        file_path = getattr(event.item, "file_path", None)
        if file_path:
            subprocess.Popen(["gio", "open", file_path])

if __name__ == "__main__":
    MAM().run()
