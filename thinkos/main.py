import subprocess
from textual.app import App, ComposeResult
from textual.widgets import Static, ListView, ListItem, Label


ASCII_BOOT = r"""
████████╗██╗  ██╗██╗███╗   ██╗██╗  ██╗ ██████╗ ███████╗
╚══██╔══╝██║  ██║██║████╗  ██║██║ ██╔╝██╔═══██╗██╔════╝
   ██║   ███████║██║██╔██╗ ██║█████╔╝ ██║   ██║███████╗
   ██║   ██╔══██║██║██║╚██╗██║██╔═██╗ ██║   ██║╚════██║
   ██║   ██║  ██║██║██║ ╚████║██║  ██╗╚██████╔╝███████║
   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝

                 THINKOS
"""


MENU_OPTIONS = [
    ("📁 Commander", "tpc"),
    ("🎬 Media", "filmz"),
    ("🧠 Dev Dashboard", "tpdev"),
    ("📊 System Monitor (soon)", None),
    ("🔐 Vault (soon)", None),
    ("🚪 Exit", "exit"),
]


class ThinkOS(App):

    CSS = """
    Screen {
        background: #111111;
        color: #cccccc;
        content-align: center middle;
    }

    #boot {
        color: #cc0000;
        text-align: center;
        padding: 2;
        border-bottom: heavy #333333;
    }

    ListView {
        padding: 2;
        border: round #333333;
        width: 60;
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
        yield Static(ASCII_BOOT, id="boot")

        self.menu = ListView()
        yield self.menu

        yield Static("ENTER Launch | q Quit", id="footer")

    def on_mount(self):
        # Populate menu AFTER mount (required for your Textual version)
        for text, _ in MENU_OPTIONS:
            self.menu.append(ListItem(Label(text)))

    def on_list_view_selected(self, event: ListView.Selected):
        index = self.menu.index(event.item)
        _, command = MENU_OPTIONS[index]

        if command == "exit":
            self.exit()
        elif command:
            self.suspend()
            subprocess.run(command)
            self.resume()


if __name__ == "__main__":
    ThinkOS().run()
