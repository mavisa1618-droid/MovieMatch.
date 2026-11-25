"""Tests for moviematch.recommender."""
from __future__ import annotations

from moviematch.recommender import find_bridge, recommend, recommend_with_min_rating, title_to_id


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


def test_find_bridge_directly_connected_adds_common_neighbour(small_catalogue, small_graph) -> None:
    path = find_bridge('Toy Story (1995)', 'Toy Story 2 (1999)', small_graph, small_catalogue)
    assert [m.title for m in path] == ['Toy Story (1995)', 'Finding Nemo (2003)', 'Toy Story 2 (1999)']


def test_find_bridge_not_connected(small_catalogue, small_graph) -> None:
    assert find_bridge('Toy Story (1995)', 'Alien (1979)', small_graph, small_catalogue) == []


def test_find_bridge_unknown_or_same_title(small_catalogue, small_graph) -> None:
    assert find_bridge('Toy Story (1995)', 'Nope (2099)', small_graph, small_catalogue) == []
    assert find_bridge('Toy Story (1995)', 'Toy Story (1995)', small_graph, small_catalogue) == []
