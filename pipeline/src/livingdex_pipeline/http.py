"""Fetching things from the internet, once.

Everything the pipeline downloads goes through here, for three reasons:

* An on-disk cache means a rebuild costs nothing and a failed run does not re-ask for what it
  already had. Most of what we fetch never changes.
* A per-host rate limit keeps us from hammering sites that are doing us a favour by existing.
* ``robots.txt`` is checked before a page is requested, not after.
* An in-memory cache on top of the disk one, because "costs nothing" was not true. A build asks
  for the same document again and again - five separate readers want
  ``pokemon-species/shellos`` while one game is being written, and all 28 games want it - and
  each of those was a file read and a JSON parse. Over three games, 12484 reads were 2644
  distinct documents: **79% of the fetching was the same answer over again.**
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import urllib.robotparser
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx

log = logging.getLogger(__name__)

#: Statuses that mean the thing is not there, rather than that this moment went badly.
#:
#: Only these are written down as refusals. A timeout, a 500 or a 429 is about the server or the
#: minute, and remembering one as "no" would put a permanent hole in the dataset over a blip.
GONE_FOR_GOOD = frozenset({404, 410})

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
    #: How to find out when this body came off the network, whether that was a moment ago or
    #: last month. It is what a citation means by "retrieved on", and it is why that date does
    #: not move every time the dataset is rebuilt from a cache that has not changed.
    #:
    #: A function rather than the date itself, because reading it means opening a second file
    #: and parsing it, and the callers that want it are a small minority: the sprite steps ask
    #: for eight thousand bodies a build and none of them cares what day it arrived.
    dated: Callable[[], date]

    @property
    def retrieved_on(self) -> date:
        return self.dated()


#: How much of what has been read is kept in memory, in bytes of raw body.
#:
#: Counted in bytes and not in entries because the documents are not the same size: a location
#: is a few hundred bytes and a Pokemon with its whole moveset is forty kilobytes, and an entry
#: count would either hold almost nothing or almost everything depending on which it met first.
#:
#: 192 MB against a cache that is 375 MB of PokeAPI JSON on disk. A build touches well under
#: half of it - three games shared a working set of 59 MB - so in practice the whole of what a
#: build re-reads fits, and a bigger build evicts the coldest rather than growing without end.
DEFAULT_MEMORY_BYTES = 192 * 1024 * 1024


class MemoryCache:
    """What has already been read, until it is pushed out by something newer.

    Least-recently-used, which is the right shape for the wrong-looking reason. The re-reads are
    not close together in time - a species is read by the wild step, then by the gift step a
    thousand species later, then by every other game - so a small cache saves nothing at all. It
    was measured: holding 256 entries saved 1% of the reads and holding the working set saved
    79%. So this is sized to hold a working set, and LRU only decides what goes when one build
    is bigger than the budget.

    Bodies rather than parsed objects, because bytes are what can be measured and a parsed
    document is several times its own size in ways nothing here can see. The parse is paid again
    on every hit, and it is the cheap half: the file read is what costs on a cold cache.
    """

    def __init__(self, limit: int = DEFAULT_MEMORY_BYTES) -> None:
        self.limit = limit
        self.hits = 0
        self.misses = 0
        self._held: OrderedDict[str, bytes] = OrderedDict()
        self._bytes = 0

    def get(self, url: str) -> bytes | None:
        body = self._held.get(url)
        if body is None:
            self.misses += 1
            return None

        self._held.move_to_end(url)
        self.hits += 1
        return body

    def put(self, url: str, body: bytes) -> None:
        # A single document larger than the whole budget would evict everything and then itself.
        if len(body) > self.limit:
            return

        if url in self._held:
            self._bytes -= len(self._held.pop(url))

        self._held[url] = body
        self._bytes += len(body)

        while self._bytes > self.limit:
            _, gone = self._held.popitem(last=False)
            self._bytes -= len(gone)

    def __len__(self) -> int:
        return len(self._held)

    @property
    def held_bytes(self) -> int:
        return self._bytes


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

    def refused(self, url: str) -> int | None:
        """The status a previous run was refused with, if it was refused.

        A missing sprite is not an error and not a surprise: a sheet only draws what its
        generation drew, and :func:`_first_picture` finds a form's file by asking for several
        names until one answers. Without this, every one of those "no" answers is asked again
        on every build for ever, and pays the rate limit each time.

        Only the codes that mean the thing is not there. A timeout, a 500 or a rate-limit
        refusal is about this moment rather than about the URL, and remembering it would turn a
        bad minute into a permanent hole in the dataset.
        """
        _, meta_path = self._paths(url)
        if not meta_path.exists():
            return None

        try:
            status = json.loads(meta_path.read_text(encoding="utf-8")).get("refused")
        except (OSError, json.JSONDecodeError):
            return None

        return int(status) if status is not None else None

    def refuse(self, url: str, status: int, *, on: date | None = None) -> None:
        """Write down that this url answered "not here", so nobody asks again."""
        _, meta_path = self._paths(url)
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.write_text(
            json.dumps(
                {
                    "url": url,
                    "refused": status,
                    "retrieved_on": (on or date.today()).isoformat(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def put(self, url: str, body: bytes, *, retrieved_on: date | None = None) -> None:
        body_path, meta_path = self._paths(url)
        body_path.parent.mkdir(parents=True, exist_ok=True)
        body_path.write_bytes(body)
        meta_path.write_text(
            json.dumps(
                {
                    "url": url,
                    "bytes": len(body),
                    "retrieved_on": (retrieved_on or date.today()).isoformat(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def retrieved_on(self, url: str) -> date | None:
        """The day this body was fetched, or nothing if it was never fetched.

        From the metadata beside the body rather than the file's timestamp, because a cache
        that is copied, restored from a backup or checked out again keeps its metadata and
        loses its timestamps. The timestamp is the fallback for entries written before this
        was recorded: it is the same fact by a less reliable route, and it beats calling
        everything in an old cache today's news.
        """
        body_path, meta_path = self._paths(url)
        if not body_path.exists():
            return None

        if meta_path.exists():
            try:
                recorded = json.loads(meta_path.read_text(encoding="utf-8")).get("retrieved_on")
            except (OSError, ValueError):
                recorded = None

            if recorded:
                return date.fromisoformat(recorded)

        return date.fromtimestamp(body_path.stat().st_mtime)

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
        memory: MemoryCache | None = None,
    ) -> None:
        self.cache = DiskCache(cache_dir)
        # Shared when one is handed in: a build runs two of these - one paced for an API and one
        # for a wiki - over the same cache directory, and what one of them has read the other
        # should not read again.
        self.memory = memory if memory is not None else MemoryCache()
        self.from_disk = 0
        self.fetched = 0
        self.refused = 0
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
        """The bytes at ``url``, from memory, then from the cache, then from the network.

        The date is read lazily. It costs a second file and a JSON parse, almost nobody wants it
        - a sprite is bytes to write out and nothing else - and asking for it on every hit
        doubled the file operations of the longest step in the build.
        """
        if not refresh:
            held = self.memory.get(url)
            if held is not None:
                return CacheEntry(url=url, body=held, from_cache=True, dated=self._dated(url))

            cached = self.cache.get(url)
            if cached is not None:
                log.debug("cache hit %s", url)
                self.from_disk += 1
                self.memory.put(url, cached)
                return CacheEntry(url=url, body=cached, from_cache=True, dated=self._dated(url))

            # Asked before and told it is not there. Costs a request and a wait every build
            # otherwise, for an answer that has not changed since the last one.
            if (status := self.cache.refused(url)) is not None:
                self.refused += 1
                log.debug("cached refusal %s for %s", status, url)
                raise httpx.HTTPStatusError(
                    f"Client error '{status}' for url '{url}' (remembered from a previous build)",
                    request=httpx.Request("GET", url),
                    response=httpx.Response(status, request=httpx.Request("GET", url)),
                )

        # robots.txt itself is exempt, or checking it would need itself first.
        if self.respect_robots and urlsplit(url).path != "/robots.txt" and not self._allowed(url):
            raise RobotsDisallowed(url)

        self._wait_turn(urlsplit(url).netloc)
        log.info("GET %s", url)
        self.fetched += 1
        response = self._client.get(url)

        if response.status_code in GONE_FOR_GOOD:
            self.cache.refuse(url, response.status_code)

        response.raise_for_status()

        today = date.today()
        self.cache.put(url, response.content, retrieved_on=today)
        self.memory.put(url, response.content)

        return CacheEntry(url=url, body=response.content, from_cache=False, dated=lambda: today)

    def _dated(self, url: str):
        """When this body was fetched, worked out only if somebody asks."""
        return lambda: self.cache.retrieved_on(url) or date.today()

    def traffic(self) -> str:
        """One line on how the fetching went, for the build summary."""
        memory = self.memory

        return (
            f"fetched {self.fetched}, {self.from_disk} off disk, {memory.hits} from memory "
            f"({memory.held_bytes / 1048576:.0f} MB held), {self.refused} refusals remembered"
        )

    def retrieved_on(self, url: str) -> date:
        """When the answer at this url was fetched, for whoever has to cite it.

        Today for anything not in the cache, which is the honest answer for a page this build
        is about to ask for.
        """
        return self.cache.retrieved_on(url) or date.today()

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
