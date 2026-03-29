# app/integrations/github_service.py
"""
GitHub REST integration with demo_github MongoDB fallback.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import structlog

from app.config import settings
from app.db.mongo import get_collection
from app.lib.retry import llm_retry

log = structlog.get_logger()

GITHUB_API = "https://api.github.com"
DEMO_COLLECTION = "demo_github"


def _repo_parts() -> tuple[str, str]:
    r = settings.GITHUB_REPO.strip()
    parts = r.split("/", 1)
    if len(parts) != 2:
        raise ValueError("GITHUB_REPO must be owner/repo")
    return parts[0], parts[1]


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


@llm_retry(max_retries=3, base_delay=0.5, max_delay=8.0)
async def _http_get(client: httpx.AsyncClient, url: str) -> Any:
    r = await client.get(url, headers=_headers())
    r.raise_for_status()
    if not r.text.strip():
        return []
    return r.json()


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        s = ts.replace("Z", "+00:00") if ts.endswith("Z") else ts
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except ValueError:
        return None


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class GitHubService:
    """Async GitHub API helper; falls back to `demo_github` on failure."""

    @staticmethod
    async def _load_demo_docs() -> list[dict]:
        col = get_collection(DEMO_COLLECTION)
        return await col.find({}).to_list(length=500)

    @staticmethod
    def _aggregate_from_demo(docs: list[dict]) -> dict[str, Any]:
        commits = [d for d in docs if d.get("doc_type") == "commit"]
        prs = [d for d in docs if d.get("doc_type") == "pull_request"]

        commits_by_engineer: dict[str, list[dict]] = {}
        for c in commits:
            author = c.get("author", "unknown")
            commits_by_engineer.setdefault(author, []).append(
                {
                    "sha": c.get("sha"),
                    "message": c.get("message"),
                    "committed_at": c.get("committed_at"),
                }
            )

        prs_by_engineer: dict[str, list[dict]] = {}
        for p in prs:
            author = p.get("author", "unknown")
            prs_by_engineer.setdefault(author, []).append(
                {
                    "number": p.get("number"),
                    "title": p.get("title"),
                    "reviews": p.get("reviews", 0),
                    "hours_open": p.get("age_hours"),
                    "url": p.get("url"),
                }
            )

        reviews_by_engineer: dict[str, int] = {}
        for p in prs:
            author = p.get("author", "unknown")
            reviews_by_engineer[author] = reviews_by_engineer.get(author, 0) + int(
                p.get("reviews") or 0
            )

        return {
            "source": "demo_github",
            "commits": commits_by_engineer,
            "pull_requests": prs_by_engineer,
            "reviews": reviews_by_engineer,
        }

    @staticmethod
    async def get_recent_activity(hours: int = 24) -> dict[str, Any]:
        """
        Commits, PRs, and review counts aggregated per engineer.
        """
        owner, repo = _repo_parts()
        since = datetime.now(UTC) - timedelta(hours=hours)
        since_s = since.replace(microsecond=0).isoformat().replace("+00:00", "Z")

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                commits_url = (
                    f"{GITHUB_API}/repos/{owner}/{repo}/commits"
                    f"?since={since_s}&per_page=100"
                )
                pulls_url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls?state=open&per_page=100"

                commits_raw = await _http_get(client, commits_url)
                pulls_raw = await _http_get(client, pulls_url)

                commits_by_engineer: dict[str, list[dict]] = {}
                for c in commits_raw:
                    name = (
                        (c.get("commit") or {}).get("author") or {}
                    ).get("name") or (c.get("author") or {}).get("login", "unknown")
                    commits_by_engineer.setdefault(name, []).append(
                        {
                            "sha": c.get("sha"),
                            "message": (c.get("commit") or {}).get("message", "")[:200],
                            "committed_at": (c.get("commit") or {}).get("author", {}).get("date"),
                        }
                    )

                prs_by_engineer: dict[str, list[dict]] = {}
                reviews_totals: dict[str, int] = {}

                for p in pulls_raw:
                    user = (p.get("user") or {}).get("login", "unknown")
                    num = p.get("number")
                    created = _parse_iso(p.get("created_at"))
                    now = datetime.now(UTC)
                    hours_open = (
                        int((now - _ensure_utc(created)).total_seconds() / 3600)
                        if created
                        else 0
                    )
                    review_count = 0
                    try:
                        rev_url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{num}/reviews"
                        reviews = await _http_get(client, rev_url)
                        if isinstance(reviews, list):
                            review_count = len(reviews)
                    except Exception:
                        pass
                    entry = {
                        "number": num,
                        "title": p.get("title"),
                        "reviews": review_count,
                        "hours_open": hours_open,
                        "url": p.get("html_url"),
                    }
                    prs_by_engineer.setdefault(user, []).append(entry)
                    reviews_totals[user] = reviews_totals.get(user, 0) + review_count

            return {
                "source": "github_api",
                "window_hours": hours,
                "commits": commits_by_engineer,
                "pull_requests": prs_by_engineer,
                "reviews": reviews_totals,
            }
        except Exception as e:
            log.warning("github.get_recent_activity.fallback", error=str(e))
            docs = await GitHubService._load_demo_docs()
            agg = GitHubService._aggregate_from_demo(docs)
            agg["window_hours"] = hours
            return agg

    @staticmethod
    async def get_open_prs_with_age() -> list[dict[str, Any]]:
        """Open PRs with hours_open and review_count."""
        owner, repo = _repo_parts()
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                pulls_url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls?state=open&per_page=100"
                pulls_raw = await _http_get(client, pulls_url)
                out: list[dict[str, Any]] = []
                now = datetime.now(UTC)
                for p in pulls_raw:
                    num = p.get("number")
                    created = _parse_iso(p.get("created_at"))
                    hours_open = (
                        int((now - _ensure_utc(created)).total_seconds() / 3600)
                        if created
                        else 0
                    )
                    review_count = 0
                    try:
                        rev_url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{num}/reviews"
                        reviews = await _http_get(client, rev_url)
                        review_count = len(reviews) if isinstance(reviews, list) else 0
                    except Exception:
                        pass
                    out.append(
                        {
                            "number": num,
                            "title": p.get("title"),
                            "author": (p.get("user") or {}).get("login"),
                            "hours_open": hours_open,
                            "review_count": review_count,
                            "url": p.get("html_url"),
                        }
                    )
            return out
        except Exception as e:
            log.warning("github.get_open_prs.fallback", error=str(e))
            docs = await GitHubService._load_demo_docs()
            prs = [d for d in docs if d.get("doc_type") == "pull_request"]
            return [
                {
                    "number": p.get("number"),
                    "title": p.get("title"),
                    "author": p.get("author"),
                    "hours_open": p.get("age_hours", 0),
                    "review_count": p.get("reviews", 0),
                    "url": p.get("url"),
                }
                for p in prs
            ]

    @staticmethod
    async def get_commit_activity_per_engineer() -> dict[str, int]:
        """Engineer -> commit count in the last 24 hours."""
        owner, repo = _repo_parts()
        since = datetime.now(UTC) - timedelta(hours=24)
        since_s = since.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                commits_url = (
                    f"{GITHUB_API}/repos/{owner}/{repo}/commits"
                    f"?since={since_s}&per_page=100"
                )
                commits_raw = await _http_get(client, commits_url)
            counts: dict[str, int] = {}
            for c in commits_raw:
                name = (
                    (c.get("commit") or {}).get("author") or {}
                ).get("name") or (c.get("author") or {}).get("login", "unknown")
                counts[name] = counts.get(name, 0) + 1
            return counts
        except Exception as e:
            log.warning("github.commit_activity.fallback", error=str(e))
            docs = await GitHubService._load_demo_docs()
            commits = [d for d in docs if d.get("doc_type") == "commit"]
            cutoff = datetime.now(UTC) - timedelta(hours=24)
            counts: dict[str, int] = {}
            for c in commits:
                ts = _parse_iso(c.get("committed_at"))
                if ts is None:
                    continue
                tsu = _ensure_utc(ts)
                if tsu < cutoff:
                    continue
                author = c.get("author", "unknown")
                counts[author] = counts.get(author, 0) + 1
            return counts

    @staticmethod
    async def get_velocity_per_engineer(sprints: int = 3) -> dict[str, float]:
        """
        Engineer -> average story points over recent sprints.
        GitHub has no native story points; API success uses commit throughput as a proxy.
        Falls back to demo heuristic when the API is unavailable.
        """
        owner, repo = _repo_parts()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                commits_url = f"{GITHUB_API}/repos/{owner}/{repo}/commits?per_page=100"
                commits_raw = await _http_get(client, commits_url)
            counts: dict[str, int] = {}
            for c in commits_raw:
                name = (
                    (c.get("commit") or {}).get("author") or {}
                ).get("name") or (c.get("author") or {}).get("login", "unknown")
                counts[name] = counts.get(name, 0) + 1
            total = sum(counts.values()) or 1
            base = 12.0 * sprints
            return {n: round(base * (cnt / total), 1) for n, cnt in counts.items()}
        except Exception as e:
            log.warning("github.velocity.fallback", error=str(e))
            docs = await GitHubService._load_demo_docs()
            commits = [d for d in docs if d.get("doc_type") == "commit"]
            counts: dict[str, int] = {}
            for c in commits:
                a = c.get("author", "unknown")
                counts[a] = counts.get(a, 0) + 1
            total = sum(counts.values()) or 1
            base = 12.0 * sprints
            return {name: round(base * (n / total), 1) for name, n in counts.items()}

    @staticmethod
    async def get_merged_pull_requests(days: int = 7) -> list[dict[str, Any]]:
        """Recently merged PRs (for weekly status reports)."""
        owner, repo = _repo_parts()
        cutoff = datetime.now(UTC) - timedelta(days=days)
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                url = (
                    f"{GITHUB_API}/repos/{owner}/{repo}/pulls"
                    "?state=closed&sort=updated&direction=desc&per_page=80"
                )
                pulls_raw = await _http_get(client, url)
            out: list[dict[str, Any]] = []
            for p in pulls_raw:
                merged_at = _parse_iso(p.get("merged_at"))
                if merged_at is None:
                    continue
                if _ensure_utc(merged_at) < cutoff:
                    continue
                out.append(
                    {
                        "number": p.get("number"),
                        "title": p.get("title"),
                        "merged_at": p.get("merged_at"),
                        "url": p.get("html_url"),
                    }
                )
            return out
        except Exception as e:
            log.warning("github.get_merged_pull_requests.fallback", error=str(e))
            docs = await GitHubService._load_demo_docs()
            prs = [d for d in docs if d.get("doc_type") == "pull_request"]
            out: list[dict[str, Any]] = []
            for p in prs:
                out.append(
                    {
                        "number": p.get("number"),
                        "title": p.get("title"),
                        "merged_at": p.get("merged_at") or p.get("committed_at"),
                        "url": p.get("url"),
                    }
                )
            return out[:20]

    @staticmethod
    async def get_team_members() -> list[str]:
        """Engineer names from recent commits."""
        owner, repo = _repo_parts()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                commits_url = f"{GITHUB_API}/repos/{owner}/{repo}/commits?per_page=50"
                commits_raw = await _http_get(client, commits_url)
            names: list[str] = []
            seen: set[str] = set()
            for c in commits_raw:
                name = (
                    (c.get("commit") or {}).get("author") or {}
                ).get("name") or (c.get("author") or {}).get("login", "unknown")
                if name not in seen:
                    seen.add(name)
                    names.append(name)
            return names
        except Exception as e:
            log.warning("github.team_members.fallback", error=str(e))
            docs = await GitHubService._load_demo_docs()
            commits = [d for d in docs if d.get("doc_type") == "commit"]
            seen: set[str] = set()
            out: list[str] = []
            for c in commits:
                a = c.get("author", "unknown")
                if a not in seen:
                    seen.add(a)
                    out.append(a)
            return out
