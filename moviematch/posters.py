"""Project 2: MovieMatch: posters.py

This module downloads movie poster images from The Movie Database (TMDB).

TMDB needs a free API key. Get one at https://www.themoviedb.org/settings/api
and set it as an environment variable before running MovieMatch:

    export TMDB_API_KEY=your_key_here

If there is no key, or there is no internet connection, the functions here
return None and MovieMatch simply shows the cards without posters.

Copyright (c) 2026 <Capucine, Mavi, Syaikha, Tamima>
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from moviematch.data_loader import Movie

MOVIE_URL = 'https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={api_key}'
IMAGE_URL = 'https://image.tmdb.org/t/p/w92{poster_path}'  # w92 = 92 pixels wide
TIMEOUT_SECONDS = 3

# Posters already downloaded this session, so each one is only fetched once.
# Maps tmdb_id to the image bytes (or None if the movie has no poster).
_poster_cache: dict[str, bytes | None] = {}


def _download(url: str) -> bytes:
    """Return the body of the web page at url."""
    with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
        return response.read()


def get_poster(movie: Movie) -> bytes | None:
    """Return the poster image for movie as JPEG bytes, or None if it can't be found.

    This needs the TMDB_API_KEY environment variable to be set.
    """
    api_key = os.environ.get('TMDB_API_KEY', '')
    if api_key == '' or movie.tmdb_id == '':
        return None

    if movie.tmdb_id in _poster_cache:
        return _poster_cache[movie.tmdb_id]

    try:
        details = json.loads(_download(MOVIE_URL.format(tmdb_id=movie.tmdb_id, api_key=api_key)))
        poster_path = details.get('poster_path')
        if poster_path:
            poster = _download(IMAGE_URL.format(poster_path=poster_path))
        else:
            poster = None
    except (urllib.error.URLError, TimeoutError, ValueError):
        # no internet, bad key, or an unexpected reply: just skip the poster
        return None

    _poster_cache[movie.tmdb_id] = poster
    return poster


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    import python_ta

    python_ta.check_all(config={
        'extra-imports': ['json', 'os', 'urllib.error', 'urllib.request', 'moviematch.data_loader'],
        'allowed-io': ['_download'],
        'max-line-length': 120,
    })
