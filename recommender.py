from __future__ import annotations
from movie import Movie
from graph import MovieGraph
from bst import BSTNode


MIN_NUM_RATINGS = 10
MAX_CANDIDATES = 50
TOP_N = 5


def find_movie_by_title(movies: dict[int, Movie], title: str) -> Movie | None:
    """Return the movie with exactly matching title, ignoring case."""
    target = title.strip().lower()

    for movie in movies.values():
        if movie.title.lower() == target:
            return movie

    return None


def get_candidate_movies(graph: MovieGraph, movie_id: int, min_rating: float) -> list[tuple[Movie, float]]:
    """Return candidate movies connected to the given movie."""
    neighbors = graph.get_neighbors(movie_id)
    candidates = []

    for neighbor_id, sim_score in neighbors.items():
        movie = graph.get_movie(neighbor_id)

        if movie.num_ratings >= MIN_NUM_RATINGS and movie.avg_rating >= min_rating:
            candidates.append((movie, sim_score))

    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[:MAX_CANDIDATES]


def sort_candidates(candidates: list[tuple[Movie, float]]) -> list[Movie]:
    """Return candidate movies sorted from highest to lowest rating using a BST."""
    if candidates == []:
        return []

    root = BSTNode(candidates[0][0])

    for movie, _ in candidates[1:]:
        root.insert(movie)

    return root.reverse_inorder()


def recommend_movies(graph: MovieGraph,
                     movies: dict[int, Movie],
                     title: str,
                     min_rating: float) -> list[tuple[str, float, int]]:
    """Return the top recommendations for the given movie title."""
    target_movie = find_movie_by_title(movies, title)

    if target_movie is None:
        return []

    candidates = get_candidate_movies(graph, target_movie.movie_id, min_rating)
    sorted_movies = sort_candidates(candidates)

    results = []
    for movie in sorted_movies[:TOP_N]:
        results.append((movie.title, movie.avg_rating, movie.num_ratings))

    return results
