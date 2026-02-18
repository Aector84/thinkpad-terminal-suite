import subprocess
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, ListView, ListItem, Label
from textual.reactive import reactive


ASCII_HEADER = r"""
████████╗██╗  ██╗██╗███╗   ██╗██╗  ██╗██████╗  █████╗ ██████╗ 
╚══██╔══╝██║  ██║██║████╗  ██║██║ ██╔╝██╔══██╗██╔══██╗██╔══██╗
   ██║   ███████║██║██╔██╗ ██║█████╔╝ ██████╔╝███████║██║  ██║
   ██║   ██╔══██║██║██║╚██╗██║██╔═██╗ ██╔═══╝ ██╔══██║██║  ██║
   ██║   ██║  ██║██║██║ ╚████║██║  ██╗██║     ██║  ██║██████╔╝
   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝╚═════╝ 
"""


class ThinkPadCommander(App):

    CSS = """
    Screen {
        background: #1a1a1a;
        color: #cccccc;
    }

    #header {
        color: #cc0000;
        text-align: center;
        padding-top: 1;
    }

    #subheader {
        color: #cc0000;
        text-align: center;
        padding-bottom: 1;
        border-bottom: heavy #333333;
    }

    #left {
        width: 50%;
        border: round #333333;
        padding: 1;
    }

    #right {
        width: 50%;
        border: round #333333;
        padding: 1;
    }

    ListView > ListItem.--highlight {
        background: #333333;
        color: white;
    }

    #footer {
        border-top: heavy #333333;
        padding: 1;
        text-align: center;
        color: #888888;
    }
    """

    current_path = reactive(Path.home())

    BINDINGS = [
        ("backspace", "up", "Up"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Static(ASCII_HEADER, id="header")
        yield Static("COMMANDER", id="subheader")

        with Horizontal():
            with Vertical(id="left"):
                self.path_display = Static(str(self.current_path))
                yield self.path_display
                self.list_view = ListView()
                yield self.list_view

            with Vertical(id="right"):
                self.info_panel = Static("Select a file or directory")
                yield self.info_panel

        yield Static(
            "ENTER Open | BACKSPACE Up | q Quit",
            id="footer"
        )

    def on_mount(self):
        self.refresh_listing()

    def refresh_listing(self):
        self.path_display.update(str(self.current_path))
        self.list_view.clear()

        try:
            entries = sorted(
                self.current_path.iterdir(),
                key=lambda x: (not x.is_dir(), x.name.lower())
            )
        except PermissionError:
            return

        for entry in entries:
            label = entry.name + ("/" if entry.is_dir() else "")
            item = ListItem(Label(label))
            item.file_path = entry
            self.list_view.append(item)

    def on_list_view_highlighted(self, event: ListView.Highlighted):
        path = getattr(event.item, "file_path", None)
        if not path:
            return

        if path.is_dir():
            try:
                count = len(list(path.iterdir()))
            except:
                count = "?"
            info = f"[DIR]\n\n{path}\n\nItems: {count}"
        else:
            size = path.stat().st_size / 1024
            info = f"[FILE]\n\n{path}\n\nSize: {size:.1f} KB"

        self.info_panel.update(info)

    def on_list_view_selected(self, event: ListView.Selected):
        path = getattr(event.item, "file_path", None)
        if not path:
            return

        if path.is_dir():
            self.current_path = path
            self.refresh_listing()
        else:
            subprocess.Popen(["gio", "open", str(path)])

    def action_up(self):
        if self.current_path.parent != self.current_path:
            self.current_path = self.current_path.parent
            self.refresh_listing()


if __name__ == "__main__":
    ThinkPadCommander().run()
