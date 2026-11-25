"""Tests for moviematch.data_loader: title cleaning and loading the real dataset."""
from __future__ import annotations

import pytest

from moviematch.data_loader import _normalize_movie_title, load_data


@pytest.mark.parametrize(('raw', 'expected'), [
    ('Toy Story (1995)', 'Toy Story (1995)'),
    ('Matrix, The (1999)', 'The Matrix (1999)'),
    ('Usual Suspects, The (1995)', 'The Usual Suspects (1995)'),
    ('Shawshank Redemption, The (1994)', 'The Shawshank Redemption (1994)'),
    # Commas that are not followed by an article must be left alone.
    ('Crouching Tiger, Hidden Dragon (Wo hu cang long) (2000)',
     'Crouching Tiger, Hidden Dragon (Wo hu cang long) (2000)'),
    # Articles inside alternate-language titles are fixed too.
    ("Amelie (Fabuleux destin d'Amélie Poulain, Le) (2001)", "Amelie (Le Fabuleux destin d'Amélie Poulain) (2001)"),
])
def test_normalize_movie_title(raw: str, expected: str) -> None:
    assert _normalize_movie_title(raw) == expected


@pytest.fixture(scope='module')
def movies():
    return load_data()


def test_load_data_filters_rarely_rated_movies(movies) -> None:
    assert movies
    assert all(movie.rating_count >= 10 for movie in movies.values())


def test_loaded_movies_have_valid_ratings(movies) -> None:
    assert all(0.0 <= movie.avg_rating <= 5.0 for movie in movies.values())


def test_loaded_movies_have_imdb_links(movies) -> None:
    toy_story = movies[1]
    assert toy_story.title == 'Toy Story (1995)'
    assert toy_story.imdb_id == '0114709'


def test_loaded_movies_have_tmdb_ids(movies) -> None:
    assert movies[1].tmdb_id == '862'
