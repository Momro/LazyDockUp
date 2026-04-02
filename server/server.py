import requests, os, re
from flask import Flask, render_template, jsonify, request
from packaging import version
from collections import defaultdict

app = Flask(__name__)
APP_VERSION = "2.6.2"
AGENTS = os.environ.get("AGENTS", "").split(",")

def normalize_v(v):
    if not v: return "0.0.0"
    clean = re.sub(r'^v', '', v.strip()).split('-')[0]
    return clean if clean else "0.0.0"

def get_clean_latest(image_name, current_tag):
    try:
        repo_name = image_name.split('/')[-1] if '/' in image_name else image_name
        if "zigbee2mqtt" in repo_name.lower(): repo_name = "koenkk/zigbee2mqtt"
        if '/' not in repo_name: repo_name = f"library/{repo_name}"
        res = requests.get(f"https://hub.docker.com/v2/repositories/{repo_name}/tags?page_size=100", timeout=5).json()
        all_tags = [t['name'] for t in res.get('results', [])]
        valid_tags = [t for t in all_tags if not any(x in t.lower() for x in ["dev", "master", "latest", "rc", "beta"]) and not (len(t) > 12 and t.isdigit())]
        valid_tags.sort(key=lambda x: version.parse(normalize_v(x)), reverse=True)
        return valid_tags[0] if valid_tags else current_tag
    except: return current_tag

def check_policy(current_v, latest_v, policy):
    try:
        cv = version.parse(normalize_v(current_v))
        lv = version.parse(normalize_v(latest_v))
        if lv <= cv: return True, None
        jt = "patch"
        if lv.major > cv.major: jt = "major"
        elif lv.minor > cv.minor: jt = "minor"
        if policy == "major" or policy == "all": return True, jt
        if policy == "minor" and jt in ["minor", "patch"]: return True, jt
        if policy == "patch" and jt == "patch": return True, jt
        return False, jt
    except: return (current_v == latest_v), None

@app.route('/')
def index(): return render_template('index.html', version=APP_VERSION)

@app.route('/api/status')
def status():
    grouped_data = defaultdict(list)
    for agent_url in AGENTS:
        url = agent_url.strip()
        if not url: continue
        try:
            r = requests.get(f"http://{url}/list", timeout=5)
            for c in r.json():
                img_base, current_tag = c['image_full'].split(':') if ':' in c['image_full'] else (c['image_full'], 'latest')
                v_label = c.get('image_version_label', 'latest')
                display_current = v_label if current_tag == "latest" else current_tag
                latest_tag = get_clean_latest(img_base, display_current)
                pol = c.get('policy', 'minor').lower()
                is_allowed, jump_type = check_policy(display_current, latest_tag, pol)
                is_up_to_date = (normalize_v(display_current) == normalize_v(latest_tag))
                grouped_data[c['hostname']].append({
                    "agent": url, "name": c['name'], "image_base": img_base,
                    "display_current": display_current, "latest_tag": latest_tag,
                    "policy": pol, "jump_type": jump_type,
                    "is_up_to_date": is_up_to_date, "can_update": not is_up_to_date and is_allowed
                })
        except: continue
    for h in grouped_data: grouped_data[h].sort(key=lambda x: x['name'])
    return jsonify(dict(sorted(grouped_data.items())))

@app.route('/api/prune', methods=['POST'])
def prune(): return requests.post(f"http://{request.json.get('agent')}/prune").json()

@app.route('/api/deploy', methods=['POST'])
def deploy():
    d = request.json
    a = d.pop('agent')
    return requests.post(f"http://{a}/update", json=d).json()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
