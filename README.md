<div align="center">

# 🦊 GitLab CI/CD CLI

**Monitor your GitLab pipelines, jobs, registries, and merge requests — right from your terminal.**

[![Python](https://img.shields.io/badge/python-3.9%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Built with Click](https://img.shields.io/badge/built%20with-Click-orange)](https://click.palletsprojects.com/)
[![Styled with Rich](https://img.shields.io/badge/styled%20with-Rich-purple)](https://github.com/Textualize/rich)

</div>

---

A lightweight, zero-configuration-after-setup CLI for **self-hosted GitLab** instances. Track multiple repositories, inspect pipeline statuses, stream job logs, browse container images, and manage merge requests — all without leaving your terminal.

---

## ✨ Features

- **Pipeline monitoring** — view status of latest or historical pipelines at a glance
- **Job inspection** — list jobs with stage, status, and duration; auto-fetch latest pipeline if no ID given
- **Live job logs** — stream full logs or tail the last N lines
- **Container Registry** — browse images and tags with sizes
- **Merge Requests** — list open, merged, or closed MRs with author info
- **Environments** — inspect deployment environments and their URLs
- **Multi-repo tracking** — add any number of repositories and check them all at once
- **Multilingual UI** — switch between 7 languages with a single command
- **Secure credentials** — token obfuscated at rest, config file locked to `0600` permissions

---

## 📦 Installation

### From source (recommended)

```bash
git clone https://github.com/wokacz/cicd-cli.git
cd gitlab-cicd-cli
pip install .
```

### Editable / development mode

```bash
pip install -e .
# or with uv:
uv pip install -e .
```

> **Requirements:** Python 3.9 or higher · GitLab 12.0+ (API v4)

---

## 🚀 Quick Start

### 1. Configure your GitLab connection

```
$ cicd init

╭─ GitLab CI/CD CLI Configuration ─╮
╰───────────────────────────────────╯
Enter GitLab URL (e.g. https://git.example.com): https://gitlab.example.com
Enter API token (Personal Access Token): ****

✔ Successfully connected to GitLab 16.10.2!
```

> **Getting an API token:** GitLab → User Settings → Access Tokens  
> Required scopes: `read_api` · `read_registry` (for container images)

### 2. Add a repository to track

```
$ cicd add mygroup/myproject

✔ Successfully added repository My Group / My Project!
```

### 3. Check pipeline status

```
$ cicd status

My Group / My Project
  Pipeline #1842 (main) · ✔ PASSED
    build:compile       ✔ PASSED
    test:unit           ✔ PASSED
    test:integration    ✔ PASSED
    deploy:staging      ✔ PASSED
```

---

## 📖 All Commands

| Command | Description |
|---|---|
| `cicd init` | Configure GitLab URL and API token |
| `cicd add <repo>` | Add a repository to the tracked list |
| `cicd remove <repo>` | Remove a repository from the tracked list |
| `cicd list` | Show all tracked repositories |
| `cicd status [repo]` | Show the latest pipeline status |
| `cicd pipelines <repo>` | List recent pipelines |
| `cicd jobs <repo> [pipeline_id]` | List jobs for a pipeline |
| `cicd logs <repo> <job_id>` | Show logs for a specific job |
| `cicd images <repo>` | Browse Container Registry images |
| `cicd mrs <repo>` | Show merge requests |
| `cicd envs <repo>` | Show deployment environments |
| `cicd language [code]` | Set or show the display language |

Pass `--help` to any command for detailed usage and examples:

```bash
cicd jobs --help
cicd pipelines --help
```

---

## 🔍 Usage Examples

### Tracking multiple repositories

```bash
cicd add backend/api
cicd add frontend/web
cicd add infra/helm-charts

# Check all tracked repos at once
cicd status
```

### Pipeline history

```bash
# Show last 10 pipelines (default)
cicd pipelines mygroup/myproject

# Show last 25 pipelines
cicd pipelines mygroup/myproject -n 25
```

### Inspecting jobs

```bash
# Jobs for the latest pipeline (no ID needed)
cicd jobs mygroup/myproject

# Jobs for a specific pipeline
cicd jobs mygroup/myproject 1842

# Jobs from the last 5 pipelines
cicd jobs mygroup/myproject -n 5
```

```
╭──────┬──────────────┬──────────────────┬──────────┬──────────────╮
│ ID   │ Stage        │ Name             │ Status   │ Duration (s) │
├──────┼──────────────┼──────────────────┼──────────┼──────────────┤
│ 9923 │ build        │ compile          │ ✔ PASSED │ 42           │
│ 9924 │ test         │ unit-tests       │ ✔ PASSED │ 118          │
│ 9925 │ test         │ integration      │ ✘ FAILED │ 73           │
│ 9926 │ deploy       │ deploy:staging   │ ⊘ SKIPPED│ -            │
╰──────┴──────────────┴──────────────────┴──────────┴──────────────╯
```

### Streaming job logs

```bash
# Full log output
cicd logs mygroup/myproject 9925

# Last 50 lines only
cicd logs mygroup/myproject 9925 --tail 50
```

### Container Registry

```bash
cicd images mygroup/myproject
```

```
mygroup/myproject/api

 Tag              Size      Created
 latest           184.3 MB  2024-04-20 11:32:01
 v2.4.1           184.1 MB  2024-04-18 09:15:44
 v2.4.0           181.7 MB  2024-04-10 14:02:33
```

### Merge Requests

```bash
# Open MRs (default)
cicd mrs mygroup/myproject

# Merged MRs
cicd mrs mygroup/myproject --state merged

# All MRs
cicd mrs mygroup/myproject --state all
```

### Environments

```bash
cicd envs mygroup/myproject
```

```
╭────┬──────────────┬──────────────────────────────────┬──────────╮
│ ID │ Name         │ URL                              │ State    │
├────┼──────────────┼──────────────────────────────────┼──────────┤
│  1 │ staging      │ https://staging.example.com      │ available│
│  2 │ production   │ https://app.example.com          │ available│
╰────┴──────────────┴──────────────────────────────────┴──────────╯
```

---

## 🌍 Language Support

The CLI supports 7 languages. All command descriptions, table headers, status labels, and messages are fully translated.

| Code | Language   |
|------|------------|
| `en` | English (default) |
| `pl` | Polish     |
| `de` | German     |
| `fr` | French     |
| `es` | Spanish    |
| `nl` | Dutch      |
| `cs` | Czech      |

```bash
# Switch to Polish
cicd language pl

# Switch back to English
cicd language en

# Show current language and available options
cicd language
```

```
ℹ Current language: en
  Available languages: en, pl, de, fr, es, nl, cs
```

---

## 🔒 Security

Credentials are stored locally in `~/.config/cicd/config.json`.

| Measure | Details |
|---|---|
| **Token obfuscation** | API token is base64-encoded before writing to disk — not stored in plain text |
| **File permissions** | Config file is created with `0600` (owner read/write only) |
| **Directory permissions** | Config directory is created with `0700` |
| **Permission audit** | A warning is shown at startup if the config file has overly open permissions |

> **Note:** Base64 encoding is obfuscation, not encryption. For high-security environments, consider storing your token in your system keychain and referencing it via an environment variable.

If you ever see a permission warning, fix it with:

```bash
chmod 600 ~/.config/cicd/config.json
chmod 700 ~/.config/cicd/
```

---

## ⚙️ Configuration File

The config file lives at `~/.config/cicd/config.json`. You can inspect it at any time:

```json
{
  "gitlab_url": "https://gitlab.example.com",
  "api_token": "Z2xwYXQt...",
  "repos": [
    "backend/api",
    "frontend/web",
    "infra/helm-charts"
  ],
  "language": "en"
}
```

> The `api_token` field is base64-encoded. Do not edit it by hand — use `cicd init` to reconfigure credentials.

---

## 🛠 Development

```bash
# Clone and install in editable mode
git clone https://github.com/your-org/gitlab-cicd-cli.git
cd gitlab-cicd-cli
uv pip install -e .

# Run directly
uv run cli.py --help

# Or via installed entry point
cicd --help
```

### Project Structure

```
cicd-cli/
├── cli.py                  # Entry-point shim
├── pyproject.toml
└── cicd/
    ├── __init__.py
    ├── cli.py              # All Click commands
    ├── config.py           # Config + security management
    ├── gitlab_client.py    # GitLab API v4 wrapper
    ├── i18n.py             # Internationalization engine
    └── lang/
        ├── en.json
        ├── pl.json
        ├── de.json
        ├── fr.json
        ├── es.json
        ├── nl.json
        └── cs.json
```

### Adding a New Language

1. Copy `cicd/lang/en.json` to `cicd/lang/<code>.json`
2. Translate all string values (keep keys, placeholders like `{version}`, and command names unchanged)
3. Register the code in `cicd/i18n.py` → `_SUPPORTED` tuple
4. Done — `cicd language <code>` will pick it up automatically

---

## 📋 Requirements

- Python **3.9+**
- GitLab instance with **API v4** (GitLab 12.0 or newer)
- Personal Access Token with:
  - `read_api` — required for all commands
  - `read_registry` — required for `cicd images`

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.