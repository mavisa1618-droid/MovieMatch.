"""Tests for moviematch.posters (no real internet access is used)."""
from __future__ import annotations

import json
import urllib.error

import pytest

from moviematch import posters
from tests.conftest import make_movie


@pytest.fixture(autouse=True)
def clear_cache():
    posters._poster_cache.clear()


@pytest.fixture
def toy_story():
    movie = make_movie(1, 'Toy Story (1995)')
    movie.tmdb_id = '862'
    return movie


def fake_tmdb(responses: dict[str, bytes], calls: list[str]):
    """Return a stand-in for posters._download that answers from responses."""
    def download(url: str) -> bytes:
        calls.append(url)
        for prefix, body in responses.items():
            if url.startswith(prefix):
                return body
        raise urllib.error.URLError('not found')
    return download


def test_no_api_key_means_no_poster(monkeypatch, toy_story) -> None:
    monkeypatch.delenv('TMDB_API_KEY', raising=False)
    assert posters.get_poster(toy_story) is None


def test_movie_without_tmdb_id(monkeypatch) -> None:
    monkeypatch.setenv('TMDB_API_KEY', 'test')
    assert posters.get_poster(make_movie(2, 'Unknown (2000)')) is None


def test_downloads_poster_once_and_caches_it(monkeypatch, toy_story) -> None:
    monkeypatch.setenv('TMDB_API_KEY', 'test')
    calls = []
    monkeypatch.setattr(posters, '_download', fake_tmdb({
        'https://api.themoviedb.org/3/movie/862': json.dumps({'poster_path': '/toy.jpg'}).encode(),
        'https://image.tmdb.org/t/p/w92/toy.jpg': b'JPEG-BYTES',
    }, calls))

    assert posters.get_poster(toy_story) == b'JPEG-BYTES'
    assert posters.get_poster(toy_story) == b'JPEG-BYTES'
    assert len(calls) == 2  # one details request + one image request, not repeated


def test_movie_with_no_poster(monkeypatch, toy_story) -> None:
    monkeypatch.setenv('TMDB_API_KEY', 'test')
    monkeypatch.setattr(posters, '_download', fake_tmdb({
        'https://api.themoviedb.org/3/movie/862': json.dumps({'poster_path': None}).encode(),
    }, []))
    assert posters.get_poster(toy_story) is None


def test_network_error_returns_none(monkeypatch, toy_story) -> None:
    monkeypatch.setenv('TMDB_API_KEY', 'test')
    monkeypatch.setattr(posters, '_download', fake_tmdb({}, []))
    assert posters.get_poster(toy_story) is None
