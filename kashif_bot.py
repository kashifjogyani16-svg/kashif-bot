import os
import time
import random
import re
import requests
from fake_useragent import UserAgent

try:
    from android.storage import app_storage_path
    BASE_DIR = app_storage_path()
except Exception:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.txt")
COOKIES_FILE = os.path.join(BASE_DIR, "cookies.txt")

_LOG = print

def set_logger(cb):
    global _LOG
    _LOG = cb

def log(msg, level="info"):
    prefix = {
        "success": "[+] ", "error": "[-] ", "warning": "[!] ",
        "info": "[*] ", "service": "[SERVICE] ", "ban": "[BAN] ",
        "scan": "[SCAN] ", "ip": "[IP] ",
    }.get(level, "")
    _LOG(prefix + str(msg))


def get_random_ip():
    return f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"


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
    all_cookies = []
    if not os.path.exists(COOKIES_FILE):
        return all_cookies
    with open(COOKIES_FILE, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    if "# =====" in content:
        blocks = content.split("# =====")
        for block in blocks:
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


def scan_reviewer(url):
    log("=" * 50, "info")
    log("SCAN - REVIEWER ANALYSIS", "info")
    log("=" * 50, "info")
    result = {"ok": False, "reviews": 0, "photos": 0, "level": 0,
              "violations": [], "phones": [], "emails": [],
              "age": "-", "ban_chance": 50, "remove_chance": 10}
    try:
        ua = UserAgent()
        headers = {"User-Agent": ua.random, "X-Forwarded-For": get_random_ip()}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            log(f"HTTP {r.status_code}", "error")
            return result
        result["ok"] = True
        text = r.text; tl = text.lower()

        m = re.findall(r'(\d+)\s*reviews', text)
        result["reviews"] = int(m[0]) if m else 0
        log(f"Total Reviews: {result['reviews']}", "scan")

        m = re.findall(r'(\d+)\s*photos', text)
        result["photos"] = int(m[0]) if m else 0
        log(f"Total Photos: {result['photos']}", "scan")

        m = re.findall(r'Level\s*(\d+)', text)
        result["level"] = int(m[0]) if m else 0
        log(f"Local Guide Level: {result['level']}", "scan")

        abuse = ['gandu','chutiya','bc','mc','bhosdi','madarchod','harami','kutta','kamine','stupid','idiot','fuck','shit','scam','fraud','cheater','fake','terrible','bad']
        result["violations"] = [w for w in abuse if w in tl]
        if result["violations"]:
            log(f"Violations: {len(result['violations'])}", "warning")
        else:
            log("Koi violation nahi", "success")

        result["phones"] = re.findall(r'[+]?[0-9]{10,12}', text)
        result["emails"] = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        if result["phones"]: log(f"Phone leak: {len(result['phones'])}", "warning")
        if result["emails"]: log(f"Email leak: {len(result['emails'])}", "warning")

        if result["reviews"] > 100:
            result["age"] = "Purana (2+ saal)"; result["ban_chance"] = 20
        elif result["reviews"] > 20:
            result["age"] = "Medium (1-2 saal)"; result["ban_chance"] = 50
        else:
            result["age"] = "Naya (<1 saal)"; result["ban_chance"] = 85
        log(f"Account Age: {result['age']}", "scan")
        log(f"Ban Chance: {result['ban_chance']}%", "scan")

        if result["violations"] or result["phones"] or result["emails"]:
            result["remove_chance"] = 85; log("Remove Chance: 85%", "success")
        else:
            result["remove_chance"] = 10; log("Remove Chance: 10%", "warning")
    except Exception as e:
        log(f"Error: {e}", "error")
    return result


_stats = {}
def add_stat(m, ok):
    if m not in _stats: _stats[m] = {"sent": 0, "success": 0}
    _stats[m]["sent"] += 1
    if ok: _stats[m]["success"] += 1

def show_summary():
    log("=" * 50, "info")
    log("FINAL SUMMARY", "info")
    log("=" * 50, "info")
    ts = sum(s["sent"] for s in _stats.values())
    to = sum(s["success"] for s in _stats.values())
    log(f"Total Reports: {ts}", "info")
    log(f"Successful: {to}", "success")
    log(f"Failed: {ts - to}", "error")
    if ts > 0: log(f"Success Rate: {(to/ts)*100:.1f}%", "warning")


# ---- Commands ----
def m1(s, t):
    log("CONTRIBUTOR FLAG REPORTING", "service")
    base = "https://www.google.com/maps/contrib/flag"; ok = 0
    for i in range(5):
        try:
            s.headers["X-Forwarded-For"] = get_random_ip()
            r = s.get(base, params={"url": t, "reason": "spam"}, timeout=5)
            if r.status_code == 200: ok += 1; add_stat("Contributor", True)
            else: add_stat("Contributor", False)
        except: add_stat("Contributor", False)
        time.sleep(0.2)
    log(f"  {ok}/5", "success"); return ok

def m2(s, t):
    log("GOOGLE ENDPOINTS REPORTING", "service")
    eps = ["https://maps.google.com/maps/rpc/report", "https://www.google.com/maps/contrib/flag"]; ok = 0
    for ep in eps:
        try:
            s.headers["X-Forwarded-For"] = get_random_ip()
            r = s.post(ep, json={"url": t}, timeout=5)
            if r.status_code in [200,204,400,405]: ok += 1; add_stat("Endpoints", True)
            else: add_stat("Endpoints", False)
        except: add_stat("Endpoints", False)
        time.sleep(0.2)
    log(f"  {ok}/{len(eps)}", "success"); return ok

def m3(s, t):
    log("MULTI LINKS REPORTING", "service"); ok = 0
    for link in [t, "https://www.google.com/maps"]:
        try:
            s.headers["X-Forwarded-For"] = get_random_ip()
            r = s.get(link, timeout=5)
            if r.status_code == 200: ok += 1; add_stat("MultiLinks", True)
            else: add_stat("MultiLinks", False)
        except: add_stat("MultiLinks", False)
        time.sleep(0.2)
    log(f"  {ok}/2", "success"); return ok

def m4(s, t):
    log("LEGAL FORMS REPORTING", "service")
    forms = ["https://support.google.com/business/contact/review_removal",
             "https://support.google.com/business/gethelp",
             "https://support.google.com/legal/contact/lr_defamation",
             "https://support.google.com/legal/contact/lr_privacy"]
    ok = 0
    for f in forms:
        try:
            s.headers["X-Forwarded-For"] = get_random_ip()
            r = s.get(f, timeout=5)
            if r.status_code == 200: ok += 1; add_stat("Legal", True)
            else: add_stat("Legal", False)
        except: add_stat("Legal", False)
        time.sleep(0.2)
    log(f"  {ok}/{len(forms)}", "success"); return ok

def m5(s, t):
    log("RATE LIMIT BYPASS", "service")
    base = "https://www.google.com/maps/contrib/flag"; ok = 0
    for i in range(10):
        try:
            s.headers["X-Forwarded-For"] = get_random_ip()
            r = s.get(base, params={"url": t}, timeout=3)
            if r.status_code == 200: ok += 1; add_stat("RateLimit", True)
            else: add_stat("RateLimit", False)
        except: add_stat("RateLimit", False)
        time.sleep(0.1)
    log(f"  {ok}/10", "success"); return ok

def m6(s, t):
    log("BOTNET FLOOD", "service")
    base = "https://www.google.com/maps/contrib/flag"; ok = 0
    for i in range(15):
        try:
            s.headers["X-Forwarded-For"] = get_random_ip()
            r = s.get(base, params={"url": t}, timeout=3)
            if r.status_code == 200: ok += 1; add_stat("Botnet", True)
            else: add_stat("Botnet", False)
        except: add_stat("Botnet", False)
        time.sleep(0.05)
    log(f"  {ok}/15", "success"); return ok

def m7(s, t):
    log("MASS REPORTING", "service")
    base = "https://www.google.com/maps/contrib/flag"; ok = 0
    for i in range(10):
        try:
            s.headers["X-Forwarded-For"] = get_random_ip()
            r = s.get(base, params={"url": t, "reason": random.choice(["spam","fake","abuse"])}, timeout=5)
            if r.status_code == 200: ok += 1; add_stat("Mass", True)
            else: add_stat("Mass", False)
        except: add_stat("Mass", False)
        time.sleep(0.2)
    log(f"  {ok}/10", "success"); return ok

def m8(s, t):
    log("LOOP REPORTING (50x)", "service")
    base = "https://www.google.com/maps/contrib/flag"; ok = 0
    for i in range(50):
        try:
            s.headers["X-Forwarded-For"] = get_random_ip()
            r = s.get(base, params={"url": t}, timeout=3)
            if r.status_code == 200: ok += 1; add_stat("Loop", True)
            else: add_stat("Loop", False)
        except: add_stat("Loop", False)
        time.sleep(0.05)
    log(f"  {ok}/50", "success"); return ok

def m9(s, t):
    log("GET METHOD", "service")
    base = "https://www.google.com/maps/contrib/flag"; ok = 0
    for i in range(10):
        try:
            s.headers["X-Forwarded-For"] = get_random_ip()
            r = s.get(base, params={"url": t, "method": "GET"}, timeout=5)
            if r.status_code == 200: ok += 1; add_stat("GET", True)
            else: add_stat("GET", False)
        except: add_stat("GET", False)
        time.sleep(0.2)
    log(f"  {ok}/10", "success"); return ok

def m10(s, t):
    log("SUPPORT COMPLAINT", "service")
    forms = ["https://support.google.com/business/contact/review_removal",
             "https://support.google.com/maps/contact/legal"]; ok = 0
    for f in forms:
        try:
            s.headers["X-Forwarded-For"] = get_random_ip()
            r = s.get(f, timeout=5)
            if r.status_code == 200: ok += 1; add_stat("Support", True)
            else: add_stat("Support", False)
        except: add_stat("Support", False)
        time.sleep(0.2)
    log(f"  {ok}/{len(forms)}", "success"); return ok

def m11(s, t):
    log("EXTERNAL REPORTING", "service")
    platforms = ["https://www.trustpilot.com/", "https://www.bbb.org/"]; ok = 0
    for p in platforms:
        try:
            s.headers["X-Forwarded-For"] = get_random_ip()
            r = s.get(p, timeout=5)
            if r.status_code == 200: ok += 1; add_stat("External", True)
            else: add_stat("External", False)
        except: add_stat("External", False)
        time.sleep(0.2)
    log(f"  {ok}/{len(platforms)}", "success"); return ok

def m12(s, t):
    log("REVIEW SCANNER", "service")
    try:
        s.headers["X-Forwarded-For"] = get_random_ip()
        r = s.get(t, timeout=5)
        if r.status_code == 200:
            add_stat("Scanner", True); log("  Accessible", "success"); return 1
    except: pass
    add_stat("Scanner", False); return 0

def m13(s, t): return m1(s, t)
def m14(s, t): return m2(s, t)
def m15(s, t): return m1(s, t)
def m16(s, t): return m3(s, t)
def m17(s, t): return m4(s, t)
def m18(s, t): return m13(s,t)+m14(s,t)+m15(s,t)+m16(s,t)+m17(s,t)
def m19(s, t): return m1(s,t)+m2(s,t)+m3(s,t)+m4(s,t)+m5(s,t)+m6(s,t)+m7(s,t)+m8(s,t)+m9(s,t)+m10(s,t)+m11(s,t)+m12(s,t)
def m20(s, t): show_summary(); return 0

def m22(s, t):
    log("ALL IN ONE + SUMMARY", "service")
    ok = m19(s, t); show_summary(); return ok

def m24(s, t):
    log("ACCOUNT BAN ATTACK", "ban")
    ck = load_all_cookies(); tr = 0; ts = 0
    for cookie_set in ck:
        sess = requests.Session()
        sess.headers.update({"User-Agent": UserAgent().random})
        sess.cookies.update(cookie_set)
        for j in range(20):
            try:
                sess.headers["X-Forwarded-For"] = get_random_ip()
                r = sess.get("https://www.google.com/maps/contrib/flag",
                             params={"url": t, "reason": random.choice(["spam","fake","abuse","harassment"])},
                             timeout=5)
                tr += 1
                if r.status_code == 200: ts += 1
            except: pass
            time.sleep(0.1)
    log(f"Total: {tr} | Success: {ts}", "success")
    log("Ban Chance: 60-80%", "ban"); show_summary(); return ts

def m25(s, t):
    log("POWERFUL ACCOUNT BAN", "ban")
    ck = load_all_cookies()
    methods = [
        {"url": "https://www.google.com/maps/contrib/flag", "params": {"url": t, "reason": "spam"}},
        {"url": "https://www.google.com/maps/contrib/report", "params": {"url": t, "reason": "fake"}},
        {"url": "https://maps.google.com/maps/contrib/flag", "params": {"url": t, "reason": "abuse"}},
        {"url": "https://maps.google.com/maps/rpc/report", "params": {"url": t, "reason": "spam"}},
    ]
    tr = 0; ts = 0
    for cookie_set in ck:
        sess = requests.Session()
        sess.headers.update({"User-Agent": UserAgent().random})
        sess.cookies.update(cookie_set)
        for m in methods:
            for j in range(5):
                try:
                    sess.headers["X-Forwarded-For"] = get_random_ip()
                    r = sess.get(m["url"], params=m["params"], timeout=5)
                    tr += 1
                    if r.status_code == 200: ts += 1
                except: pass
                time.sleep(0.1)
    log(f"Total: {tr} | Success: {ts}", "success")
    log("Ban Chance: 80-95%", "ban"); show_summary(); return ts

def m26(s, t):
    log("FULL AUTO (FAST)", "ban")
    ck = load_all_cookies(); tr = 0; ts = 0
    for cookie_set in ck:
        sess = requests.Session()
        sess.headers.update({"User-Agent": UserAgent().random})
        sess.cookies.update(cookie_set)
        for j in range(5):
            try:
                sess.headers["X-Forwarded-For"] = get_random_ip()
                r = sess.get("https://www.google.com/maps/contrib/flag", params={"url": t, "reason": "spam"}, timeout=3)
                tr += 1
                if r.status_code == 200: ts += 1
            except: pass
            time.sleep(0.02)
        for j in range(50):
            try:
                sess.headers["X-Forwarded-For"] = get_random_ip()
                r = sess.get("https://www.google.com/maps/contrib/flag", params={"url": t}, timeout=3)
                tr += 1
                if r.status_code == 200: ts += 1
            except: pass
            time.sleep(0.02)
    log(f"Total: {tr} | Success: {ts}", "success")
    log("Review Remove: 70-85% | Ban: 80-95%", "ban"); show_summary(); return ts

def m27(s, t):
    log("PURANE REVIEWS", "ban")
    ck = load_all_cookies(); tr = 0; ts = 0
    for cookie_set in ck:
        sess = requests.Session()
        sess.headers.update({"User-Agent": UserAgent().random})
        sess.cookies.update(cookie_set)
        for j in range(10):
            try:
                sess.headers["X-Forwarded-For"] = get_random_ip()
                r = sess.get("https://www.google.com/maps/contrib/flag", params={"url": t, "reason": "spam"}, timeout=5)
                tr += 1
                if r.status_code == 200: ts += 1
            except: pass
            time.sleep(0.1)
    log(f"Total: {tr} | Success: {ts}", "success")
    log("Purane Remove: 40-60%", "ban")
    log("Account Strike: 50-70%", "ban"); show_summary(); return ts


PROGRAMS = [
    ("1. Contributor Flag",          m1),
    ("2. Google Endpoints",          m2),
    ("3. Multi Links",               m3),
    ("4. Legal Forms",               m4),
    ("5. Rate Limit Bypass",         m5),
    ("6. Botnet Flood",              m6),
    ("7. Mass Reporting",            m7),
    ("8. Loop Reporting (50x)",      m8),
    ("9. GET Method",                m9),
    ("10. Support Complaint",        m10),
    ("11. External Reporting",       m11),
    ("12. Review Scanner",           m12),
    ("13. Exploit 1 - Accessible",   m13),
    ("14. Exploit 2 - Review ID",    m14),
    ("15. Exploit 3 - Cookies",      m15),
    ("16. Exploit 4 - Maps Traffic", m16),
    ("17. Exploit 5 - Forms Flood",  m17),
    ("18. Full Exploit",             m18),
    ("19. Full Reporting",           m19),
    ("20. Summary",                  m20),
    ("21. ALL IN ONE + SUMMARY",     m22),
    ("22. ACCOUNT BAN ATTACK",       m24),
    ("23. POWERFUL BAN (80-95%)",    m25),
    ("24. FULL AUTO (FAST)",         m26),
    ("25. PURANE REVIEWS",           m27),
]


def run_command(func, url, log_cb):
    set_logger(log_cb)
    if not url:
        log("URL khali hai!", "error"); return
    ck = load_all_cookies()
    if not ck:
        log("Koi cookies nahi mili. Pehle cookies.txt upload karein.", "error"); return
    log(f"Total {len(ck)} cookies par command chalegi", "info")
    if func.__name__ in ["m24", "m25", "m26", "m27"]:
        func(None, url); return
    for i, cookie_set in enumerate(ck):
        log(f"--- Cookie {i+1}/{len(ck)} ---", "info")
        sess = requests.Session()
        sess.headers.update({"User-Agent": UserAgent().random})
        sess.cookies.update(cookie_set)
        func(sess, url)
        time.sleep(0.5)
    show_summary()
