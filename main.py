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
            background_color=(0, 0, 0, 1), foreground_color=(0, 1, 0, 1)
        )
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

        self.gmail_status = Label(text="Accounts file: load nahi hui",
                                  size_hint_y=None, height=30, color=(0.8,0.8,0.8,1))
        self.add_widget(self.gmail_status)

        b1 = Button(text="SELECT ACCOUNTS.TXT", size_hint_y=None, height=60,
                    background_color=(0.2, 0.4, 0.8, 1))
        b1.bind(on_press=self.pick_accounts); self.add_widget(b1)

        self.cookie_status = Label(text="Cookies file: load nahi hui",
                                   size_hint_y=None, height=30, color=(0.8,0.8,0.8,1))
        self.add_widget(self.cookie_status)

        b2 = Button(text="SELECT COOKIES.TXT", size_hint_y=None, height=60,
                    background_color=(0.2, 0.4, 0.8, 1))
        b2.bind(on_press=self.pick_cookies); self.add_widget(b2)

        b3 = Button(text="REFRESH COUNT", size_hint_y=None, height=50,
                    background_color=(0, 0.6, 0, 1))
        b3.bind(on_press=self.refresh_count); self.add_widget(b3)

        Clock.schedule_once(lambda dt: self.refresh_count(None), 0.3)

    def pick_accounts(self, i):
        if not FILECHOOSER_OK:
            self.log_callback("[ERROR] File chooser available nahi."); return
        try:
            filechooser.open_file(on_selection=self._acc,
                                  filters=[("Text files", "*.txt")])
        except Exception as e:
            self.log_callback(f"[ERROR] {e}")

    def _acc(self, sel):
        if not sel: return
        if kashif_bot.copy_file_to_app(sel[0], kashif_bot.ACCOUNTS_FILE):
            self.log_callback(f"[ACCOUNTS] Load: {os.path.basename(sel[0])}")
            self.refresh_count(None)

    def pick_cookies(self, i):
        if not FILECHOOSER_OK:
            self.log_callback("[ERROR] File chooser available nahi."); return
        try:
            filechooser.open_file(on_selection=self._ck,
                                  filters=[("Text files", "*.txt")])
        except Exception as e:
            self.log_callback(f"[ERROR] {e}")

    def _ck(self, sel):
        if not sel: return
        if kashif_bot.copy_file_to_app(sel[0], kashif_bot.COOKIES_FILE):
            self.log_callback(f"[COOKIES] Load: {os.path.basename(sel[0])}")
            self.refresh_count(None)

    def refresh_count(self, i):
        a, c = kashif_bot.get_counts()
        self.count_label.text = f"Loaded: {a} Accounts | {c} Cookies"
        self.gmail_status.text = f"Accounts file: {'OK' if a > 0 else 'khali'}"
        self.cookie_status.text = f"Cookies file: {'OK' if c > 0 else 'khali'}"


class ScanProgramsPanel(BoxLayout):
    def __init__(self, log_callback, runner, **kwargs):
        super().__init__(orientation='vertical', spacing=8, padding=8, **kwargs)
        self.log_callback = log_callback
        self.runner = runner
        self.scanned_url = None

        self.add_widget(Label(text="Target URL:", size_hint_y=None, height=28))
        self.url_input = TextInput(
            multiline=False, size_hint_y=None, height=50,
            background_color=(0.1, 0.1, 0.1, 1), foreground_color=(1, 1, 1, 1))
        self.add_widget(self.url_input)

        self.scan_btn = Button(text="SCAN / ANALYZE", size_hint_y=None, height=55,
                               background_color=(0.8, 0.6, 0, 1))
        self.scan_btn.bind(on_press=self.do_scan)
        self.add_widget(self.scan_btn)

        self.results_box = TextInput(
            readonly=True, multiline=True, size_hint_y=None, height=180,
            background_color=(0.05, 0.05, 0.15, 1),
            foreground_color=(1, 1, 0.5, 1), font_size=13)
        self.add_widget(self.results_box)

        self.prog_header = Label(text="Programs (pehle SCAN karein)",
                                 size_hint_y=None, height=28,
                                 color=(0.6, 0.6, 0.6, 1), bold=True)
        self.add_widget(self.prog_header)

        scroll = ScrollView()
        self.inner = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None)
        self.inner.bind(minimum_height=self.inner.setter('height'))
        self.prog_buttons = []

        for name, func in kashif_bot.PROGRAMS:
            row = BoxLayout(size_hint_y=None, height=55, spacing=5)
            row.add_widget(Label(text=name, size_hint_x=0.7))
            btn = Button(text="START", size_hint_x=0.3,
                         background_color=(0, 0.5, 0, 1))
            btn.disabled = True
            btn.bind(on_press=lambda x, f=func, n=name: self.start(f, n))
            row.add_widget(btn)
            self.inner.add_widget(row)
            self.prog_buttons.append(btn)

        scroll.add_widget(self.inner); self.add_widget(scroll)

    def do_scan(self, i):
        url = self.url_input.text.strip()
        if not url:
            self.log_callback("[ERROR] Pehle URL daalein."); return
        self.scan_btn.disabled = True; self.scan_btn.text = "SCANNING..."
        self.results_box.text = ""

        def worker():
            res = kashif_bot.scan_reviewer(url)
            def update(dt):
                if res["ok"]:
                    self.results_box.text = (
                        f"=== SCAN RESULTS ===\n"
                        f"Reviews      : {res['reviews']}\n"
                        f"Photos       : {res['photos']}\n"
                        f"Level        : {res['level']}\n"
                        f"Violations   : {len(res['violations'])}\n"
                        f"Phone leaks  : {len(res['phones'])}\n"
                        f"Email leaks  : {len(res['emails'])}\n"
                        f"Account Age  : {res['age']}\n"
                        f"Ban Chance   : {res['ban_chance']}%\n"
                        f"Remove Chance: {res['remove_chance']}%\n"
                    )
                    self.scanned_url = url
                    self.prog_header.text = "Programs (ready - START dabayein)"
                    self.prog_header.color = (0, 1, 0, 1)
                    for b in self.prog_buttons: b.disabled = False
                else:
                    self.results_box.text = "Scan fail. URL check karein."
                self.scan_btn.disabled = False; self.scan_btn.text = "SCAN / ANALYZE"
            Clock.schedule_once(update, 0)
        threading.Thread(target=worker, daemon=True).start()

    def start(self, func, name):
        if not self.scanned_url:
            self.log_callback("[ERROR] Pehle SCAN karein."); return
        self.runner(func, self.scanned_url, name)


class KashifApp(App):
    def build(self):
        self.title = "Kashif Master Bot"
        self.logs_panel = LogsPanel()
        tabs = TabbedPanel(do_default_tab=False)

        t1 = TabbedPanelItem(text="Input")
        t1.add_widget(InputPanel(log_callback=self.logs_panel.log))
        tabs.add_widget(t1)

        t2 = TabbedPanelItem(text="Scan & Programs")
        t2.add_widget(ScanProgramsPanel(log_callback=self.logs_panel.log,
                                        runner=self.run_command))
        tabs.add_widget(t2)

        t3 = TabbedPanelItem(text="Logs")
        t3.add_widget(self.logs_panel)
        tabs.add_widget(t3)

        return tabs

    def run_command(self, func, url, name):
        self.logs_panel.log(f"\n=== {name} START ===")
        def w():
            try:
                kashif_bot.run_command(func, url, self.logs_panel.log)
                self.logs_panel.log(f"=== {name} DONE ===")
            except Exception as e:
                self.logs_panel.log(f"[ERROR] {name}: {e}")
        threading.Thread(target=w, daemon=True).start()


if __name__ == "__main__":
    KashifApp().run()
