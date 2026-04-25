"""CLI entry-point – all user-facing commands live here."""

from __future__ import annotations

import click
from rich import box
from rich.console import Console
from rich.markup import escape as rich_escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from cicd import config
from cicd.gitlab_client import GitLabClient, GitLabError
from cicd.i18n import current_language, init_from_config, load as load_lang
from cicd.i18n import supported_languages, t

console = Console(highlight=False)

# -- status rendering ---------------------------------------------------

_STATUS_ICON_STYLE: dict[str, tuple[str, str]] = {
    "success": ("\u2714", "bold green"),
    "passed": ("\u2714", "bold green"),
    "failed": ("\u2718", "bold red"),
    "running": ("\u25b6", "bold yellow"),
    "pending": ("\u25cc", "dim"),
    "canceled": ("\u2298", "dim"),
    "skipped": ("\u2298", "dim"),
    "manual": ("\u23f8", "bold cyan"),
    "created": ("\u25cc", "dim"),
}


def _status_text(raw: str) -> Text:
    """Build a Rich Text object for a pipeline/job status value."""
    icon, style = _STATUS_ICON_STYLE.get(raw, ("?", ""))
    label = t(f"status_label.{raw}")
    if label == f"status_label.{raw}":
        label = raw.upper()
    txt = Text(f"{icon} {label}", style=style)
    return txt


def _client() -> GitLabClient:
    cfg = config.load()
    return GitLabClient(cfg["gitlab_url"], cfg["api_token"])


def _init_i18n() -> None:
    """Load the language from saved config (best-effort)."""
    init_from_config(config.load)


def _error(msg: str) -> None:
    """Print a consistent error line."""
    console.print(Text(f"\u2718 {msg}", style="bold red"))


def _success(msg: str) -> None:
    """Print a consistent success line."""
    console.print(Text(f"\u2714 {msg}", style="bold green"))


def _info(msg: str) -> None:
    """Print an informational line."""
    console.print(Text(f"\u2139 {msg}", style="bold blue"))


# -- help formatting ----------------------------------------------------


class RichGroup(click.Group):
    """Custom group that loads i18n before every invocation and
    renders a richer help screen."""

    def invoke(self, ctx: click.Context) -> None:
        _init_i18n()
        super().invoke(ctx)

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        _init_i18n()
        super().format_help(ctx, formatter)

    def get_short_help_str(self, limit: int = 150) -> str:
        _init_i18n()
        return t("app.description")


class RichCommand(click.Command):
    """Command subclass that refreshes help text from i18n on every render."""

    def __init__(self, *args, i18n_key: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self._i18n_key = i18n_key

    def get_short_help_str(self, limit: int = 150) -> str:
        if self._i18n_key:
            _init_i18n()
            return t(f"{self._i18n_key}.short_help")
        return super().get_short_help_str(limit)

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        _init_i18n()
        if self._i18n_key:
            self.help = t(f"{self._i18n_key}.help")
        super().format_help(ctx, formatter)


# -- root group ---------------------------------------------------------


@click.group(cls=RichGroup)
@click.version_option(package_name="gitlab-cicd-cli")
def main():
    """GitLab CI/CD CLI - monitor your pipelines from the terminal."""


# -- init ---------------------------------------------------------------


@main.command(cls=RichCommand, i18n_key="init")
def init():
    """Configure connection to a GitLab instance."""
    console.print(
        Panel(
            Text(t("app.config_panel"), style="bold"),
            style="blue",
            expand=False,
        )
    )

    url = click.prompt(t("init.prompt_url"))
    url = url.rstrip("/")
    if not url.startswith("http"):
        url = f"https://{url}"

    token = click.prompt(t("init.prompt_token"), hide_input=True)

    client = GitLabClient(url, token)
    try:
        version = client.ping()
    except GitLabError as exc:
        _error(t("init.error", error=str(exc)))
        raise SystemExit(1)
    except Exception as exc:
        _error(t("init.connection_error", error=str(exc)))
        raise SystemExit(1)

    cfg = config.load()
    cfg["gitlab_url"] = url
    cfg["api_token"] = token
    config.save(cfg)

    _success(t("init.success", version=version))


# -- add ----------------------------------------------------------------


@main.command(cls=RichCommand, i18n_key="add")
@click.argument("repo")
def add(repo: str):
    """Add a repository to track (e.g. group/project)."""
    config.require_init()
    cfg = config.load()
    client = _client()

    try:
        project = client.project(repo)
    except GitLabError as exc:
        _error(t("add.error", error=str(exc)))
        raise SystemExit(1)

    if repo not in cfg["repos"]:
        cfg["repos"].append(repo)
        config.save(cfg)

    _success(t("add.success", name=project["name_with_namespace"]))


# -- remove -------------------------------------------------------------


@main.command(cls=RichCommand, i18n_key="remove")
@click.argument("repo")
def remove(repo: str):
    """Remove a repository from tracked list."""
    config.require_init()
    cfg = config.load()

    if repo in cfg["repos"]:
        cfg["repos"].remove(repo)
        config.save(cfg)
        _success(t("remove.success", repo=repo))
    else:
        _info(t("remove.not_tracked", repo=repo))


# -- list ---------------------------------------------------------------


@main.command(name="list", cls=RichCommand, i18n_key="list")
def list_repos():
    """Display tracked repositories."""
    config.require_init()
    cfg = config.load()

    if not cfg["repos"]:
        _info(t("list.empty"))
        return

    console.print(
        Panel(
            Text(t("list.title"), style="bold"),
            style="blue",
            expand=False,
        )
    )
    for repo in cfg["repos"]:
        console.print(Text(f"  \u2022 {repo}"))


# -- status -------------------------------------------------------------


@main.command(cls=RichCommand, i18n_key="status")
@click.argument("repo", required=False)
def status(repo: str | None):
    """Show the status of the latest pipeline."""
    config.require_init()
    cfg = config.load()
    client = _client()

    repos = [repo] if repo else cfg["repos"]
    if not repos:
        _info(t("status.empty"))
        return

    for rpath in repos:
        try:
            project = client.project(rpath)
            pipeline_list = client.pipelines(rpath, per_page=1)
        except GitLabError as exc:
            _error(t("status.error", repo=rpath, error=str(exc)))
            continue

        proj_name = rich_escape(project["name_with_namespace"])
        console.print()
        console.print(Text(proj_name, style="bold underline"))

        if not pipeline_list:
            console.print(Text(f"  {t('status.no_pipelines')}", style="dim"))
            continue

        latest = pipeline_list[0]
        pid = latest["id"]
        ref = latest.get("ref", "?")

        # Build the line with Text objects to avoid markup issues
        line = Text("  ")
        line.append(t("status.pipeline_info", id=str(pid), ref=ref))
        line.append(" \u00b7 ")
        line.append_text(_status_text(latest["status"]))
        console.print(line)

        jobs_list = client.pipeline_jobs(rpath, pid)
        for job in sorted(jobs_list, key=lambda j: j["id"]):
            name = job["name"]
            stage = job.get("stage", "")

            job_line = Text("    ")
            job_line.append(f"{stage}:{name}", style="dim")
            job_line.append("  ")
            job_line.append_text(_status_text(job["status"]))
            console.print(job_line)


# -- pipelines ----------------------------------------------------------


@main.command(cls=RichCommand, i18n_key="pipelines")
@click.argument("repo")
@click.option(
    "-n",
    "--count",
    default=10,
    show_default=True,
    help="Number of pipelines to show",
)
def pipelines(repo: str, count: int):
    """Display recent pipelines for a repo."""
    config.require_init()
    client = _client()

    table = Table(
        title=t("pipelines.title", repo=repo),
        box=box.ROUNDED,
        title_style="bold blue",
    )
    table.add_column(t("table.id"), style="bold")
    table.add_column(t("table.branch"))
    table.add_column(t("table.status"))
    table.add_column(t("table.created"))

    try:
        for p in client.pipelines(repo, per_page=count):
            created = (p.get("created_at") or "")[:19].replace("T", " ")
            table.add_row(
                str(p["id"]),
                p.get("ref", ""),
                _status_text(p["status"]),
                created,
            )
    except GitLabError as exc:
        _error(t("pipelines.error", error=str(exc)))
        raise SystemExit(1)

    console.print(table)


# -- jobs ---------------------------------------------------------------


@main.command(cls=RichCommand, i18n_key="jobs")
@click.argument("repo")
@click.argument("pipeline_id", type=int, required=False, default=None)
@click.option(
    "-n",
    "--count",
    default=1,
    show_default=True,
    help="Show jobs from last N pipelines",
)
def jobs(repo: str, pipeline_id: int | None, count: int):
    """Display jobs for a pipeline (defaults to latest)."""
    config.require_init()
    client = _client()

    try:
        if pipeline_id is not None:
            # Explicit pipeline ID given – show only that one
            target_ids = [pipeline_id]
        else:
            # Fetch the last N pipelines
            recent = client.pipelines(repo, per_page=count)
            if not recent:
                _info(t("jobs.no_pipelines", repo=repo))
                return
            target_ids = [p["id"] for p in recent]

        for pid in target_ids:
            table = Table(
                title=t("jobs.title", repo=repo, pipeline_id=str(pid)),
                box=box.ROUNDED,
                title_style="bold blue",
            )
            table.add_column(t("table.id"), style="bold")
            table.add_column(t("table.stage"))
            table.add_column(t("table.name"))
            table.add_column(t("table.status"))
            table.add_column(t("table.duration"))

            for j in client.pipeline_jobs(repo, pid):
                dur = j.get("duration")
                table.add_row(
                    str(j["id"]),
                    j.get("stage", ""),
                    j["name"],
                    _status_text(j["status"]),
                    f"{dur:.0f}" if dur else "-",
                )

            console.print(table)
            console.print()

    except GitLabError as exc:
        _error(t("jobs.error", error=str(exc)))
        raise SystemExit(1)


# -- logs ---------------------------------------------------------------


@main.command(cls=RichCommand, i18n_key="logs")
@click.argument("repo")
@click.argument("job_id", type=int)
@click.option(
    "--tail",
    "-t",
    default=0,
    show_default=True,
    help="Show last N lines (0 = all)",
)
def logs(repo: str, job_id: int, tail: int):
    """Show logs for a job."""
    config.require_init()
    client = _client()

    try:
        log = client.job_log(repo, job_id)
    except GitLabError as exc:
        _error(t("logs.error", error=str(exc)))
        raise SystemExit(1)

    lines = log.splitlines()
    if tail:
        lines = lines[-tail:]

    for line in lines:
        # Print raw log lines; avoid Rich markup interpretation
        console.print(Text(line))


# -- images (container registry) ----------------------------------------


@main.command(cls=RichCommand, i18n_key="images")
@click.argument("repo")
def images(repo: str):
    """Show Container Registry images for a repo."""
    config.require_init()
    client = _client()

    try:
        registries = client.registry_repos(repo)
    except GitLabError as exc:
        _error(t("images.error", error=str(exc)))
        raise SystemExit(1)

    if not registries:
        _info(t("images.empty", repo=repo))
        return

    for reg in registries:
        reg_path = reg.get("path", str(reg["id"]))
        console.print()
        console.print(Text(reg_path, style="bold"))

        tags = client.registry_tags(repo, reg["id"])
        if not tags:
            console.print(Text(f"  {t('images.no_tags')}", style="dim"))
            continue

        table = Table(box=box.SIMPLE)
        table.add_column(t("table.tag"))
        table.add_column(t("table.size"))
        table.add_column(t("table.created"))

        for tag in tags:
            size_mb = (tag.get("total_size") or 0) / 1_048_576
            created = (tag.get("created_at") or "")[:19].replace("T", " ")
            table.add_row(
                tag["name"],
                f"{size_mb:.1f} MB" if size_mb else "-",
                created,
            )
        console.print(table)


# -- mrs ----------------------------------------------------------------


@main.command(cls=RichCommand, i18n_key="mrs")
@click.argument("repo")
@click.option(
    "--state",
    default="opened",
    show_default=True,
    type=click.Choice(["opened", "merged", "closed", "all"]),
)
def mrs(repo: str, state: str):
    """Show merge requests."""
    config.require_init()
    client = _client()

    table = Table(
        title=t("mrs.title", repo=repo, state=state),
        box=box.ROUNDED,
        title_style="bold blue",
    )
    table.add_column(t("table.id"), style="bold")
    table.add_column(t("table.title"))
    table.add_column(t("table.author"))
    table.add_column(t("table.state"))

    try:
        for mr in client.merge_requests(repo, state):
            table.add_row(
                f"!{mr['iid']}",
                mr["title"][:60],
                mr.get("author", {}).get("username", "?"),
                mr["state"],
            )
    except GitLabError as exc:
        _error(t("mrs.error", error=str(exc)))
        raise SystemExit(1)

    console.print(table)


# -- envs ---------------------------------------------------------------


@main.command(cls=RichCommand, i18n_key="envs")
@click.argument("repo")
def envs(repo: str):
    """Show environments for a repo."""
    config.require_init()
    client = _client()

    table = Table(
        title=t("envs.title", repo=repo),
        box=box.ROUNDED,
        title_style="bold blue",
    )
    table.add_column(t("table.id"), style="bold")
    table.add_column(t("table.name"))
    table.add_column(t("table.url"))
    table.add_column(t("table.state"))

    try:
        for env in client.environments(repo):
            table.add_row(
                str(env["id"]),
                env["name"],
                env.get("external_url", "-") or "-",
                env.get("state", "?"),
            )
    except GitLabError as exc:
        _error(t("envs.error", error=str(exc)))
        raise SystemExit(1)

    console.print(table)


# -- language -----------------------------------------------------------


@main.command(cls=RichCommand, i18n_key="language")
@click.argument("lang", required=False, default=None)
def language(lang: str | None):
    """Set or show the display language."""
    if lang is None:
        cur = current_language()
        _info(t("language.current", lang=cur))
        available = ", ".join(supported_languages())
        console.print(Text(f"  {t('language.available', langs=available)}", style="dim"))
        return

    if lang not in supported_languages():
        available = ", ".join(supported_languages())
        _error(t("language.invalid", lang=lang, available=available))
        raise SystemExit(1)

    cfg = config.load()
    cfg["language"] = lang
    config.save(cfg)

    # Reload so the success message is in the new language
    load_lang(lang)
    _success(t("language.success", lang=lang))


# -- entry point --------------------------------------------------------

if __name__ == "__main__":
    main()