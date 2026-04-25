"""Thin wrapper around the GitLab v4 REST API."""

from __future__ import annotations

from urllib.parse import quote as urlquote

import requests

from cicd.i18n import t


class GitLabError(Exception):
    pass


class GitLabClient:
    """Stateless client - every method takes explicit params for easy testing."""

    def __init__(self, base_url: str, token: str, timeout: int = 15):
        self.base = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers["PRIVATE-TOKEN"] = token
        self.session.timeout = timeout  # type: ignore[assignment]

    # -- helpers ---------------------------------------------------------

    def _url(self, path: str) -> str:
        return f"{self.base}/api/v4{path}"

    def _get(self, path: str, **params) -> dict | list:
        resp = self.session.get(self._url(path), params=params)
        if resp.status_code == 401:
            raise GitLabError(t("error.invalid_token"))
        if resp.status_code == 404:
            raise GitLabError(t("error.not_found", path=path))
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def _enc(project_path: str) -> str:
        """URL-encode a 'group/project' path for the API."""
        return urlquote(project_path, safe="")

    # -- connection check ------------------------------------------------

    def ping(self) -> str:
        """Return GitLab version string or raise on failure."""
        data = self._get("/version")
        return data.get("version", "?")

    # -- projects --------------------------------------------------------

    def project(self, path: str) -> dict:
        return self._get(f"/projects/{self._enc(path)}")

    # -- pipelines -------------------------------------------------------

    def pipelines(self, path: str, per_page: int = 5) -> list[dict]:
        return self._get(
            f"/projects/{self._enc(path)}/pipelines",
            per_page=per_page,
            order_by="id",
            sort="desc",
        )

    def pipeline_jobs(self, path: str, pipeline_id: int) -> list[dict]:
        return self._get(
            f"/projects/{self._enc(path)}/pipelines/{pipeline_id}/jobs",
            per_page=100,
        )

    # -- container registry ----------------------------------------------

    def registry_repos(self, path: str) -> list[dict]:
        return self._get(
            f"/projects/{self._enc(path)}/registry/repositories",
            per_page=50,
        )

    def registry_tags(self, path: str, repo_id: int) -> list[dict]:
        return self._get(
            f"/projects/{self._enc(path)}/registry/repositories/{repo_id}/tags",
            per_page=50,
        )

    # -- merge requests --------------------------------------------------

    def merge_requests(self, path: str, state: str = "opened") -> list[dict]:
        return self._get(
            f"/projects/{self._enc(path)}/merge_requests",
            state=state,
            per_page=20,
            order_by="updated_at",
            sort="desc",
        )

    # -- environments ----------------------------------------------------

    def environments(self, path: str) -> list[dict]:
        return self._get(
            f"/projects/{self._enc(path)}/environments",
            per_page=20,
        )

    # -- job log ---------------------------------------------------------

    def job_log(self, path: str, job_id: int) -> str:
        resp = self.session.get(
            self._url(f"/projects/{self._enc(path)}/jobs/{job_id}/trace")
        )
        resp.raise_for_status()
        return resp.text