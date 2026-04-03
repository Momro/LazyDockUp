# LazyDockUp Central 🦥🐳

**LazyDockUp** is a minimalist, multi-host Docker container updater designed for home labs and enthusiasts who want to keep their stacks up-to-date without the complexity of enterprise tools. 

It keeps things simple: It pulls the latest images, updates your `docker-compose.yaml` files, and restarts your containers while maintaining their exact configuration.

> [!IMPORTANT]  
> **Vibe Coding Project:** This entire project was built using **Vibe Coding** methodologies, powered by **Google Gemini**. It's a testament to rapid, iterative development where the focus is on the "vibe"—clean code, essential features, and great UX.

*Haha, gemini wrote that as well. It's not a testament. I think it's kinda sad that AI is doing this for me 2026. Nothing in this project, including this readme, was written by me.*

---

## Features

- 🖥️ **Multi-Host Management:** Monitor and update multiple Docker hosts from a single central dashboard.
- 🛡️ **Update Policies:** Fine-grained control via labels. Choose to allow only `patch`, `minor`, or `major` updates.
- 🔗 **Smart Release Links:** Direct links to GitHub Releases or Docker Hub Tags for every update.
- 🤖 **Uptime Kuma Integration:** Automatically pokes your Uptime Kuma instance when updates are found.
- 🧹 **One-Click Prune:** Clean up dangling images on any host with a single click.
- 🌓 **Minimalist Dark Mode:** Super clean UI powered by Pico.css.
- 🌐 **International:** Supports English and German (configured via Environment Variables).

---

## Architecture

LazyDockUp consists of two parts:
1. **The Server:** The central brain/dashboard that polls agents and checks for updates.
2. **The Agent:** A lightweight helper running on every host that talks to the Docker socket and edits your local compose files.

---

## Quick Start

### 1. Deploy the Stack
Create a `docker-compose.yaml` on your main host:

```yaml
services:
  ldu-server:
    image: momro/lazydockup-server:latest
    container_name: lazydockup-server
    ports:
      - "5002:5000"
    environment:
      - AGENTS=ldu-agent:5001,192.168.0.44:5001
      - APP_LANG=de
      - TZ=Europe/Berlin
      - KUMA_PUSH_URL="https:/kuma.example.com/api/push/TOKEN..." # in case you want to use Kuma
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - /etc/timezone:/etc/timezone:ro
    restart: unless-stopped

  ldu-agent:
    image: momro/lazydockup-agent:latest
    container_name: lazydockup-agent
    ports:
      - "5001:5001"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /home/user/docker:/stacks
      - /etc/localtime:/etc/localtime:ro
      - /etc/timezone:/etc/timezone:ro
    environment:
      - HOST_PATH_BASE=/home/user/docker
      - DW_HOSTNAME=Docker-Host
      - TZ=Europe/Berlin
    restart: unless-stopped
```

Find the docker files at https://hub.docker.com/u/momro

### 2. Configure your Stacks
Add labels to the services you want LazyDockUp to manage:

```yaml
services:
  my-app:
    image: some-repo/my-app:1.2.3
    labels:
      - "lazydockup.policy=minor" # Options: patch, minor, major
```

## Update Policies

| Policy | Description | Example |
| :--- | :--- | :--- |
| `patch` | Only allow the last digit to change. | `1.2.3` -> `1.2.4` ✅ |
| `minor` | Allow minor versions, block major jumps. | `1.2.3` -> `1.9.0` ✅ |
| `major` | Allow all updates, including breaking changes. | `1.2.3` -> `2.0.0` ✅ |

---

## Environment Variables

### Server
- `AGENTS`: List of agent addresses (`ip:port`).
- `APP_LANG`: UI Language (`en` or `de`).
- `KUMA_PUSH_URL`: Uptime Kuma Push Monitor URL. Background check runs every 12 hours.
- `TZ`: Your timezone (e.g., `Europe/Berlin`).

### Agent
- `HOST_PATH_BASE`: The absolute path on your host where your compose files are stored.
- `DW_HOSTNAME`: The friendly name of the host to display in the UI.
- `TZ`: Your timezone.

---

## Roadmap
- [x] Multi-Host Support
- [x] SemVer Policy Enforcement
- [x] Uptime Kuma Integration
- [x] OCI Label support for version detection
- [ ] Authentication / Password protection
- [ ] Notifications (Discord/Telegram)

---

**Developed with ❤️ and Gemini.**
