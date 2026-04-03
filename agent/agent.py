import os, re, subprocess, docker, socket
from flask import Flask, jsonify, request

app = Flask(__name__)
client = docker.from_env()

HOST_PATH_BASE = os.environ.get('HOST_PATH_BASE', '/home/docker/docker').rstrip('/')
CONTAINER_PATH_BASE = '/stacks'
MY_HOSTNAME = os.environ.get('DW_HOSTNAME', socket.gethostname())

@app.route('/list')
def list_containers():
    containers = []
    for c in client.containers.list(filters={"status": "running"}):
        if not c.image.tags: continue
        compose_dir = c.labels.get('com.docker.compose.project.working_dir', '')
        if not compose_dir: continue
        
        containers.append({
            "name": c.name,
            "image_full": c.image.tags[0],
            "image_version_label": c.image.labels.get('org.opencontainers.image.version', 'unknown'),
            "labels": c.image.labels,
            "compose_dir": compose_dir,
            "policy": c.labels.get('lazydockup.policy') or c.labels.get('dockwatch.policy') or 'minor',
            "hostname": MY_HOSTNAME
        })
    return jsonify(containers)

@app.route('/prune', methods=['POST'])
def prune_images():
    result = client.images.prune(filters={'dangling': True})
    reclaimed = result.get('SpaceReclaimed', 0) / (1024 * 1024)
    return jsonify({"status": "ok", "reclaimed_mb": round(reclaimed, 2)})

@app.route('/update', methods=['POST'])
def update():
    data = request.json
    local_path = data['compose_dir'].replace(HOST_PATH_BASE, CONTAINER_PATH_BASE)
    c_file = next((os.path.join(local_path, f) for f in ["docker-compose.yaml", "docker-compose.yml"] if os.path.exists(os.path.join(local_path, f))), None)
    if not c_file: return jsonify({"error": f"File not found in {local_path}"}), 404
    with open(c_file, 'r') as f: content = f.read()
    pattern = rf"(image:\s*{re.escape(data['image_base'])}):[a-zA-Z0-9._-]+"
    new_content = re.sub(pattern, f"\\1:{data['latest_tag']}", content)
    with open(c_file, 'w') as f: f.write(new_content)
    subprocess.run(["docker", "compose", "up", "-d", "--remove-orphans"], cwd=local_path)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
