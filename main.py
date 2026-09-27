import os
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.clock import Clock

import kashif_bot

try:
    from plyer import filechooser
    FILECHOOSER_OK = True
except Exception:
    FILECHOOSER_OK = False


class LogsPanel(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.log_box = TextInput(
            readonly=True, multiline=True, font_size=12,
            background_color=(0, 0, 0, 1), foreground_color=(0, 1, 0, 1))
        s = ScrollView(); s.add_widget(self.log_box); self.add_widget(s)

    def log(self, msg):
        def _u(dt): self.log_box.text += str(msg) + "\n"
        Clock.schedule_once(_u, 0)


class InputPanel(BoxLayout):
    def __init__(self, log_callback, **kwargs):
        super().__init__(orientation='vertical', spacing=10, padding=12, **kwargs)
        self.log_callback = log_callback

        self.count_label = Label(text="", size_hint_y=None, height=35,
                                 color=(1, 1, 0, 1), bold=True)
        self.add_widget(self.count_label)

        self.add_widget(Label(text="accounts.txt", size_hint_y=None, height=25))
        b1 = Button(text="SELECT ACCOUNTS.TXT", size_hint_y=None, height=55,
                    background_color=(0.2, 0.4, 0.8, 1))
        b1.bind(on_press=self.pick_acc); self.add_widget(b1)

        self.add_widget(Label(text="cookies.txt", size_hint_y=None, height=25))
        b2 = Button(text="SELECT COOKIES.TXT", size_hint_y=None, height=55,
                    background_color=(0.2, 0.4, 0.8, 1))
        b2.bind(on_press=self.pick_ck); self.add_widget(b2)

        b3 = Button(text="REFRESH", size_hint_y=None, height=45,
                    background_color=(0, 0.6, 0, 1))
        b3.bind(on_press=self.refresh); self.add_widget(b3)

        b4 = Button(text="TEST SERVER", size_hint_y=None, height=50,
                    background_color=(0.6, 0.3, 0, 1))
        b4.bind(on_press=self.test_srv); self.add_widget(b4)

        b5 = Button(text="TEST FIREFOX", size_hint_y=None, height=50,
                    background_color=(0.6, 0.3, 0, 1))
        b5.bind(on_press=self.test_ff); self.add_widget(b5)

        Clock.schedule_once(lambda dt: self.refresh(None), 0.3)

    def pick_acc(self, i):
        if not FILECHOOSER_OK: return
        try: filechooser.open_file(on_selection=self._acc,
                                   filters=[("Text files", "*.txt")])
        except Exception as e: self.log_callback(f"[ERROR] {e}")

    def _acc(self, sel):
        if not sel: return
        if kashif_bot.copy_file_to_app(sel[0], kashif_bot.ACCOUNTS_FILE):
            self.log_callback(f"[ACCOUNTS] Loaded: {os.path.basename(sel[0])}")
            self.refresh(None)

    def pick_ck(self, i):
        if not FILECHOOSER_OK: return
        try: filechooser.open_file(on_selection=self._ck,
                                   filters=[("Text files", "*.txt")])
        except Exception as e: self.log_callback(f"[ERROR] {e}")

    def _ck(self, sel):
        if not sel: return
        if kashif_bot.copy_file_to_app(sel[0], kashif_bot.COOKIES_FILE):
            self.log_callback(f"[COOKIES] Loaded: {os.path.basename(sel[0])}")
            self.refresh(None)

    def refresh(self, i):
        a, c = kashif_bot.get_counts()
        self.count_label.text = f"Accounts: {a} | Cookies: {c}"

    def test_srv(self, i):
        def w(): kashif_bot.test_server(self.log_callback)
        threading.Thread(target=w, daemon=True).start()

    def test_ff(self, i):
        def w(): kashif_bot.test_firefox(self.log_callback)
        threading.Thread(target=w, daemon=True).start()


class CommandsPanel(BoxLayout):
    def __init__(self, log_callback, runner, **kwargs):
        super().__init__(orientation='vertical', spacing=8, padding=8, **kwargs)
        self.log_callback = log_callback
        self.runner = runner

        self.add_widget(Label(text="Target URL:", size_hint_y=None, height=28))
        self.url_input = TextInput(multiline=False, size_hint_y=None, height=50,
                                   background_color=(0.1, 0.1, 0.1, 1),
                                   foreground_color=(1, 1, 1, 1))
        self.add_widget(self.url_input)

        scroll = ScrollView()
        self.inner = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None)
        self.inner.bind(minimum_height=self.inner.setter('height'))

        for name, cmd in kashif_bot.PROGRAMS:
            row = BoxLayout(size_hint_y=None, height=55, spacing=5)
            row.add_widget(Label(text=name, size_hint_x=0.65))
            btn = Button(text="RUN", size_hint_x=0.35,
                         background_color=(0, 0.6, 0, 1))
            btn.bind(on_press=lambda x, c=cmd, n=name: self.start(c, n))
            row.add_widget(btn)
            self.inner.add_widget(row)

        scroll.add_widget(self.inner); self.add_widget(scroll)

    def start(self, cmd, name):
        url = self.url_input.text.strip()
        if not url:
            self.log_callback("[ERROR] URL daalein"); return
        self.runner(cmd, url, name)


class KashifApp(App):
    def build(self):
        self.title = "Kashif Bot"
        self.logs = LogsPanel()
        tabs = TabbedPanel(do_default_tab=False)

        t1 = TabbedPanelItem(text="Input")
        t1.add_widget(InputPanel(log_callback=self.logs.log))
        tabs.add_widget(t1)

        t2 = TabbedPanelItem(text="Commands")
        t2.add_widget(CommandsPanel(log_callback=self.logs.log,
                                    runner=self.runner))
        tabs.add_widget(t2)

        t3 = TabbedPanelItem(text="Logs")
        t3.add_widget(self.logs)
        tabs.add_widget(t3)

        return tabs

    def runner(self, cmd, url, name):
        self.logs.log(f"\n=== {name} START ===")
        def w():
            try:
                kashif_bot.run_command(cmd, url, self.logs.log)
                self.logs.log(f"=== {name} DONE ===")
            except Exception as e:
                self.logs.log(f"[ERROR] {e}")
        threading.Thread(target=w, daemon=True).start()


if __name__ == "__main__":
    KashifApp().run()
