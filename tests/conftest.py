"""Shared fixtures for the MovieMatch test suite."""
from __future__ import annotations

import pytest

from moviematch.data_loader import Movie
from moviematch.graph import WeightedGraph, build_from_movies


def make_movie(movie_id: int, title: str, genres: set[str] = frozenset(), tags: set[str] = frozenset(),
               high_raters: set[int] = frozenset(), avg_rating: float = 4.0) -> Movie:
    """Return a Movie with the given attributes (a small helper to keep tests readable)."""
    movie = Movie(movie_id, title)
    movie.genres = set(genres)
    movie.tags = set(tags)
    movie.high_raters = set(high_raters)
    movie.avg_rating = avg_rating
    movie.rating_count = 50
    return movie


@pytest.fixture
def small_catalogue() -> dict[int, Movie]:
    """A tiny hand-made catalogue where the expected similarities are easy to reason about."""
    movies = [
        make_movie(1, 'Toy Story (1995)', {'Animation', 'Comedy'}, {'pixar'}, {1, 2, 3}, 3.9),
        make_movie(2, 'Toy Story 2 (1999)', {'Animation', 'Comedy'}, {'pixar'}, {1, 2, 3}, 3.8),
        make_movie(3, 'Finding Nemo (2003)', {'Animation', 'Comedy'}, {'pixar'}, {1, 4}, 4.2),
        make_movie(4, 'Alien (1979)', {'Horror', 'Sci-Fi'}, {'space'}, {9}, 4.0),
    ]
    return {movie.movie_id: movie for movie in movies}


@pytest.fixture
def small_graph(small_catalogue: dict[int, Movie]) -> WeightedGraph:
    """The similarity graph built from small_catalogue."""
    return build_from_movies(small_catalogue)
