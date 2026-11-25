"""Tests for moviematch.recommender."""
from __future__ import annotations

from moviematch.recommender import recommend, recommend_with_min_rating, title_to_id


def test_title_to_id(small_catalogue) -> None:
    assert title_to_id(small_catalogue)['Alien (1979)'] == 4


def test_recommend_unknown_title_returns_empty(small_catalogue, small_graph) -> None:
    assert recommend('Not A Real Movie (2099)', small_graph, small_catalogue) == []


def test_recommend_returns_at_most_five(small_catalogue, small_graph) -> None:
    assert len(recommend('Toy Story (1995)', small_graph, small_catalogue)) <= 5


def test_recommend_never_includes_searched_movie(small_catalogue, small_graph) -> None:
    results = recommend_with_min_rating('Toy Story (1995)', small_graph, small_catalogue, 0.0)
    assert 'Toy Story (1995)' not in [movie.title for movie, _ in results]


def test_min_rating_filters_results(small_catalogue, small_graph) -> None:
    results = recommend_with_min_rating('Toy Story (1995)', small_graph, small_catalogue, 4.0)
    assert [movie.title for movie, _ in results] == ['Finding Nemo (2003)']


def test_min_rating_too_high_returns_empty(small_catalogue, small_graph) -> None:
    assert recommend_with_min_rating('Toy Story (1995)', small_graph, small_catalogue, 5.0) == []
