"""The fetching rules: cache first, wait your turn, ask permission."""

from __future__ import annotations

import json
import os
import time
from datetime import date, timedelta
from pathlib import Path

import httpx
import pytest

from livingdex_pipeline.http import DiskCache, PoliteClient, RobotsDisallowed

ROBOTS_ALLOW_ALL = "User-agent: *\nDisallow:\n"
ROBOTS_DISALLOW_WIKI = "User-agent: *\nDisallow: /wiki/\n"


class Recorder:
    """A transport that answers from a script and remembers what was asked."""

    def __init__(self, routes: dict[str, str], robots: str = ROBOTS_ALLOW_ALL) -> None:
        self.routes = routes
        self.robots = robots
        self.requests: list[str] = []

    def transport(self) -> httpx.MockTransport:
        def handle(request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            self.requests.append(url)

            if request.url.path == "/robots.txt":
                return httpx.Response(200, text=self.robots)

            if url in self.routes:
                return httpx.Response(200, text=self.routes[url])

            return httpx.Response(404, text="not here")

        return httpx.MockTransport(handle)


def client_for(recorder: Recorder, cache: Path, **kwargs) -> PoliteClient:
    return PoliteClient(
        cache,
        client=httpx.Client(transport=recorder.transport()),
        sleep=lambda _: None,
        **kwargs,
    )


def test_a_page_is_fetched_once_and_then_read_from_disk(tmp_path: Path) -> None:
    recorder = Recorder({"https://example.test/a": "hello"})

    with client_for(recorder, tmp_path) as client:
        first = client.fetch("https://example.test/a")
        second = client.fetch("https://example.test/a")

    assert first.body == b"hello"
    assert first.from_cache is False
    assert second.from_cache is True

    # robots.txt once, the page once. The second call never left the machine.
    assert recorder.requests.count("https://example.test/a") == 1


def test_the_cache_survives_a_new_client(tmp_path: Path) -> None:
    recorder = Recorder({"https://example.test/a": "hello"})

    with client_for(recorder, tmp_path) as client:
        client.fetch("https://example.test/a")

    with client_for(recorder, tmp_path) as second_client:
        again = second_client.fetch("https://example.test/a")

    assert again.from_cache is True
    assert recorder.requests.count("https://example.test/a") == 1


def test_refresh_goes_back_to_the_source(tmp_path: Path) -> None:
    recorder = Recorder({"https://example.test/a": "hello"})

    with client_for(recorder, tmp_path) as client:
        client.fetch("https://example.test/a")
        again = client.fetch("https://example.test/a", refresh=True)

    assert again.from_cache is False
    assert recorder.requests.count("https://example.test/a") == 2


def test_robots_txt_is_obeyed_rather_than_worked_around(tmp_path: Path) -> None:
    recorder = Recorder(
        {"https://example.test/wiki/Bulbasaur": "page"}, robots=ROBOTS_DISALLOW_WIKI
    )

    with client_for(recorder, tmp_path) as client, pytest.raises(RobotsDisallowed):
        client.fetch("https://example.test/wiki/Bulbasaur")

    # The disallowed page was never requested, only robots.txt.
    assert recorder.requests == ["https://example.test/robots.txt"]


def test_a_site_with_no_robots_txt_is_still_rate_limited_but_not_refused(tmp_path: Path) -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)

        return httpx.Response(200, text="page")

    client = PoliteClient(
        tmp_path,
        client=httpx.Client(transport=httpx.MockTransport(handle)),
        sleep=lambda _: None,
    )

    with client:
        assert client.get_text("https://example.test/a") == "page"


def test_requests_to_one_host_are_spaced_out(tmp_path: Path) -> None:
    recorder = Recorder({f"https://example.test/{n}": "x" for n in range(3)})
    slept: list[float] = []

    client = PoliteClient(
        tmp_path,
        min_interval_seconds=2.0,
        client=httpx.Client(transport=recorder.transport()),
        sleep=slept.append,
    )

    with client:
        for n in range(3):
            client.fetch(f"https://example.test/{n}")

    # robots.txt plus three pages: every request after the first waits.
    assert len(slept) >= 3
    assert all(delay <= 2.0 for delay in slept)


def test_a_failed_request_is_not_cached(tmp_path: Path) -> None:
    recorder = Recorder({})

    with client_for(recorder, tmp_path) as client:
        with pytest.raises(httpx.HTTPStatusError):
            client.fetch("https://example.test/missing")

        with pytest.raises(httpx.HTTPStatusError):
            client.fetch("https://example.test/missing")

    assert recorder.requests.count("https://example.test/missing") == 2


def test_json_comes_back_parsed(tmp_path: Path) -> None:
    recorder = Recorder({"https://example.test/a.json": '{"name": "chimchar"}'})

    with client_for(recorder, tmp_path) as client:
        assert client.get_json("https://example.test/a.json") == {"name": "chimchar"}


def cached_files(root: Path, url: str) -> tuple[Path, Path]:
    """The body and the metadata one url was cached as.

    Found by reading the metadata rather than by rebuilding the cache's own naming, so a test
    that pokes at the files does not have to know how they are named. robots.txt is cached
    beside the page, which is why matching on the url is what this does.
    """
    for meta_path in sorted(root.rglob("*.json")):
        if json.loads(meta_path.read_text(encoding="utf-8"))["url"] == url:
            return meta_path.with_suffix(".body"), meta_path

    raise AssertionError(f"{url} is not in the cache under {root}")


def test_a_cached_page_keeps_the_day_it_was_actually_fetched(tmp_path: Path) -> None:
    # The date a citation carries is a claim about when a source was read, so it has to survive
    # a rebuild. Stamping it with today's date on every build made a dataset that had not
    # changed look as though every fact in it had been checked again this morning.
    recorder = Recorder({"https://example.test/a": "hello"})
    last_week = date.today() - timedelta(days=7)

    with client_for(recorder, tmp_path) as client:
        client.fetch("https://example.test/a")

    # Age the entry by hand: what matters is that the answer comes from what was written
    # beside the body rather than from the clock.
    _, meta_path = cached_files(tmp_path, "https://example.test/a")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["retrieved_on"] = last_week.isoformat()
    meta_path.write_text(json.dumps(meta), encoding="utf-8")

    with client_for(recorder, tmp_path) as client:
        again = client.fetch("https://example.test/a")

        assert again.from_cache is True
        assert again.retrieved_on == last_week
        assert client.retrieved_on("https://example.test/a") == last_week


def test_a_page_fetched_now_is_dated_now(tmp_path: Path) -> None:
    recorder = Recorder({"https://example.test/a": "hello"})

    with client_for(recorder, tmp_path) as client:
        fresh = client.fetch("https://example.test/a")

    assert fresh.from_cache is False
    assert fresh.retrieved_on == date.today()


def test_a_page_nobody_has_fetched_is_dated_today(tmp_path: Path) -> None:
    # Today is the honest answer for something this build is about to ask for.
    recorder = Recorder({})

    with client_for(recorder, tmp_path) as client:
        assert client.retrieved_on("https://example.test/never") == date.today()


def test_an_old_cache_entry_falls_back_to_the_file_it_was_written_as(tmp_path: Path) -> None:
    # Entries written before the date was recorded have no metadata to read. The file's own
    # timestamp is the same fact by a less reliable route, and it beats calling a cache from
    # last year today's news.
    cache = DiskCache(tmp_path)
    cache.put("https://example.test/old", b"hello")

    body_path, meta_path = cached_files(tmp_path, "https://example.test/old")
    meta_path.unlink()
    long_ago = time.time() - 60 * 60 * 24 * 30
    os.utime(body_path, (long_ago, long_ago))

    assert cache.retrieved_on("https://example.test/old") == date.fromtimestamp(long_ago)


def test_a_url_that_was_never_cached_has_no_date_of_its_own(tmp_path: Path) -> None:
    assert DiskCache(tmp_path).retrieved_on("https://example.test/nothing") is None
