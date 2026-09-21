"""The fetching rules: cache first, wait your turn, ask permission."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from livingdex_pipeline.http import PoliteClient, RobotsDisallowed

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
