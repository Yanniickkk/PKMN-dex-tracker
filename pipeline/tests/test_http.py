"""The fetching rules: cache first, wait your turn, ask permission."""

from __future__ import annotations

import json
import os
import time
from datetime import date, timedelta
from pathlib import Path

import httpx
import pytest

from livingdex_pipeline.http import DiskCache, MemoryCache, PoliteClient, RobotsDisallowed

ROBOTS_ALLOW_ALL = "User-agent: *\nDisallow:\n"
ROBOTS_DISALLOW_WIKI = "User-agent: *\nDisallow: /wiki/\n"


class Recorder:
    """A transport that answers from a script and remembers what was asked."""

    def __init__(
        self,
        routes: dict[str, str],
        robots: str = ROBOTS_ALLOW_ALL,
        status: int = 404,
    ) -> None:
        self.routes = routes
        self.robots = robots
        #: What an unknown url answers. 404 unless a test is about a server having a bad
        #: minute, which is a different kind of no.
        self.status = status
        self.requests: list[str] = []

    def transport(self) -> httpx.MockTransport:
        def handle(request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            self.requests.append(url)

            if request.url.path == "/robots.txt":
                return httpx.Response(200, text=self.robots)

            if url in self.routes:
                return httpx.Response(200, text=self.routes[url])

            return httpx.Response(self.status, text="not here")

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


def test_a_missing_thing_is_only_asked_for_once(tmp_path: Path) -> None:
    """A 404 is an answer, and it does not change.

    The sprite steps live on this. A sheet only draws what its generation drew, and a form's
    file is found by asking for several names until one answers - so a build asks for hundreds
    of pictures that are not there. Asking again on every build for ever costs a request and a
    wait each time, for an answer nobody expects to change.
    """
    recorder = Recorder({})

    with client_for(recorder, tmp_path) as client:
        for _ in range(2):
            with pytest.raises(httpx.HTTPStatusError):
                client.fetch("https://example.test/missing")

    assert recorder.requests.count("https://example.test/missing") == 1


def test_a_server_having_a_bad_minute_is_asked_again(tmp_path: Path) -> None:
    """The other half of the rule, and the one that keeps it safe.

    A 500 or a 429 is about the server or the moment rather than about the url. Writing one down
    as "not there" would turn a blip into a permanent hole in the dataset that only --refresh
    could ever fill.
    """
    recorder = Recorder({}, status=503)

    with client_for(recorder, tmp_path) as client:
        for _ in range(2):
            with pytest.raises(httpx.HTTPStatusError):
                client.fetch("https://example.test/wobbly")

    assert recorder.requests.count("https://example.test/wobbly") == 2


def test_what_has_been_read_is_not_read_again(tmp_path: Path) -> None:
    """The second ask does not touch the disk at all."""
    recorder = Recorder({"https://example.test/a.json": '{"name": "rowlet"}'})

    with client_for(recorder, tmp_path) as client:
        client.fetch("https://example.test/a.json")
        assert client.from_disk == 0  # it was fetched, not read back
        assert client.memory.hits == 0

        client.fetch("https://example.test/a.json")
        assert client.memory.hits == 1
        assert client.from_disk == 0


def test_a_shared_memory_is_shared(tmp_path: Path) -> None:
    """Two clients over one cache directory, which is what a build runs.

    One is paced for an API and one for a wiki, and what either has read the other should not
    read again.
    """
    recorder = Recorder({"https://example.test/a.json": '{"name": "litten"}'})
    shared = MemoryCache()

    with client_for(recorder, tmp_path, memory=shared) as one:
        one.fetch("https://example.test/a.json")

    with client_for(recorder, tmp_path, memory=shared) as two:
        two.fetch("https://example.test/a.json")
        assert two.memory.hits == 1
        assert two.from_disk == 0

    assert recorder.requests.count("https://example.test/a.json") == 1


def test_memory_gives_up_its_coldest_when_it_is_full() -> None:
    memory = MemoryCache(limit=20)

    memory.put("a", b"0123456789")
    memory.put("b", b"0123456789")
    assert memory.get("a") == b"0123456789"

    # "b" is the colder of the two now, so it is the one that goes.
    memory.put("c", b"0123456789")

    assert memory.get("b") is None
    assert memory.get("a") == b"0123456789"
    assert memory.get("c") == b"0123456789"


def test_one_thing_too_big_for_the_budget_does_not_empty_it() -> None:
    memory = MemoryCache(limit=20)
    memory.put("small", b"0123456789")
    memory.put("huge", b"x" * 100)

    assert memory.get("small") == b"0123456789"
    assert memory.get("huge") is None


def test_the_date_is_only_read_when_it_is_wanted(tmp_path: Path) -> None:
    """Reading it opens a second file, and the sprite steps never want it."""
    recorder = Recorder({"https://example.test/a.png": "x"})

    with client_for(recorder, tmp_path) as client:
        client.fetch("https://example.test/a.png")
        entry = client.fetch("https://example.test/a.png")

        # Nothing has been read off disk: the body came from memory and the date was not asked
        # for, so the metadata file beside it was never opened.
        assert client.from_disk == 0
        assert entry.retrieved_on == date.today()


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


def test_a_collection_is_dated_by_the_newest_thing_read_under_it(tmp_path: Path) -> None:
    # The evolution graph is read chain by chain and cited as the collection, and a collection
    # url is one no build ever fetches. Asking the cache about it got nothing and fell through
    # to today, so that citation moved every day while the chains behind it had not been read
    # in a week.
    cache = DiskCache(tmp_path)
    cache.put("https://example.test/chain/1", b"one", retrieved_on=date(2026, 9, 20))
    cache.put("https://example.test/chain/2", b"two", retrieved_on=date(2026, 9, 22))
    cache.put("https://example.test/other/9", b"nine", retrieved_on=date(2026, 9, 25))

    assert cache.newest_under("https://example.test/chain") == date(2026, 9, 22)


def test_a_refusal_is_not_something_that_was_read(tmp_path: Path) -> None:
    # A remembered 404 carries a date too, and it is the day nobody got an answer.
    cache = DiskCache(tmp_path)
    cache.put("https://example.test/chain/1", b"one", retrieved_on=date(2026, 9, 20))
    cache.refuse("https://example.test/chain/2", 404, on=date(2026, 9, 25))

    assert cache.newest_under("https://example.test/chain") == date(2026, 9, 20)


def test_a_collection_nothing_was_read_under_has_no_date(tmp_path: Path) -> None:
    assert DiskCache(tmp_path).newest_under("https://example.test/chain") is None
