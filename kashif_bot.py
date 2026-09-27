import os
import requests

try:
    from android.storage import app_storage_path
    BASE_DIR = app_storage_path()
except Exception:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.txt")
COOKIES_FILE = os.path.join(BASE_DIR, "cookies.txt")

SERVER_URL = "http://127.0.0.1:5000"

_LOG = print

def set_logger(cb):
    global _LOG
    _LOG = cb

def log(msg, level="info"):
    prefix = {"success": "[+] ", "error": "[-] ", "warning": "[!] ", "info": "[*] "}.get(level, "")
    _LOG(prefix + str(msg))


def copy_file_to_app(src, dest):
    import shutil
    if not src or not os.path.exists(src):
        return False
    shutil.copy(src, dest)
    return True


def load_accounts():
    accounts = []
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if ":" in line and not line.startswith("#"):
                    email, password = line.split(":", 1)
                    accounts.append({"email": email.strip(), "password": password.strip()})
    return accounts


def load_all_cookies():
    """Pehla cookie set return karta hai (dict)."""
    all_cookies = []
    if not os.path.exists(COOKIES_FILE):
        return all_cookies
    with open(COOKIES_FILE, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    if "# =====" in content:
        for block in content.split("# ====="):
            block = block.strip()
            if not block or "ACCOUNT" not in block:
                continue
            cookies = {}
            for line in block.split("\n"):
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    cookies[k.strip()] = v.strip()
            if cookies:
                all_cookies.append(cookies)
    else:
        cookies = {}
        for line in content.split("\n"):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                cookies[k.strip()] = v.strip()
        if cookies:
            all_cookies.append(cookies)
    return all_cookies


def get_counts():
    return len(load_accounts()), len(load_all_cookies())


def test_server(log_cb):
    set_logger(log_cb)
    log("Server test shuru...")
    try:
        r = requests.get(f"{SERVER_URL}/ping", timeout=5)
        if r.status_code == 200:
            log(f"Server OK: {r.json().get('msg')}", "success")
            return True
        else:
            log(f"Server HTTP {r.status_code}", "error")
    except Exception as e:
        log(f"Server connect nahi hua: {e}", "error")
        log("Termux mein 'python server.py' chala rahe hain?", "warning")
    return False


def test_firefox(log_cb):
    set_logger(log_cb)
    log("Firefox test shuru (10-30 sec lagenge)...")
    try:
        r = requests.get(f"{SERVER_URL}/test", timeout=60)
        data = r.json()
        for line in data.get("logs", []):
            log(line, "info" if "OK" in line else "warning")
        return data.get("ok", False)
    except Exception as e:
        log(f"Firefox test fail: {e}", "error")
        return False


def run_command(cmd_name, url, log_cb):
    """APK se Termux server par command bhejta hai."""
    set_logger(log_cb)

    if not url:
        log("URL khali hai!", "error")
        return

    # Cookies load
    ck_sets = load_all_cookies()
    if not ck_sets:
        log("Cookies nahi milin — bina cookie try", "warning")
        cookies = {}
    else:
        cookies = ck_sets[0]  # pehla set use karo
        log(f"Cookies loaded: {len(cookies)} keys", "info")

    # Server check
    if not test_server(log_cb):
        return

    # Endpoint chuno
    if "SCAN" in cmd_name.upper():
        endpoint = f"{SERVER_URL}/scan"
    else:
        endpoint = f"{SERVER_URL}/report"

    log(f"Sending: {endpoint}", "info")
    log(f"URL: {url}", "info")

    try:
        r = requests.post(
            endpoint,
            json={"url": url, "cookies": cookies, "command": cmd_name},
            timeout=120,
        )
        data = r.json()
        for line in data.get("logs", []):
            log(line, "info")
        if data.get("ok"):
            log("Command complete", "success")
        else:
            log("Command fail", "error")
    except Exception as e:
        log(f"Error: {e}", "error")


PROGRAMS = [
    ("Scan URL (Firefox)", "SCAN"),
    ("Report Attempt", "REPORT"),
    ("Report + Screenshot", "REPORT"),
    ("Full Auto", "REPORT"),
]
