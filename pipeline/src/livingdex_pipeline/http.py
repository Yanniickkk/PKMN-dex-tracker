"""Fetching things from the internet, once.

Everything the pipeline downloads goes through here, for three reasons:

* An on-disk cache means a rebuild costs nothing and a failed run does not re-ask for what it
  already had. Most of what we fetch never changes.
* A per-host rate limit keeps us from hammering sites that are doing us a favour by existing.
* ``robots.txt`` is checked before a page is requested, not after.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import urllib.robotparser
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx

log = logging.getLogger(__name__)

#: Identifies the project and gives an operator somewhere to complain.
USER_AGENT = "LivingDexTracker/0.1 (dataset build; +https://github.com/Yanniickkk/PKMN-dex-tracker)"


class RobotsDisallowed(Exception):
    """Raised when robots.txt says not to fetch a URL. Not retried, not worked around."""

    def __init__(self, url: str) -> None:
        super().__init__(f"robots.txt disallows {url}")
        self.url = url


@dataclass(frozen=True)
class CacheEntry:
    url: str
    body: bytes
    from_cache: bool


class DiskCache:
    """Response bodies on disk, keyed by URL.

    No expiry. Dex numbers and encounter tables are historical facts; when something really has
    changed, the answer is ``--refresh``, not a guessed TTL.
    """

    def __init__(self, root: Path) -> None:
        self.root = root

    def _paths(self, url: str) -> tuple[Path, Path]:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        host = urlsplit(url).netloc or "unknown"
        directory = self.root / host
        return directory / f"{digest}.body", directory / f"{digest}.json"

    def get(self, url: str) -> bytes | None:
        body_path, _ = self._paths(url)
        return body_path.read_bytes() if body_path.exists() else None

    def put(self, url: str, body: bytes) -> None:
        body_path, meta_path = self._paths(url)
        body_path.parent.mkdir(parents=True, exist_ok=True)
        body_path.write_bytes(body)
        meta_path.write_text(
            json.dumps({"url": url, "bytes": len(body)}, indent=2),
            encoding="utf-8",
        )

    def forget(self, url: str) -> None:
        for path in self._paths(url):
            path.unlink(missing_ok=True)


class PoliteClient:
    """An HTTP client that caches, waits its turn, and asks permission first."""

    def __init__(
        self,
        cache_dir: Path,
        *,
        min_interval_seconds: float = 1.0,
        respect_robots: bool = True,
        user_agent: str = USER_AGENT,
        client: httpx.Client | None = None,
        sleep=time.sleep,
    ) -> None:
        self.cache = DiskCache(cache_dir)
        self.min_interval_seconds = min_interval_seconds
        self.respect_robots = respect_robots
        self.user_agent = user_agent
        self._client = client or httpx.Client(
            headers={"User-Agent": user_agent},
            timeout=30.0,
            follow_redirects=True,
        )
        self._sleep = sleep
        self._last_request_at: dict[str, float] = {}
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}

    def __enter__(self) -> PoliteClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def fetch(self, url: str, *, refresh: bool = False) -> CacheEntry:
        """The bytes at ``url``, from the cache when we already have them."""
        if not refresh:
            cached = self.cache.get(url)
            if cached is not None:
                log.debug("cache hit %s", url)
                return CacheEntry(url=url, body=cached, from_cache=True)

        # robots.txt itself is exempt, or checking it would need itself first.
        if self.respect_robots and urlsplit(url).path != "/robots.txt" and not self._allowed(url):
            raise RobotsDisallowed(url)

        self._wait_turn(urlsplit(url).netloc)
        log.info("GET %s", url)
        response = self._client.get(url)
        response.raise_for_status()

        self.cache.put(url, response.content)
        return CacheEntry(url=url, body=response.content, from_cache=False)

    def get_text(self, url: str, *, refresh: bool = False) -> str:
        return self.fetch(url, refresh=refresh).body.decode("utf-8")

    def get_json(self, url: str, *, refresh: bool = False) -> Any:
        return json.loads(self.fetch(url, refresh=refresh).body)

    def _wait_turn(self, host: str) -> None:
        last = self._last_request_at.get(host)
        now = time.monotonic()

        if last is not None:
            remaining = self._interval_for(host) - (now - last)
            if remaining > 0:
                self._sleep(remaining)
                now = time.monotonic()

        self._last_request_at[host] = now

    def _interval_for(self, host: str) -> float:
        """How long to wait between requests to one host.

        A site that states a Crawl-delay is asking for it in writing, so it wins whenever it is
        the slower of the two. Our own interval is a floor, never a licence to go faster than
        the site asked.
        """
        parser = self._robots.get(host)
        declared = parser.crawl_delay(self.user_agent) if parser is not None else None

        return max(self.min_interval_seconds, float(declared or 0))

    def _allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        host = parts.netloc

        if host not in self._robots:
            self._robots[host] = self._load_robots(parts.scheme, host)

        parser = self._robots[host]
        # A site with no robots.txt, or one we could not read, is treated as allowing us. That
        # is what the standard says; the rate limit still applies.
        return True if parser is None else parser.can_fetch(self.user_agent, url)

    def _load_robots(self, scheme: str, host: str) -> urllib.robotparser.RobotFileParser | None:
        robots_url = urlunsplit((scheme or "https", host, "/robots.txt", "", ""))
        try:
            body = self.fetch(robots_url, refresh=False).body.decode("utf-8", errors="replace")
        except (httpx.HTTPError, OSError) as error:
            log.warning("could not read %s (%s); assuming crawling is allowed", robots_url, error)
            return None

        parser = urllib.robotparser.RobotFileParser()
        parser.parse(body.splitlines())
        return parser
