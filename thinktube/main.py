from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input, ListView, ListItem, Label
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
import subprocess
import yt_dlp

THINKTUBE_ASCII = r"""
████████╗██╗  ██╗██╗███╗   ██╗██╗  ██╗████████╗██╗   ██╗██████╗ ███████╗
╚══██╔══╝██║  ██║██║████╗  ██║██║ ██╔╝╚══██╔══╝██║   ██║██╔══██╗██╔════╝
   ██║   ███████║██║██╔██╗ ██║█████╔╝    ██║   ██║   ██║██████╔╝█████╗  
   ██║   ██╔══██║██║██║╚██╗██║██╔═██╗    ██║   ██║   ██║██╔══██╗██╔══╝  
   ██║   ██║  ██║██║██║ ╚████║██║  ██╗   ██║   ╚██████╔╝██████╔╝███████╗
   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═════╝ ╚══════╝
"""

class TPVid(App):
    CSS = """
    Screen {
        background: #0a0a0a;
    }

    #header {
        color: #5aa9ff;
        text-align: center;
        padding-bottom: 1;
    }

    #subtitle {
        color: #5aa9ff;
        text-align: center;
    }

    #divider {
        text-align: center;
        color: #222222;
        padding-bottom: 1;
    }

    #live {
        text-align: center;
        color: #cc0000;
        padding-bottom: 1;
    }

    Input {
        border: round #222222;
        margin: 1 4;
    }

    ListView {
        border: round #222222;
        margin: 1 4;
        height: 60%;
    }

    Footer {
        background: #111111;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(THINKTUBE_ASCII, id="header")
        yield Static("Media Engine Mode", id="subtitle")
        yield Static("────────────────────────────────────────", id="divider")
        yield Static("● LIVE", id="live")

        self.search = Input(placeholder="Search YouTube and press ENTER")
        yield self.search

        self.results = ListView()
        yield self.results

        yield Footer()

    def on_input_submitted(self, event: Input.Submitted):
        query = event.value.strip()
        if not query:
            return

        self.results.clear()

        ydl_opts = {"quiet": True, "extract_flat": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch5:{query}", download=False)

        self.current_results = []

        for entry in info["entries"]:
            title = entry["title"]
            url = entry["url"]
            self.current_results.append((title, url))
            self.results.append(ListItem(Label(title)))

    def on_list_view_selected(self, event):
        index = self.results.index(event.item)
        title, url = self.current_results[index]

        subprocess.Popen([
            "mpv",
            "--force-window=yes",
            "--geometry=960x540+100+100",
            f"https://youtube.com/watch?v={url}"
        ])

    BINDINGS = [
        ("q", "quit", "Quit")
    ]


if __name__ == "__main__":
    TPVid().run()
