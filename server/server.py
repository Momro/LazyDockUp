import requests, os, re, time, threading
from flask import Flask, render_template, jsonify, request
from packaging import version
from collections import defaultdict
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
APP_VERSION = "3.1.2"
AGENTS = os.environ.get("AGENTS", "").split(",")
KUMA_URL = os.environ.get("KUMA_PUSH_URL", "").strip('"')
LANG = os.environ.get("APP_LANG", "en").lower()

TRANSLATIONS = {
    "en": {
        "title": "LazyDockUp Central", "ready": "Systems ready.", "polling": "Polling agents...",
        "no_agents": "No agents online.", "update_singular": "Update", "update_plural": "Updates",
        "prune_btn": "Prune Images", "collapse_btn": "▲ Collapse Host", "current": "Current",
        "upgrade": "Upgrade", "blocked": "Blocked", "policy_warn": "Upgrade blocked (Policy)"
    },
    "de": {
        "title": "LazyDockUp Central", "ready": "Systeme bereit.", "polling": "Abfrage der Agents...",
        "no_agents": "Keine Agents online.", "update_singular": "Update", "update_plural": "Updates",
        "prune_btn": "Images bereinigen", "collapse_btn": "▲ Host einklappen", "current": "Aktuell",
        "upgrade": "Upgrade", "blocked": "Blockiert", "policy_warn": "Upgrade blockiert (Policy)"
    }
}
T = TRANSLATIONS.get(LANG, TRANSLATIONS["en"])

def normalize_v(v):
    if not v or v in ["latest", "unknown"]: return "0.0.0"
    match = re.search(r'(\d+\.\d+\.\d+|\d+\.\d+)', v)
    return match.group(1) if match else "0.0.0"

def get_release_url(image_base, labels):
    source = labels.get('org.opencontainers.image.source', '')
    if "github.com" in source: return source.replace(".git", "") + "/releases"
    repo = image_base
    if '/' not in repo: repo = f"library/{repo}"
    return f"https://hub.docker.com/r/{repo}/tags"

def get_clean_latest(image_name, current_tag):
    try:
        full_repo = image_name
        if "zigbee2mqtt" in image_name.lower(): full_repo = "koenkk/zigbee2mqtt"
        if "recipes" in image_name.lower(): full_repo = "vabene1111/recipes"
        if '/' not in full_repo: full_repo = f"library/{full_repo}"
        res = requests.get(f"https://hub.docker.com/v2/repositories/{full_repo}/tags?page_size=100", timeout=5).json()
        all_tags = [t['name'] for t in res.get('results', [])]
        valid_tags = []
        is_alpine = "alpine" in current_tag.lower()
        for t in all_tags:
            if any(x in t.lower() for x in ["dev", "master", "latest", "rc", "beta", "amd64", "arm64"]): continue
            if is_alpine and "alpine" not in t.lower(): continue
            if not is_alpine and "-" in t: continue
            if re.search(r'\d+\.\d+', t): valid_tags.append(t)
        valid_tags.sort(key=lambda x: version.parse(normalize_v(x)), reverse=True)
        return valid_tags[0] if valid_tags else current_tag
    except: return current_tag

def check_policy(current_v, latest_v, policy):
    try:
        cv, lv = version.parse(normalize_v(current_v)), version.parse(normalize_v(latest_v))
        if lv <= cv: return True, None
        jt = "patch"
        if lv.major > cv.major: jt = "major"
        elif lv.minor > cv.minor: jt = "minor"
        if policy in ["major", "all"]: return True, jt
        if policy == "minor" and jt in ["minor", "patch"]: return True, jt
        if policy == "patch" and jt == "patch": return True, jt
        return False, jt
    except: return True, None

def run_background_check():
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] Running background update check...")
    update_found = False
    for agent_url in AGENTS:
        try:
            r = requests.get(f"http://{agent_url.strip()}/list", timeout=10)
            for c in r.json():
                img_base, current_tag = c['image_full'].split(':') if ':' in c['image_full'] else (c['image_full'], 'latest')
                v_label = c.get('image_version_label', 'unknown')
                comp_v = v_label if v_label != 'unknown' else current_tag
                if normalize_v(comp_v) != normalize_v(get_clean_latest(img_base, comp_v)):
                    update_found = True; break
        except: continue
    if KUMA_URL:
        status = "down" if update_found else "up"
        msg = "Updates available" if update_found else "All OK"
        try:
            requests.get(f"{KUMA_URL}&status={status}&msg={msg}", timeout=5)
            print(f"[{now}] Kuma notified: {status}")
        except Exception as e: print(f"[{now}] Kuma Error: {e}")

@app.route('/')
def index(): return render_template('index.html', version=APP_VERSION, t=T)

@app.route('/api/status')
def status():
    grouped_data = defaultdict(list)
    for agent_url in AGENTS:
        url = agent_url.strip()
        if not url: continue
        try:
            r = requests.get(f"http://{url}/list", timeout=5)
            for c in r.json():
                img_base, curr_tag = c['image_full'].split(':') if ':' in c['image_full'] else (c['image_full'], 'latest')
                v_label = c.get('image_version_label', 'unknown')
                comp_v = v_label if v_label != 'unknown' else curr_tag
                latest_v = get_clean_latest(img_base, comp_v)
                pol = c.get('policy', 'minor').lower()
                is_allowed, jt = check_policy(comp_v, latest_v, pol)
                ui_current = curr_tag if curr_tag != "latest" or v_label == "unknown" else f"latest ({v_label})"
                grouped_data[c['hostname']].append({
                    "agent": url, "name": c['name'], "image_base": img_base,
                    "display_current": ui_current, "latest_tag": latest_v,
                    "policy": pol, "jump_type": jt, "compose_dir": c.get('compose_dir'),
                    "is_up_to_date": (normalize_v(comp_v) == normalize_v(latest_v)),
                    "can_update": (normalize_v(comp_v) != normalize_v(latest_v)) and is_allowed,
                    "release_url": get_release_url(img_base, c.get('labels', {}))
                })
        except: continue
    for h in grouped_data: grouped_data[h].sort(key=lambda x: x['name'])
    return jsonify(dict(sorted(grouped_data.items())))

@app.route('/api/prune', methods=['POST'])
def prune(): return requests.post(f"http://{request.json['agent']}/prune").json()

@app.route('/api/deploy', methods=['POST'])
def deploy():
    d = request.json
    a = d.pop('agent')
    return requests.post(f"http://{a}/update", json=d).json()

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=run_background_check, trigger="interval", hours=12)
    scheduler.start()
    threading.Thread(target=run_background_check).start()
    app.run(host='0.0.0.0', port=5000)
