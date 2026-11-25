"""Tests for moviematch.graph: similarity scores and graph construction."""
from __future__ import annotations

import pytest

from moviematch.graph import WeightedGraph, combined_similarity, overlap_similarity
from tests.conftest import make_movie


class TestOverlapSimilarity:
    def test_identical_sets(self) -> None:
        assert overlap_similarity({'a', 'b'}, {'a', 'b'}) == 1.0

    def test_disjoint_sets(self) -> None:
        assert overlap_similarity({'a'}, {'b'}) == 0.0

    def test_partial_overlap(self) -> None:
        assert overlap_similarity({'a', 'b'}, {'b', 'c'}) == pytest.approx(1 / 3)

    def test_both_empty_is_zero_not_error(self) -> None:
        assert overlap_similarity(set(), set()) == 0.0

    def test_is_symmetric(self) -> None:
        assert overlap_similarity({'a'}, {'a', 'b', 'c'}) == overlap_similarity({'a', 'b', 'c'}, {'a'})


class TestCombinedSimilarity:
    def test_identical_movies_score_one(self) -> None:
        m1 = make_movie(1, 'A (2000)', {'Drama'}, {'sad'}, {1})
        m2 = make_movie(2, 'B (2000)', {'Drama'}, {'sad'}, {1})
        assert combined_similarity(m1, m2) == 1.0

    def test_weights_are_20_30_50(self) -> None:
        genre_only = combined_similarity(make_movie(1, 'A (2000)', {'Drama'}), make_movie(2, 'B (2000)', {'Drama'}))
        tags_only = combined_similarity(make_movie(1, 'A (2000)', tags={'x'}), make_movie(2, 'B (2000)', tags={'x'}))
        users_only = combined_similarity(make_movie(1, 'A (2000)', high_raters={7}),
                                         make_movie(2, 'B (2000)', high_raters={7}))
        assert (genre_only, tags_only, users_only) == (0.2, 0.3, 0.5)

    def test_score_is_between_zero_and_one(self, small_catalogue) -> None:
        for m1 in small_catalogue.values():
            for m2 in small_catalogue.values():
                assert 0.0 <= combined_similarity(m1, m2) <= 1.0


class TestWeightedGraph:
    def test_edges_are_undirected(self) -> None:
        graph = WeightedGraph()
        m1, m2 = make_movie(1, 'A (2000)'), make_movie(2, 'B (2000)')
        graph.add_vertex(m1)
        graph.add_vertex(m2)
        graph.add_edge(1, 2, 0.5)
        assert graph.get_neighbours(1) == [(m2, 0.5)]
        assert graph.get_neighbours(2) == [(m1, 0.5)]

    def test_neighbours_sorted_by_score(self, small_graph) -> None:
        scores = [score for _, score in small_graph.get_neighbours(1)]
        assert scores == sorted(scores, reverse=True)

    def test_dissimilar_movies_not_connected(self, small_graph) -> None:
        # Alien shares nothing with the Pixar films, so it should have no edges.
        assert small_graph.get_neighbours(4) == []

    def test_most_similar_movie_ranked_first(self, small_graph) -> None:
        best_match, _ = small_graph.get_neighbours(1)[0]
        assert best_match.title == 'Toy Story 2 (1999)'


class TestShortestPath:
    def _chain_graph(self) -> WeightedGraph:
        """A -- B -- C -- D, plus a weak shortcut-free side branch B -- E."""
        graph = WeightedGraph()
        for i, name in enumerate('ABCDE', start=1):
            graph.add_vertex(make_movie(i, f'{name} (2000)'))
        graph.add_edge(1, 2, 0.5)
        graph.add_edge(2, 3, 0.5)
        graph.add_edge(3, 4, 0.5)
        graph.add_edge(2, 5, 0.3)
        return graph

    def test_path_includes_both_ends(self) -> None:
        path = self._chain_graph().shortest_path(1, 4)
        assert [m.title[0] for m in path] == ['A', 'B', 'C', 'D']

    def test_path_to_itself(self) -> None:
        assert [m.movie_id for m in self._chain_graph().shortest_path(3, 3)] == [3]

    def test_no_path_returns_empty_list(self, small_graph) -> None:
        # Alien is not connected to the Pixar films
        assert small_graph.shortest_path(1, 4) == []

    def test_prefers_stronger_edges_on_ties(self) -> None:
        graph = WeightedGraph()
        for i in range(1, 5):
            graph.add_vertex(make_movie(i, f'M{i} (2000)'))
        # two paths of length 2 from 1 to 4: through 2 (weak) or through 3 (strong)
        graph.add_edge(1, 2, 0.2)
        graph.add_edge(2, 4, 0.2)
        graph.add_edge(1, 3, 0.9)
        graph.add_edge(3, 4, 0.9)
        assert [m.movie_id for m in graph.shortest_path(1, 4)] == [1, 3, 4]
